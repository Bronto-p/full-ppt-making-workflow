# Full PPT Making Workflow

This repository defines a four-stage workflow for making client PPT decks with image-based slide generation and optional editable reconstruction.

The core idea is simple:

1. Plan the client's PPT order before design work starts.
2. Confirm sample slides and reference images before full production.
3. Produce the final image-based deck with one generated image per slide.
4. When needed, reconstruct the image-based deck into a more editable layered PPTX.

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

Sample planning rule:

- plan 3 sample slides by default for every order
- use 2 samples only when the deck is very short, page types are not varied, or the user explicitly chooses a smaller sample set
- choose representative page types, normally cover/opening, standard content, and the most complex page type

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

Sample rule:

- generate 3 sample slides by default, regardless of whether the client provided a template, reference image, verbal style direction, old PPT, or redesign request
- generate 2 samples only for short/simple decks or when the user explicitly chooses fewer samples
- do not use a single sample slide as the normal path
- samples should test the visual system across representative page types

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
- final image-based `.pptx`

Primary responsibility:

- validate all approved inputs
- build per-slide production jobs
- dispatch one slide job per worker when available
- ensure each worker receives the required payload
- record dispatches, blockers, and results
- QA every generated slide image
- assemble the final image-based PPTX

Every slide worker must receive:

1. `text_content`: the approved text for that slide
2. `reference_images`: actual approved reference image inputs, not just text descriptions
3. `required_images`: actual client asset image inputs when the slide requires them

Important rule:

A file path is traceability, not visual input. The parent agent must verify and prepare actual image inputs for workers whenever the runtime supports image handoff. If a worker cannot access, view, or attach a reference image or required client image to the selected image backend, it must return a blocker instead of inventing a replacement.

Stage 3 follows the `codex-ppt` production model: one final generated image per slide, state-recorded slide jobs, QA, speaker notes, and PPTX assembly.

## Stage 4: `ppt-editable-reconstruction`

Use this skill when the client wants a more editable PPTX after the image-based deck is produced.

Inputs:

- full Stage 3 project folder, ideally including:
  - `origin_image/slide_XX.png`
  - `slide_plan.md`
  - `approved_style_reference.md`
  - `reference_mapping.md`
  - `prompts/slide_XX.json`
  - original required client image assets
  - final image-based `.pptx`

Outputs:

- page-level manifests and editable page PPTX files
- page previews and validation files
- final editable `.pptx`
- final validation report

Primary responsibility:

- convert each image-based slide into a more editable layered PowerPoint page
- use prior production metadata instead of guessing from the flattened screenshot only
- preserve main slide text as native editable text boxes where practical
- use `$imagegen` for clean/generated backgrounds, client-image-preserving background fusion, visual assets, and repairs
- preserve client-required images from their original asset files, not from the flattened slide alone
- assemble the final editable deck

Important rule:

When a slide contains client-required images, the page worker must receive both the full slide source image and the original client image assets. The source slide shows placement and treatment; the original asset preserves identity. By default, client images should be imagegen-preserved inside the reconstructed background/scene rather than pasted later as obvious overlays, unless the manifest records that a separate movable image layer is the better choice.

Stage 4 is not required for every order. Use it when the client needs editability after the high-fidelity image-based PPT is complete.

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

### Page reconstruction outputs

Stage 4 page workers produce:

- `manifest.json`
- `imagegen-jobs.json`
- `clean_background.png` when applicable
- `assets/`
- `page.pptx`
- `preview.png`
- `split_assets_contact.png`
- `validation.json`
- `page_result.json`

## Non-Negotiable Rules

- Do not start Stage 2 before the full slide plan is approved.
- Stage 2 normally produces 3 sample slides; do not use a single sample as the normal path.
- Do not start Stage 3 before samples and reference mapping are approved.
- Do not start full production if any slide lacks a reference image.
- Do not treat a path string as a substitute for actual image input.
- Do not let workers invent missing required client images.
- Do not create final image-based slides with local drawing, HTML/SVG/canvas screenshots, Pillow, python-pptx/PptxGenJS, or manual overlays.
- Every Stage 3 final slide image must be produced by the selected image generation backend.
- Do not use the flattened full-slide screenshot as the final editable background in Stage 4.
- Stage 4 client-required image regions must be reconstructed with the original client asset as input whenever they are regenerated or fused into the background.
- Do not call a deck complete if any slide/page is blocked, missing, or unrecorded.
