#!/usr/bin/env python3
"""Create a material visibility manifest for a PPT order folder."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
PDF_EXTS = {".pdf"}
ZIP_MEDIA_EXTS = {".docx", ".pptx", ".xlsx"}
SKIP_DIRS = {"material_ingestion", "__MACOSX", ".git", "__pycache__"}
SKIP_FILES = {"material_manifest.json", "ingestion_notes.md"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify_image(path: Path) -> dict[str, Any]:
    try:
        from PIL import Image
        with Image.open(path) as image:
            image.load()
            return {"visual_status": "viewable", "width": image.width, "height": image.height, "mode": image.mode}
    except ImportError:
        return {"visual_status": "unverified", "blocker": "Pillow is not installed"}
    except Exception as exc:
        return {"visual_status": "blocked", "blocker": f"cannot open image: {exc}"}


def extract_zip_media(path: Path, root: Path, output_root: Path) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            media_names = [
                name for name in names
                if name.lower().startswith(("word/media/", "ppt/media/", "xl/media/"))
            ]
            for index, name in enumerate(media_names, start=1):
                suffix = Path(name).suffix.lower() or ".bin"
                out_dir = output_root / "extracted_media" / path.stem
                out = out_dir / f"{index:03d}_{Path(name).name}"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(archive.read(name))
                item = {
                    "source_file": rel(root, path),
                    "source_member": name,
                    "output": rel(root, out),
                    "kind": "embedded_media",
                    "sha256": sha256_file(out),
                }
                if suffix in IMG_EXTS:
                    item.update(verify_image(out))
                outputs.append(item)
    except Exception as exc:
        outputs.append({"source_file": rel(root, path), "kind": "embedded_media", "visual_status": "blocked", "blocker": str(exc)})
    return outputs


def render_pdf(path: Path, root: Path, output_root: Path, dpi: int) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    try:
        import fitz
    except ImportError:
        return [{
            "source_file": rel(root, path),
            "kind": "rendered_page",
            "visual_status": "unverified",
            "blocker": "PyMuPDF is not installed",
        }]
    try:
        doc = fitz.open(path)
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        out_dir = output_root / "rendered_pages" / path.stem
        out_dir.mkdir(parents=True, exist_ok=True)
        for index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            out = out_dir / f"page_{index:03d}.png"
            pix.save(out)
            item = {
                "source_file": rel(root, path),
                "source_page": index,
                "output": rel(root, out),
                "kind": "rendered_page",
                "sha256": sha256_file(out),
            }
            item.update(verify_image(out))
            outputs.append(item)
    except Exception as exc:
        outputs.append({"source_file": rel(root, path), "kind": "rendered_page", "visual_status": "blocked", "blocker": str(exc)})
    return outputs


def make_contact_sheet(root: Path, images: list[dict[str, Any]], output_root: Path) -> str | None:
    viewable = [item for item in images if item.get("visual_status") == "viewable" and item.get("output")]
    if not viewable:
        return None
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    thumbs = []
    for item in viewable[:80]:
        path = root / item["output"]
        try:
            image = Image.open(path).convert("RGB")
            image.thumbnail((240, 135))
            thumbs.append((item, image.copy()))
        except Exception:
            continue
    if not thumbs:
        return None
    cols = 4
    cell_w, cell_h = 280, 185
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (item, image) in enumerate(thumbs):
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        sheet.paste(image, (x + 20, y + 10))
        label = item.get("output") or item.get("source_file", "")
        draw.text((x + 20, y + 150), label[-38:], fill=(0, 0, 0))
    out = output_root / "material_contact_sheets" / "contact_sheet_001.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=90)
    return rel(root, out)


def scan(root: Path, output_root: Path, dpi: int) -> dict[str, Any]:
    files = []
    derived = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.name in SKIP_FILES:
            continue
        suffix = path.suffix.lower()
        entry: dict[str, Any] = {
            "path": rel(root, path),
            "suffix": suffix,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "text_status": "not_checked",
            "visual_status": "not_checked",
        }
        if suffix in IMG_EXTS:
            entry.update(verify_image(path))
        elif suffix in ZIP_MEDIA_EXTS:
            entry["visual_status"] = "container_needs_extracted_media"
            derived.extend(extract_zip_media(path, root, output_root))
        elif suffix in PDF_EXTS:
            entry["visual_status"] = "container_needs_rendered_pages"
            derived.extend(render_pdf(path, root, output_root, dpi))
        files.append(entry)
    contact_sheet = make_contact_sheet(root, derived, output_root)
    return {
        "schema_version": 1,
        "created_at": now_iso(),
        "root": str(root),
        "files": files,
        "derived_visuals": derived,
        "contact_sheets": [contact_sheet] if contact_sheet else [],
        "notes": [
            "Text extraction is not a substitute for visual inspection.",
            "If visual_status is blocked/unverified/container_needs_*, ask for exports or inspect derived outputs before planning.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("order_folder")
    parser.add_argument("--out-dir", default="material_ingestion")
    parser.add_argument("--dpi", type=int, default=180)
    args = parser.parse_args()

    root = Path(args.order_folder).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Order folder not found: {root}")
    output_root = root / args.out_dir
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = scan(root, output_root, args.dpi)
    manifest_path = root / "material_manifest.json"
    write_json(manifest_path, manifest)
    notes_path = root / "ingestion_notes.md"
    notes_path.write_text(
        "# Ingestion Notes\n\n"
        f"- Material manifest: `{manifest_path.name}`\n"
        f"- Derived visuals: `{args.out_dir}/`\n"
        "- Inspect rendered pages, extracted media, and contact sheets before assigning slide images.\n",
        encoding="utf-8",
    )
    print(manifest_path)
    print(f"files={len(manifest['files'])}")
    print(f"derived_visuals={len(manifest['derived_visuals'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
