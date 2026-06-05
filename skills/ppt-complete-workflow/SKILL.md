---
name: ppt-complete-workflow
description: "Run the full client PPT workflow in one skill: inspect an order folder, write an exact-content ppt_plan.md, generate sequential style samples with a shared visual reference, collect approval, then produce the final image-based PPT/PPTX deck. Use when the user wants PPT planning, sample slides, full production, or the whole plan-to-deck workflow from client documents, templates, images, logos, screenshots, charts, or other order assets."
---

# PPT Complete Workflow

## Purpose

Turn a client order folder into a finished image-based `.pptx` through one controlled workflow:

1. Plan the deck in `ppt_plan.md`.
2. Generate a sample round, using Sample 1 as the visual anchor for Samples 2 and 3.
3. Update the plan from feedback until the user approves the sample direction.
4. Produce every final slide image and assemble the PowerPoint.

This skill replaces the old split workflow of `ppt-plan-order`, `ppt-style-sample`, and `ppt-full-production`.

## Core Rule

`ppt_plan.md` is the source of truth. Slide workers must not infer missing content, invent client products, invent client photos, or replace required client assets with lookalikes.

## Inputs

Accept an order folder containing any mix of:

- client requirement files, chat logs, Word/PDF/TXT/Markdown/spreadsheet content
- old PPT/PPTX decks to redesign or reuse as content
- template decks, rendered template pages, style references, screenshots
- logos, product photos, portraits, certificates, charts, UI screenshots, and other client assets

Start from the client requirement file when identifiable, then inspect the folder and connect every relevant file to deck requirements, slide content, template/reference use, or image use.

## Outputs

Create or update these files in the order folder:

```text
ppt_plan.md
sample_plan.md
sample_feedback.md
approved_sample_reference.md
samples/
production/{deck_name}/
```

Final production output lives under:

```text
production/{deck_name}/
├── origin_image/
├── prompts/
├── deck_spec.json
├── outline.md
├── speech.md
├── slide_jobs.json
├── slide_run_state.json
└── {deck_name}.pptx
```

## Phase 1: Plan

Always create or update `ppt_plan.md` with this structure:

```markdown
# PPT Plan

## Deck Requirements
- Goal:
- Audience:
- Slide count:
- Overall theme:
- Overall template/style:
- Main source files:
- Template/reference files:
- Image asset files:
- Asset truth rule:

## Slide Plan

### Slide 1: {slide title}
- Content:
- Template/theme:
- Page layout/structure:
- Template/reference path:
- Images:
  - Path:
  - Role:
  - Use on slide:
  - Asset fidelity rule:
```

### Exact Content Rules

- `Content` must contain the exact slide-ready text, numbers, labels, data points, claims, and section headings intended to appear on the slide.
- Do not write only descriptions such as "introduce the product", "show the team background", "summarize the market", or "explain the process".
- If the client supplied page-by-page content, preserve the order and copy the actual text/data for each page into the matching slide's `Content`.
- If the client supplied long-form material, break it into slides and write the exact extracted/condensed slide text for each slide, not a topic summary.
- If a slide depends on a table, chart, timeline, process, quote, product name, certificate text, or UI copy, include the actual values or labels in `Content`.
- If content is unreadable or missing, write `Content: NEEDS SOURCE - {specific missing item}` and stop before sample or production until the missing source is resolved.

### Asset Truth Rules

- Use local paths for every referenced source, template, reference image, and client image asset.
- If a slide has no client image asset, write `Images: none`.
- Do not describe or request "client product-like", "similar product", "product-style", "brand-like", "company-like", "realistic client background", or any fake substitute.
- If the plan says not to use a client photo/product/logo, the visual direction must not ask for anything resembling that client photo/product/logo.
- Client products, people, logos, certificates, charts, UI screenshots, and identifiable brand materials may appear only when an actual supplied file is listed in `Images` for that slide.
- If no real client asset is available, choose abstract, typographic, geometric, iconographic, diagrammatic, or non-identifiable stock-neutral visuals.
- Every listed image needs `Path`, `Role`, `Use on slide`, and `Asset fidelity rule`.
- `Asset fidelity rule` must say one of:
  - `must use exact supplied image; no redraw or lookalike`
  - `may crop/fit/color-balance only; no content changes`
  - `style reference only; do not reproduce client product/person/logo`

### Planning QA

Before sample generation, scan `ppt_plan.md` and fix failures:

- any slide `Content` is only a topic description
- any slide asks for fake or lookalike client/product imagery
- any existing asset path is missing or unassigned when its intended slide is clear
- `Template/reference path` or `Images` invents a path
- the slide layout conflicts with the asset truth rule

Do not proceed to samples if any slide contains `NEEDS SOURCE`.

## Phase 2: Sequential Sample Round

Create a three-slide sample round by default. If the deck has fewer than three slides, sample every slide.

Pick:

- Sample 1: cover/opening or strongest style-setting slide
- Sample 2: standard content slide
- Sample 3: difficult slide with images, data, process, comparison, timeline, or dense layout

Write `sample_plan.md`:

```markdown
# Sample Plan

## Source Plan
- Plan path:
- Slide count:
- Overall theme:
- Overall template/style:
- Template/reference files:
- Image asset files:
- Asset truth rule:

## Selected Sample Slides

### Sample 1: Slide {N} - {slide title}
- Why this slide:
- Content:
- Template/theme:
- Page layout/structure:
- Template/reference path:
- Images:

### Sample 2: Slide {N} - {slide title}
- Why this slide:
- Content:
- Template/theme:
- Page layout/structure:
- Template/reference path:
- Images:
- Required style reference:

### Sample 3: Slide {N} - {slide title}
- Why this slide:
- Content:
- Template/theme:
- Page layout/structure:
- Template/reference path:
- Images:
- Required style reference:

## Image Backend
- Selected backend:
- Why:
- Fallback status:

## Round
- Current round:
- Output folder:
```

### Sequential Sample Rules

- Generate Sample 1 first.
- Inspect Sample 1 for content accuracy, text legibility, style quality, and asset fidelity.
- If Sample 1 is wrong, repair or regenerate it before making Sample 2 or Sample 3.
- After Sample 1 passes agent QA, attach the actual Sample 1 image as `Required style reference` for Sample 2 and Sample 3.
- Generate Sample 2 and Sample 3 using Sample 1 as the shared style reference, plus their own required slide assets.
- Sample 2 and Sample 3 must match Sample 1's design system: typography, spacing, color behavior, density, image treatment, and visual language.
- Sample 2 and Sample 3 must not copy Sample 1's content or product/photo unless their own slide plan lists the same required asset.
- Do not start three independent sample workers in parallel. The first sample must exist before the other two are dispatched.

### Sample Workflow

1. Preflight the selected sample slides against the Planning QA rules.
2. Select the image backend. Read `docs/backend-selection.md` when needed.
3. Create `samples/round_XX/sample_spec.json` and prompt jobs.
4. Generate and QA Sample 1.
5. Add Sample 1 as a visible/attached style reference for Sample 2 and Sample 3.
6. Generate and QA Sample 2 and Sample 3.
7. Show all samples to the user and ask whether style, layout structure, image usage, and text quality pass.
8. Append feedback to `sample_feedback.md`.
9. If feedback changes content, theme, layout, template choice, image usage, density, or page structure, update `ppt_plan.md` before the next round.
10. When the user approves, copy approved images to `samples/approved/` and write `approved_sample_reference.md`.

## Approved Sample Reference

Write `approved_sample_reference.md` after user approval:

```markdown
# Approved Sample Reference

## Approved Samples
- Slide:
- Sample path:
- Source round:
- Use in production:

## Final Style Direction
- Theme:
- Layout system:
- Typography:
- Color/visual treatment:
- Image treatment:
- Asset fidelity rules:

## Production Handoff
- Use these samples as style references for every production slide.
- Upload/include the approved sample images when dispatching production slide workers.
- Match the theme, typography, density, spacing, and image treatment.
- Do not copy sample slide content or exact layout unless the target slide uses the same page type.
- Do not use fake client product/person/logo imagery.

## Sample Generation Method
- Backend used:
- Tool name:
- Mode:
- Prompt source:
- Input context preparation:
- Handoff rule:
```

## Phase 3: Full Production

Do not produce the final deck before the user approves samples.

1. Preflight `ppt_plan.md`, `approved_sample_reference.md`, and `samples/approved/`.
2. Treat `ppt_plan.md` as authoritative for exact slide content, layout, template/reference path, image path, image role, placement, and asset fidelity.
3. Build production files:

```bash
python3 scripts/build_production_spec.py \
  --plan <order_folder>/ppt_plan.md \
  --approved-samples <order_folder>/approved_sample_reference.md \
  --out-dir <order_folder>/production/<deck_name> \
  --deck-name <deck_name> \
  --force
```

4. Prepare one JSON prompt job per slide:

```bash
python3 scripts/prepare_slide_prompts.py \
  --spec <order_folder>/production/<deck_name>/deck_spec.json \
  --out-dir <order_folder>/production/<deck_name> \
  --selected-backend "<approved backend label>" \
  --force
```

5. Use the same backend/tool/mode as the approved sample reference unless the user explicitly approves a change.
6. Include the approved samples as style references in every production slide job.
7. Include the actual required client images for each slide. Do not rely on path text alone.
8. Dispatch one slide job per worker when subagents are available. Each worker receives exactly one `prompts/slide_XX.json`.
9. Record dispatches, results, blockers, and repairs with the bundled state scripts.
10. QA every final slide for exact content match, legibility, truncation, overlap, required asset use, asset fidelity, and style consistency.
11. Write or revise `speech.md` with `## Slide N: {Title}` headings.
12. Assemble only after every slide is recorded or accepted:

```bash
python3 scripts/assemble_ppt.py \
  <order_folder>/production \
  <deck_name>.pptx \
  --aspect-ratio 16:9
```

## Worker Handoff Rules

- Before dispatching workers, read `docs/slide-generation-and-subagents.md` and `prompts/slide-worker.md`.
- Before using client images, read `docs/user-supplied-assets.md`.
- In built-in image mode, call `view_image` for approved sample images and required slide assets, then label visible images by role in the worker handoff.
- In CLI/API fallback mode, verify that each image path is passed as an image input; otherwise record a blocker.
- If a worker cannot access a required image, record a blocker instead of generating a fake substitute.

## Hard Constraints

- Never let slide content remain as topic-only descriptions in the plan.
- Never use fake/lookalike client products, people, logos, screenshots, charts, or certificates.
- Never generate a slide from a text-only path when the slide requires actual image content.
- Every sample and final slide image must be one complete 16:9 full-slide image generated by the selected image backend.
- Do not generate separate slide parts and assemble them locally.
- Do not use local drawing, SVG, HTML/CSS/canvas screenshots, Pillow, python-pptx, PptxGenJS, or manual overlays as substitutes for image-backend slide generation.
- Do not change the approved backend/method during production unless the user explicitly approves.
- Do not assemble `.pptx` while any slide is pending, dispatched, blocked, or missing.
- Do not call samples approved from the agent's judgment. Approval must come from the user.

## Vendored Resources

This skill vendors the codex-ppt production machinery:

- `scripts/*.py`
- `docs/*.md`
- `prompts/slide-worker.md`
- `references/*.md`
- `requirements.txt`

Read these only when needed:

- `docs/backend-selection.md` before backend selection or backend changes.
- `docs/user-supplied-assets.md` before using client images.
- `docs/slide-generation-and-subagents.md` before worker dispatch and state recording.
- `docs/project-assembly-and-reporting.md` before QA, notes, assembly, and final reporting.
- `docs/cli-api-fallback.md` only when CLI/API fallback is selected.
- `references/codex-ppt-license.txt` for upstream license attribution.

## Final Responses

After planning, report the `ppt_plan.md` path, slide count, assigned template/reference files, assigned image assets, and that no PPT has been generated.

After each sample round, report the sample round folder, sample image paths, whether `ppt_plan.md` changed, pending feedback, and that no final deck was generated.

After sample approval, report `approved_sample_reference.md`, `samples/approved/`, approved sample paths, and that production must include these approved samples as style references.

After production, report the production directory, final `.pptx`, `origin_image/`, `deck_spec.json`, `outline.md`, `speech.md`, `slide_jobs.json`, slide count, backend used, and any blockers or known limitations.
