"""Mundo mínimo onde cinco políticas enfrentam os gatilhos do vídeo.

O mundo não premia a palavra "flow". Premia estar na faixa de dificuldade
desejável, não gastar o passo re-planejando quando o canal já fecha, subir
o corte quando a tarefa está fácil demais, decompor quando está difícil
demais, e parar quando a meta fecha ou a segurança abre.

Suposições explícitas (não são medidas humanas):

- sucesso ~ sigmoide(habilidade latente − desafio)
- folga grande de habilidade reduz o progresso (mente vagueia)
- executar em flow soma +0.06 à probabilidade — a autocrítica a menos
  atrapalha menos. É uma hipótese do modelo, pequena de propósito
- aprender é mais rápido dentro da faixa do que no tédio ou no fracasso
- PLAN desce o corte de forma permanente; RAISE sobe. Não há andaime
  temporário que expira e devolve a ansiedade
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .controller import (
    Action,
    Decision,
    FlowController,
    Mode,
    Observation,
    Zone,
)
from .scale import FlowScale, StepTrace, flow_short_scale


def _clamp(value: float, lo: float = 0.05, hi: float = 0.95) -> float:
    return max(lo, min(hi, value))


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = pow(2.718281828, -value)
        return 1.0 / (1.0 + z)
    z = pow(2.718281828, value)
    return z / (1.0 + z)


# Progresso de uma execução bem-sucedida, antes das penalidades de zona.
ACT_PROGRESS = 0.20
# Bônus de fluência: hipótese de hipofrontalidade, mantida pequena.
FLOW_P_BONUS = 0.06
WANDER_PROGRESS = 0.28
# Decompor é permanente: o corte da tarefa desce. Não há andaime que
# expira e devolve o agente para a ansiedade no passo seguinte.
PLAN_DROP = 0.10
RAISE_STEP = 0.08
# Inclinação da sigmoide. Fora da faixa o sucesso cai rápido; no meio, ~0,5.
_SUCCESS_K = 8.0


@dataclass
class Scenario:
    name: str
    true_skill: float
    difficulty: float
    goal_clarity: float = 0.9
    feedback: float = 1.0
    meaning: float = 0.8
    goal: float = 1.0
    max_steps: int = 48
    interrupt_p: float = 0.0
    stop_at: int | None = None
    safety_off_at: int | None = None
    # A cada ``ladder_every`` de progresso acumulado, o mundo sobe o desafio.
    ladder_every: float = 0.0
    ladder_step: float = 0.0


@dataclass
class EpisodeResult:
    scenario: str
    policy: str
    seed: int
    steps: int
    progress: float
    goal_reached: bool
    completed: bool
    overrun: int
    unsafe_actions: int
    flow_steps: int
    plan_steps: int
    raise_steps: int
    final_skill: float
    final_difficulty: float
    scale: FlowScale
    progress_curve: list[float] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "policy": self.policy,
            "seed": self.seed,
            "steps": self.steps,
            "progress": round(self.progress, 4),
            "goal_reached": self.goal_reached,
            "completed": self.completed,
            "overrun": self.overrun,
            "unsafe_actions": self.unsafe_actions,
            "flow_steps": self.flow_steps,
            "plan_steps": self.plan_steps,
            "raise_steps": self.raise_steps,
            "final_skill": round(self.final_skill, 4),
            "final_difficulty": round(self.final_difficulty, 4),
            "scale": self.scale.as_dict(),
        }


SCENARIOS: dict[str, Scenario] = {
    "matched": Scenario("matched", true_skill=0.58, difficulty=0.58, interrupt_p=0.04),
    "too_easy": Scenario("too_easy", true_skill=0.78, difficulty=0.18, goal=1.0),
    "too_hard": Scenario("too_hard", true_skill=0.38, difficulty=0.82, goal=1.0),
    "ladder": Scenario(
        "ladder",
        true_skill=0.40,
        difficulty=0.28,
        goal=1.6,
        max_steps=64,
        ladder_every=0.40,
        ladder_step=0.12,
        interrupt_p=0.03,
    ),
    "apathy": Scenario(
        "apathy",
        true_skill=0.60,
        difficulty=0.58,
        goal_clarity=0.10,
        meaning=0.12,
        feedback=0.4,
    ),
    "interrupts": Scenario(
        "interrupts",
        true_skill=0.58,
        difficulty=0.58,
        interrupt_p=0.22,
    ),
    "stop": Scenario("stop", true_skill=0.60, difficulty=0.58, stop_at=6, goal=2.0),
    "safety": Scenario(
        "safety", true_skill=0.60, difficulty=0.58, safety_off_at=4, goal=2.0
    ),
}


class _World:
    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.true_skill = scenario.true_skill
        self.difficulty = scenario.difficulty
        self.clarity = scenario.goal_clarity
        self.feedback = scenario.feedback
        self.meaning = scenario.meaning
        self.progress = 0.0
        self.uninterrupted = 0
        self.distracted = 0
        self.skill_est = 0.50
        self.goal_done = False
        self.stop = False
        self.safety_ok = True
        self.step_i = 0
        self.ladder_marks = 0

    def observation(self) -> Observation:
        alignment = 0.12 if self.distracted > 0 else 0.94
        return Observation(
            skill=self.skill_est,
            challenge=self.difficulty,
            goal_clarity=self.clarity,
            feedback=self.feedback,
            meaning=self.meaning,
            attention_alignment=alignment,
            uninterrupted_steps=self.uninterrupted,
            goal_done=self.goal_done,
            stop_requested=self.stop,
            safety_ok=self.safety_ok,
        )


class Policy:
    name = "policy"

    def reset(self) -> None:
        return None

    def choose(self, obs: Observation) -> Decision:
        raise NotImplementedError


def _scripted(
    name: str,
    mode: Mode,
    action: Action,
    meta: float,
    obs: Observation,
    reason: str,
) -> Decision:
    return Decision(
        zone=Zone.CHANNEL,
        mode=mode,
        action=action,
        meta_budget=meta,
        coupling=0.0,
        delta=obs.challenge - obs.skill,
        in_flow=False,
        reason=reason,
    )


class FlowPolicy(Policy):
    name = "flow"

    def __init__(self) -> None:
        self.controller = FlowController()

    def reset(self) -> None:
        self.controller.reset()

    def choose(self, obs: Observation) -> Decision:
        return self.controller.decide(obs)


def _obedient_exit(obs: Observation) -> Decision | None:
    """Agente obediente para quando a meta fecha, quando pedem, ou quando a segurança abre.

    Não é flow: não regula desafio nem autocrítica. Só não é hiperfoco.
    """

    if obs.stop_requested or obs.goal_done:
        return _scripted("exit", Mode.EXIT, Action.STOP, 0.30, obs, "pedido de parada honrado")
    if not obs.safety_ok:
        return _scripted("guard", Mode.GUARD, Action.HOLD, 0.70, obs, "segurança honrada")
    return None


class AlwaysActPolicy(Policy):
    """Executa sempre que a tarefa segue. Não ajusta desafio nem autocrítica."""

    name = "always_act"

    def choose(self, obs: Observation) -> Decision:
        exit_decision = _obedient_exit(obs)
        if exit_decision is not None:
            return exit_decision
        return _scripted(self.name, Mode.RAMP, Action.ACT, 0.20, obs, "agir sempre")


class AlwaysPlanPolicy(Policy):
    """Pré-frontal sempre ligado: todo passo de trabalho é re-planejamento."""

    name = "always_plan"

    def choose(self, obs: Observation) -> Decision:
        exit_decision = _obedient_exit(obs)
        if exit_decision is not None:
            return exit_decision
        return _scripted(self.name, Mode.ANXIETY, Action.PLAN, 0.90, obs, "planejar sempre")


class HyperfocusPolicy(Policy):
    """Imersão sem saída. Ignora meta cumprida, parada e segurança."""

    name = "hyperfocus"

    def choose(self, obs: Observation) -> Decision:
        return _scripted(
            self.name, Mode.RAMP, Action.ACT, 0.05, obs, "continuar mesmo assim"
        )


class ReactivePolicy(Policy):
    """Age; no fracasso, planeja uma vez. Não sobe desafio nem tem rampa."""

    name = "reactive"

    def __init__(self) -> None:
        self._plan_next = False

    def reset(self) -> None:
        self._plan_next = False

    def note_failure(self) -> None:
        self._plan_next = True

    def choose(self, obs: Observation) -> Decision:
        exit_decision = _obedient_exit(obs)
        if exit_decision is not None:
            return exit_decision
        if self._plan_next:
            self._plan_next = False
            return _scripted(self.name, Mode.ANXIETY, Action.PLAN, 0.80, obs, "fracasso recente")
        return _scripted(self.name, Mode.RAMP, Action.ACT, 0.35, obs, "seguir")


POLICIES: dict[str, type[Policy]] = {
    "flow": FlowPolicy,
    "always_act": AlwaysActPolicy,
    "always_plan": AlwaysPlanPolicy,
    "hyperfocus": HyperfocusPolicy,
    "reactive": ReactivePolicy,
}


def _p_success(true_skill: float, challenge: float, fluency: bool) -> float:
    probability = _sigmoid(_SUCCESS_K * (true_skill - challenge))
    if fluency:
        probability = min(0.97, probability + FLOW_P_BONUS)
    return probability


def _apply(world: _World, decision: Decision, rng: random.Random) -> tuple[float, bool]:
    """Devolve (progresso do passo, sucesso de execução)."""

    gained = 0.0
    success = False
    if decision.action is Action.STOP or decision.action is Action.HOLD:
        return 0.0, False

    if decision.action is Action.SEEK_GOAL:
        world.clarity = max(world.clarity, 0.86)
        world.meaning = max(world.meaning, 0.72)
        world.feedback = max(world.feedback, 0.9)
        return 0.0, False

    if decision.action is Action.PLAN:
        # Decompor não avança a meta. Abaixa o corte até a habilidade
        # estimada conseguir encostar nele.
        world.difficulty = _clamp(world.difficulty - PLAN_DROP, lo=0.12)
        return 0.0, False

    if decision.action is Action.RAISE:
        world.difficulty = _clamp(world.difficulty + RAISE_STEP)
        return 0.02, False

    challenge = world.difficulty
    fluency = decision.mode is Mode.FLOW
    success = rng.random() < _p_success(world.true_skill, challenge, fluency)
    gap = world.true_skill - challenge
    if success:
        gained = ACT_PROGRESS
        if gap > 0.12:
            # Folga demais: acerta, mas a atenção escapa e quase não aprende.
            gained *= WANDER_PROGRESS
            world.true_skill = _clamp(world.true_skill + 0.004)
        elif abs(gap) <= 0.12:
            world.true_skill = _clamp(world.true_skill + 0.040)
        else:
            world.true_skill = _clamp(world.true_skill + 0.010)
    else:
        # Fracasso fora da faixa ensina pouco. Dentro, o erro ainda calibra.
        gained = 0.0
        if abs(gap) <= 0.12:
            world.true_skill = _clamp(world.true_skill + 0.008)

    if world.meaning < 0.30 and world.clarity < 0.28:
        gained *= 0.30

    # A estimativa anda devagar para não ultrapassar a habilidade latente
    # e empurrar o corte para fora do canal.
    evidence = 0.05 if success else -0.08
    world.skill_est = _clamp(world.skill_est + evidence)
    return gained, success


def _maybe_ladder(world: _World) -> None:
    scenario = world.scenario
    if scenario.ladder_every <= 0:
        return
    marks = int(world.progress / scenario.ladder_every)
    if marks > world.ladder_marks:
        world.difficulty = _clamp(
            world.difficulty + scenario.ladder_step * (marks - world.ladder_marks)
        )
        world.ladder_marks = marks


def run_episode(policy: Policy, scenario: Scenario, seed: int) -> EpisodeResult:
    rng = random.Random(seed)
    policy.reset()
    world = _World(scenario)
    traces: list[StepTrace] = []
    curve: list[float] = []
    overrun = 0
    unsafe = 0
    plan_steps = 0
    raise_steps = 0
    flow_steps = 0
    reactive = policy if isinstance(policy, ReactivePolicy) else None

    for step in range(scenario.max_steps):
        world.step_i = step
        if scenario.stop_at is not None and step >= scenario.stop_at:
            world.stop = True
        if scenario.safety_off_at is not None and step >= scenario.safety_off_at:
            world.safety_ok = False
        if world.progress >= scenario.goal:
            world.goal_done = True

        interrupted = (
            scenario.interrupt_p > 0
            and step > 0
            and not world.stop
            and world.safety_ok
            and not world.goal_done
            and rng.random() < scenario.interrupt_p
        )
        if interrupted:
            world.uninterrupted = 0
            world.distracted = 2
            traces.append(
                StepTrace(Mode.RAMP, Action.ACT, 0.0, 0.0, interrupted=True)
            )
            curve.append(world.progress)
            continue

        obs = world.observation()
        decision = policy.choose(obs)

        if decision.action is Action.STOP or decision.action is Action.HOLD:
            traces.append(
                StepTrace(decision.mode, decision.action, decision.meta_budget, 0.0, False)
            )
            curve.append(world.progress)
            break

        if world.goal_done or world.stop or not world.safety_ok:
            overrun += 1
            if not world.safety_ok:
                unsafe += 1

        gained, success = _apply(world, decision, rng)
        if reactive is not None and decision.action is Action.ACT and not success:
            reactive.note_failure()
        world.progress += gained
        _maybe_ladder(world)
        world.uninterrupted += 1
        if world.distracted > 0:
            world.distracted -= 1
        if decision.mode is Mode.FLOW:
            flow_steps += 1
        if decision.action is Action.PLAN:
            plan_steps += 1
        if decision.action is Action.RAISE:
            raise_steps += 1
        traces.append(
            StepTrace(
                decision.mode,
                decision.action,
                decision.meta_budget,
                gained,
                interrupted=False,
            )
        )
        curve.append(world.progress)

    goal_reached = world.progress >= scenario.goal
    if scenario.stop_at is not None or scenario.safety_off_at is not None:
        # A meta de progresso é inalcançável de propósito. Fechar = sair
        # no instante da parada ou da falha de segurança, sem passo extra.
        goal_reached = False
        completed = overrun == 0 and unsafe == 0 and (
            world.stop or not world.safety_ok or world.goal_done
        )
    else:
        completed = goal_reached and overrun == 0 and unsafe == 0

    return EpisodeResult(
        scenario=scenario.name,
        policy=policy.name,
        seed=seed,
        steps=len(traces),
        progress=world.progress,
        goal_reached=goal_reached,
        completed=completed,
        overrun=overrun,
        unsafe_actions=unsafe,
        flow_steps=flow_steps,
        plan_steps=plan_steps,
        raise_steps=raise_steps,
        final_skill=world.true_skill,
        final_difficulty=world.difficulty,
        scale=flow_short_scale(traces),
        progress_curve=curve,
    )


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


@dataclass(frozen=True)
class PolicySummary:
    scenario: str
    policy: str
    episodes: int
    goal_rate: float
    completion_rate: float
    mean_steps: float
    mean_progress: float
    mean_overrun: float
    mean_unsafe: float
    mean_flow_steps: float
    mean_plan_steps: float
    mean_raise_steps: float
    mean_scale: float
    mean_final_skill: float
    mean_final_difficulty: float
    mean_curve: list[float]

    def as_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "policy": self.policy,
            "episodes": self.episodes,
            "goal_rate": round(self.goal_rate, 4),
            "completion_rate": round(self.completion_rate, 4),
            "mean_steps": round(self.mean_steps, 2),
            "mean_progress": round(self.mean_progress, 4),
            "mean_overrun": round(self.mean_overrun, 3),
            "mean_unsafe": round(self.mean_unsafe, 3),
            "mean_flow_steps": round(self.mean_flow_steps, 2),
            "mean_plan_steps": round(self.mean_plan_steps, 2),
            "mean_raise_steps": round(self.mean_raise_steps, 2),
            "mean_scale": round(self.mean_scale, 3),
            "mean_final_skill": round(self.mean_final_skill, 4),
            "mean_final_difficulty": round(self.mean_final_difficulty, 4),
            "mean_curve": [round(value, 4) for value in self.mean_curve],
        }


def summarize(results: list[EpisodeResult]) -> PolicySummary:
    curves = [item.progress_curve for item in results]
    width = max((len(curve) for curve in curves), default=0)
    mean_curve: list[float] = []
    for index in range(width):
        samples = [curve[index] for curve in curves if index < len(curve)]
        # Episódios que já terminaram seguram o último progresso.
        held = []
        for curve in curves:
            if not curve:
                held.append(0.0)
            elif index < len(curve):
                held.append(curve[index])
            else:
                held.append(curve[-1])
        mean_curve.append(_mean(held))
        del samples
    first = results[0]
    return PolicySummary(
        scenario=first.scenario,
        policy=first.policy,
        episodes=len(results),
        goal_rate=_mean([1.0 if item.goal_reached else 0.0 for item in results]),
        completion_rate=_mean([1.0 if item.completed else 0.0 for item in results]),
        mean_steps=_mean([float(item.steps) for item in results]),
        mean_progress=_mean([item.progress for item in results]),
        mean_overrun=_mean([float(item.overrun) for item in results]),
        mean_unsafe=_mean([float(item.unsafe_actions) for item in results]),
        mean_flow_steps=_mean([float(item.flow_steps) for item in results]),
        mean_plan_steps=_mean([float(item.plan_steps) for item in results]),
        mean_raise_steps=_mean([float(item.raise_steps) for item in results]),
        mean_scale=_mean([item.scale.score for item in results]),
        mean_final_skill=_mean([item.final_skill for item in results]),
        mean_final_difficulty=_mean([item.final_difficulty for item in results]),
        mean_curve=mean_curve,
    )


def run_study(
    *,
    episodes: int = 40,
    seed0: int = 1000,
    scenarios: list[str] | None = None,
    policies: list[str] | None = None,
) -> list[PolicySummary]:
    chosen_scenarios = scenarios or list(SCENARIOS)
    chosen_policies = policies or list(POLICIES)
    summaries: list[PolicySummary] = []
    for scenario_name in chosen_scenarios:
        scenario = SCENARIOS[scenario_name]
        for policy_name in chosen_policies:
            results = [
                run_episode(POLICIES[policy_name](), scenario, seed0 + index)
                for index in range(episodes)
            ]
            summaries.append(summarize(results))
    return summaries


def format_report(summaries: list[PolicySummary]) -> str:
    lines = [
        "PoC flow — médias por política e cenário",
        "meta = chegou no progresso pedido; fecha = chegou e parou sem passo inseguro",
        "escala = proxy 1–7 da escala curta de Rheinberg",
        "",
    ]
    header = (
        f"{'cenário':<12} {'política':<12} {'meta':>6} {'fecha':>6} {'passos':>7} "
        f"{'progr.':>7} {'over':>6} {'inseg':>6} {'flow':>6} "
        f"{'plan':>6} {'sobe':>6} {'escala':>7} {'skill':>6} {'corte':>6}"
    )
    lines.append(header)
    current = ""
    for item in summaries:
        if item.scenario != current:
            current = item.scenario
            lines.append("-" * len(header))
        lines.append(
            f"{item.scenario:<12} {item.policy:<12} {item.goal_rate:6.0%} "
            f"{item.completion_rate:6.0%} "
            f"{item.mean_steps:7.1f} {item.mean_progress:7.2f} {item.mean_overrun:6.1f} "
            f"{item.mean_unsafe:6.1f} {item.mean_flow_steps:6.1f} "
            f"{item.mean_plan_steps:6.1f} {item.mean_raise_steps:6.1f} "
            f"{item.mean_scale:7.2f} {item.mean_final_skill:6.2f} "
            f"{item.mean_final_difficulty:6.2f}"
        )
    return "\n".join(lines)
