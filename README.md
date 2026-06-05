# Full PPT Making Workflow

Codex skills for building client PowerPoint decks from source materials.

The main workflow is now a single skill, `ppt-complete-workflow`, which replaces the older three-step split across planning, style samples, and final production.

## Skills

### `ppt-complete-workflow`

Runs the full client PPT workflow:

1. Inspect a client order folder.
2. Write an exact-content `ppt_plan.md`.
3. Generate a sequential sample round.
4. Collect user approval and update the plan from feedback.
5. Produce final slide images and assemble the image-based `.pptx`.

This skill includes the shared codex-ppt machinery for backend selection, prompt preparation, slide worker handoff, state recording, QA, speaker notes, and final PPTX assembly.

### `image-to-editable-ppt`

Converts images, PDFs, or image-based PPT/PPTX files into a high-fidelity editable PowerPoint using imagegen-first layered reconstruction.

## Key Guardrails

The unified workflow enforces several rules that are important for client work:

- Slide `Content` must contain exact slide-ready text, numbers, labels, and claims. Topic-only descriptions are not enough.
- Client products, people, logos, charts, screenshots, certificates, and brand assets may appear only when a real supplied file is assigned to that slide.
- Fake or lookalike client imagery is forbidden.
- Every planned image includes an `Asset fidelity rule`, such as exact-use, crop/fit only, or style-reference only.
- If required source content is unreadable or missing, the plan marks it as `NEEDS SOURCE` and generation should stop.
- Sample 1 is generated first and becomes the visual anchor for Sample 2 and Sample 3.
- Final production must include approved sample images as style references.

## Repository Layout

```text
skills/
├── ppt-complete-workflow/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── docs/
│   ├── prompts/
│   ├── references/
│   ├── scripts/
│   └── requirements.txt
└── image-to-editable-ppt/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── prompts/
    ├── references/
    ├── scripts/
    └── requirements.txt
```

## Installation

Copy the skill folders you want into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R skills/ppt-complete-workflow ~/.codex/skills/
cp -R skills/image-to-editable-ppt ~/.codex/skills/
```

Restart Codex or reload skills after copying.

## Usage

Invoke the full PPT workflow explicitly:

```text
Use $ppt-complete-workflow on this client order folder.
```

Typical order folder inputs include:

- client requirement documents
- source Word/PDF/TXT/Markdown files
- old PPT/PPTX decks
- template decks or style reference images
- logos, product photos, portraits, charts, screenshots, certificates, and other client assets

The workflow writes planning and production artifacts into the order folder:

```text
ppt_plan.md
sample_plan.md
sample_feedback.md
approved_sample_reference.md
samples/
production/{deck_name}/
```

## Validation

Validate a skill folder with Codex's skill creator validator:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/ppt-complete-workflow
```

Check Python script syntax:

```bash
python3 -m py_compile skills/ppt-complete-workflow/scripts/build_production_spec.py
```

## Notes

This repository stores skills, not a plugin. Each folder under `skills/` is intended to be copied into `~/.codex/skills/`.

The PPT workflow vendors codex-ppt resources and keeps upstream license attribution under `references/codex-ppt-license.txt`.
