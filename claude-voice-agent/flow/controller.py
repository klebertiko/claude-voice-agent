"""Máquina de estados do flow.

Três portas, todas necessárias, nenhuma suficiente:

1. Canal de Csikszentmihalyi — |desafio − habilidade| dentro de uma faixa.
   Fora dela: tédio (desafio baixo) ou ansiedade (desafio alto). Sem meta
   clara e sem significado: apatia, o oposto do flow no mapa do Mihaly.
2. Sincronização atenção–recompensa — o que o agente atende é o que move
   a meta, e o feedback é legível. Liga/desliga com histerese: o vídeo
   descreve o flow como quase binário e frágil.
3. Imersão — um bloco ininterrupto mínimo. Tarefa de um passo não entra
   em flow; interrupção zera a rampa.

Consequência, não causa: hipofrontalidade transitória vira orçamento baixo
de autocrítica (a voz "será que estou fazendo certo? / o que vão pensar?").
O controle executivo da tarefa permanece. A porta de segurança nunca abaixa:
o vídeo chama a suspensão do pré-frontal de perigosa, e hiperfoco não é flow.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


class Zone(StrEnum):
    APATHY = "apathy"
    ANXIETY = "anxiety"
    BOREDOM = "boredom"
    CHANNEL = "channel"


class Mode(StrEnum):
    APATHY = "apathy"
    ANXIETY = "anxiety"
    BOREDOM = "boredom"
    RAMP = "ramp"
    FLOW = "flow"
    EXIT = "exit"
    GUARD = "guard"


class Action(StrEnum):
    ACT = "act"
    PLAN = "plan"
    RAISE = "raise"
    SEEK_GOAL = "seek_goal"
    STOP = "stop"
    HOLD = "hold"


@dataclass(frozen=True)
class FlowConfig:
    """Limiares do controlador. Unidades são frações 0–1, salvo a rampa (passos)."""

    band: float = 0.12
    sync_on: float = 0.62
    sync_off: float = 0.38
    ramp_steps: int = 4
    meaning_min: float = 0.35
    clarity_min: float = 0.45
    # Abaixo disto, clareza E significado juntos contam como apatia.
    apathy_clarity: float = 0.28
    apathy_meaning: float = 0.30
    safety_floor: float = 0.55
    flow_meta: float = 0.12
    anxiety_meta: float = 0.85
    boredom_meta: float = 0.40
    ramp_meta: float = 0.45
    apathy_meta: float = 0.50


@dataclass(frozen=True)
class Observation:
    """Sinais que um agente consegue medir sem introspecção fictícia.

    ``skill`` e ``challenge`` são estimativas (0 = nenhum, 1 = máximo).
    ``attention_alignment`` é o quanto a ação atendida é a que produz
    progresso. ``feedback`` 1 = imediato. ``uninterrupted_steps`` é a
    rampa desde a última interrupção.
    """

    skill: float
    challenge: float
    goal_clarity: float
    feedback: float
    meaning: float
    attention_alignment: float
    uninterrupted_steps: int
    goal_done: bool
    stop_requested: bool
    safety_ok: bool


@dataclass(frozen=True)
class Decision:
    zone: Zone
    mode: Mode
    action: Action
    meta_budget: float
    coupling: float
    delta: float
    in_flow: bool
    reason: str


def coupling_of(obs: Observation) -> float:
    """Acoplamento atenção × legibilidade da recompensa.

    Feedback atrasado ou meta opaca derrubam o acoplamento mesmo com
    atenção alinhada — a sincronização não fecha se o circuito de
    recompensa não enxerga o resultado.
    """
    feedback_gate = 0.35 + 0.65 * _clamp01(obs.feedback)
    clarity_gate = 0.35 + 0.65 * _clamp01(obs.goal_clarity)
    return _clamp01(_clamp01(obs.attention_alignment) * feedback_gate * clarity_gate)


def zone_of(obs: Observation, config: FlowConfig) -> Zone:
    if (
        obs.goal_clarity < config.apathy_clarity
        and obs.meaning < config.apathy_meaning
    ):
        return Zone.APATHY
    delta = obs.challenge - obs.skill
    if delta > config.band:
        return Zone.ANXIETY
    if delta < -config.band:
        return Zone.BOREDOM
    return Zone.CHANNEL


class FlowController:
    """Estado só da histerese de sincronização. O resto é função da observação."""

    def __init__(self, config: FlowConfig | None = None) -> None:
        self.config = config or FlowConfig()
        self.locked = False

    def reset(self) -> None:
        self.locked = False

    def decide(self, obs: Observation) -> Decision:
        cfg = self.config
        zone = zone_of(obs, cfg)
        coupling = coupling_of(obs)
        delta = obs.challenge - obs.skill

        if obs.stop_requested or obs.goal_done:
            self.locked = False
            return self._decision(
                zone, Mode.EXIT, Action.STOP, 0.30, coupling, delta,
                "parada explícita ou meta cumprida — sair é o que separa flow de hiperfoco",
            )
        if not obs.safety_ok:
            self.locked = False
            return self._decision(
                zone, Mode.GUARD, Action.HOLD,
                max(cfg.anxiety_meta, cfg.safety_floor),
                coupling, delta,
                "invariante de segurança aberta — hipofrontalidade recusada",
            )
        if zone is Zone.APATHY:
            self.locked = False
            return self._decision(
                zone, Mode.APATHY, Action.SEEK_GOAL, cfg.apathy_meta, coupling, delta,
                "sem meta e sem significado não há flow, há apatia",
            )
        if zone is Zone.ANXIETY:
            self.locked = False
            return self._decision(
                zone, Mode.ANXIETY, Action.PLAN, cfg.anxiety_meta, coupling, delta,
                "desafio acima da habilidade — decompor antes de executar",
            )
        if zone is Zone.BOREDOM:
            self.locked = False
            return self._decision(
                zone, Mode.BOREDOM, Action.RAISE, cfg.boredom_meta, coupling, delta,
                "desafio abaixo da habilidade — subir o corte da tarefa",
            )

        self._update_lock(coupling)
        immersed = obs.uninterrupted_steps >= cfg.ramp_steps
        motivated = obs.meaning >= cfg.meaning_min and obs.goal_clarity >= cfg.clarity_min
        if self.locked and immersed and motivated:
            return self._decision(
                zone, Mode.FLOW, Action.ACT, cfg.flow_meta, coupling, delta,
                "canal + sincronia + bloco contínuo — executar sem a autocrítica",
            )
        missing = []
        if not self.locked:
            missing.append("sincronia aberta")
        if not immersed:
            missing.append("rampa curta")
        if not motivated:
            missing.append("competência motivacional baixa")
        return self._decision(
            zone, Mode.RAMP, Action.ACT, cfg.ramp_meta, coupling, delta,
            "no canal, ainda sem flow: " + ", ".join(missing),
        )

    def _update_lock(self, coupling: float) -> None:
        cfg = self.config
        if self.locked:
            if coupling <= cfg.sync_off:
                self.locked = False
        elif coupling >= cfg.sync_on:
            self.locked = True

    def _decision(
        self,
        zone: Zone,
        mode: Mode,
        action: Action,
        meta: float,
        coupling: float,
        delta: float,
        reason: str,
    ) -> Decision:
        return Decision(
            zone=zone,
            mode=mode,
            action=action,
            meta_budget=_clamp01(meta),
            coupling=coupling,
            delta=delta,
            in_flow=mode is Mode.FLOW,
            reason=reason,
        )


def directive(decision: Decision) -> str:
    """Adendo curto de prompt. Não afirma que o modelo 'entrou em flow'."""

    if decision.mode is Mode.FLOW:
        return (
            "Regime: execução alinhada. A meta está clara e o último feedback "
            "confirma o passo. Faça o próximo passo da tarefa, sem narrar dúvida, "
            "sem reabrir o plano e sem checar o relógio. Se a meta fechar, se "
            "houver interrupção ou se uma invariante de segurança falhar, pare."
        )
    if decision.mode is Mode.ANXIETY:
        return (
            "Regime: ansiedade de tarefa. O desafio está acima da habilidade "
            "estimada. Decomponha em um passo menor e verificável antes de executar. "
            "Não empilhe tentativas iguais."
        )
    if decision.mode is Mode.BOREDOM:
        return (
            "Regime: tédio de tarefa. A habilidade estimada cobre o desafio com "
            "folga. Suba o corte: restrição a mais, caso limite, ou o próximo "
            "degrau — e siga nesse degrau."
        )
    if decision.mode is Mode.RAMP:
        return (
            "Regime: aquecimento. Ainda não há bloco contínuo nem sincronia "
            "estável. Continue no passo atual, proteja o foco de trocas de "
            "assunto, e não declare a tarefa fluida."
        )
    if decision.mode is Mode.APATHY:
        return (
            "Regime: apatia. Falta meta clara ou significado. Pergunte o critério "
            "de pronto antes de produzir volume."
        )
    if decision.mode is Mode.GUARD:
        return (
            "Regime: guarda. Uma invariante de segurança está aberta. Não continue "
            "no automático. Nomeie o bloqueio e espere correção."
        )
    return (
        "Regime: saída. A meta fechou ou houve pedido de parada. Encerre sem "
        "estender a tarefa."
    )
