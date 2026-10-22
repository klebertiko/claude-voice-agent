"""Roda o estudo simulado e imprime o relatório.

    uv run python -m claude_agent_voice.flow
"""

from __future__ import annotations

import json
from pathlib import Path

from .sim import format_report, run_study


def main() -> None:
    summaries = run_study(episodes=40, seed0=1000)
    print(format_report(summaries))
    out = Path("/tmp/flow_report.json")
    out.write_text(
        json.dumps([item.as_dict() for item in summaries], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\njson: {out}")


if __name__ == "__main__":
    main()
