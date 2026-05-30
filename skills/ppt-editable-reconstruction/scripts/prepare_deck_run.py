#!/usr/bin/env python3
import argparse
import hashlib
from pathlib import Path

from PIL import Image

from deck_run_state import now_iso, read_json, rel_to_run, save_deck, set_run_status, sha256_file, write_json
from deck_run_state import DEFAULT_MAX_CONCURRENT_PAGES
from _input_normalization import normalize_inputs


def source_size(path):
    with Image.open(path) as image:
        return image.size


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_record(path):
    path = Path(path).resolve()
    if not path.exists() or not path.is_file():
        return None
    return {"path": str(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def read_json_if_exists(path):
    path = Path(path)
    if not path.exists():
        return None
    data = read_json(path)
    return data if isinstance(data, dict) else None


def normalize_asset_record(image):
    if not isinstance(image, dict):
        return None
    raw_path = image.get("path") or image.get("attachment")
    if not raw_path:
        return None
    path = Path(str(raw_path)).expanduser()
    record = {
        "path": str(path.resolve()) if path.exists() else str(path),
        "role": image.get("role"),
        "preservation": image.get("preservation") or image.get("fidelity") or image.get("constraints"),
    }
    if path.exists() and path.is_file():
        record["sha256"] = sha256_file(path)
    return record


def stage3_page_context(stage3_project, page_index):
    if not stage3_project:
        return None
    project = Path(stage3_project).expanduser().resolve()
    if not project.exists():
        raise SystemExit(f"Stage 3 project folder not found: {project}")
    slide_id = f"slide_{page_index:02d}"
    artifacts = {}
    for name in [
        "deck_spec.json",
        "slide_jobs.json",
        "material_manifest.json",
        "approval_log.json",
        "slide_plan.md",
        "approved_style_reference.md",
        "reference_mapping.md",
    ]:
        record = artifact_record(project / name)
        if record:
            artifacts[name] = record
    prompt_path = project / "prompts" / f"{slide_id}.json"
    prompt_job = read_json_if_exists(prompt_path) or {}
    slide_jobs = read_json_if_exists(project / "slide_jobs.json") or {}
    slide_job = None
    for candidate in slide_jobs.get("slides", []):
        try:
            candidate_number = int(candidate.get("number", -1))
        except (TypeError, ValueError):
            candidate_number = -1
        if candidate.get("slide_id") == slide_id or candidate_number == page_index:
            slide_job = candidate
            break
    required_images = []
    for image in prompt_job.get("required_images") or (slide_job or {}).get("required_images") or []:
        record = normalize_asset_record(image)
        if record:
            required_images.append(record)
    reference_images = []
    for image in prompt_job.get("reference_images") or (slide_job or {}).get("reference_images") or []:
        record = normalize_asset_record(image)
        if record:
            reference_images.append(record)
    return {
        "stage3_project": str(project),
        "slide_id": slide_id,
        "artifacts": artifacts,
        "prompt_job_path": str(prompt_path) if prompt_path.exists() else None,
        "prompt_job": prompt_job,
        "slide_job": slide_job,
        "required_client_assets": required_images,
        "reference_images": reference_images,
        "metadata_available": bool(prompt_job or slide_job),
    }


def validate_stage3_context(stage3_project, pages):
    if not stage3_project:
        return
    gaps = []
    for page in pages:
        context = stage3_page_context(stage3_project, page["page_index"])
        if not context or not context.get("metadata_available"):
            gaps.append(f"page_{page['page_index']:03d}: missing prompts/slide_{page['page_index']:02d}.json and slide_jobs metadata")
    if gaps:
        raise SystemExit("Stage 3 metadata is incomplete; cannot prepare reconstruction requests:\n" + "\n".join(gaps))


def page_request(run_dir, deck, page, stage3_project=None):
    page_dir = (run_dir / page["page_dir"]).resolve()
    source = (run_dir / page["source_image"]).resolve()
    width_px, height_px = source_size(source)
    page_id = page["page_id"]
    slide_size = page.get("slide") or deck.get("slide") or {"width": 13.333, "height": 7.5}
    stage3_context = stage3_page_context(stage3_project, page["page_index"])
    return {
        "schema_version": 1,
        "run_id": deck["run_id"],
        "page_id": page_id,
        "page_index": page["page_index"],
        "page_dir": str(page_dir),
        "source_image": str(source),
        "source_size_px": {"width": width_px, "height": height_px},
        "slide": slide_size,
        "max_concurrent_pages": deck["max_concurrent_pages"],
        "metadata_loss": deck.get("metadata_loss", []),
        "stage3_context": stage3_context,
        "allowed_write_scope": str(page_dir),
        "forbidden_paths": [
            str(run_dir / "deck_manifest.json"),
            str(run_dir / "page_jobs.json"),
            str(run_dir / "notes_manifest.json"),
            str(run_dir / "final"),
            str(run_dir / "input"),
        ],
        "required_outputs": {
            "manifest": str(page_dir / "manifest.json"),
            "imagegen_jobs": str(page_dir / "imagegen-jobs.json"),
            "page_pptx": str(page_dir / "page.pptx"),
            "preview": str(page_dir / "preview.png"),
            "contact_sheet": str(page_dir / "split_assets_contact.png"),
            "validation": str(page_dir / "validation.json"),
            "page_result": str(page_dir / "page_result.json"),
        },
    }


def write_page_jobs(run_dir, deck, stage3_project=None):
    jobs = {
        "schema_version": 1,
        "run_id": deck["run_id"],
        "run_status": "inputs_prepared",
        "max_concurrent_pages": deck["max_concurrent_pages"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "pages": [],
    }
    for page in deck["pages"]:
        page_dir = run_dir / page["page_dir"]
        request_path = page_dir / "page_request.json"
        request = page_request(run_dir, deck, page, stage3_project=stage3_project)
        write_json(request_path, request)
        write_json(
            page_dir / "imagegen-jobs.json",
            {"schema_version": 1, "run_id": deck["run_id"], "page_id": page["page_id"], "jobs": []},
        )
        jobs["pages"].append(
            {
                "page_id": page["page_id"],
                "page_index": page["page_index"],
                "status": "pending",
                "page_dir": page["page_dir"],
                "source": page["source_image"],
                "page_request": rel_to_run(run_dir, request_path),
                "manifest": page["manifest"],
                "validation": page["validation"],
                "dispatch": None,
                "result": None,
                "repair": [],
                "blocker": None,
                "accepted": False,
            }
        )
    write_json(run_dir / "page_jobs.json", jobs)


def upgrade_deck_manifest(deck_path, max_concurrent_pages, stage3_project=None):
    run_dir = deck_path.parent
    deck = read_json(deck_path)
    run_id = run_dir.name
    output_name = Path(deck.get("output", f"{run_id}_edited.pptx")).name
    metadata_loss = list(deck.get("metadata_loss") or [])
    if not stage3_project:
        metadata_loss.append(
            "No Stage 3 project folder was provided; page requests cannot include production prompt jobs, "
            "approval records, reference mappings, or original client asset provenance."
        )
    deck.update(
        {
            "schema_version": 1,
            "run_id": run_id,
            "prepared_at": now_iso(),
            "output": f"final/{output_name}",
            "page_jobs": "page_jobs.json",
            "run_state": "run_state.json",
            "max_concurrent_pages": max_concurrent_pages,
            "stage3_project": str(Path(stage3_project).expanduser().resolve()) if stage3_project else None,
            "metadata_loss": metadata_loss,
        }
    )
    for index, page in enumerate(deck.get("pages", []), start=1):
        page_id = f"page_{index:03d}"
        page["page_id"] = page_id
        page["status"] = "pending"
        page["page_request"] = f"{page['page_dir']}/page_request.json"
        page["dispatch"] = None
        page["result"] = None
        page["repair"] = []
        page["blocker"] = None
        page["accepted"] = False
    validate_stage3_context(stage3_project, deck.get("pages", []))
    save_deck(run_dir, deck)
    write_page_jobs(run_dir, deck, stage3_project=stage3_project)
    set_run_status(run_dir, "inputs_prepared", "prepared inputs and page jobs")
    return deck


def main():
    parser = argparse.ArgumentParser(description="Create a stable image-to-editable-ppt run directory.")
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--out-root", default="output/image-to-editable-ppt")
    parser.add_argument("--job-dir")
    parser.add_argument("--dpi", type=int, default=180)
    parser.add_argument("--stage3-project", help="Full Stage 3 project folder to connect prompt jobs, mappings, approvals, and original assets into page requests.")
    parser.add_argument(
        "--max-concurrent-pages",
        type=int,
        default=DEFAULT_MAX_CONCURRENT_PAGES,
        help="Maximum page subagents that may be dispatched at the same time.",
    )
    args = parser.parse_args()
    if args.max_concurrent_pages < 1:
        raise SystemExit("--max-concurrent-pages must be >= 1")

    deck_path = normalize_inputs(args.inputs, out_root=args.out_root, job_dir=args.job_dir, dpi=args.dpi)
    run_dir = deck_path.parent
    if not (run_dir / "pages").exists():
        raise SystemExit(f"Input normalization did not create pages/: {run_dir}")
    deck = upgrade_deck_manifest(deck_path, args.max_concurrent_pages, stage3_project=args.stage3_project)
    print(deck_path)
    print(f"run_id={deck['run_id']}")
    print(f"pages={deck['page_count']}")
    print(f"max_concurrent_pages={deck['max_concurrent_pages']}")


if __name__ == "__main__":
    main()
