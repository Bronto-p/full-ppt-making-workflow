# Full PPT Making Workflow

This repository defines a three-stage workflow for making client PPT decks with image-based slide generation.

The core idea is simple:

1. Plan the client's PPT order before design work starts.
2. Confirm sample slides and reference images before full production.
3. Produce the final deck with one generated image per slide, using the approved plan and approved references.

## Stage 1: `ppt-order-planner`

Use this skill when a client order folder arrives.

Inputs:

- client requirement document
- client content files such as DOCX, PDF, TXT, MD, or PPTX
- template files, reference images, old PPT files, logos, product images, screenshots, charts, or other assets

Outputs:

- `order_materials.md`
- `slide_plan.md`

Primary responsibility:

- read the client requirement document first
- verify what materials exist
- plan every slide's text content
- plan every slide's image usage
- plan every slide's template/style direction
- create a draft reference-image mapping plan
- define the sample strategy

Approval gate:

Before moving to Stage 2, the client or user must approve the full `slide_plan.md`, including:

- every slide's text content
- every slide's required and optional image usage
- every slide's template/style plan
- the draft reference-image mapping
- the sample strategy

Stage 1 must not generate sample slides, final slide images, `deck_spec.json`, `speech.md`, or PPTX files.

## Stage 2: `ppt-sample-iteration`

Use this skill after `slide_plan.md` is approved.

Inputs:

- approved `order_materials.md`
- approved `slide_plan.md`
- referenced client assets and template/reference files
- client feedback, when iterating

Outputs:

- `sample_plan.md`
- `sample_feedback.md`
- `approved_style_reference.md`
- `reference_mapping.md`
- approved reference images under `samples/approved/`

Primary responsibility:

- plan the sample round
- generate or coordinate sample slides
- incorporate client feedback
- update `slide_plan.md` when feedback changes the plan
- create the final approved style reference
- create the final slide-to-reference mapping

Approval gate:

Before moving to Stage 3:

- the client must approve the sample direction
- `approved_style_reference.md` must exist
- `reference_mapping.md` must exist
- every slide must map to at least one approved reference image
- every mapped reference image must exist or be clearly blocked

A reference image can be reused by many slides. A client template can also provide different rendered reference images for different slides or page types.

Stage 2 must not generate the full deck, final `origin_image/slide_XX.png` set, `deck_spec.json`, `speech.md`, or PPTX files.

## Stage 3: `ppt-full-production`

Use this skill after sample approval and final reference mapping.

Inputs:

- approved `slide_plan.md`
- `approved_style_reference.md`
- `reference_mapping.md`
- approved reference images
- required client image assets

Outputs:

- `outline.md`
- `deck_spec.json`
- `prompts/slide_XX.json`
- `slide_jobs.json`
- `slide_run_state.json`
- `origin_image/slide_XX.png`
- `speech.md`
- final `.pptx`

Primary responsibility:

- validate all approved inputs
- build per-slide production jobs
- dispatch one slide job per worker when available
- ensure each worker receives the required payload
- record dispatches, blockers, and results
- QA every generated slide image
- assemble the final PPTX

Every slide worker must receive:

1. `text_content`: the approved text for that slide
2. `reference_images`: actual approved reference image inputs, not just text descriptions
3. `required_images`: actual client asset image inputs when the slide requires them

Important rule:

A file path is traceability, not visual input. The parent agent must verify and prepare actual image inputs for workers whenever the runtime supports image handoff. If a worker cannot access, view, or attach a reference image or required client image to the selected image backend, it must return a blocker instead of inventing a replacement.

Stage 3 follows the `codex-ppt` production model: one final generated image per slide, state-recorded slide jobs, QA, speaker notes, and PPTX assembly.

## Cross-Stage Contract Files

### `order_materials.md`

Defines what the client provided and how each material should be used.

### `slide_plan.md`

Defines the client-approved production plan:

- slide text
- image usage
- template/style plan
- draft reference-image mapping
- sample strategy

### `approved_style_reference.md`

Defines the approved visual system:

- palette
- background
- typography
- layout rules
- image treatment
- text density
- prohibited visual choices
- page type references

### `reference_mapping.md`

Defines which approved reference image each slide must use.

This is mandatory for full production. Text-only style descriptions are not sufficient.

### `prompts/slide_XX.json`

Defines the self-contained production job for one slide:

- approved text content
- reference images
- required images
- optional images
- layout intent
- constraints

## Non-Negotiable Rules

- Do not start Stage 2 before the full slide plan is approved.
- Do not start Stage 3 before samples and reference mapping are approved.
- Do not start full production if any slide lacks a reference image.
- Do not treat a path string as a substitute for actual image input.
- Do not let workers invent missing required client images.
- Do not create final slides with local drawing, HTML/SVG/canvas screenshots, Pillow, python-pptx/PptxGenJS, or manual overlays.
- Every final slide image must be produced by the selected image generation backend.
- Do not call a deck complete if any slide is blocked, missing, or unrecorded.
