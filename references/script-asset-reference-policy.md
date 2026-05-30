# Script, Asset, And Reference Policy

This workflow is built on top of two existing local skills:

- `codex-ppt`
- `image-to-editable-ppt`

Do not copy their scripts into this repository unless a wrapper or fork becomes necessary. Prefer reusing the installed skill scripts directly so bug fixes and behavior stay centralized.

## Scripts

### Stage 1: `ppt-order-planner`

No dedicated scripts are needed yet.

The output formats are still human-reviewed planning documents:

- `order_materials.md`
- `slide_plan.md`

Add scripts later only if repeated real orders show stable parsing needs, such as extracting client requirements or checking referenced files.

Possible future scripts:

- `scan_order_folder.py`
- `validate_slide_plan.py`

### Stage 2: `ppt-sample-iteration`

No dedicated scripts are needed yet.

The main outputs are planning and approval artifacts:

- `sample_plan.md`
- `sample_feedback.md`
- `approved_style_reference.md`
- `reference_mapping.md`

Add scripts later when the `reference_mapping.md` format is stable enough to validate mechanically.

Possible future script:

- `validate_reference_mapping.py`

### Stage 3: `ppt-full-production`

Reuse `codex-ppt` scripts from:

```text
/Users/yuruihe/.codex/skills/codex-ppt/scripts/
```

Useful scripts:

- `codex_ppt_runtime.py`: bootstrap/check the runtime.
- `prepare_slide_prompts.py`: prepare per-slide jobs when compatible with the deck spec.
- `slide_job_status.py`: inspect dispatchable and recorded slides.
- `record_slide_dispatch.py`: record slide worker dispatch.
- `record_slide_result.py`: copy selected generated images and record provenance.
- `record_slide_blocker.py`: record slide blockers.
- `slide_run_state.py`: manage slide run state.
- `assemble_ppt.py`: assemble `origin_image/slide_XX.png` into final PPTX.

Do not hand-edit slide state JSON when these scripts apply.

Possible workflow-specific wrapper later:

- `build_deck_spec_from_workflow_plan.py`, converting `slide_plan.md`, `approved_style_reference.md`, and `reference_mapping.md` into the `deck_spec.json` expected by production.

Do not add that wrapper until the workflow document formats have stabilized.

### Stage 4: `ppt-editable-reconstruction`

Reuse `image-to-editable-ppt` scripts from:

```text
/Users/yuruihe/.codex/skills/image-to-editable-ppt/scripts/
```

Useful scripts:

- `image_to_editable_ppt_runtime.py`: bootstrap/check the runtime.
- `prepare_deck_run.py`: create run/page directories and normalize inputs when compatible.
- `page_job_status.py`: inspect page dispatch status.
- `record_page_dispatch.py`: record page worker dispatch.
- `record_page_result.py`: validate and record page results.
- `queue_page_repairs.py`: create repair queue items.
- `record_imagegen_result.py`: copy and record selected imagegen results.
- `process_asset_sheet.py`: process asset sheets, crop source assets, and remove backgrounds.
- `make_page_contact_sheet.py`: create contact sheets.
- `build_pptx_from_manifest.py`: build page PPTX from manifest.
- `validate_pptx.py`: validate page/final PPTX files.
- `finalize_deck_run.py`: assemble accepted page PPTX files into the final editable deck.

Use the original scripts for deterministic state and validation whenever possible.

Possible workflow-specific wrapper later:

- `prepare_editable_reconstruction_from_full_production.py`, connecting Stage 3 artifacts (`origin_image`, `prompts/slide_XX.json`, `slide_plan.md`, `reference_mapping.md`, original client assets) to the page run structure expected by `image-to-editable-ppt`.

Do not add that wrapper until the Stage 4 run format has been tested on real orders.

## Assets

Do not add generic PPT templates, stock images, icons, fonts, or sample client assets to this workflow repository yet.

Reasons:

- Client assets belong in each order folder.
- Approved reference images are generated or supplied per order.
- Hardcoded design assets would fight the client's template/reference direction.

Use per-order directories for:

- client images
- rendered template pages
- generated samples
- approved references
- final slide images
- editable reconstruction assets

## References

References are useful here because they define contracts and workflows, not fixed visual styles.

Current repository-level reference:

- `references/script-asset-reference-policy.md`

Skill-level references are appropriate when a single stage needs detailed rules, such as Stage 4's layered reconstruction references.

Avoid duplicating large reference content across skills. If a rule applies to the whole workflow, keep it in `WORKFLOW.md` or repository-level `references/`.
