"""Escala curta de flow (Rheinberg) com proxies observáveis.

O vídeo descreve o questionário pós-atividade, notas de 1 a 7:

- eu estava totalmente concentrado
- tudo aconteceu de forma fluida e automática
- eu não percebi o tempo passar
- eu estava completamente envolvido

Um agente não responde questionário. Cada item vira uma razão medida no
episódio. Isto não valida o sentimento; valida o padrão operacional.
"""

from __future__ import annotations

from dataclasses import dataclass

from .controller import Action, Mode


@dataclass(frozen=True)
class StepTrace:
    mode: Mode
    action: Action
    meta_budget: float
    progress: float
    interrupted: bool


@dataclass(frozen=True)
class FlowScale:
    """Quatro itens em 1–7 e a média, no formato da escala curta."""

    concentration: float
    automaticity: float
    timelessness: float
    absorption: float
    score: float

    def as_dict(self) -> dict[str, float]:
        return {
            "concentration": round(self.concentration, 3),
            "automaticity": round(self.automaticity, 3),
            "timelessness": round(self.timelessness, 3),
            "absorption": round(self.absorption, 3),
            "score": round(self.score, 3),
        }


def _to7(fraction: float) -> float:
    fraction = max(0.0, min(1.0, fraction))
    return 1.0 + 6.0 * fraction


def flow_short_scale(steps: list[StepTrace]) -> FlowScale:
    if not steps:
        return FlowScale(1.0, 1.0, 1.0, 1.0, 1.0)

    engaged = [
        step for step in steps
        if not step.interrupted and step.action in {Action.ACT, Action.PLAN, Action.RAISE}
    ]
    concentration = _to7(len(engaged) / len(steps))

    flow_steps = [step for step in steps if step.mode is Mode.FLOW]
    if flow_steps:
        automatic = sum(
            1 for step in flow_steps
            if step.action is Action.ACT and step.meta_budget <= 0.25
        ) / len(flow_steps)
        # Pouca autocrítica enquanto produz = o relógio deixou de ser monitorado.
        clock = sum(step.meta_budget for step in flow_steps) / len(flow_steps)
        timeless = _to7(1.0 - clock)
        automaticity = _to7(automatic)
    else:
        automaticity = 1.0
        timeless = 1.0

    absorption = _to7(len(flow_steps) / len(steps))
    score = (concentration + automaticity + timeless + absorption) / 4.0
    return FlowScale(
        concentration=concentration,
        automaticity=automaticity,
        timelessness=timeless,
        absorption=absorption,
        score=score,
    )
