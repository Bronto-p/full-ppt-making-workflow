#!/usr/bin/env python3
"""Validate reference_mapping.md before full production."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


SLIDE_HEADING_RE = re.compile(r"^##\s+(?:Slide\s+(\d+)|第\s*(\d+)\s*页)\b", re.IGNORECASE)
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\((<[^>]+>|[^)]+)\)")
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def split_table_row(line: str) -> list[str]:
    return [normalize_cell(cell) for cell in line.strip().strip("|").split("|")]


def is_divider(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def section_tables(content: str) -> dict[str, list[dict[str, str]]]:
    section = ""
    header: list[str] | None = None
    tables: dict[str, list[dict[str, str]]] = {}
    for line in content.splitlines():
        if line.startswith("## "):
            section = line.lstrip("#").strip().lower()
            header = None
            continue
        if not TABLE_ROW_RE.match(line):
            continue
        cells = split_table_row(line)
        if is_divider(cells):
            continue
        if header is None:
            header = [cell.lower() for cell in cells]
            continue
        row = {header[index]: cells[index] if index < len(cells) else "" for index in range(len(header))}
        tables.setdefault(section, []).append(row)
    return tables


def slide_numbers_from_plan(path: Path | None) -> set[int]:
    if path is None:
        return set()
    numbers: set[int] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = SLIDE_HEADING_RE.match(line)
        if match:
            numbers.add(int(match.group(1) or match.group(2)))
    return numbers


def clean_path_token(value: str) -> str:
    value = value.strip().strip("`").strip()
    if value.startswith("<") and value.endswith(">"):
        value = value[1:-1].strip()
    else:
        title_match = re.match(r"(.+?)\s+(['\"])[^'\"]*\2\s*$", value)
        if title_match:
            value = title_match.group(1).strip()
    return value


def image_paths_from_cell(value: str) -> list[str]:
    paths: list[str] = []
    for match in MARKDOWN_IMAGE_RE.finditer(value):
        paths.append(clean_path_token(match.group(1)))
    without_markdown = MARKDOWN_IMAGE_RE.sub("", value)
    for token in re.split(r"(?:<br\s*/?>|[,;，；])", without_markdown, flags=re.IGNORECASE):
        token = clean_path_token(token)
        if not token or token.lower() in {"n/a", "none", "-", "blocked", "待定"}:
            continue
        if re.search(r"\.(png|jpe?g|webp|bmp|gif|tiff?)$", token, re.IGNORECASE):
            paths.append(token)
    unique: list[str] = []
    for path in paths:
        if path not in unique:
            unique.append(path)
    return unique


def resolve_path(project_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def load_latest_approved_hashes(log_path: Path | None, stage: str) -> dict[str, str]:
    if log_path is None or not log_path.exists():
        return {}
    data = json.loads(log_path.read_text(encoding="utf-8"))
    approvals = [item for item in data.get("approvals", []) if item.get("stage") in {stage, "sample"}]
    if not approvals:
        return {}
    latest = approvals[-1]
    return {
        str(item.get("path")): str(item.get("sha256"))
        for item in latest.get("artifacts", [])
        if item.get("path") and item.get("sha256")
    }


def validate(args: argparse.Namespace) -> tuple[list[str], dict[str, Any]]:
    mapping_path = Path(args.reference_mapping).expanduser().resolve()
    project_root = Path(args.project_root).expanduser().resolve() if args.project_root else mapping_path.parent
    content = mapping_path.read_text(encoding="utf-8")
    tables = section_tables(content)
    ref_rows = tables.get("reference images", [])
    mapping_rows = tables.get("slide to reference mapping", [])
    problems: list[str] = []
    if not ref_rows:
        problems.append("Missing `## Reference Images` table.")
    if not mapping_rows:
        problems.append("Missing `## Slide To Reference Mapping` table.")

    reference_files: dict[str, list[str]] = {}
    for row in ref_rows:
        ref_id = row.get("reference id") or row.get("id") or row.get("reference")
        file_cell = row.get("file") or row.get("reference image") or ""
        if ref_id:
            reference_files[ref_id] = image_paths_from_cell(file_cell)

    expected_slides = slide_numbers_from_plan(Path(args.slide_plan).expanduser().resolve() if args.slide_plan else None)
    seen_slides: set[int] = set()
    normalized_rows: list[dict[str, Any]] = []
    image_hashes: dict[str, str] = {}
    for index, row in enumerate(mapping_rows, start=1):
        slide_cell = row.get("slide") or ""
        match = re.search(r"\d+", slide_cell)
        if not match:
            problems.append(f"Mapping row {index}: missing slide number.")
            continue
        slide_number = int(match.group(0))
        if slide_number in seen_slides:
            problems.append(f"Slide {slide_number}: duplicate mapping row.")
        seen_slides.add(slide_number)
        row_text = " ".join(row.values()).lower()
        if "blocked" in row_text or "missing" in row_text or "待定" in row_text:
            problems.append(f"Slide {slide_number}: mapping is blocked or unresolved.")
        ref_id = row.get("reference id") or ""
        image_values = image_paths_from_cell(row.get("reference image") or "")
        if not image_values and ref_id in reference_files:
            image_values = reference_files[ref_id]
        if not image_values:
            problems.append(f"Slide {slide_number}: no reference image path.")
        resolved_images: list[dict[str, Any]] = []
        for value in image_values:
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", value):
                problems.append(f"Slide {slide_number}: reference image is not a local file: {value}")
                continue
            path = resolve_path(project_root, value)
            if not path.exists() or not path.is_file():
                problems.append(f"Slide {slide_number}: missing reference image: {value}")
                continue
            if "origin_image" in path.parts:
                problems.append(f"Slide {slide_number}: reference image must not come from origin_image/: {value}")
            digest = sha256_file(path)
            rel = path.relative_to(project_root).as_posix() if path.is_relative_to(project_root) else str(path)
            image_hashes[rel] = digest
            resolved_images.append({"path": rel, "sha256": digest})
        normalized_rows.append(
            {
                "slide": slide_number,
                "page_type": row.get("page type"),
                "reference_id": ref_id,
                "reference_images": resolved_images,
                "notes": row.get("notes"),
            }
        )

    for number in sorted(expected_slides - seen_slides):
        problems.append(f"Slide {number}: missing mapping row.")
    if expected_slides and len(seen_slides - expected_slides) > 0:
        for number in sorted(seen_slides - expected_slides):
            problems.append(f"Slide {number}: mapping row has no matching slide in slide_plan.md.")

    approved_hashes = load_latest_approved_hashes(
        Path(args.approval_log).expanduser().resolve() if args.approval_log else None,
        "reference_mapping",
    )
    if args.approval_log:
        rel_mapping = mapping_path.relative_to(project_root).as_posix() if mapping_path.is_relative_to(project_root) else str(mapping_path)
        current_mapping_hash = sha256_file(mapping_path)
        if approved_hashes.get(rel_mapping) != current_mapping_hash:
            problems.append("reference_mapping.md is missing from latest approval or changed after approval.")

    normalized = {
        "schema_version": 1,
        "reference_mapping": str(mapping_path),
        "project_root": str(project_root),
        "slides": sorted(normalized_rows, key=lambda item: item["slide"]),
        "image_hashes": image_hashes,
        "approval_checked": bool(args.approval_log),
    }
    return problems, normalized


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference_mapping")
    parser.add_argument("--slide-plan")
    parser.add_argument("--project-root")
    parser.add_argument("--approval-log")
    parser.add_argument("--write-normalized-json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    problems, normalized = validate(args)
    if args.write_normalized_json:
        out = Path(args.write_normalized_json).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems, **normalized}, ensure_ascii=False, indent=2))
    elif problems:
        print("Reference mapping validation failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
    else:
        print(f"Reference mapping validation passed for {len(normalized['slides'])} slide(s).")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
