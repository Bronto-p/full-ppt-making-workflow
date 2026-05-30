# Full PPT Making Workflow

This repository defines a four-stage workflow for making client PPT decks with image-based slide generation and optional editable reconstruction.

The core idea is simple:

0. Ingest the client's files into viewable, checkable materials before planning.
1. Plan the client's PPT order before design work starts.
2. Confirm sample slides and reference images before full production.
3. Produce the final image-based deck with one generated image per slide.
4. When needed, reconstruct the image-based deck into a more editable layered PPTX.

## Stage 0: Material Ingestion And Visibility Check

Use this required preflight whenever an order folder contains anything beyond plain text.

Inputs:

- DOCX, PDF, PPT/PPTX, TXT, MD, images, charts, spreadsheets, archives, links, or other client files

Outputs:

- `material_manifest.json`
- `material_contact_sheets/`
- rendered document or deck pages when needed
- extracted embedded images when available
- `ingestion_notes.md`

Script entrypoint:

```bash
python skills/ppt-order-planner/scripts/ingest_materials.py <order_folder>
```

Validation helpers:

```bash
python skills/ppt-order-planner/scripts/lint_slide_plan.py <order_folder>/slide_plan.md
python skills/ppt-order-planner/scripts/approval_log.py check --log <order_folder>/approval_log.json --stage plan --artifact slide_plan.md
```

Primary responsibility:

- prove which files the agent can read as text
- prove which files the agent can see visually
- extract or render embedded pictures, charts, tables, screenshots, and scanned pages
- mark files that are password-protected, corrupted, linked-only, externally hosted, too large, unsupported, or visually inaccessible
- record file hashes and normalized local paths for traceability

Important rule:

Do not assume a picture inside a DOCX, PDF, PPTX, spreadsheet, or archive is visible to the agent just because the container file exists. If embedded visuals matter, create rendered pages, extracted images, or contact sheets and inspect those outputs. If a client file references cloud links or externally linked media, download/export them into the order folder or mark them blocked.

## Stage 1: `ppt-order-planner`

Use this skill when a client order folder arrives.

Inputs:

- client requirement document
- client content files such as DOCX, PDF, TXT, MD, or PPTX
- template files, reference images, old PPT files, logos, product images, screenshots, charts, or other assets
- Stage 0 ingestion outputs when the order contains embedded visuals or non-plain-text files

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

Before moving to Stage 2, the agent must return to the user and ask for approval. The user is responsible for asking the client when client approval is needed. Do not infer approval from silence, filenames, or the agent's own judgment.

The user/client approval must cover the full `slide_plan.md`, including:

- every slide's text content
- every slide's required and optional image usage
- every slide's template/style plan
- the draft reference-image mapping
- the sample strategy

Record the approval in an approval log with date, approver source, approved artifact paths, and file hashes when practical.

Stage 1 must not generate sample slides, final slide images, `deck_spec.json`, `speech.md`, or PPTX files.

## Stage 2: `ppt-sample-iteration`

Use this skill after `slide_plan.md` is approved.

Inputs:

- approved `order_materials.md`
- approved `slide_plan.md`
- `material_manifest.json` or equivalent ingestion notes when the source contains embedded visuals
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

- the agent must return to the user and ask whether the client approved the sample direction
- `approved_style_reference.md` must exist
- `reference_mapping.md` must exist
- every slide must map to at least one approved reference image
- every mapped reference image must exist or be clearly blocked
- approval must be recorded; if feedback changed text, layout, image policy, style, or mapping, ask the user again before production

Validate `reference_mapping.md` before production:

```bash
python skills/ppt-sample-iteration/scripts/validate_reference_mapping.py <order_folder>/reference_mapping.md --slide-plan <order_folder>/slide_plan.md --approval-log <order_folder>/approval_log.json
```

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

Structured contract rule:

Stage 3 should prefer structured contract files derived from approved Markdown artifacts:

- `material_manifest.json`
- `approval_log.json`
- `deck_spec.json`
- per-slide `prompts/slide_XX.json`

If the structured files cannot prove the approved text, reference images, required images, preservation rules, and open-question status for every slide, stop before generation.

When only Markdown artifacts exist, build the structured contract with:

```bash
python skills/ppt-full-production/scripts/build_deck_spec.py --project-root <order_folder> --out <deck_dir>/deck_spec.json
```

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

Backend rule:

Use the native/built-in image generation tool first. Use CLI/API fallback only when the native backend is unavailable, cannot attach the required visual inputs, lacks a required capability, or the user explicitly authorizes fallback. If API fallback might send client materials outside the native tool path, stop and ask the user first.

Strict-asset rule:

If a slide requires exact logos, screenshots, certificates, charts, faces, UI, document proof, or data labels and the selected image generation backend cannot preserve them reliably as visual inputs, record a blocker. Do not replace them with generated approximations. Do not silently switch to manual overlays unless the user changes the production rules.

Stage 3 includes its own `scripts/` directory with wrapper entrypoints for the `codex-ppt` production scripts. Use the local `skills/ppt-full-production/scripts/` entrypoints for runtime checks, slide jobs, dispatch/result/blocker state, and PPTX assembly.

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
- Stage 0 material manifest and approval log when available

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

Stage 4 must connect each page to the Stage 3 prompt job and original client assets. If only flattened slide images/PPT/PDF are available, report the loss of metadata and ask the user before reconstructing any page where required client assets cannot be identified.

When Stage 3 artifacts are available, pass them explicitly:

```bash
python skills/ppt-editable-reconstruction/scripts/prepare_deck_run.py <image_based_pptx_or_images> --stage3-project <stage3_deck_dir>
```

Stage 4 includes its own `scripts/` directory with wrapper entrypoints for the `image-to-editable-ppt` reconstruction scripts. Use the local `skills/ppt-editable-reconstruction/scripts/` entrypoints for run/page state, page dispatch/result state, imagegen result recording, asset processing, validation, and final editable deck assembly.

Stage 4 is not required for every order. Use it when the client needs editability after the high-fidelity image-based PPT is complete.

## Cross-Stage Contract Files

### `order_materials.md`

Defines what the client provided and how each material should be used.

### `material_manifest.json`

Defines what files were found, which text and visual contents were actually accessible, which embedded assets were extracted or rendered, file hashes, and any unsupported/protected/linked materials.

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

### `approval_log.json`

Records every approval checkpoint. Each approval must come back through the user; the agent must not contact the client directly or assume approval. Include the approved artifact names, version or hash, approval date, and what changed since the previous approval.

## Scripts, Assets, And References

Not every skill needs all three directories.

- Stage 1 and Stage 2 are planning and approval skills. They do not need dedicated scripts or generic assets right now.
- Stage 3 owns `scripts/`, `prompts/`, `references/`, and `requirements.txt` because it performs deterministic full-deck production and assembly.
- Stage 4 owns `scripts/`, `prompts/`, `references/`, and `requirements.txt` because it performs deterministic page reconstruction, validation, and final assembly.
- Generic `assets/` directories are not added at the skill level right now. Client assets, generated samples, approved references, final slide images, and reconstruction assets belong in each order's project folder.

## Cross-Stage QA And Failure Handling

- Before planning: verify text visibility and visual visibility separately for each material.
- Before sample generation: verify selected sample slides include the hardest asset and layout risks, not only attractive pages.
- Before full production: validate `deck_spec.json`, reference images, required images, preservation rules, approvals, and open questions.
- Before final PPT assembly: validate slide count, numeric slide order, image aspect ratio, readable text, required asset presence, and no blocked slides.
- Before editable finalization: validate page count, native editable text, no full-slide screenshot fallback with duplicated editable text, asset provenance, and rendered preview similarity to the source.
- For password-protected, corrupted, scanned, linked, external, animated, video, Excel-chart, comment/tracked-change, or unsupported files: record the limitation and ask the user for exported/rendered alternatives.
- For confidential, legal, medical, financial, personal, face, certificate, or proprietary materials: do not use API fallback unless the user explicitly confirms it is allowed.

## Non-Negotiable Rules

- Do not start Stage 2 before the full slide plan is approved.
- Every approval checkpoint must return to the user; the user decides whether to ask the client and then tells the agent the result.
- Stage 2 normally produces 3 sample slides; do not use a single sample as the normal path.
- Do not start Stage 3 before samples and reference mapping are approved.
- Do not start full production if any slide lacks a reference image.
- Do not treat a path string as a substitute for actual image input.
- Do not let workers invent missing required client images.
- Use the native/built-in image generation backend first; only consider API fallback when native generation is unavailable, insufficient, or explicitly authorized by the user.
- Do not create final image-based slides with local drawing, HTML/SVG/canvas screenshots, Pillow, python-pptx/PptxGenJS, or manual overlays.
- Every Stage 3 final slide image must be produced by the selected image generation backend.
- Do not use the flattened full-slide screenshot as the final editable background in Stage 4.
- Stage 4 client-required image regions must be reconstructed with the original client asset as input whenever they are regenerated or fused into the background.
- Do not call a deck complete if any slide/page is blocked, missing, or unrecorded.
