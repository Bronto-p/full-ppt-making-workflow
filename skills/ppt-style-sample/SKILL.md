---
name: ppt-style-sample
description: Create a three-slide sample round from an existing ppt_plan.md by dispatching one slide-generation subagent per sample slide, collect user feedback, update the plan when feedback changes content/theme/layout/image decisions, and repeat sample rounds until the user approves the direction for later PPT production.
---

# PPT Style Sample

## Purpose

Create a three-slide sample round from `ppt_plan.md`, get user feedback, revise the samples and the plan, and repeat until the user says the samples pass.

The main agent does not personally make three slides one after another when subagents are available. The main agent prepares three slide jobs, starts one separate slide subagent for each selected sample slide, then records each worker's result.

This skill is independent. It can be used by itself when a user provides a plan and assets. When it follows `ppt-plan-order`, use that skill's `ppt_plan.md` as the source of truth.

## Input

Prefer an order folder containing:

- `ppt_plan.md`
- template or style reference files listed in the plan
- image assets listed in the plan

If `ppt_plan.md` is missing but the user provides a clear slide plan in chat, create sample files from that. If neither a plan nor usable slide details are available, stop and ask for a plan.

## Outputs

Create or update these files in the order folder:

```text
sample_plan.md
sample_feedback.md
approved_sample_reference.md
```

Create sample image rounds under:

```text
samples/
├── round_01/
│   ├── sample_spec.json
│   ├── prompts/
│   ├── slide_jobs.json
│   ├── slide_run_state.json
│   └── origin_image/
│       ├── slide_01.png
│       ├── slide_02.png
│       └── slide_03.png
├── round_02/
└── approved/
    ├── slide_01.png
    ├── slide_02.png
    └── slide_03.png
```

`samples/*/origin_image/` is for sample-round outputs only. It is not the final production deck's `origin_image/` folder.

## Fixed Sample Plan Structure

Always write `sample_plan.md` with this structure:

```markdown
# Sample Plan

## Source Plan
- Plan path:
- Slide count:
- Overall theme:
- Overall template/style:
- Template/reference files:
- Image asset files:

## Selected Sample Slides

### Sample 1: Slide {N} - {slide title}
- Why this slide:
- Content:
- Template/theme:
- Page layout/structure:
- Template/reference path:
- Images:

### Sample 2: Slide {N} - {slide title}
- Why this slide:
- Content:
- Template/theme:
- Page layout/structure:
- Template/reference path:
- Images:

### Sample 3: Slide {N} - {slide title}
- Why this slide:
- Content:
- Template/theme:
- Page layout/structure:
- Template/reference path:
- Images:

## Image Backend
- Selected backend:
- Why:
- Fallback status:

## Round
- Current round:
- Output folder:
```

Pick three representative slides by default:

- one cover/opening or high-level context slide
- one standard content slide
- one difficult slide with images, data, process, comparison, timeline, or dense layout

If the plan has fewer than three slides, sample every slide.

## Workflow

1. Read `ppt_plan.md`.
   - Extract deck requirements, slide count, template/reference paths, and image paths.
   - Verify the three selected sample slides include enough variation to test the theme and page structure.

2. Preflight the plan for worker handoff.
   - Check that selected slides have `Content`, `Template/theme`, `Page layout/structure`, `Template/reference path`, and `Images`.
   - Check that listed local template/reference/image paths exist when they are not `none`.
   - If a selected slide's plan is vague, improve `ppt_plan.md` directly before generating samples.
   - This is not a new approval gate. It only prevents sending incomplete packets to slide workers.

3. Confirm or select the image backend using the copied codex-ppt rules.
   - Read `docs/backend-selection.md`.
   - Prefer the built-in image generation tool when available.
   - Use CLI/API fallback only when the built-in backend is unavailable, lacks a required capability, or the user explicitly asks for fallback.
   - Keep the selected backend fixed for all sample slides in a round unless the user changes it.

4. Prepare sample jobs.
   - Create `samples/round_XX/sample_spec.json`.
   - Include deck-level theme/style and the three selected slides.
   - Include actual template/reference images and required slide images as `input_images` or `required_images`.
   - Run `scripts/prepare_slide_prompts.py` when compatible:

```bash
python scripts/prepare_slide_prompts.py \
  --spec <order_folder>/samples/round_XX/sample_spec.json \
  --out-dir <order_folder>/samples/round_XX \
  --selected-backend "<selected backend>" \
  --force
```

5. Dispatch sample slide workers using the copied codex-ppt production machinery.
   - Read `docs/slide-generation-and-subagents.md` and `prompts/slide-worker.md`.
   - The main agent owns `sample_plan.md`, `sample_feedback.md`, `approved_sample_reference.md`, sample job files, state files, QA, and plan updates.
   - Start one separate subagent per selected sample slide when subagents are available.
   - Give each worker exactly one `prompts/slide_XX.json` job.
   - Send the worker the slide content, template/theme, page layout/structure, template/reference files, and image files from the plan.
   - Make actual image inputs available to the worker; do not rely on path text alone.
   - Use `prompts/slide-worker.md` as the worker handoff base.
   - Record dispatches and results with the bundled state scripts.

Use the same dispatch loop shape as codex-ppt:

```bash
python scripts/slide_job_status.py <order_folder>/samples/round_XX

python scripts/record_slide_dispatch.py \
  <order_folder>/samples/round_XX \
  --slide slide_01 \
  --agent-id <subagent id> \
  --agent-nickname "<nickname if available>" \
  --prompt-file prompts/slide_01.json
```

After each worker returns, inspect the selected image and record it:

```bash
python scripts/record_slide_result.py \
  <order_folder>/samples/round_XX \
  --slide slide_01 \
  --agent-id <subagent id> \
  --backend-used "<selected backend>" \
  --selected-source <absolute path to generated image> \
  --qa-note "<one sentence>"
```

If a worker cannot use the selected backend or cannot access required images, record a blocker:

```bash
python scripts/record_slide_blocker.py \
  <order_folder>/samples/round_XX \
  --slide slide_01 \
  --agent-id <subagent id> \
  --reason "<blocker reason>"
```

6. Show the three samples to the user.
   - Ask whether the style, layout structure, image usage, and text quality pass.
   - If the user gives corrections, append them to `sample_feedback.md`.

7. Update the plan from feedback.
   - If feedback changes theme, layout, template choice, content density, image usage, or page structure, update `ppt_plan.md`.
   - Do not treat sample feedback as only image repair; use it to improve the production plan.
   - Generate another sample round after plan changes.

8. Finalize approval.
   - When the user says the samples pass, copy the approved samples into `samples/approved/`.
   - Write `approved_sample_reference.md`.
   - Include approved sample paths, final style notes, sample generation method, backend used, and how production should use the samples.

## Approved Sample Reference Structure

Always write `approved_sample_reference.md` with this structure after approval:

```markdown
# Approved Sample Reference

## Approved Samples
- Slide:
- Sample path:
- Source round:
- Use in production:

## Final Style Direction
- Theme:
- Layout system:
- Typography:
- Color/visual treatment:
- Image treatment:

## Production Handoff
- Use these samples as style references for every production slide.
- Upload/include the approved sample images when dispatching production slide workers.
- Match the theme, typography, density, spacing, and image treatment.
- Do not copy sample slide content or exact layout unless the target slide uses the same page type.

## Sample Generation Method
- Backend used:
- Tool name:
- Mode:
- Prompt source:
- Input context preparation:
- Handoff rule:
```

## Hard Constraints

- Create a three-slide sample round by default.
- Start one separate subagent per selected sample slide when subagents are available; each subagent generates exactly one slide.
- Do not generate the full deck in this skill.
- Do not assemble a final PPTX in this skill.
- Every sample slide image must be generated as one complete 16:9 full-slide image by the selected image backend.
- Do not generate separate slide parts and assemble them into a slide image.
- Do not skip plan preflight; feedback that affects production must update `ppt_plan.md`.
- Do not change the selected image backend between sample slides in the same round.
- Do not use local drawing, SVG, HTML/CSS/canvas screenshots, Pillow, python-pptx, PptxGenJS, or manual overlays as substitutes for image-backend sample generation.
- Do not let workers invent missing required client images.
- Do not let workers use only file path text when the slide depends on an actual image; prepare or upload the actual image input.
- Do not put rejected variants in `samples/approved/`.
- Do not call samples approved from the agent's own judgment. Approval must come from the user.

## Vendored Codex-PPT Resources

This skill vendors the upstream codex-ppt resource layout from [ningzimu/codex-ppt-skill](https://github.com/ningzimu/codex-ppt-skill):

- all upstream `scripts/*.py`
- all upstream `docs/*.md`
- all upstream `prompts/*.md`, including `prompts/slide-worker.md`
- all upstream `references/*.md`
- `requirements.txt`
- `references/codex-ppt-original-SKILL.md`
- `references/codex-ppt-license.txt`

Use the copied codex-ppt slide creation machinery for sample slide creation: backend selection, prompt-job preparation, subagent handoff, state recording, result recording, blocker recording, QA expectations, source-image handling, and CLI/API fallback. Do not reimplement those mechanics in prose when the copied scripts and docs apply.

This skill stops at approved sample references. Do not assemble a final PPTX here even though the upstream assembly resources are vendored for compatibility and for the later production skill to match the same codex-ppt behavior.

The only intentional workflow differences from codex-ppt are:

- Input source is `ppt_plan.md`, not a freeform article/outline.
- The parent prepares a three-slide sample round instead of codex-ppt's normal one-sample gate.
- Each sample slide still follows codex-ppt's one-job-per-worker rule.
- Sample approval updates `ppt_plan.md` when feedback changes production decisions.
- Approved samples are copied to `samples/approved/` and written into `approved_sample_reference.md` for later production use.

Read these copied references only when needed:

- `docs/backend-selection.md` before selecting backend.
- `docs/user-supplied-assets.md` before using client images.
- `docs/slide-generation-and-subagents.md` before dispatching workers or recording state.
- `docs/cli-api-fallback.md` only when CLI/API fallback is selected.
- `references/codex-ppt-license.txt` for upstream license attribution.

## Final Response

After each round, report:

- sample round folder
- three sample image paths
- whether `ppt_plan.md` changed
- what user feedback is still pending
- that no final deck was generated

After approval, report:

- `approved_sample_reference.md`
- `samples/approved/`
- the approved sample image paths
- that production should include these approved samples as style references
