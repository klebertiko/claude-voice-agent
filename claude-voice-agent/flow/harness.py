"""Encaixe do flow no harness de agentes.

O harness é o ciclo que conduz o agente: olha o grafo de skills, escolhe
um nó, executa, guarda o resultado na memória. Este módulo é o que esse
ciclo pergunta antes de cada passo.

Não conhece a Lilith nem áudio. O grafo, a memória e o passo vêm de fora.
Quando o grafo não tem o vizinho que o regime pede, a resposta diz isso
em vez de inventar um nó — engenharia do grafo continua com quem o mantém.

A memória é a capacidade. Ela sobe mais quando o acerto acontece com a
dificuldade perto do que o agente já pratica, que é o efeito de
aprendizagem do flow no vídeo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .controller import (
    Action,
    Decision,
    FlowConfig,
    FlowController,
    Observation,
    Zone,
)


def _clamp(value: float, lo: float = 0.05, hi: float = 0.95) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class SkillNode:
    """Um nó do grafo: uma skill com a dificuldade de praticá-la agora.

    ``easier`` e ``harder`` são ids de vizinhos. Descer é decompor.
    Subir é aumentar o corte. Lista vazia significa que o grafo ainda
    não tem esse caminho.
    """

    id: str
    difficulty: float
    easier: tuple[str, ...] = ()
    harder: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillGraph:
    nodes: tuple[SkillNode, ...]

    def __post_init__(self) -> None:
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("id de skill repetido no grafo")
        known = set(ids)
        for node in self.nodes:
            missing = [link for link in (*node.easier, *node.harder) if link not in known]
            if missing:
                raise ValueError(f"vizinho inexistente em {node.id}: {missing}")

    def get(self, node_id: str) -> SkillNode:
        for node in self.nodes:
            if node.id == node_id:
                return node
        raise KeyError(node_id)


@dataclass
class SkillMemory:
    """Quanto o agente já pratica cada skill. Ausência usa o prior 0,50."""

    estimates: dict[str, float] = field(default_factory=dict)
    prior: float = 0.50

    def estimate(self, node_id: str) -> float:
        return self.estimates.get(node_id, self.prior)

    def record(self, node_id: str, success: bool, *, in_band: bool) -> float:
        """Atualiza a capacidade depois de um passo real.

        Acerto dentro da faixa sobe mais. Erro fora da faixa desce mais.
        Acerto entediado quase não ensina.
        """

        current = self.estimate(node_id)
        if success and in_band:
            delta = 0.05
        elif success:
            delta = 0.02
        elif in_band:
            delta = -0.03
        else:
            delta = -0.08
        updated = _clamp(current + delta)
        self.estimates[node_id] = updated
        return updated


@dataclass(frozen=True)
class HarnessStep:
    """O que o harness já sabe neste passo, sem olhar para dentro do modelo."""

    attention_node: str
    goal_clarity: float
    feedback: float
    meaning: float
    uninterrupted_steps: int
    goal_done: bool = False
    stop_requested: bool = False
    safety_ok: bool = True
    # Nó que de fato moveu a meta no passo anterior. Vazio no primeiro passo.
    progress_node: str = ""


@dataclass(frozen=True)
class HarnessAdvice:
    decision: Decision
    node_id: str
    suggested_node: str
    missing_edge: str | None
    note: str


def _alignment(step: HarnessStep) -> float:
    if not step.progress_node or step.progress_node == step.attention_node:
        return 0.94
    return 0.15


class FlowSession:
    """Uma sessão de trabalho. A histerese da sincronia vive aqui."""

    def __init__(
        self,
        graph: SkillGraph,
        memory: SkillMemory | None = None,
        config: FlowConfig | None = None,
    ) -> None:
        self.graph = graph
        self.memory = memory or SkillMemory()
        self.controller = FlowController(config)

    def advise(self, step: HarnessStep) -> HarnessAdvice:
        node = self.graph.get(step.attention_node)
        decision = self.controller.decide(
            Observation(
                skill=self.memory.estimate(node.id),
                challenge=node.difficulty,
                goal_clarity=step.goal_clarity,
                feedback=step.feedback,
                meaning=step.meaning,
                attention_alignment=_alignment(step),
                uninterrupted_steps=step.uninterrupted_steps,
                goal_done=step.goal_done,
                stop_requested=step.stop_requested,
                safety_ok=step.safety_ok,
            )
        )
        suggested, missing = self._move(node, decision.action)
        return HarnessAdvice(
            decision=decision,
            node_id=node.id,
            suggested_node=suggested,
            missing_edge=missing,
            note=_note(node, suggested, missing, decision),
        )

    def learn(self, node_id: str, success: bool, advice: HarnessAdvice) -> float:
        """Grava o passo na memória. A faixa é a zona que o conselho usou."""

        return self.memory.record(
            node_id,
            success,
            in_band=advice.decision.zone is Zone.CHANNEL,
        )

    def _move(self, node: SkillNode, action: Action) -> tuple[str, str | None]:
        if action is Action.PLAN:
            if node.easier:
                return node.easier[0], None
            return node.id, "easier"
        if action is Action.RAISE:
            if node.harder:
                return node.harder[0], None
            return node.id, "harder"
        return node.id, None


def _note(node: SkillNode, suggested: str, missing: str | None, decision: Decision) -> str:
    if missing == "easier":
        return f"A skill {node.id} está difícil demais e o grafo não tem um nó mais fácil ligado a ela."
    if missing == "harder":
        return f"A skill {node.id} está fácil demais e o grafo não tem um nó mais difícil ligado a ela."
    if suggested != node.id:
        return f"Sair de {node.id} e praticar {suggested}."
    if decision.action is Action.SEEK_GOAL:
        return "Pedir o critério de pronto antes de escolher skill."
    if decision.action is Action.STOP:
        return "Encerrar. O grafo não deve continuar sozinho."
    if decision.action is Action.HOLD:
        return "Segurar. A segurança está aberta."
    if decision.in_flow:
        return f"Praticar {node.id} sem reabrir o plano."
    return f"Continuar em {node.id}."
