---
name: ppt-full-production
description: Produce the final image-based PPT deck from an approved client PPT plan. Use after ppt-order-planner and ppt-sample-iteration have produced approved slide_plan.md, approved_style_reference.md, reference_mapping.md, and approved reference images; this skill prepares per-slide jobs, dispatches slide workers, records generated results, QA checks, writes speaker notes, and assembles the final PPTX using the codex-ppt style workflow.
---

# PPT Full Production

## Purpose

This skill performs the third stage of the client PPT workflow: final full-deck production.

It is a production-only adaptation of the `codex-ppt` workflow. It assumes planning and sample approval are already complete.

Do not re-plan the deck, re-select the style, or ask for new sample approval in this skill. Use the approved plan and approved reference images as the production contract.

## Workflow Position

The overall workflow is:

1. `ppt-order-planner`: creates `order_materials.md` and `slide_plan.md`; client approves the full plan.
2. `ppt-sample-iteration`: creates approved sample/reference images, `approved_style_reference.md`, and `reference_mapping.md`.
3. `ppt-full-production`: generates every final slide image, records state, QA checks, writes notes, and assembles the final PPTX.

This skill only performs step 3.

## Required Inputs

The order/project folder must contain:

- `order_materials.md`
- `material_manifest.json` or equivalent ingestion notes when the source contained embedded visuals
- `approval_log.json` when prior stages recorded approvals
- `slide_plan.md`
- `approved_style_reference.md`
- `reference_mapping.md`
- approved reference images listed in `reference_mapping.md`
- all required client image assets listed in `slide_plan.md`

If any required input is missing, stop and report what is missing. Do not start production.

## Scripts

This skill includes `scripts/` wrappers for the production scripts from `codex-ppt`. Use these local script entrypoints for deterministic production state and assembly:

- `codex_ppt_runtime.py`: bootstrap/check runtime.
- `build_deck_spec.py`: conservatively build `deck_spec.json` from approved Markdown artifacts and stop on ambiguous text, blocked mappings, missing assets, or stale approvals.
- `prepare_slide_prompts.py`: prepare per-slide prompt jobs when compatible with `deck_spec.json`.
- `slide_job_status.py`: inspect pending, dispatched, blocked, and recorded slides.
- `record_slide_dispatch.py`: record slide worker dispatch.
- `record_slide_result.py`: copy selected generated slide images and record backend id, aspect ratio, and provenance.
- `record_slide_blocker.py`: record blockers.
- `reset_slide_for_retry.py`: reset blocked/dispatched slides back to pending with retry history.
- `slide_run_state.py`: manage slide run state.
- `assemble_ppt.py`: assemble final image-based PPTX.

Do not hand-edit slide state JSON when a local script entrypoint applies.

Production should use a structured `deck_spec.json` built from the approved plan artifacts. If the project still only has Markdown plans, the parent agent must either create a fully structured `deck_spec.json` and validate it, or stop before generation. Do not proceed when the conversion leaves any slide's approved text, reference images, required images, preservation rules, or open-question status ambiguous.

## Production Contract

Before creating any prompt jobs or final slide images, validate:

- Every slide in `slide_plan.md` has approved text content.
- Every slide has a row in `reference_mapping.md`.
- Every slide maps to at least one approved reference image.
- Every mapped reference image path exists.
- Every mapped reference image can be opened/viewed as an actual local image.
- Every required client image asset path exists.
- Every required client image can be opened/viewed as an actual local image.
- Every required client image has a role and preservation rule.
- No open question blocks production.
- The latest approval was returned through the user after any material plan, sample, style, or reference-mapping change.
- Confidential/client-sensitive materials have user approval before any API/CLI fallback is used.

Reference images can be reused across many slides. A deck may use one approved content reference for many pages, or it may map each slide to a different client template page.

Text-only style descriptions are not enough for full production. Every slide must have an actual reference image.

## Image Access Rules

Image paths are required for traceability, but a path string is not the same as visual input.

For every slide job:

- The job JSON must list all reference images and required images with absolute paths and roles.
- The parent agent must verify every image exists before dispatch.
- The parent agent must prepare every image as explicit visual context for the slide worker whenever the runtime supports image handoff.
- The slide worker must actually open, view, or otherwise inspect every listed reference image and required image before generation.
- If a worker can see only a path string but cannot access, view, or attach the image to the selected image backend, it must return a blocker.
- Do not allow a worker to replace a missing required image with a similar generated image.

Reference image usage:

- Use as style/layout/template reference.
- Match palette, typography, spacing, layout density, visual hierarchy, and image treatment.
- Do not copy unrelated text or content from the reference image.

Required client image usage:

- Treat as strict input assets.
- Preserve original content, logos, UI, data, labels, portraits, certificates, charts, and other business-critical details.
- Do not redraw, approximate, replace, or hallucinate these images.

## Output Structure

Use the production structure from `codex-ppt`:

```text
{deck_name}/
├── origin_image/
│   ├── slide_01.png
│   ├── slide_02.png
│   └── ...
├── prompts/
│   ├── slide_01.json
│   └── ...
├── slide_jobs.json
├── slide_run_state.json
├── deck_spec.json
├── outline.md
├── speech.md
└── {deck_name}.pptx
```

Also keep or copy these planning artifacts in the project folder:

```text
order_materials.md
slide_plan.md
approved_style_reference.md
reference_mapping.md
samples/approved/
assets/
```

## Workflow

### 1. Validate Approved Inputs

Read `slide_plan.md`, `approved_style_reference.md`, and `reference_mapping.md`.

Stop if:

- `approved_style_reference.md` is missing.
- `reference_mapping.md` is missing.
- any slide lacks text content.
- any slide lacks a reference image mapping.
- any mapped reference image is missing.
- any required slide image asset is missing.
- any required image has no role or preservation rule.
- open questions indicate the client has not approved text, image usage, reference mapping, or production constraints.

### 2. Confirm Image Backend

Use the same image backend policy as `codex-ppt`:

- Use the native/built-in image generation/editing tool first.
- Use CLI/API fallback only when the native backend is unavailable, cannot attach required visual inputs, lacks a required capability, or the user explicitly authorizes fallback.
- Before API/CLI fallback sends client materials outside the native tool path, ask the user whether that is allowed.
- Keep the selected backend fixed for all slides.

Record the selected backend in `deck_spec.json` and every slide job.

### 3. Build Production Artifacts

Create or update:

- `outline.md`
- `deck_spec.json`
- `prompts/slide_XX.json`
- `slide_jobs.json`
- `slide_run_state.json`

`outline.md` should reflect the approved slide plan. Do not invent a new deck outline.

`deck_spec.json` should be built from:

- `slide_plan.md`
- `approved_style_reference.md`
- `reference_mapping.md`
- required client assets
- selected image backend

When the project only has the approved Markdown artifacts, use the converter first and treat any converter error as a production blocker:

```bash
python skills/ppt-full-production/scripts/build_deck_spec.py --project-root <order_folder> --slide-plan <order_folder>/slide_plan.md --approved-style-reference <order_folder>/approved_style_reference.md --reference-mapping <order_folder>/reference_mapping.md --approval-log <order_folder>/approval_log.json --out <deck_dir>/deck_spec.json
```

Every slide job must be self-contained. Do not rely on conversation context.

### 4. Per-Slide Job Contract

Each `prompts/slide_XX.json` must include `text_content`, `reference_images`, and `required_images` when the slide has required client assets. Do not collapse references and strict client assets into one ambiguous image list.

The three mandatory payload groups for every worker are:

1. `text_content`
2. `reference_images`
3. `required_images` if the slide has required client assets

If `text_content` is missing, return a blocker. If `reference_images` is empty, return a blocker. If any required image is inaccessible, return a blocker.

If a required client image demands exact preservation and the selected image backend cannot preserve it reliably, return a blocker instead of approximating it. Examples include logos, screenshots, charts, certificates, portraits, UI, product labels, and data-heavy figures.

### 5. Dispatch Slide Workers

Use the production discipline from `codex-ppt`:

- One slide job per worker is the default production path.
- If subagents are available, use them. Do not generate the full deck serially in the parent agent unless subagents are unavailable or the user explicitly asks for a single-agent run.
- If subagents are unavailable, stop and report the blocker before image generation; do not silently switch workflows.
- The parent owns `outline.md`, `deck_spec.json`, `prompts/`, `origin_image/`, state files, QA, `speech.md`, and final assembly.
- Workers must not edit shared project files.
- The parent records dispatch and results with state scripts.

Worker handoff must include:

```text
Generate slide <N> for this approved client PPT deck.

Deck dir: <absolute deck dir>
Slide job file: <absolute deck dir>/prompts/slide_<NN>.json
Output target owned by parent: <absolute deck dir>/origin_image/slide_<NN>.png
Selected image backend: <confirmed backend>

Mandatory input payload:
- text_content: from the approved slide plan
- reference_images: actual image inputs prepared by parent
- required_images: actual client asset image inputs prepared by parent, if any

Input images prepared by parent:
- <absolute path> - approved reference image; use for style/layout/template reference
- <absolute path> - strict required client asset; preserve original content
- <absolute path> - rendered source page or placement evidence, if needed

Read the JSON job. Open/view every listed bitmap before generation. Use the selected image backend only.
If any reference image or required image cannot be accessed, viewed, or attached to the image backend, return blocker=<reason>.

Return only:
backend_used=<backend>
selected_source=<absolute path to generated image>
qa_note=<one sentence>
```

### 6. Record Results

After a worker returns:

- Visually inspect the selected image.
- Confirm text readability.
- Confirm style matches the mapped reference image.
- Confirm required client images are included and preserved.
- Record the result with `record_slide_result.py`.
- If a worker reports image access failure, backend failure, or required asset failure, record a blocker with `record_slide_blocker.py`.

Final images must be copied into `origin_image/slide_XX.png`.

Do not hand-edit slide status files.

### 7. QA And Repair

Before assembly, inspect every final slide image.

Check:

- approved text content appears accurately
- Chinese text is readable and not garbled
- title and key points are not truncated
- style follows the slide's mapped reference image
- required client images are present and not replaced by redraws
- generated image aspect ratio and slide order are correct
- no required source asset has been silently degraded or substituted
- no unwanted page number, watermark, unrelated logo, or obvious artifact
- important elements do not overlap

Regenerate severe failures. Use backend editing for localized fixes when available. Do not repair final slides with local drawing, HTML/SVG/canvas screenshots, Pillow overlays, python-pptx/PptxGenJS layouts, or manual compositing.

### 8. Speaker Notes And Assembly

Create `speech.md` when notes are expected or useful. Use headings that map to slide numbers.

Assemble the PPTX with this skill's local assembly wrapper:

```bash
python skills/ppt-full-production/scripts/assemble_ppt.py {base_dir} {deck_name}.pptx --aspect-ratio 16:9
```

`assemble_ppt.py` accepts either the parent directory (`{base_dir}/{deck_name}`) or the deck project directory itself as its first argument. Before assembly, it validates exact `slide_id` to `origin_image/slide_XX` mappings and result provenance; extra or wrong-numbered formal slide images block assembly.

Before assembly, ensure `slide_jobs.json` shows all generated slides as recorded and no slides as pending, dispatched, or blocked.

## Hard Rules

- Do not start without `slide_plan.md`, `approved_style_reference.md`, and `reference_mapping.md`.
- Do not start if any slide lacks a reference image.
- Do not start if any required client image is missing.
- Do not use path strings as a substitute for visual image input.
- Do not let workers invent missing required images.
- Use the native/built-in image generation backend first; API/CLI fallback requires native unavailability/insufficiency or explicit user authorization.
- Every final slide image must be produced by the selected image backend.
- Do not create final slides with local drawing, HTML/SVG/canvas screenshots, Pillow, python-pptx/PptxGenJS, or manual overlays.
- Keep the selected image backend fixed for all slides.
- Record dispatches, blockers, and results with state files/scripts.
- Do not call the deck complete if any slide is blocked or unrecorded.

## Final Report

Report:

- project directory
- final PPTX path
- slide image directory
- `outline.md`
- `speech.md`
- `slide_jobs.json`
- `reference_mapping.md`
- number of slides
- selected image backend
- whether every slide used mapped reference images
- whether every required client asset was included or any blocker remains
- any regenerated slides or known limitations
