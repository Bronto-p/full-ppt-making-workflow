#!/usr/bin/env python3
"""Lint slide_plan.md before sample iteration or production handoff."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SLIDE_HEADING_RE = re.compile(r"^##\s+(?:Slide\s+(\d+)|第\s*(\d+)\s*页)\b[:：]?\s*(.*)$", re.IGNORECASE)
SECTION_RE = re.compile(r"^###\s+(.+?)\s*$")
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
EMPTY_MARKERS = {"", "-", "none", "n/a", "na", "no", "无", "暂无", "不适用", "已解决", "none."}


def normalize_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def split_table_row(line: str) -> list[str]:
    return [normalize_cell(cell) for cell in line.strip().strip("|").split("|")]


def is_divider_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def parse_slides(content: str) -> list[dict[str, Any]]:
    lines = content.splitlines()
    slides: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line_number, line in enumerate(lines, start=1):
        match = SLIDE_HEADING_RE.match(line)
        if match:
            if current:
                current["end_line"] = line_number - 1
                slides.append(current)
            number = int(match.group(1) or match.group(2))
            current = {"number": number, "title": match.group(3).strip(), "start_line": line_number, "lines": []}
            continue
        if current is not None:
            current["lines"].append(line)
    if current:
        current["end_line"] = len(lines)
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


def has_field(lines: list[str], field: str) -> bool:
    pattern = re.compile(rf"^\s*[-*]\s*{re.escape(field)}\s*:\s*(.+)$", re.IGNORECASE)
    for line in lines:
        match = pattern.match(line)
        if match and normalize_cell(match.group(1)).lower() not in EMPTY_MARKERS:
            return True
    return False


def open_questions(lines: list[str]) -> list[str]:
    questions: list[str] = []
    for line in lines:
        if re.match(r"^\s*[-*]\s+", line):
            value = normalize_cell(re.sub(r"^\s*[-*]\s+", "", line))
            if value.lower() not in EMPTY_MARKERS:
                questions.append(value)
    return questions


def required_image_blocks(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        if re.match(r"^\s*[-*]\s*File\s*:\s*(.+)$", line, re.IGNORECASE):
            if current:
                blocks.append(current)
            current = [line]
        elif current is not None:
            if re.match(r"^\s*[-*]\s*(Optional|Free image generation/search)\s*:", line, re.IGNORECASE):
                blocks.append(current)
                current = None
            else:
                current.append(line)
    if current:
        blocks.append(current)
    return blocks


def draft_mapping_slides(content: str) -> set[int]:
    in_section = False
    header: list[str] | None = None
    mapped: set[int] = set()
    for line in content.splitlines():
        if line.startswith("## "):
            in_section = "draft reference mapping plan" in line.lower()
            header = None
            continue
        if not in_section or not TABLE_ROW_RE.match(line):
            continue
        cells = split_table_row(line)
        if is_divider_row(cells):
            continue
        if header is None:
            header = [cell.lower() for cell in cells]
            continue
        if not cells:
            continue
        match = re.search(r"\d+", cells[0])
        if match:
            mapped.add(int(match.group(0)))
    return mapped


def lint(path: Path, *, allow_open_questions: bool) -> list[str]:
    content = path.read_text(encoding="utf-8")
    slides = parse_slides(content)
    problems: list[str] = []
    if not slides:
        return ["No slide sections found. Expected headings like `## Slide 1: Title`."]
    seen: set[int] = set()
    for slide in slides:
        number = slide["number"]
        if number in seen:
            problems.append(f"Slide {number}: duplicate slide heading.")
        seen.add(number)
        text = section_block(slide, "Content") or section_block(slide, "Text")
        style = (
            section_block(slide, "Template / Reference")
            or section_block(slide, "Template / Style Plan")
            or section_block(slide, "Template")
        )
        images = section_block(slide, "Images")
        questions = section_block(slide, "Open Questions")
        if not text:
            problems.append(f"Slide {number}: missing `### Content` section.")
        elif not (has_field(text, "Title") or any(line.strip() for line in text)):
            problems.append(f"Slide {number}: text section does not contain usable approved text.")
        if not style:
            problems.append(f"Slide {number}: missing `### Template / Reference` section.")
        elif not has_field(style, "Approval status"):
            problems.append(f"Slide {number}: style plan missing `Approval status`.")
        if not images:
            problems.append(f"Slide {number}: missing `### Images` section.")
        else:
            lowered = "\n".join(images).lower()
            if "required" not in lowered or "optional" not in lowered:
                problems.append(f"Slide {number}: image section must state required and optional image policy.")
            for block in required_image_blocks(images):
                file_line = next((line for line in block if re.search(r"File\s*:", line, re.IGNORECASE)), "")
                file_value = normalize_cell(re.sub(r"^.*?File\s*:\s*", "", file_line, flags=re.IGNORECASE))
                if file_value.lower() in EMPTY_MARKERS:
                    continue
                if not any(re.search(r"Role\s*:\s*\S", line, re.IGNORECASE) for line in block):
                    problems.append(f"Slide {number}: required image `{file_value}` is missing Role.")
                if not any(re.search(r"Preservation\s*:\s*\S", line, re.IGNORECASE) for line in block):
                    problems.append(f"Slide {number}: required image `{file_value}` is missing Preservation.")
        unresolved = open_questions(questions)
        if unresolved and not allow_open_questions:
            problems.append(f"Slide {number}: unresolved open questions: {'; '.join(unresolved)}")

    mapped = draft_mapping_slides(content)
    for number in sorted(seen):
        if number not in mapped:
            problems.append(f"Slide {number}: missing row in `## Draft Reference Mapping Plan`.")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slide_plan")
    parser.add_argument("--allow-open-questions", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    problems = lint(Path(args.slide_plan).expanduser().resolve(), allow_open_questions=args.allow_open_questions)
    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems}, ensure_ascii=False, indent=2))
    else:
        if problems:
            print("Slide plan lint failed:")
            for problem in problems:
                print(f"- {problem}")
        else:
            print("Slide plan lint passed.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
