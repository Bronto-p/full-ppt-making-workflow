---
name: ppt-complete-workflow
description: "Run the full client PPT workflow for any PPT job: new decks, whole-deck redesigns, selected-slide redesigns, continuation of an existing workflow, sample rounds, production, QA, or assembly. Inspect the available files, define the exact scope, write or update an exact-content ppt_plan.md for that scope, generate sequential style samples when approval is needed, collect approval, then produce the requested image-based PPT/PPTX output. Use when the user wants PPT planning, beautification, redesign, polishing, sample slides, full production, or plan-to-deck work from existing PPT/PPTX files, client documents, templates, images, logos, screenshots, charts, or other order assets."
---

# PPT Complete Workflow

## Purpose

Handle any client PPT job through one controlled workflow that scales to the request. The job may be a new deck, a full redesign, a selected-slide redesign, a sample-only round, a continuation from existing workflow files, or final production.

The controlled workflow is:

1. Define the job scope and plan the requested deck or slide range in `ppt_plan.md`.
2. Generate a sample round, using Sample 1 as the visual anchor for Samples 2 and 3.
3. Update the plan from feedback until the user approves the sample direction.
4. Produce every requested final slide image and assemble or update the PowerPoint output.

This skill replaces the old split workflow of `ppt-plan-order`, `ppt-style-sample`, and `ppt-full-production`.

## Scope Rule

Before planning, identify the job mode and write it into `ppt_plan.md` under `Deck Requirements` as `Job mode:` and `Requested scope:`.

Supported job modes:

- `new deck`: create a deck from source documents and assets.
- `whole-deck redesign`: redesign all slides from an existing PPT/PPTX.
- `selected-slide redesign`: redesign only specified slides, such as "last three pages", "slides 8-10", or "the appendix".
- `continuation`: continue from existing `ppt_plan.md`, sample files, approved samples, or production files.
- `sample-only`: create style samples without final production.
- `production-only`: produce final slides from an already approved plan and sample reference.
- `QA/repair`: inspect, compare, fix, or regenerate existing sample/final slides.

Full workflow means the full control loop for the requested scope, not necessarily a brand-new deck. For selected-slide jobs, inspect the whole source deck enough to understand context, theme, numbering, and neighboring slides, but plan and produce only the requested slides unless the user asks to change the whole deck.

If the request references a relative range such as "last three pages", first determine the source deck's total slide count and convert it to exact slide numbers in `Requested scope:`. If the range cannot be determined, stop and ask for the missing source deck or slide range.

For existing PPT/PPTX redesign jobs, treat the source deck as client content. Extract the requested slides' actual text/data/order and the original embedded media files when possible, preserve them, and use neighboring or whole-deck slides only as context unless they are also in scope.

Rendered whole-slide images are page-state references only. They may be used to understand layout, detect off-canvas content, compare before/after results, or guide style matching, but they are not client image assets and must not be cropped into substitute assets. If the slide contains photos, certificates, documents, charts, screenshots, logos, or other client materials, extract the original embedded images from the PPT/PPTX package relationships/media or equivalent structured API instead of cropping them from a slide render.

## Core Rule

`ppt_plan.md` is the source of truth. Slide workers must not infer missing content, invent client products, invent client photos, or replace required client assets with lookalikes.

For partial PPT jobs, `ppt_plan.md` is still required, but it may cover only the requested slide range. Do not skip planning because the job is small.

## Inputs

Accept an order folder containing any mix of:

- client requirement files, chat logs, Word/PDF/TXT/Markdown/spreadsheet content
- old PPT/PPTX decks to redesign or reuse as content
- template decks, rendered template pages, style references, screenshots
- logos, product photos, portraits, certificates, charts, UI screenshots, and other client assets

Start from the client requirement file when identifiable. If the user directly names a PPT/PPTX and a slide range, start from that deck and range. Then inspect the folder and connect every relevant file to requirements, slide content, template/reference use, or image use.

For PPT/PPTX sources, classify extracted media before planning:

- `content asset`: client photos, proof documents, certificates, charts, screenshots, paper images, product images, portraits, application proofs, or any image the slide content depends on.
- `decorative/template asset`: backgrounds, wave shapes saved as pictures, header strips, repeated logos, design ornaments, page chrome, and other theme materials.
- `whole-slide reference`: rendered slide images used only to inspect current layout and off-page/overflow problems.

Only `content asset` files belong under slide `Images` unless the slide explicitly needs an exact logo/header image. Decorative/template assets belong under `Template/reference files` or `Overall template/style`. Whole-slide references belong under `Template/reference files` or `Main source files`; never list them as content images.

## Outputs

Create or update these files in the order folder as needed for the job mode:

```text
ppt_plan.md
sample_plan.md
sample_feedback.md
approved_sample_reference.md
samples/
production/{deck_name}/
```

For selected-slide redesigns, use a deck name that makes the scope clear, such as `{source_name}_slides_08-10_redesign`, and preserve a traceable link to the original source deck in `ppt_plan.md`.

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

Always create or update `ppt_plan.md` with this structure. For selected-slide jobs, include only the requested slides in `Slide Plan`, using their original slide numbers.

```markdown
# PPT Plan

## Deck Requirements
- Job mode:
- Requested scope:
- Source deck:
- Source deck slide count:
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

### Slide {original or output slide number}: {slide title}
- Source slide:
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
- If the client supplied an existing PPT/PPTX, extract the actual text, numbers, labels, titles, and data from each requested source slide into `Content`; do not replace it with a summary such as "beautify this slide".
- If the client supplied long-form material, break it into slides and write the exact extracted/condensed slide text for each slide, not a topic summary.
- If a slide depends on a table, chart, timeline, process, quote, product name, certificate text, or UI copy, include the actual values or labels in `Content`.
- If content is unreadable or missing, write `Content: NEEDS SOURCE - {specific missing item}` and stop before sample or production until the missing source is resolved.

### Asset Truth Rules

- Use local paths for every referenced source, template, reference image, and client image asset.
- If a slide has no client image asset, write `Images: none`.
- For existing PPT/PPTX files, extract original embedded media files from the deck package/relationships or structured presentation APIs. Do not crop photos, certificates, tables, screenshots, documents, logos, or paper images out of a rendered whole-slide image when the original embedded media is available.
- Do not list background images, page chrome, repeated title bars, decorative wave images, or whole-slide renders as slide `Images` unless they are required exact client content. Put them in `Template/reference files` or describe them in `Overall template/style`.
- If an extracted image is a background, decorative header, logo strip, or theme ornament, label it as a `decorative/template asset`; do not treat it as proof material, document evidence, or client content.
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
- any whole-slide render or cropped screenshot is listed as a content image instead of a reference
- any decorative/template asset is misclassified as proof/client content
- any existing asset path is missing or unassigned when its intended slide is clear
- `Template/reference path` or `Images` invents a path
- the slide layout conflicts with the asset truth rule

Do not proceed to samples if any slide contains `NEEDS SOURCE`.

### Plan Approval Gate

After `ppt_plan.md` passes Planning QA, stop and report the plan to the user. This report is a confirmation gate, not a progress update.

Do not create `sample_plan.md`, generate samples, edit the source deck, create final slide images, assemble/update a PPTX, or produce any draft/final PPT output until the user explicitly confirms the plan or explicitly waives the planning gate. Phrases such as "继续", "确认", "按这个计划做", "可以生成样张", "skip approval", or an equivalent explicit instruction count as approval. Silence, inferred urgency, or a small selected-slide scope does not count as approval.

If the user changes the requested scope, content, style, asset usage, or output format during this gate, update `ppt_plan.md`, run Planning QA again, and ask for confirmation again.

## Phase 2: Sequential Sample Round

Create a three-slide sample round by default for new decks and whole-deck redesigns. If the requested scope has fewer than three slides, sample every requested slide.

For selected-slide redesigns:

- If exactly one to three slides are in scope, the sample round should normally use those same slides.
- Do not treat a small scope as permission to skip the workflow; still create `sample_plan.md`, generate sequentially, QA, show the user, and wait for approval before final assembly unless the user explicitly asked to skip approval.
- If the user asked for a quick direct edit and explicitly waived samples, record that waiver in `sample_feedback.md` or `approved_sample_reference.md`, then continue with production for the requested scope only.

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

Do not produce the final deck or final selected-slide output before the user approves samples, unless the user explicitly waived sample approval for this job.

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

For selected-slide redesigns, production covers only the requested slides. If updating the original deck is required, preserve unchanged slides and replace only the requested slide numbers. If the assembly scripts cannot safely replace selected slides, create a scoped output deck with the redesigned slides and clearly report that it is not a full replacement deck.

## Worker Handoff Rules

- Before dispatching workers, read `docs/slide-generation-and-subagents.md` and `prompts/slide-worker.md`.
- Before using client images, read `docs/user-supplied-assets.md`.
- In built-in image mode, call `view_image` for approved sample images and required slide assets, then label visible images by role in the worker handoff.
- In CLI/API fallback mode, verify that each image path is passed as an image input; otherwise record a blocker.
- If a worker cannot access a required image, record a blocker instead of generating a fake substitute.

## Hard Constraints

- Never let slide content remain as topic-only descriptions in the plan.
- Never skip `ppt_plan.md` for selected-slide beautification, polishing, or redesign requests.
- Never expand a selected-slide request into a whole-deck rewrite unless the user approves that expanded scope.
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

After planning, report the `ppt_plan.md` path, job mode, requested scope, slide count, assigned template/reference files, assigned image assets, and that no PPT has been generated. End by explicitly asking the user to confirm the plan before samples or production. Do not continue past this point until the user confirms or explicitly waives this gate.

After each sample round, report the sample round folder, sample image paths, whether `ppt_plan.md` changed, pending feedback, and that no final deck was generated.

After sample approval, report `approved_sample_reference.md`, `samples/approved/`, approved sample paths, and that production must include these approved samples as style references.

After production, report the production directory, final `.pptx`, `origin_image/`, `deck_spec.json`, `outline.md`, `speech.md`, `slide_jobs.json`, slide count, backend used, and any blockers or known limitations.
