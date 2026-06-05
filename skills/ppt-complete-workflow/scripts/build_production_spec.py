#!/usr/bin/env python3
"""Build a codex-ppt production spec from ppt_plan.md and approved samples."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


SLIDE_FIELD_NAMES = [
    "Content",
    "Template/theme",
    "Page layout/structure",
    "Template/reference path",
    "Images",
]


def _die(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def _read_text(path: Path) -> str:
    if not path.exists():
        _die(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return text.lower() or "final-deck"


def _section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    next_heading = re.search(r"^##\s+", text[match.end() :], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end() : end].strip()


def _clean_value(value: str) -> str:
    lines: List[str] = []
    for line in value.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        lines.append(stripped)
    return "\n".join(lines).strip()


def _parse_bullets(block: str) -> Dict[str, str]:
    result: Dict[str, List[str]] = {}
    current_key: Optional[str] = None
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        match = re.match(r"^\s*-\s*([^:]+):\s*(.*)$", line)
        if match:
            current_key = match.group(1).strip()
            result.setdefault(current_key, []).append(match.group(2).strip())
        elif current_key and line.strip():
            result[current_key].append(line.strip())
    return {key: _clean_value("\n".join(parts)) for key, parts in result.items()}


def _path_value(value: str, *, base_dir: Path) -> Optional[Path]:
    value = _clean_value(value)
    if not value or value.lower() in {"none", "n/a", "na", "no"}:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def _ensure_path(path: Path, *, label: str, allow_missing: bool) -> None:
    if allow_missing:
        return
    if not path.exists():
        _die(f"Missing {label}: {path}")


def _parse_slide_fields(block: str) -> Dict[str, str]:
    field_pattern = re.compile(
        r"^-\s*(" + "|".join(re.escape(name) for name in SLIDE_FIELD_NAMES) + r"):\s*(.*)$",
        re.MULTILINE,
    )
    matches = list(field_pattern.finditer(block))
    fields: Dict[str, str] = {}
    for index, match in enumerate(matches):
        field = match.group(1)
        inline_value = match.group(2)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        continuation = block[match.end() : end]
        fields[field] = _clean_value("\n".join([inline_value, continuation]))
    return fields


def _split_key_points(content: str) -> List[str]:
    content = _clean_value(content)
    if not content:
        return []
    lines = [line.strip("- ").strip() for line in content.splitlines() if line.strip()]
    if len(lines) > 1:
        return lines
    parts = [part.strip() for part in re.split(r"[;；]\s*", content) if part.strip()]
    return parts if len(parts) > 1 else [content]


def _parse_images(raw: str, *, base_dir: Path, allow_missing: bool) -> List[Dict[str, str]]:
    if not raw or raw.lower().strip() == "none":
        return []
    images: List[Dict[str, str]] = []
    current: Dict[str, str] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^-?\s*(Path|Role|Use on slide|Asset fidelity rule):\s*(.*)$", stripped, re.IGNORECASE)
        if not match:
            continue
        key = match.group(1).lower()
        value = match.group(2).strip()
        if key == "path":
            if current.get("path"):
                images.append(current)
            current = {"path": value}
        elif key == "role":
            current["role"] = value
        elif key == "use on slide":
            current["use"] = value
        elif key == "asset fidelity rule":
            current["fidelity"] = value
    if current.get("path"):
        images.append(current)

    normalized: List[Dict[str, str]] = []
    for image in images:
        path = _path_value(image["path"], base_dir=base_dir)
        if path is None:
            continue
        _ensure_path(path, label="planned slide image asset", allow_missing=allow_missing)
        role_parts = [image.get("role", "").strip(), image.get("use", "").strip()]
        role = "; ".join(part for part in role_parts if part) or "planned slide image asset"
        fidelity = image.get("fidelity", "").strip()
        normalized.append(
            {
                "path": str(path),
                "role": f"strict input asset; {role}",
                "fidelity": fidelity
                or "preserve the supplied image content while fitting it into the slide composition",
            }
        )
    return normalized


def _parse_slides(plan_text: str, *, base_dir: Path, allow_missing: bool) -> List[Dict[str, Any]]:
    slide_pattern = re.compile(r"^### Slide\s+(\d+):\s*(.+?)\s*$", re.MULTILINE)
    matches = list(slide_pattern.finditer(plan_text))
    if not matches:
        _die("No slide entries found in ppt_plan.md.")

    slides: List[Dict[str, Any]] = []
    for index, match in enumerate(matches):
        number = int(match.group(1))
        title = match.group(2).strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(plan_text)
        fields = _parse_slide_fields(plan_text[match.end() : end])
        missing = [name for name in SLIDE_FIELD_NAMES if name not in fields]
        if missing:
            _die(f"Slide {number} is missing required plan field(s): {', '.join(missing)}")

        template_ref = _path_value(fields["Template/reference path"], base_dir=base_dir)
        required_images = _parse_images(fields["Images"], base_dir=base_dir, allow_missing=allow_missing)
        if template_ref is not None:
            _ensure_path(template_ref, label=f"slide {number} template/reference", allow_missing=allow_missing)
            required_images.insert(
                0,
                {
                    "path": str(template_ref),
                    "role": "slide-specific template or visual reference",
                    "fidelity": "use as layout/style reference only; do not copy irrelevant text",
                },
            )

        content = fields["Content"]
        theme = fields["Template/theme"]
        layout = fields["Page layout/structure"]
        slides.append(
            {
                "number": number,
                "title": title,
                "role": theme or "content",
                "intent": layout,
                "key_points": _split_key_points(content),
                "local_context": {
                    "plan_content": content,
                    "template_theme": theme,
                    "page_layout_structure": layout,
                },
                "layout": {
                    "composition": layout,
                    "template_reference_path": str(template_ref) if template_ref else "none",
                },
                "visual_elements": {
                    "planned_images": [
                        {"path": image["path"], "role": image["role"]} for image in required_images
                    ],
                },
                "required_images": required_images,
                "constraints": [
                    "Follow ppt_plan.md for content, layout structure, template/reference use, and image placement.",
                    "Match the approved samples as style references across the deck.",
                    "Do not render an extra slide number unless the plan explicitly requires one.",
                ],
            }
        )
    return slides


def _parse_approved_samples(text: str, *, base_dir: Path, allow_missing: bool) -> List[Dict[str, Any]]:
    block = _section(text, "Approved Samples")
    entries: List[Dict[str, str]] = []
    current: Dict[str, str] = {}
    for line in block.splitlines():
        match = re.match(r"^\s*-\s*([^:]+):\s*(.*)$", line)
        if not match:
            continue
        key = match.group(1).strip().lower().replace(" ", "_")
        value = match.group(2).strip()
        if key == "slide" and current:
            entries.append(current)
            current = {}
        current[key] = value
    if current:
        entries.append(current)

    normalized: List[Dict[str, Any]] = []
    for entry in entries:
        path_text = entry.get("sample_path", "")
        sample_path = _path_value(path_text, base_dir=base_dir)
        if sample_path is None:
            continue
        _ensure_path(sample_path, label="approved sample image", allow_missing=allow_missing)
        slide_number = None
        slide_match = re.search(r"(?:Slide\s*)?(\d+)", entry.get("slide", ""), re.IGNORECASE)
        if slide_match:
            slide_number = int(slide_match.group(1))
        normalized.append(
            {
                "slide": entry.get("slide", ""),
                "slide_number": slide_number,
                "sample_path": str(sample_path),
                "source_round": entry.get("source_round", ""),
                "use_in_production": entry.get("use_in_production", ""),
            }
        )
    return normalized


def _should_reuse_sample(entry: Dict[str, Any], policy: str) -> bool:
    if policy == "always":
        return True
    if policy == "never":
        return False
    use = str(entry.get("use_in_production", "")).lower()
    negative = ["style reference", "reference only", "do not reuse", "regenerate"]
    positive = ["reuse", "use as final", "final slide", "accepted final", "keep as final"]
    return any(term in use for term in positive) and not any(term in use for term in negative)


def _style_from_approved_reference(text: str, requirements: Dict[str, str]) -> Dict[str, Any]:
    final_style = _parse_bullets(_section(text, "Final Style Direction"))
    return {
        "name": final_style.get("Theme") or requirements.get("Overall theme") or "approved sample style",
        "visual_direction": final_style.get("Layout system") or requirements.get("Overall template/style") or "",
        "typography": final_style.get("Typography", ""),
        "color_palette": final_style.get("Color/visual treatment", ""),
        "image_treatment": final_style.get("Image treatment", ""),
        "plan_overall_theme": requirements.get("Overall theme", ""),
        "plan_overall_template_style": requirements.get("Overall template/style", ""),
    }


def _sample_generation_method(text: str, approved_samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    method = _parse_bullets(_section(text, "Sample Generation Method"))
    normalized = {key.lower().replace(" ", "_"): value for key, value in method.items()}
    normalized["approved_sample_paths"] = [entry["sample_path"] for entry in approved_samples]
    normalized.setdefault(
        "handoff_rule",
        "Production workers must use the same backend/tool/mode as the approved sample round.",
    )
    return normalized


def _write_outline(path: Path, requirements: Dict[str, str], slides: List[Dict[str, Any]], plan_path: Path) -> None:
    lines = [
        "# Production Outline",
        "",
        f"- Source plan: {plan_path}",
        f"- Goal: {requirements.get('Goal', '')}",
        f"- Audience: {requirements.get('Audience', '')}",
        f"- Slide count: {len(slides)}",
        "",
    ]
    for slide in slides:
        lines.extend(
            [
                f"## Slide {slide['number']}: {slide['title']}",
                "",
                slide["local_context"]["plan_content"],
                "",
                f"- Template/theme: {slide['local_context']['template_theme']}",
                f"- Page layout/structure: {slide['local_context']['page_layout_structure']}",
                "",
            ]
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_speech(path: Path, slides: List[Dict[str, Any]]) -> None:
    lines: List[str] = ["# Speaker Notes", ""]
    for slide in slides:
        lines.extend(
            [
                f"## Slide {slide['number']}: {slide['title']}",
                "",
                slide["local_context"]["plan_content"],
                "",
            ]
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan).expanduser().resolve()
    approved_path = Path(args.approved_samples).expanduser().resolve()
    order_dir = Path(args.order_folder).expanduser().resolve() if args.order_folder else plan_path.parent
    plan_text = _read_text(plan_path)
    approved_text = _read_text(approved_path)

    requirements = _parse_bullets(_section(plan_text, "Deck Requirements"))
    slides = _parse_slides(plan_text, base_dir=order_dir, allow_missing=args.allow_missing)
    approved_samples = _parse_approved_samples(approved_text, base_dir=order_dir, allow_missing=args.allow_missing)
    if not approved_samples:
        _die("No approved sample images found in approved_sample_reference.md.")

    deck_name = args.deck_name or _slug(order_dir.name)
    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else order_dir / "production" / deck_name
    if out_dir.exists() and any(out_dir.iterdir()) and not args.force:
        _die(f"Output directory is not empty: {out_dir} (use --force)")
    (out_dir / "origin_image").mkdir(parents=True, exist_ok=True)

    sample_by_slide = {
        entry["slide_number"]: entry
        for entry in approved_samples
        if entry.get("slide_number") is not None
    }
    for slide in slides:
        sample = sample_by_slide.get(slide["number"])
        if not sample or not _should_reuse_sample(sample, args.reuse_approved_samples):
            continue
        source = Path(sample["sample_path"])
        target = out_dir / "origin_image" / f"slide_{slide['number']:02d}.png"
        shutil.copy2(source, target)
        slide["sample_approved"] = True
        slide["approved_sample_source"] = str(source)

    method = _sample_generation_method(approved_text, approved_samples)
    selected_backend = args.selected_backend or method.get("backend_used") or method.get("selected_backend") or ""
    spec = {
        "deck_name": deck_name,
        "language": args.language,
        "goal": requirements.get("Goal", ""),
        "audience": requirements.get("Audience", ""),
        "slide_count": len(slides),
        "source_plan": str(plan_path),
        "approved_sample_reference": str(approved_path),
        "selected_image_backend": selected_backend,
        "sample_generation_method": method,
        "style": _style_from_approved_reference(approved_text, requirements),
        "deck_context": {
            "goal": requirements.get("Goal", ""),
            "audience": requirements.get("Audience", ""),
            "overall_theme": requirements.get("Overall theme", ""),
            "overall_template_style": requirements.get("Overall template/style", ""),
            "main_source_files": requirements.get("Main source files", ""),
        },
        "approved_style_references": [
            {
                "path": entry["sample_path"],
                "role": f"approved sample style reference; {entry.get('slide', '')}".strip(),
                "fidelity": "match style, typography, density, spacing, visual treatment, and image handling only",
            }
            for entry in approved_samples
        ],
        "slides": slides,
    }

    spec_path = out_dir / "deck_spec.json"
    outline_path = out_dir / "outline.md"
    speech_path = out_dir / "speech.md"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_outline(outline_path, requirements, slides, plan_path)
    if not args.no_speech_draft:
        _write_speech(speech_path, slides)

    print(f"Wrote production spec: {spec_path}")
    print(f"Wrote outline: {outline_path}")
    if not args.no_speech_draft:
        print(f"Wrote speaker-note draft: {speech_path}")
    print(f"Slide count: {len(slides)}")
    print(f"Approved style references: {len(approved_samples)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="Path to ppt_plan.md.")
    parser.add_argument("--approved-samples", required=True, help="Path to approved_sample_reference.md.")
    parser.add_argument("--order-folder", help="Order folder used to resolve relative paths.")
    parser.add_argument("--out-dir", help="Production deck project directory.")
    parser.add_argument("--deck-name", help="Deck/project name. Defaults to the order folder name.")
    parser.add_argument("--language", default="Chinese", help="Deck language for image prompts.")
    parser.add_argument("--selected-backend", help="Override backend label if approved reference is incomplete.")
    parser.add_argument(
        "--reuse-approved-samples",
        choices=["auto", "always", "never"],
        default="auto",
        help="Copy matching approved samples into origin_image when they should be reused as final slides.",
    )
    parser.add_argument("--allow-missing", action="store_true", help="Do not fail when referenced local files are missing.")
    parser.add_argument("--no-speech-draft", action="store_true", help="Skip writing speech.md draft.")
    parser.add_argument("--force", action="store_true", help="Allow writing into a non-empty output directory.")
    return build(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
