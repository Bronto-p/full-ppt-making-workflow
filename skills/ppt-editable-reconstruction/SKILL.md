---
name: ppt-editable-reconstruction
description: Convert the final image-based PPT workflow output into a more editable PPTX. Use after ppt-full-production when the user wants the generated image slides reconstructed into object-level PowerPoint pages with editable text, layered assets, and imagegen-preserved backgrounds using the original slide image plus original client image assets.
---

# PPT Editable Reconstruction

## Purpose

This skill performs the fourth stage of the client PPT workflow: converting the final image-based deck into a more editable PowerPoint deck.

It is based on the `image-to-editable-ppt` architecture, but it is specialized for this workflow. It should use the third-stage project artifacts instead of treating the final slide screenshots as the only source of truth.

The goal is not to place a full-slide screenshot behind editable text. The goal is to reconstruct each slide as layered PPT content:

- clean/generated background image
- imagegen-preserved client images integrated into that background when the source slide visually embeds them
- generated or source-derived visual assets when separate layers are needed
- native editable PowerPoint text boxes for main slide text
- simple native shapes only where they improve editability without degrading fidelity

## Required Inputs

Best input is the full third-stage production project folder containing:

- `origin_image/slide_XX.png`
- `slide_plan.md`
- `approved_style_reference.md`
- `reference_mapping.md`
- `prompts/slide_XX.json`
- required client image assets
- final image-based `.pptx`, if available

If only an image-based PPT/PPTX, PDF, or slide images are provided, this skill can still run, but it must report that it lacks prior production metadata and may need more inspection or user confirmation.

## Relationship To Image-To-Editable-PPT

Reuse the orchestration model from `image-to-editable-ppt`:

- every page is rebuilt by a page subagent
- main agent only orchestrates
- each page has its own page directory
- state changes are script-driven when scripts are available
- page workers output `manifest.json`, `page.pptx`, `preview.png`, `split_assets_contact.png`, `validation.json`, and `page_result.json`
- final assembly combines accepted page PPTX files into one final editable deck

Use this skill's local `scripts/` entrypoints whenever compatible. Do not reimplement deterministic run/page state machinery by hand.

## Scripts

This skill includes `scripts/` wrappers for the page reconstruction scripts from `image-to-editable-ppt`. Use these local script entrypoints for deterministic run/page state, page building, validation, and final assembly:

- `image_to_editable_ppt_runtime.py`: bootstrap/check runtime.
- `prepare_deck_run.py`: create run/page directories and normalize inputs when compatible.
- `page_job_status.py`: inspect page dispatch status.
- `record_page_dispatch.py`: record page worker dispatch.
- `record_page_result.py`: validate and record page results.
- `queue_page_repairs.py`: create page repair queue items.
- `record_imagegen_result.py`: copy and record selected imagegen results.
- `process_asset_sheet.py`: process asset sheets, crop source assets, and remove backgrounds.
- `make_page_contact_sheet.py`: create contact sheets.
- `build_pptx_from_manifest.py`: build page PPTX from manifest.
- `validate_pptx.py`: validate page/final PPTX files.
- `finalize_deck_run.py`: assemble accepted page PPTX files into final editable deck.

Use these local script entrypoints whenever compatible.

If workflow-specific preparation becomes stable later, add a small wrapper to connect Stage 3 artifacts (`origin_image`, `prompts/slide_XX.json`, `slide_plan.md`, `reference_mapping.md`, and original client assets) to the page run structure expected by `image-to-editable-ppt`. Do not add that wrapper until tested on real orders.

## Reference Map

Read these before dispatching or doing page reconstruction:

- `references/layered-reconstruction.md`: page-level reconstruction order and layer model.
- `references/text-classification.md`: editable text vs incidental background text vs image-contained text vs artistic text.
- `references/background-and-client-images.md`: clean background and original client image preservation/fusion strategy.
- `references/page-worker-contract.md`: worker prompt requirements and return contract.
- `prompts/page-worker.md`: page worker handoff template.

Use `$imagegen` for all image generation, image editing, background generation, client-image-preserving fusion, transparent assets, and repairs. Read:

```text
${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/SKILL.md
```

## Workflow

1. Prepare the editable reconstruction run.
   - Normalize the input into page images: one `source.png` per slide.
   - If the third-stage project exists, connect each page to its `prompts/slide_XX.json`, `slide_plan.md` entry, `reference_mapping.md` entry, and required client images.
   - Preserve speaker notes when available.

2. Dispatch every page to a page subagent.
   - Main agent does not rebuild pages.
   - Every page, including single-slide input, must be handled by a page worker.
   - If page subagents are unavailable, stop and report a blocker.

3. Page worker performs layered reconstruction.
   - Inspect the source page deeply.
   - Classify text and visual objects.
   - Generate or edit a clean background using the full page source and relevant original client image assets.
   - Inspect the clean background before continuing.
   - Generate or preserve foreground visual assets only when they should remain separate.
   - Add native editable text boxes for main slide text.
   - Build `page.pptx`, render `preview.png`, create contact sheet, validate, and repair local failures.

4. Main agent records page results and queues repairs.
   - Use local state scripts whenever compatible.
   - Do not hand-edit run state JSON.
   - Repair the smallest failing layer or asset.

5. Assemble final editable PPTX.
   - Combine accepted page PPTX files.
   - Copy speaker notes when available.
   - Run deck validation.
   - Report known limitations.

## Hard Rules

- The original full-slide source image alone is not enough when the slide contains client-required images. Provide the full slide source and the original client asset images to the page worker.
- Client-required images should be preserved through imagegen using the original image asset as input, not inferred only from the flattened slide screenshot.
- By default, client-required images should be visually integrated into the generated background/scene rather than pasted later as obvious floating overlays.
- If a client image must remain independently movable/editable as a picture layer, record that decision in the manifest and preserve the original image asset.
- Main slide text should become native editable PowerPoint text boxes.
- Image-contained text inside product screenshots, charts, certificates, portraits, UI screenshots, or photos should remain inside the preserved image/background treatment unless the plan explicitly asks to recreate it as editable text.
- Incidental tiny background text may remain in the generated background when it functions as visual texture or belongs to a background image.
- Artistic word art, logo-like text, highly stylized title marks, and texture-bound lettering may be generated as image assets if native text would destroy the visual identity. Record the reason.
- Do not use SVG/native shapes to approximate complex generated visuals when imagegen or source-preserving assets would be more faithful.
- Do not use a full-slide screenshot as the background plus editable text overlay as the final reconstruction.
- Do not call the deck complete unless each page has required page outputs, preview, validation, and recorded result.

## Acceptance Criteria

- Output is a valid editable `.pptx`.
- Each source slide maps to one output slide.
- Main slide text is native editable PPT text wherever practical.
- Client-required images are preserved from original assets, not hallucinated from the flattened slide.
- Backgrounds are reconstructed without duplicated main editable text.
- Every page has `manifest.json`, `page.pptx`, `preview.png`, `split_assets_contact.png`, `validation.json`, and `page_result.json`.
- Every page has a documented background strategy, text classification, client image strategy, asset provenance, and known limits.
- Final deck has validation output and a concise QA report.
