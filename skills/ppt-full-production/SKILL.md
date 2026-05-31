---
name: ppt-full-production
description: Produce the final image-based PPT/PPTX deck after a user has approved PPT style samples. Use when an order folder already has ppt_plan.md from ppt-plan-order plus approved_sample_reference.md and samples/approved/ from ppt-style-sample, and the user wants full production, final slide images, speaker notes, and assembled PowerPoint output.
---

# PPT Full Production

## Purpose

Turn an approved PPT plan and approved sample round into a finished image-based `.pptx`.

This is the third step in the workflow:

1. `ppt-plan-order` creates `ppt_plan.md`.
2. `ppt-style-sample` generates sample rounds, applies feedback to the plan, and writes `approved_sample_reference.md`.
3. `ppt-full-production` creates every final slide image, QA-checks the deck, writes speaker notes, and assembles the final PowerPoint.

Use the same codex-ppt production machinery vendored in this skill: one full-slide 16:9 image per page, one slide job per worker, recorded state files, and local `.pptx` assembly.

After `ppt-style-sample` approves the direction, `ppt_plan.md` is the production source of truth. This skill should not redo the sample audit or invent new slide decisions. It only verifies that the plan is complete enough for worker handoff and then enforces the plan slide by slide.

## Input

Prefer an order folder containing:

- `ppt_plan.md`
- `approved_sample_reference.md`
- `samples/approved/`
- all template/reference files and image assets listed in `ppt_plan.md`

If `approved_sample_reference.md` or approved sample images are missing, stop and send the user back to `ppt-style-sample`. Do not generate the full deck from agent judgment alone.

## Outputs

Create the production deck project under the order folder unless the user specifies another destination:

```text
production/{deck_name}/
├── origin_image/
│   ├── slide_01.png
│   ├── slide_02.png
│   └── ...
├── prompts/
│   ├── slide_01.json
│   └── ...
├── deck_spec.json
├── outline.md
├── speech.md
├── slide_jobs.json
├── slide_run_state.json
└── {deck_name}.pptx
```

`origin_image/` is for final production slide images only. Do not put drafts, rejected variants, or sample-round files there unless an approved sample is intentionally reused as a final slide.

## Workflow

1. Preflight the handoff.
   - Read `ppt_plan.md` and `approved_sample_reference.md`.
   - Treat `ppt_plan.md` as authoritative for slide content, layout, template/reference path, required image path, image role, and image placement.
   - Confirm every planned slide has `Content`, `Template/theme`, `Page layout/structure`, `Template/reference path`, and `Images`.
   - Verify local template/reference/image paths exist when they are not `none`.
   - Confirm approved samples exist and identify the approved backend, method, style notes, and sample image paths.
   - Do not reinterpret sample feedback here. If `sample_feedback.md` conflicts with `ppt_plan.md`, stop and report that the sample skill handoff is inconsistent instead of silently redesigning production.

2. Build the production project files.
   - Default output is `{order_folder}/production/{deck_name}/`.
   - Prefer the helper to convert the plan and approved samples into codex-ppt production files:

```bash
python scripts/build_production_spec.py \
  --plan <order_folder>/ppt_plan.md \
  --approved-samples <order_folder>/approved_sample_reference.md \
  --out-dir <order_folder>/production/<deck_name> \
  --deck-name <deck_name> \
  --force
```

   - Then prepare one JSON prompt job per slide:

```bash
python scripts/prepare_slide_prompts.py \
  --spec <order_folder>/production/<deck_name>/deck_spec.json \
  --out-dir <order_folder>/production/<deck_name> \
  --selected-backend "<approved backend label>" \
  --force
```

   - If the helper is incompatible with a custom plan, manually create equivalent `deck_spec.json`, `outline.md`, `speech.md`, `prompts/slide_XX.json`, `slide_jobs.json`, and `slide_run_state.json` using the same fields expected by the vendored codex-ppt scripts.

3. Keep the approved sample method fixed.
   - Read `docs/backend-selection.md` only if the approved reference does not clearly identify the backend or if the user asks to change it.
   - Use the same backend/tool/mode as `approved_sample_reference.md`.
   - Include every approved sample image as a style reference in production slide jobs.
   - Do not switch from built-in image generation to CLI/API fallback, or the reverse, unless the user explicitly re-approves the backend change.

4. Dispatch slide workers.
   - Before dispatching, read `docs/slide-generation-and-subagents.md` and `prompts/slide-worker.md`.
   - The main agent owns `deck_spec.json`, `outline.md`, `prompts/`, `origin_image/`, `slide_jobs.json`, `slide_run_state.json`, QA, `speech.md`, and assembly.
   - Start one separate subagent per pending slide job whenever subagents are available.
   - Give each worker exactly one `prompts/slide_XX.json` job and the actual approved sample images plus any required slide images from that job's `input_images`.
   - Do not rely on path text alone when a slide depends on a client image. The parent must make each file visible to the worker/image backend before generation.
   - In built-in image mode, call `view_image` for each local approved sample image and required slide image, then label those visible images in the worker handoff by role and order.
   - In CLI/API fallback mode, ensure the JSON job lists the exact file paths and that the fallback command can pass those files as image inputs; otherwise record a blocker instead of generating from text only.
   - Record every dispatch:

```bash
python scripts/slide_job_status.py <order_folder>/production/<deck_name>

python scripts/record_slide_dispatch.py \
  <order_folder>/production/<deck_name> \
  --slide slide_01 \
  --agent-id <subagent id> \
  --agent-nickname "<nickname if available>" \
  --prompt-file prompts/slide_01.json
```

5. Record worker results.
   - Inspect each returned candidate image.
   - If acceptable, record it so the script copies it into `origin_image/slide_XX.png`:

```bash
python scripts/record_slide_result.py \
  <order_folder>/production/<deck_name> \
  --slide slide_01 \
  --agent-id <subagent id> \
  --backend-used "<approved backend label>" \
  --selected-source <absolute path to generated image> \
  --qa-note "<one sentence>"
```

   - If a worker cannot use the approved backend or cannot access required images, record a blocker:

```bash
python scripts/record_slide_blocker.py \
  <order_folder>/production/<deck_name> \
  --slide slide_01 \
  --agent-id <subagent id> \
  --reason "<blocker reason>"
```

6. QA and repair.
   - Before QA and assembly, read `docs/project-assembly-and-reporting.md`.
   - Check every final slide image for content match, text legibility, garbled text, truncation, overlap, required image usage, style consistency, and unwanted page numbers.
   - Regenerate severe failures with a tighter one-slide prompt using the same approved backend.
   - Use image editing only for localized fixes when the approved backend supports it.
   - Record repaired slide results with `record_slide_result.py`; do not manually replace a final image without updating state.

7. Write speaker notes and assemble the PPT.
   - Keep `outline.md` aligned with the final `ppt_plan.md`.
   - Write or revise `speech.md` with `## Slide N: {Title}` headings.
   - Before assembly, verify `slide_job_status.py` shows every slide as `recorded` or `accepted`.
   - If the runtime environment is missing, bootstrap it:

```bash
python scripts/codex_ppt_runtime.py bootstrap
```

   - Assemble:

```bash
python scripts/assemble_ppt.py \
  <order_folder>/production \
  <deck_name>.pptx \
  --aspect-ratio 16:9
```

## Hard Constraints

- Do not produce a full deck before the user has approved samples.
- Every final slide must be one complete 16:9 full-slide image generated by the approved image backend.
- Do not use local drawing, SVG, HTML/CSS/canvas screenshots, Pillow, python-pptx, PptxGenJS, or manual overlays as substitutes for final slide image generation.
- Do not generate a blank/background slide image and then place text, charts, client images, or shapes on top with local tools. The image backend must generate or edit the whole final slide page as one complete image.
- Start one separate subagent per pending slide job whenever subagents are available. If required subagents cannot be spawned, stop and report a blocker unless the user changes the workflow.
- Do not let workers invent missing required client images.
- Do not let workers use only file path text when a slide depends on actual image content.
- Do not change the approved backend/method between slides.
- Do not assemble `.pptx` while any slide is `pending`, `dispatched`, or `blocked`.
- Do not place rejected variants or non-final drafts in `origin_image/`.

## Vendored Codex-PPT Resources

This skill vendors the upstream codex-ppt resource layout from [ningzimu/codex-ppt-skill](https://github.com/ningzimu/codex-ppt-skill):

- `scripts/*.py`
- `docs/*.md`
- `prompts/slide-worker.md`
- `references/*.md`
- `requirements.txt`
- `references/codex-ppt-original-SKILL.md`
- `references/codex-ppt-license.txt`

Read these copied references only when needed:

- `docs/slide-generation-and-subagents.md` before prompt job dispatch, state recording, or blockers.
- `docs/project-assembly-and-reporting.md` before QA, notes, assembly, and final reporting.
- `docs/user-supplied-assets.md` before generating slides that require client images.
- `docs/backend-selection.md` only when the approved sample reference lacks a backend or the user requests a backend change.
- `docs/cli-api-fallback.md` only when CLI/API fallback is the approved backend.
- `references/codex-ppt-license.txt` for upstream license attribution.

## Final Response

After production succeeds, report:

- production project directory
- final `.pptx` path
- `origin_image/` path
- `deck_spec.json`, `outline.md`, `speech.md`, and `slide_jobs.json` paths
- slide count
- approved backend used
- whether every non-sample slide was recorded with `record_slide_result.py`
- any reused approved sample slides, regenerated slides, blockers, or known limitations

If blocked, report the exact phase, slide id if relevant, evidence path, and what must change before production can continue.
