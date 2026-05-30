#!/usr/bin/env python3
"""Create a material visibility manifest for a PPT order folder."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
PDF_EXTS = {".pdf"}
PLAIN_TEXT_EXTS = {".txt", ".md", ".markdown", ".csv", ".tsv", ".json"}
ZIP_MEDIA_EXTS = {".docx", ".pptx", ".xlsx"}
OFFICE_RENDER_EXTS = {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"}
SKIP_DIRS = {"material_ingestion", "__MACOSX", ".git", "__pycache__"}
SKIP_FILES = {"material_manifest.json", "ingestion_notes.md"}
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


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


def safe_output_stem(root: Path, path: Path) -> str:
    relative = rel(root, path)
    digest = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:8]
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(relative).with_suffix("").as_posix()).strip("_")
    return f"{stem[:80] or path.stem}_{digest}"


def is_inside(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def text_result(text: str, *, sources: list[str] | None = None) -> dict[str, Any]:
    stripped = text.strip()
    status = "readable" if stripped else "empty"
    result: dict[str, Any] = {
        "text_status": status,
        "text_chars": len(stripped),
    }
    if sources:
        result["text_sources"] = sources
    if stripped:
        result["text_sha256"] = hashlib.sha256(stripped.encode("utf-8")).hexdigest()
        result["text_excerpt"] = stripped[:1200]
    return result


def blocked_text_result(message: str, *, status: str = "blocked") -> dict[str, Any]:
    return {"text_status": status, "text_blocker": message}


def extract_plain_text(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except Exception as exc:
        return blocked_text_result(str(exc))
    for encoding in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return text_result(raw.decode(encoding), sources=[path.name])
        except UnicodeDecodeError:
            continue
    return blocked_text_result("cannot decode as text")


def xml_text(xml_bytes: bytes) -> str:
    root = ET.fromstring(xml_bytes)
    parts: list[str] = []
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag in {"t", "v"} and node.text:
            parts.append(node.text)
    return "\n".join(parts)


def natural_key(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value)]


def extract_docx_text(archive: zipfile.ZipFile) -> tuple[str, list[str]]:
    names = archive.namelist()
    text_parts: list[str] = []
    sources: list[str] = []
    wanted = [
        name for name in names
        if name == "word/document.xml"
        or name.startswith(("word/header", "word/footer", "word/footnotes", "word/endnotes", "word/comments"))
        and name.endswith(".xml")
    ]
    for name in sorted(wanted, key=natural_key):
        try:
            text = xml_text(archive.read(name))
        except ET.ParseError:
            continue
        if text.strip():
            text_parts.append(text)
            sources.append(name)
    return "\n".join(text_parts), sources


def extract_pptx_text(archive: zipfile.ZipFile) -> tuple[str, list[str]]:
    text_parts: list[str] = []
    sources: list[str] = []
    names = archive.namelist()
    wanted = [
        name for name in names
        if name.startswith(("ppt/slides/slide", "ppt/notesSlides/notesSlide", "ppt/comments/comment"))
        and name.endswith(".xml")
    ]
    for name in sorted(wanted, key=natural_key):
        try:
            text = xml_text(archive.read(name))
        except ET.ParseError:
            continue
        if text.strip():
            text_parts.append(f"[{name}]\n{text}")
            sources.append(name)
    return "\n".join(text_parts), sources


def extract_xlsx_text(archive: zipfile.ZipFile) -> tuple[str, list[str]]:
    names = archive.namelist()
    shared_strings: list[str] = []
    if "xl/sharedStrings.xml" in names:
        try:
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.iter():
                if item.tag.rsplit("}", 1)[-1] == "si":
                    value = "\n".join(
                        node.text or ""
                        for node in item.iter()
                        if node.tag.rsplit("}", 1)[-1] == "t"
                    ).strip()
                    shared_strings.append(value)
        except ET.ParseError:
            pass

    text_parts: list[str] = []
    sources: list[str] = []
    for name in sorted((n for n in names if n.startswith("xl/worksheets/") and n.endswith(".xml")), key=natural_key):
        try:
            root = ET.fromstring(archive.read(name))
        except ET.ParseError:
            continue
        values: list[str] = []
        for cell in root.iter():
            if cell.tag.rsplit("}", 1)[-1] != "c":
                continue
            cell_type = cell.attrib.get("t")
            raw_value = ""
            for child in cell:
                tag = child.tag.rsplit("}", 1)[-1]
                if tag == "v" and child.text:
                    raw_value = child.text
                elif tag == "is":
                    inline = "\n".join(
                        node.text or ""
                        for node in child.iter()
                        if node.tag.rsplit("}", 1)[-1] == "t"
                    ).strip()
                    if inline:
                        raw_value = inline
            if cell_type == "s" and raw_value.isdigit():
                index = int(raw_value)
                if index < len(shared_strings):
                    raw_value = shared_strings[index]
            if raw_value.strip():
                values.append(raw_value.strip())
        if values:
            text_parts.append(f"[{name}]\n" + "\n".join(values))
            sources.append(name)
    return "\n".join(text_parts), sources


def extract_office_text(path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            if path.suffix.lower() == ".docx":
                text, sources = extract_docx_text(archive)
            elif path.suffix.lower() == ".pptx":
                text, sources = extract_pptx_text(archive)
            elif path.suffix.lower() == ".xlsx":
                text, sources = extract_xlsx_text(archive)
            else:
                return blocked_text_result("unsupported Office text container", status="unverified")
    except Exception as exc:
        return blocked_text_result(str(exc))
    return text_result(text, sources=sources)


def extract_pdf_text(path: Path) -> dict[str, Any]:
    try:
        import fitz
    except ImportError:
        return blocked_text_result("PyMuPDF is not installed", status="unverified")
    try:
        with fitz.open(path) as doc:
            text = "\n".join(page.get_text("text") for page in doc)
        return text_result(text, sources=[path.name])
    except Exception as exc:
        return blocked_text_result(str(exc))


def check_text_visibility(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix in PLAIN_TEXT_EXTS:
        return extract_plain_text(path)
    if suffix in {".docx", ".pptx", ".xlsx"}:
        return extract_office_text(path)
    if suffix in PDF_EXTS:
        return extract_pdf_text(path)
    if suffix in IMG_EXTS:
        return {"text_status": "not_applicable"}
    if suffix in {".doc", ".ppt", ".xls"}:
        return blocked_text_result("legacy Office binary text extraction requires conversion/export", status="unverified")
    return {"text_status": "unsupported"}


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


def office_container_findings(path: Path, root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            for rels_name in [name for name in names if name.endswith(".rels")]:
                try:
                    rels_root = ET.fromstring(archive.read(rels_name))
                except ET.ParseError:
                    continue
                for relationship in rels_root.findall(f"{{{REL_NS}}}Relationship"):
                    target = relationship.attrib.get("Target", "")
                    rel_type = relationship.attrib.get("Type", "")
                    mode = relationship.attrib.get("TargetMode", "")
                    rel_id = relationship.attrib.get("Id", "")
                    lowered_type = rel_type.lower()
                    if mode.lower() == "external":
                        findings.append(
                            {
                                "source_file": rel(root, path),
                                "kind": "external_linked_asset",
                                "relationship_part": rels_name,
                                "relationship_id": rel_id,
                                "target": target,
                                "relationship_type": rel_type,
                                "visual_status": "blocked",
                                "blocker": "external linked material must be downloaded/exported locally",
                            }
                        )
                    elif any(term in lowered_type for term in ("oleobject", "package", "video", "media", "chart")):
                        findings.append(
                            {
                                "source_file": rel(root, path),
                                "kind": "office_relationship",
                                "relationship_part": rels_name,
                                "relationship_id": rel_id,
                                "target": target,
                                "relationship_type": rel_type,
                                "visual_status": "needs_manual_review",
                            }
                        )
            if path.suffix.lower() == ".pptx":
                animated = [
                    name for name in names
                    if name.startswith("ppt/slides/slide")
                    and name.endswith(".xml")
                    and (b"<p:timing" in archive.read(name) or b"<p:anim" in archive.read(name))
                ]
                if animated:
                    findings.append(
                        {
                            "source_file": rel(root, path),
                            "kind": "ppt_animation_or_timing",
                            "slide_parts": animated,
                            "visual_status": "needs_manual_review",
                            "blocker": "animations/timing are not represented in static extracted media",
                        }
                    )
    except Exception as exc:
        findings.append(
            {
                "source_file": rel(root, path),
                "kind": "office_container_inspection",
                "visual_status": "blocked",
                "blocker": str(exc),
            }
        )
    return findings


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
                out_dir = output_root / "extracted_media" / safe_output_stem(root, path)
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


def render_pdf_pages(
    pdf_path: Path,
    *,
    source_file: Path,
    root: Path,
    output_root: Path,
    dpi: int,
) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    try:
        import fitz
    except ImportError:
        return [{
            "source_file": rel(root, source_file),
            "kind": "rendered_page",
            "visual_status": "unverified",
            "blocker": "PyMuPDF is not installed",
        }]
    try:
        doc = fitz.open(pdf_path)
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        out_dir = output_root / "rendered_pages" / safe_output_stem(root, source_file)
        out_dir.mkdir(parents=True, exist_ok=True)
        for index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            out = out_dir / f"page_{index:03d}.png"
            pix.save(out)
            item = {
                "source_file": rel(root, source_file),
                "source_page": index,
                "output": rel(root, out),
                "kind": "rendered_page",
                "sha256": sha256_file(out),
            }
            item.update(verify_image(out))
            outputs.append(item)
    except Exception as exc:
        outputs.append({"source_file": rel(root, source_file), "kind": "rendered_page", "visual_status": "blocked", "blocker": str(exc)})
    return outputs


def render_pdf(path: Path, root: Path, output_root: Path, dpi: int) -> list[dict[str, Any]]:
    return render_pdf_pages(path, source_file=path, root=root, output_root=output_root, dpi=dpi)


def find_soffice() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def render_office(path: Path, root: Path, output_root: Path, dpi: int) -> list[dict[str, Any]]:
    soffice = find_soffice()
    if not soffice:
        return [
            {
                "source_file": rel(root, path),
                "kind": "rendered_page",
                "visual_status": "unverified",
                "blocker": "LibreOffice/soffice is not installed; export this Office file to PDF or page images",
            }
        ]
    try:
        with tempfile.TemporaryDirectory() as temp:
            temp_dir = Path(temp)
            subprocess.run(
                [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(temp_dir), str(path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            pdfs = sorted(temp_dir.glob("*.pdf"))
            if not pdfs:
                raise RuntimeError("Office conversion did not produce a PDF")
            return render_pdf_pages(pdfs[0], source_file=path, root=root, output_root=output_root, dpi=dpi)
    except Exception as exc:
        return [{"source_file": rel(root, path), "kind": "rendered_page", "visual_status": "blocked", "blocker": str(exc)}]


def image_item_path(root: Path, item: dict[str, Any]) -> Path | None:
    raw = item.get("output") or item.get("path")
    if not raw:
        return None
    path = Path(str(raw))
    if path.is_absolute():
        return path
    return root / path


def make_contact_sheet(root: Path, images: list[dict[str, Any]], output_root: Path) -> str | None:
    viewable = [item for item in images if item.get("visual_status") == "viewable" and image_item_path(root, item)]
    if not viewable:
        return None
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    thumbs = []
    for item in viewable[:80]:
        path = image_item_path(root, item)
        if path is None:
            continue
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
        label = item.get("output") or item.get("path") or item.get("source_file", "")
        draw.text((x + 20, y + 150), label[-38:], fill=(0, 0, 0))
    out = output_root / "material_contact_sheets" / "contact_sheet_001.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=90)
    return rel(root, out)


def scan(root: Path, output_root: Path, dpi: int) -> dict[str, Any]:
    files = []
    derived = []
    contact_sheet_items = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if is_inside(path, output_root):
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
        entry.update(check_text_visibility(path))
        if suffix in IMG_EXTS:
            entry.update(verify_image(path))
            contact_sheet_items.append(entry)
        elif suffix in OFFICE_RENDER_EXTS:
            if suffix in ZIP_MEDIA_EXTS:
                media_items = extract_zip_media(path, root, output_root)
                derived.extend(media_items)
            findings = office_container_findings(path, root) if suffix in ZIP_MEDIA_EXTS else []
            rendered = render_office(path, root, output_root, dpi)
            derived.extend(rendered)
            derived.extend(findings)
            if any(item.get("visual_status") == "viewable" for item in rendered):
                entry["visual_status"] = "rendered_pages_available"
            elif rendered:
                entry["visual_status"] = rendered[0].get("visual_status", "container_needs_rendered_pages")
                entry["visual_blocker"] = rendered[0].get("blocker")
            else:
                entry["visual_status"] = "container_needs_rendered_pages"
            if findings:
                entry["container_findings"] = findings
        elif suffix in PDF_EXTS:
            rendered = render_pdf(path, root, output_root, dpi)
            derived.extend(rendered)
            if any(item.get("visual_status") == "viewable" for item in rendered):
                entry["visual_status"] = "rendered_pages_available"
            elif rendered:
                entry["visual_status"] = rendered[0].get("visual_status", "container_needs_rendered_pages")
                entry["visual_blocker"] = rendered[0].get("blocker")
            else:
                entry["visual_status"] = "container_needs_rendered_pages"
        files.append(entry)
    contact_sheet = make_contact_sheet(root, contact_sheet_items + derived, output_root)
    return {
        "schema_version": 1,
        "created_at": now_iso(),
        "root": str(root),
        "files": files,
        "derived_visuals": derived,
        "contact_sheets": [contact_sheet] if contact_sheet else [],
        "notes": [
            "Text extraction proves text readability only; it is not a substitute for visual inspection.",
            "If visual_status is blocked/unverified/container_needs_*, ask for exports or inspect derived outputs before planning.",
            "Office linked/external media, animations, videos, OLE objects, and charts may require exported local assets even when text extraction succeeds.",
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
