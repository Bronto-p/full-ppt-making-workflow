# Slide Generation And Subagents

Read this before full-deck image generation, preparing slide jobs, dispatching workers, recording results, or handling blockers.

## Final Slide Image Generation

Every final slide image must be produced by the selected image generation backend. Do not create final slides with local drawing, HTML/SVG/canvas screenshots, Pillow overlays, python-pptx/PptxGenJS layouts, or manual compositing.

The selected backend should be the native/built-in image generation tool unless it is unavailable, insufficient for required image inputs, or the user explicitly authorizes CLI/API fallback.

## Worker Inputs

Each slide worker must receive three payload groups:

1. `text_content`: approved slide text.
2. `reference_images`: actual image inputs, not only paths or text descriptions.
3. `required_images`: actual client image assets when the slide requires them.

A path is traceability. It is not visual input by itself. If the worker cannot open, view, or attach a required image to the backend, it must return a blocker.

Do not collapse `reference_images` and `required_images` into one ambiguous list. A reference image is visual guidance; a required image is strict client content.

## Parent Responsibilities

The parent agent owns shared files and state:

- `deck_spec.json`
- `slide_jobs.json`
- `slide_run_state.json`
- `prompts/slide_XX.json`
- `origin_image/`
- `speech.md`
- final PPTX assembly

Workers must not edit shared files. They return generated image candidates and notes only.

## Dispatch Discipline

Dispatch one worker per slide when subagents are available. Record dispatch with `scripts/record_slide_dispatch.py`, results with `scripts/record_slide_result.py`, and blockers with `scripts/record_slide_blocker.py`.

## QA Before Recording

Before recording a result, inspect the image for text accuracy, readability, reference-style match, required asset preservation, aspect ratio, numeric slide order, and obvious layout artifacts.
