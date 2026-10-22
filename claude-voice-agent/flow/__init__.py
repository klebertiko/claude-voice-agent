"""Controlador de flow para agentes — tradução operacional do modelo do vídeo.

Não reproduz neuroquímica. Implementa as variáveis de controle que o relato
de Csikszentmihalyi, a hipofrontalidade transitória e a sincronização
atenção–recompensa deixam observáveis: canal desafio/habilidade, orçamento
de autocrítica, acoplamento com histerese e saída voluntária (flow ≠ hiperfoco).
"""

from .controller import (
    Action,
    Decision,
    FlowConfig,
    FlowController,
    Mode,
    Observation,
    Zone,
    directive,
)
from .harness import (
    FlowSession,
    HarnessAdvice,
    HarnessStep,
    SkillGraph,
    SkillMemory,
    SkillNode,
)
from .scale import FlowScale, flow_short_scale
from .sim import POLICIES, SCENARIOS, run_study

__all__ = [
    "Action",
    "Decision",
    "FlowConfig",
    "FlowController",
    "FlowScale",
    "FlowSession",
    "HarnessAdvice",
    "HarnessStep",
    "Mode",
    "Observation",
    "POLICIES",
    "SCENARIOS",
    "SkillGraph",
    "SkillMemory",
    "SkillNode",
    "Zone",
    "directive",
    "flow_short_scale",
    "run_study",
]
