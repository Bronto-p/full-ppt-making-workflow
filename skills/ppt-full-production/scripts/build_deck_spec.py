#!/usr/bin/env python3
"""Build a conservative deck_spec.json from approved Markdown workflow artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


SLIDE_HEADING_RE = re.compile(r"^##\s+(?:Slide\s+(\d+)|第\s*(\d+)\s*页)\b[:：]?\s*(.*)$", re.IGNORECASE)
SECTION_RE = re.compile(r"^###\s+(.+?)\s*$")
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\((<[^>]+>|[^)]+)\)")
EMPTY_MARKERS = {"", "-", "none", "n/a", "na", "no", "无", "暂无", "不适用", "已解决"}


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
        if not token or token.lower() in EMPTY_MARKERS | {"blocked", "待定"}:
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


def parse_slides(content: str) -> list[dict[str, Any]]:
    slides: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line_number, line in enumerate(content.splitlines(), start=1):
        match = SLIDE_HEADING_RE.match(line)
        if match:
            if current:
                current["end_line"] = line_number - 1
                slides.append(current)
            current = {
                "number": int(match.group(1) or match.group(2)),
                "heading_title": match.group(3).strip(),
                "start_line": line_number,
                "lines": [],
            }
            continue
        if current is not None:
            current["lines"].append(line)
    if current:
        current["end_line"] = len(content.splitlines())
        slides.append(current)
    return slides


def section_block(slide: dict[str, Any], section_name: str) -> list[str]:
    current: str | None = None
    block: list[str] = []
    for line in slide["lines"]:
        section = SECTION_RE.match(line)
        if section:
            current = section.group(1).strip().lower()
            continue
        if current and section_name.lower() in current:
            block.append(line)
    return block


def field_value(lines: list[str], field: str) -> str:
    pattern = re.compile(rf"^\s*[-*]\s*{re.escape(field)}\s*:\s*(.*)$", re.IGNORECASE)
    for line in lines:
        match = pattern.match(line)
        if match:
            return normalize_cell(match.group(1))
    return ""


def bullet_values(lines: list[str]) -> list[str]:
    values = []
    for line in lines:
        match = re.match(r"^\s*[-*]\s+(.+)$", line)
        if match:
            value = normalize_cell(match.group(1))
            if value.lower() not in EMPTY_MARKERS:
                values.append(value)
    return values


def unresolved_questions(lines: list[str]) -> list[str]:
    values = []
    for value in bullet_values(lines):
        if value.lower() not in EMPTY_MARKERS:
            values.append(value)
    return values


def required_images_from_slide(slide: dict[str, Any], project_root: Path, problems: list[str]) -> list[dict[str, Any]]:
    images = section_block(slide, "Images")
    required: list[dict[str, Any]] = []
    current: dict[str, str] | None = None
    in_required = False
    for line in images:
        if re.match(r"^\s*[-*]\s*Required\s*:", line, re.IGNORECASE):
            in_required = True
            continue
        if re.match(r"^\s*[-*]\s*(Optional|Free image generation/search)\s*:", line, re.IGNORECASE):
            in_required = False
            if current:
                required.append(current)
                current = None
            continue
        if not in_required:
            continue
        match = re.match(r"^\s*[-*]\s*(File|Role|Preservation|Fidelity|Constraints)\s*:\s*(.*)$", line, re.IGNORECASE)
        if not match:
            continue
        key = match.group(1).lower()
        value = normalize_cell(match.group(2))
        if key == "file":
            if current:
                required.append(current)
            current = {"path": value}
        elif current is not None:
            if key == "preservation":
                current["preservation"] = value
            elif key == "fidelity":
                current["fidelity"] = value
            else:
                current[key] = value
    if current:
        required.append(current)

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(required, start=1):
        path_value = item.get("path", "")
        if path_value.lower() in EMPTY_MARKERS:
            continue
        path = resolve_path(project_root, path_value)
        if not path.exists():
            problems.append(f"Slide {slide['number']}: required image does not exist: {path_value}")
            continue
        if not (item.get("role") and (item.get("preservation") or item.get("fidelity") or item.get("constraints"))):
            problems.append(f"Slide {slide['number']}: required image {index} needs role and preservation/fidelity/constraints.")
        normalized.append(
            {
                "path": str(path),
                "role": item.get("role") or "required client image",
                "preservation": item.get("preservation") or item.get("fidelity") or item.get("constraints"),
                "sha256": sha256_file(path),
            }
        )
    return normalized


def parse_mapping(content: str) -> tuple[dict[str, list[str]], dict[int, dict[str, Any]]]:
    section = ""
    header: list[str] | None = None
    reference_files: dict[str, list[str]] = {}
    slide_mapping: dict[int, dict[str, Any]] = {}
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
        if section == "reference images":
            ref_id = row.get("reference id") or row.get("id") or row.get("reference")
            if ref_id:
                reference_files[ref_id] = image_paths_from_cell(row.get("file") or row.get("reference image") or "")
        elif section == "slide to reference mapping":
            slide_cell = row.get("slide") or ""
            match = re.search(r"\d+", slide_cell)
            if match:
                slide_number = int(match.group(0))
                ref_id = row.get("reference id") or ""
                paths = image_paths_from_cell(row.get("reference image") or "")
                if not paths and ref_id in reference_files:
                    paths = reference_files[ref_id]
                slide_mapping[slide_number] = {
                    "page_type": row.get("page type"),
                    "reference_id": ref_id,
                    "reference_image_paths": paths,
                    "notes": row.get("notes"),
                    "raw": row,
                }
    return reference_files, slide_mapping


def approved_hashes(log_path: Path | None) -> dict[str, str]:
    if not log_path or not log_path.exists():
        return {}
    data = json.loads(log_path.read_text(encoding="utf-8"))
    approvals = data.get("approvals", [])
    if not approvals:
        return {}
    latest = approvals[-1]
    return {
        str(item.get("path")): str(item.get("sha256"))
        for item in latest.get("artifacts", [])
        if item.get("path") and item.get("sha256")
    }


def build_spec(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    slide_plan_path = Path(args.slide_plan).expanduser().resolve()
    style_path = Path(args.approved_style_reference).expanduser().resolve()
    mapping_path = Path(args.reference_mapping).expanduser().resolve()
    project_root = Path(args.project_root).expanduser().resolve() if args.project_root else slide_plan_path.parent
    problems: list[str] = []
    for required_path, label in [
        (slide_plan_path, "slide_plan.md"),
        (style_path, "approved_style_reference.md"),
        (mapping_path, "reference_mapping.md"),
    ]:
        if not required_path.exists():
            problems.append(f"Missing {label}: {required_path}")
    if problems:
        return {}, problems

    slide_plan = slide_plan_path.read_text(encoding="utf-8")
    style_markdown = style_path.read_text(encoding="utf-8")
    mapping_markdown = mapping_path.read_text(encoding="utf-8")
    _reference_files, slide_mapping = parse_mapping(mapping_markdown)
    slides = parse_slides(slide_plan)
    if not slides:
        problems.append("slide_plan.md has no slide headings.")

    spec_slides: list[dict[str, Any]] = []
    seen_numbers: set[int] = set()
    for slide in slides:
        number = slide["number"]
        if number in seen_numbers:
            problems.append(f"Slide {number}: duplicate slide number.")
        seen_numbers.add(number)
        text = section_block(slide, "Text")
        questions = unresolved_questions(section_block(slide, "Open Questions"))
        if questions:
            problems.append(f"Slide {number}: unresolved open questions: {'; '.join(questions)}")
        title = field_value(text, "Title") or slide["heading_title"] or f"Slide {number}"
        body_values = [
            value for value in bullet_values(text)
            if not value.lower().startswith(("source:", "rewrite allowed:", "title:", "must preserve:"))
        ]
        mapping = slide_mapping.get(number)
        if not mapping:
            problems.append(f"Slide {number}: no row in reference_mapping.md")
            continue
        reference_images: list[dict[str, Any]] = []
        for path_value in mapping.get("reference_image_paths", []):
            if "blocked" in path_value.lower():
                problems.append(f"Slide {number}: reference image is blocked: {path_value}")
                continue
            path = resolve_path(project_root, path_value)
            if not path.exists():
                problems.append(f"Slide {number}: reference image does not exist: {path_value}")
                continue
            if "origin_image" in path.parts:
                problems.append(f"Slide {number}: reference image must not come from origin_image/: {path_value}")
            reference_images.append(
                {
                    "path": str(path),
                    "role": f"approved reference image {mapping.get('reference_id') or ''}".strip(),
                    "fidelity": "match approved style/layout/page-type guidance only; do not copy unrelated content",
                    "sha256": sha256_file(path),
                }
            )
        if not reference_images:
            problems.append(f"Slide {number}: no usable local reference image.")
        spec_slides.append(
            {
                "number": number,
                "title": title,
                "role": mapping.get("page_type"),
                "intent": field_value(text, "Source"),
                "key_points": body_values,
                "local_context": {
                    "approved_slide_plan_markdown": "\n".join(slide["lines"]).strip(),
                    "reference_mapping_notes": mapping.get("notes"),
                },
                "reference_images": reference_images,
                "required_images": required_images_from_slide(slide, project_root, problems),
                "constraints": [],
            }
        )

    approval_log = Path(args.approval_log).expanduser().resolve() if args.approval_log else None
    hashes = approved_hashes(approval_log)
    if approval_log:
        for path in (slide_plan_path, style_path, mapping_path):
            key = path.relative_to(project_root).as_posix() if path.is_relative_to(project_root) else str(path)
            if hashes.get(key) != sha256_file(path):
                problems.append(f"{key}: missing from latest approval or changed after approval.")

    spec = {
        "schema_version": 1,
        "deck_name": args.deck_name or project_root.name,
        "language": args.language,
        "goal": args.goal,
        "aspect_ratio": args.aspect_ratio,
        "selected_image_backend": args.selected_backend,
        "max_concurrent_slides": args.max_concurrent_slides,
        "source_artifacts": {
            "slide_plan": str(slide_plan_path),
            "approved_style_reference": str(style_path),
            "reference_mapping": str(mapping_path),
            "approval_log": str(approval_log) if approval_log else None,
            "artifact_hashes": {
                "slide_plan": sha256_file(slide_plan_path),
                "approved_style_reference": sha256_file(style_path),
                "reference_mapping": sha256_file(mapping_path),
            },
        },
        "style": {
            "approved_style_reference_markdown": style_markdown,
        },
        "slides": sorted(spec_slides, key=lambda item: item["number"]),
    }
    return spec, problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slide-plan", default="slide_plan.md")
    parser.add_argument("--approved-style-reference", default="approved_style_reference.md")
    parser.add_argument("--reference-mapping", default="reference_mapping.md")
    parser.add_argument("--approval-log")
    parser.add_argument("--project-root")
    parser.add_argument("--out", default="deck_spec.json")
    parser.add_argument("--deck-name")
    parser.add_argument("--goal")
    parser.add_argument("--language", default="Chinese")
    parser.add_argument("--aspect-ratio", choices=["16:9", "4:3"], default="16:9")
    parser.add_argument("--selected-backend", default="built-in image tool")
    parser.add_argument("--max-concurrent-slides", type=int, default=6)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    spec, problems = build_spec(args)
    if problems:
        print("Cannot build deck_spec.json:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1

    out = Path(args.out).expanduser().resolve()
    if out.exists() and not args.force:
        raise SystemExit(f"Output exists: {out} (use --force)")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out)
    print(f"slides={len(spec['slides'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
