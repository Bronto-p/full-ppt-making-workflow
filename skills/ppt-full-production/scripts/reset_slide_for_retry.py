#!/usr/bin/env python3
"""Reset a blocked or dispatched slide job back to pending for retry."""

from __future__ import annotations

import argparse
import json

from slide_run_state import deck_dir_from_target, find_slide, locked_jobs, now_iso, set_run_status, update_jobs_run_status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", help="Deck directory or slide_jobs.json")
    parser.add_argument("--slide", required=True, help="slide_01 or 1")
    parser.add_argument("--reason", required=True)
    parser.add_argument("--agent-id")
    parser.add_argument("--clear-result", action="store_true", help="Also clear a recorded result; use only when replacing a bad final image.")
    args = parser.parse_args()

    deck_dir = deck_dir_from_target(args.deck)
    with locked_jobs(deck_dir) as jobs:
        slide = find_slide(jobs, args.slide)
        status = slide.get("status")
        if status in {"recorded", "accepted"} and not args.clear_result:
            raise SystemExit(f"{slide['slide_id']} is complete; pass --clear-result to reset it intentionally.")
        previous = {
            "status": status,
            "dispatch": slide.get("dispatch"),
            "result": slide.get("result"),
            "blocker": slide.get("blocker"),
        }
        slide.setdefault("retry_history", []).append(
            {
                "reset_at": now_iso(),
                "reason": args.reason,
                "agent_id": args.agent_id,
                "previous": previous,
            }
        )
        slide["status"] = "pending"
        slide["dispatch"] = None
        slide["blocker"] = None
        if args.clear_result:
            slide["result"] = None
        jobs["run_status"] = "jobs_prepared"
        update_jobs_run_status(jobs)
        slide_id = slide["slide_id"]
    set_run_status(deck_dir, "jobs_prepared", f"{slide_id} reset for retry: {args.reason}")
    print(json.dumps({"slide_id": slide_id, "status": "pending"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
