#!/usr/bin/env python3
"""Append and validate PPT workflow approval checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_log(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "approvals": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("approvals"), list):
        raise SystemExit(f"Invalid approval log schema: {path}")
    return data


def write_log(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def artifact_record(project_root: Path, artifact: str) -> dict[str, Any]:
    path = Path(artifact).expanduser()
    if not path.is_absolute():
        path = project_root / path
    path = path.resolve()
    if not path.exists() or not path.is_file():
        raise SystemExit(f"Approved artifact does not exist: {path}")
    return {
        "path": path.relative_to(project_root).as_posix() if path.is_relative_to(project_root) else str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def latest_approval(log: dict[str, Any], stage: str | None = None) -> dict[str, Any] | None:
    approvals = log.get("approvals", [])
    if stage:
        approvals = [item for item in approvals if item.get("stage") == stage]
    return approvals[-1] if approvals else None


def current_artifact_map(project_root: Path, artifacts: list[str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for artifact in artifacts:
        path = Path(artifact).expanduser()
        if not path.is_absolute():
            path = project_root / path
        path = path.resolve()
        if not path.exists():
            raise SystemExit(f"Artifact is missing: {path}")
        key = path.relative_to(project_root).as_posix() if path.is_relative_to(project_root) else str(path)
        hashes[key] = sha256_file(path)
    return hashes


def cmd_add(args: argparse.Namespace) -> int:
    log_path = Path(args.log).expanduser().resolve()
    project_root = Path(args.project_root or log_path.parent).expanduser().resolve()
    log = read_log(log_path)
    approval = {
        "stage": args.stage,
        "approved_at": args.date or now_iso(),
        "approved_by": args.approved_by,
        "approval_source": args.source,
        "note": args.note,
        "artifacts": [artifact_record(project_root, artifact) for artifact in args.artifact],
    }
    log.setdefault("approvals", []).append(approval)
    log["updated_at"] = now_iso()
    write_log(log_path, log)
    print(json.dumps({"status": "added", "log": str(log_path), "stage": args.stage}, ensure_ascii=False))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    log_path = Path(args.log).expanduser().resolve()
    project_root = Path(args.project_root or log_path.parent).expanduser().resolve()
    if not log_path.exists():
        raise SystemExit(f"Approval log not found: {log_path}")
    log = read_log(log_path)
    approval = latest_approval(log, args.stage)
    if approval is None:
        raise SystemExit(f"No approval checkpoint found{f' for stage {args.stage}' if args.stage else ''}.")
    expected = {
        str(item.get("path")): str(item.get("sha256"))
        for item in approval.get("artifacts", [])
        if item.get("path") and item.get("sha256")
    }
    artifacts = args.artifact or list(expected)
    current = current_artifact_map(project_root, artifacts)
    problems: list[str] = []
    for path, current_hash in current.items():
        approved_hash = expected.get(path)
        if not approved_hash:
            problems.append(f"{path}: not present in latest approval")
        elif approved_hash != current_hash:
            problems.append(f"{path}: hash changed since approval")
    if problems:
        print(json.dumps({"status": "failed", "problems": problems}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(json.dumps({"status": "ok", "stage": approval.get("stage"), "approved_at": approval.get("approved_at")}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="Append an approval checkpoint.")
    add.add_argument("--log", default="approval_log.json")
    add.add_argument("--project-root")
    add.add_argument("--stage", required=True, choices=["plan", "sample", "reference_mapping", "production", "reconstruction"])
    add.add_argument("--approved-by", required=True, help="Example: user-confirmed client approval")
    add.add_argument("--source", default="user")
    add.add_argument("--date")
    add.add_argument("--note")
    add.add_argument("--artifact", action="append", required=True)
    add.set_defaults(func=cmd_add)

    check = subparsers.add_parser("check", help="Verify artifacts still match the latest approval.")
    check.add_argument("--log", default="approval_log.json")
    check.add_argument("--project-root")
    check.add_argument("--stage", choices=["plan", "sample", "reference_mapping", "production", "reconstruction"])
    check.add_argument("--artifact", action="append")
    check.set_defaults(func=cmd_check)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
