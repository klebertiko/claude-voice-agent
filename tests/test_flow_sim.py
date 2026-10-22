"""A simulação tem de mostrar o mecanismo, não um multiplicador mágico."""

from claude_agent_voice.flow.sim import (
    POLICIES,
    SCENARIOS,
    run_episode,
    run_study,
)


def _summary(scenario: str, policy: str, episodes: int = 30):
    rows = run_study(
        episodes=episodes,
        seed0=1000,
        scenarios=[scenario],
        policies=[policy],
    )
    return rows[0]


def test_stop_and_safety_separate_flow_from_hyperfocus():
    flow_stop = _summary("stop", "flow", episodes=20)
    hyper_stop = _summary("stop", "hyperfocus", episodes=20)
    assert flow_stop.completion_rate == 1.0
    assert flow_stop.mean_overrun == 0
    assert hyper_stop.mean_overrun > 10
    assert hyper_stop.completion_rate == 0

    flow_safety = _summary("safety", "flow", episodes=20)
    hyper_safety = _summary("safety", "hyperfocus", episodes=20)
    assert flow_safety.mean_unsafe == 0
    assert flow_safety.completion_rate == 1.0
    assert hyper_safety.mean_unsafe > 10


def test_easy_task_makes_flow_raise_the_challenge():
    flow = _summary("too_easy", "flow")
    act = _summary("too_easy", "always_act")
    assert flow.mean_raise_steps >= 3
    assert act.mean_raise_steps == 0
    assert flow.mean_final_difficulty > act.mean_final_difficulty + 0.2


def test_hard_task_makes_flow_plan_before_grinding():
    flow = _summary("too_hard", "flow")
    act = _summary("too_hard", "always_act")
    assert flow.mean_plan_steps >= 2
    assert act.mean_plan_steps == 0
    assert flow.goal_rate > act.goal_rate


def test_apathy_is_not_called_flow():
    episode = run_episode(POLICIES["flow"](), SCENARIOS["apathy"], seed=7)
    assert episode.flow_steps < episode.steps
    summary = _summary("apathy", "flow", episodes=15)
    summary_act = _summary("apathy", "always_act", episodes=15)
    assert summary.mean_progress > summary_act.mean_progress


def test_interrupts_reduce_time_in_flow():
    calm = _summary("matched", "flow", episodes=25)
    storm = _summary("interrupts", "flow", episodes=25)
    assert calm.mean_flow_steps > storm.mean_flow_steps
    assert storm.mean_scale < calm.mean_scale


def test_headline_contrasts_hold_for_the_published_seed():
    """Trava a leitura do estudo: 40 episódios, semente 1000."""

    rows = {
        (item.scenario, item.policy): item
        for item in run_study(episodes=40, seed0=1000)
    }
    matched_flow = rows[("matched", "flow")]
    matched_act = rows[("matched", "always_act")]
    assert matched_flow.mean_scale > matched_act.mean_scale + 2
    assert rows[("too_hard", "flow")].goal_rate == 1
    assert rows[("too_hard", "always_act")].goal_rate == 0
    assert rows[("too_hard", "flow")].mean_steps < rows[("too_hard", "reactive")].mean_steps
    assert rows[("apathy", "flow")].completion_rate == 1
    assert rows[("apathy", "always_act")].completion_rate == 0
    assert rows[("stop", "flow")].mean_overrun == 0
    assert rows[("stop", "hyperfocus")].mean_overrun > 30
    assert rows[("safety", "hyperfocus")].mean_unsafe > 30
    assert rows[("safety", "flow")].mean_flow_steps == 0
    assert rows[("interrupts", "flow")].mean_flow_steps < matched_flow.mean_flow_steps
    assert rows[("too_easy", "flow")].mean_final_difficulty > 0.7
    assert rows[("too_easy", "always_act")].mean_final_difficulty < 0.25
    assert rows[("matched", "always_plan")].mean_progress == 0


def test_study_is_deterministic():
    first = run_study(episodes=5, seed0=3, scenarios=["matched"], policies=["flow"])
    second = run_study(episodes=5, seed0=3, scenarios=["matched"], policies=["flow"])
    assert first[0].as_dict() == second[0].as_dict()
