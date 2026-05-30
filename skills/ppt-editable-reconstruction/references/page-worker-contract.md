# Page Worker Contract

Each page worker receives exactly one source page and rebuilds only that page.

## Required Inputs

The handoff must include:

- run dir
- page id
- page dir
- source image path
- related third-stage metadata when available:
  - `slide_plan.md`
  - `reference_mapping.md`
  - `approved_style_reference.md`
  - `prompts/slide_XX.json`
- original client image assets required on this page
- allowed write scope
- required outputs

## Required Worker Actions

Before writing `manifest.json`, the worker must:

1. Open/view the source page.
2. Open/view every original client image asset for this page.
3. Read the page's prior production metadata if available.
4. Build a text classification inventory.
5. Build a visual/object inventory.
6. Decide background strategy and client image strategy.
7. Decide which objects are native shapes, generated assets, source-derived assets, or native text.

## Required Outputs

In the page dir:

```text
manifest.json
imagegen-jobs.json
clean_background.png
assets/
page.pptx
preview.png
split_assets_contact.png
validation.json
page_result.json
```

If a page does not need a separate `clean_background.png`, manifest must explain the chosen background strategy.

## Blockers

Return a blocker if:

- source page cannot be opened
- required client image cannot be opened
- `$imagegen` is needed but unavailable
- imagegen cannot use the original client asset as input for preservation
- the worker cannot produce required outputs
- the resulting page would rely on a full-slide screenshot fallback

## Return Format

```text
page_manifest=<absolute path>
page_pptx=<absolute path>
preview=<absolute path>
contact_sheet=<absolute path>
validation=<absolute path>
page_result=<absolute path>
qa_note=<one sentence>
known_limits=<none or short list>
```
