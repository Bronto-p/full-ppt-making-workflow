# Project Assembly And Reporting

Read this before initializing the project directory, writing speaker notes, assembling the PPTX, or sending the final report.

## Project Directory

Keep production artifacts in the deck project folder:

- `outline.md`
- `deck_spec.json`
- `prompts/slide_XX.json`
- `slide_jobs.json`
- `slide_run_state.json`
- `origin_image/slide_XX.png`
- `speech.md`
- final `.pptx`

Also keep or copy approved planning artifacts:

- `order_materials.md`
- `slide_plan.md`
- `approved_style_reference.md`
- `reference_mapping.md`
- approved sample/reference images
- required client assets

## Assembly

Before assembly, confirm every slide is recorded and no slide is pending, dispatched, or blocked. Assemble with this skill's local wrapper:

```bash
python skills/ppt-full-production/scripts/assemble_ppt.py {base_dir} {deck_name}.pptx --aspect-ratio 16:9
```

## Final Report

Report the project directory, final PPTX path, slide image directory, state file, number of slides, backend used, whether every slide used mapped references, and any remaining blockers or known limitations.
