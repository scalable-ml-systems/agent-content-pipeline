from __future__ import annotations

import json
import sys

from app.pipeline import run_pipeline


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: python -m app.main "your topic here"')
        return 1

    topic = " ".join(sys.argv[1:]).strip()
    if not topic:
        print("Error: topic must be non-empty.")
        return 1

    state = run_pipeline(topic)

    final_output = state.get("final_output", {})
    print(json.dumps(final_output, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
