# Page Worker Prompt

```text
Reconstruct one page for ppt-editable-reconstruction.

Run dir: <absolute run dir>
Page id: <page_001>
Page dir: <absolute page dir>
Source image: <absolute page dir>/source.png

You may write only inside this page dir. Do not edit deck-level manifests, run state, final output, source originals, or other page directories.

Read and obey:
- ${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/SKILL.md
- <skill root>/references/layered-reconstruction.md
- <skill root>/references/text-classification.md
- <skill root>/references/background-and-client-images.md
- <skill root>/references/page-worker-contract.md
- /Users/yuruihe/.codex/skills/image-to-editable-ppt/references/manifest-schema.md
- /Users/yuruihe/.codex/skills/image-to-editable-ppt/references/qa-rubric.md
- /Users/yuruihe/.codex/skills/image-to-editable-ppt/references/script-contracts.md

Related metadata, if available:
- slide_plan.md: <path>
- approved_style_reference.md: <path>
- reference_mapping.md: <path>
- production slide job: <path to prompts/slide_XX.json>

Original client image assets for this page:
- <absolute path> - role and preservation rule

Task:
Rebuild the source page as an object-level editable PowerPoint page. Do not use the full slide screenshot as a background fallback.

Important:
When the page contains client-required images, use the original client image asset together with the full slide source image during imagegen reconstruction. The source page shows placement and visual treatment; the original asset preserves identity. Do not infer client images only from the flattened slide screenshot.

Required reconstruction order:
1. Inspect source page and all client assets.
2. Build text classification: editable slide text, image-contained text, incidental background text, artistic text.
3. Build visual/object inventory.
4. Decide background and client image strategy.
5. Generate/edit clean or integrated background with $imagegen when needed.
6. Inspect background: no duplicated main editable text, client images preserved, visual identity retained.
7. Generate or preserve separate foreground assets only when they should remain separate.
8. Add native editable PPT text boxes for main slide text.
9. Build page.pptx, render preview.png, create contact sheet, validate, and repair smallest failures.

Required outputs in page dir:
- manifest.json
- imagegen-jobs.json
- clean_background.png when applicable
- assets/
- page.pptx
- preview.png
- split_assets_contact.png
- validation.json
- page_result.json

manifest.json must record:
- text_classification
- visual_inventory
- background_strategy
- client_image_strategy
- asset_provenance
- quality_checks
- known_limits

Return only:
page_manifest=<absolute path>
page_pptx=<absolute path>
preview=<absolute path>
contact_sheet=<absolute path>
validation=<absolute path>
page_result=<absolute path>
qa_note=<one sentence>
known_limits=<none or short list>
```
