"""O harness pergunta ao flow qual nó do grafo praticar e o que a memória guarda."""

import pytest

from claude_agent_voice.flow.controller import Action, Mode
from claude_agent_voice.flow.harness import (
    FlowSession,
    HarnessStep,
    SkillGraph,
    SkillMemory,
    SkillNode,
)


def _graph() -> SkillGraph:
    return SkillGraph(
        (
            SkillNode("rascunho", 0.20, harder=("revisao",)),
            SkillNode("revisao", 0.52, easier=("rascunho",), harder=("argumento",)),
            SkillNode("argumento", 0.82, easier=("revisao",)),
        )
    )


def _step(node: str, **overrides) -> HarnessStep:
    base = dict(
        attention_node=node,
        goal_clarity=0.9,
        feedback=1.0,
        meaning=0.8,
        uninterrupted_steps=6,
    )
    base.update(overrides)
    return HarnessStep(**base)


def test_boredom_walks_to_the_harder_neighbor():
    session = FlowSession(_graph(), SkillMemory(estimates={"rascunho": 0.70}))
    advice = session.advise(_step("rascunho"))
    assert advice.decision.action is Action.RAISE
    assert advice.suggested_node == "revisao"
    assert advice.missing_edge is None


def test_anxiety_walks_to_the_easier_neighbor():
    session = FlowSession(_graph(), SkillMemory(estimates={"argumento": 0.30}))
    advice = session.advise(_step("argumento"))
    assert advice.decision.action is Action.PLAN
    assert advice.suggested_node == "revisao"


def test_missing_edge_asks_for_graph_work_instead_of_inventing_a_node():
    graph = SkillGraph((SkillNode("sozinho", 0.90),))
    session = FlowSession(graph, SkillMemory(estimates={"sozinho": 0.20}))
    advice = session.advise(_step("sozinho"))
    assert advice.decision.action is Action.PLAN
    assert advice.suggested_node == "sozinho"
    assert advice.missing_edge == "easier"
    assert "não tem um nó mais fácil" in advice.note


def test_matched_node_stays_and_can_enter_flow():
    session = FlowSession(_graph(), SkillMemory(estimates={"revisao": 0.50}))
    advice = session.advise(_step("revisao"))
    assert advice.decision.mode is Mode.FLOW
    assert advice.suggested_node == "revisao"
    assert advice.decision.meta_budget < 0.2


def test_attention_on_a_different_node_than_progress_blocks_flow():
    session = FlowSession(_graph(), SkillMemory(estimates={"revisao": 0.50}))
    advice = session.advise(_step("revisao", progress_node="rascunho"))
    assert advice.decision.in_flow is False
    assert advice.decision.mode is Mode.RAMP


def test_memory_grows_faster_inside_the_band():
    memory = SkillMemory()
    inside = FlowSession(_graph(), memory)
    advice = inside.advise(_step("revisao"))
    assert advice.decision.zone.value == "channel"
    after_inside = inside.learn("revisao", success=True, advice=advice)

    outside_memory = SkillMemory()
    outside = FlowSession(_graph(), outside_memory)
    bored = outside.advise(_step("rascunho"))
    after_outside = outside.learn("rascunho", success=True, advice=bored)

    assert after_inside - 0.50 > after_outside - 0.50


def test_stop_does_not_walk_the_graph():
    session = FlowSession(_graph(), SkillMemory(estimates={"revisao": 0.50}))
    advice = session.advise(_step("revisao", stop_requested=True))
    assert advice.decision.action is Action.STOP
    assert advice.suggested_node == "revisao"


def test_graph_rejects_a_dangling_neighbor():
    with pytest.raises(ValueError):
        SkillGraph((SkillNode("a", 0.4, harder=("nao-existe",)),))
