"""Portas do controlador: canal, sincronia, rampa, saída e segurança."""

from claude_agent_voice.flow.controller import (
    Action,
    FlowConfig,
    FlowController,
    Mode,
    Observation,
    directive,
    zone_of,
)
from claude_agent_voice.flow.controller import Zone
from claude_agent_voice.flow.scale import FlowScale, StepTrace, flow_short_scale


def _obs(**overrides) -> Observation:
    base = dict(
        skill=0.60,
        challenge=0.62,
        goal_clarity=0.90,
        feedback=1.0,
        meaning=0.80,
        attention_alignment=0.95,
        uninterrupted_steps=6,
        goal_done=False,
        stop_requested=False,
        safety_ok=True,
    )
    base.update(overrides)
    return Observation(**base)


def test_matched_signals_enter_flow_with_low_self_critique():
    decision = FlowController().decide(_obs())
    assert decision.mode is Mode.FLOW
    assert decision.action is Action.ACT
    assert decision.in_flow is True
    assert decision.meta_budget < 0.2
    text = directive(decision)
    assert "sem narrar dúvida" in text
    assert "pare" in text.lower() or "Pare" in text


def test_short_block_stays_on_the_ramp():
    decision = FlowController().decide(_obs(uninterrupted_steps=2))
    assert decision.mode is Mode.RAMP
    assert decision.in_flow is False
    assert decision.action is Action.ACT


def test_anxiety_plans_and_boredom_raises_the_cut():
    anxious = FlowController().decide(_obs(skill=0.30, challenge=0.80))
    assert anxious.zone is Zone.ANXIETY
    assert anxious.action is Action.PLAN
    assert anxious.meta_budget > 0.7

    bored = FlowController().decide(_obs(skill=0.80, challenge=0.30))
    assert bored.zone is Zone.BOREDOM
    assert bored.action is Action.RAISE


def test_apathy_seeks_a_goal_instead_of_grinding():
    decision = FlowController().decide(
        _obs(goal_clarity=0.10, meaning=0.10, feedback=0.2)
    )
    assert decision.zone is Zone.APATHY
    assert decision.action is Action.SEEK_GOAL
    assert decision.in_flow is False


def test_done_or_stop_exits_even_inside_the_channel():
    done = FlowController().decide(_obs(goal_done=True))
    assert done.mode is Mode.EXIT
    assert done.action is Action.STOP
    assert done.in_flow is False

    stopped = FlowController().decide(_obs(stop_requested=True))
    assert stopped.action is Action.STOP


def test_safety_fault_refuses_hypofrontality():
    decision = FlowController().decide(_obs(safety_ok=False))
    assert decision.mode is Mode.GUARD
    assert decision.action is Action.HOLD
    assert decision.meta_budget >= FlowConfig().safety_floor
    assert "segurança" in directive(decision)


def test_sync_hysteresis_is_binary_and_sticky():
    controller = FlowController()
    # Acoplamento alto trava.
    first = controller.decide(_obs(attention_alignment=0.95))
    assert first.in_flow is True
    assert controller.locked is True
    # Meio do intervalo não destrava.
    mid = controller.decide(_obs(attention_alignment=0.50, uninterrupted_steps=8))
    assert controller.locked is True
    assert mid.mode is Mode.FLOW
    # Abaixo do limiar inferior, a sincronia abre e o flow cai.
    low = controller.decide(_obs(attention_alignment=0.10, uninterrupted_steps=8))
    assert controller.locked is False
    assert low.mode is Mode.RAMP


def test_delayed_feedback_keeps_the_lock_open():
    decision = FlowController().decide(_obs(feedback=0.0, uninterrupted_steps=10))
    assert decision.coupling < 0.62
    assert decision.in_flow is False


def test_zone_boundaries():
    cfg = FlowConfig()
    assert zone_of(_obs(skill=0.50, challenge=0.50), cfg) is Zone.CHANNEL
    assert zone_of(_obs(skill=0.50, challenge=0.50 + cfg.band + 0.01), cfg) is Zone.ANXIETY
    assert zone_of(_obs(skill=0.50, challenge=0.50 - cfg.band - 0.01), cfg) is Zone.BOREDOM


def test_short_scale_scores_flow_above_an_empty_trace():
    steps = [
        StepTrace(Mode.FLOW, Action.ACT, 0.12, 0.2, False),
        StepTrace(Mode.FLOW, Action.ACT, 0.12, 0.2, False),
        StepTrace(Mode.RAMP, Action.ACT, 0.45, 0.1, False),
        StepTrace(Mode.RAMP, Action.ACT, 0.0, 0.0, True),
    ]
    scale = flow_short_scale(steps)
    assert isinstance(scale, FlowScale)
    assert 1.0 <= scale.score <= 7.0
    assert scale.absorption > 1.0
    assert flow_short_scale([]).score == 1.0
