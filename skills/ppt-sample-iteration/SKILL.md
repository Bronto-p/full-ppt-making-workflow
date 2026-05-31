---
name: ppt-sample-iteration
description: Run the sample-slide iteration stage for a client PPT order. Use after ppt-order-planner has created and the client has approved slide_plan.md, and before full deck production, to plan 3 sample slides by default (2 only for short/simple decks or explicit user choice), generate or coordinate image-based samples, collect client feedback, update the style/template plan, and produce approved_style_reference.md plus reference_mapping.md.
---

# PPT Sample Iteration

## Purpose

This skill handles the second stage of the client PPT workflow: sample slides, style approval, and final reference-image mapping.

Use it after `ppt-order-planner` has created `slide_plan.md` and the user confirms the client has approved the plan. This skill turns the initial template/style plan into client-approved visual references before full PPT production.

Final PPT production is out of scope. Do not generate the full deck, `deck_spec.json`, final `origin_image/slide_XX.png` set, `speech.md`, or PPTX files in this skill.

## Workflow Position

The overall workflow is:

1. `ppt-order-planner`: organize client requirements, materials, per-slide text, image assets, and initial template/style plan.
2. `ppt-sample-iteration`: generate sample slides, handle feedback, lock the approved template/style references, and map every slide to a reference image.
3. Full production: use the approved plan and references to generate the full image-based PPT workflow.

This skill only performs step 2.

## Required Inputs

The order folder should contain:

- `order_materials.md`
- `slide_plan.md`
- `material_manifest.json` or equivalent ingestion notes when source files contain embedded visuals
- the source files referenced by those plans

If `slide_plan.md` is missing, stop and ask the user to run or provide the output from `ppt-order-planner` first.

If the full slide plan has not been approved through the user, stop and ask the user for plan approval first. The user is responsible for asking the client when client approval is needed. The approved plan must cover each slide's text, image usage, template/style plan, draft reference-image mapping, sample strategy, and whether embedded visuals were correctly read.

If client feedback is provided, read it before planning the next sample round.

## Core Rules

- Samples are used to confirm the visual system before full deck production.
- Whether the client provided a template or not, sample approval is still required before full production.
- Full production cannot start unless every slide maps to at least one approved reference image.
- A reference image can be reused across many slides.
- A reference image may come from an approved generated sample, a rendered client template page, a client-provided style/reference image, or another client-approved visual reference.
- Text-only style descriptions are not enough for full production.
- Use image-based slide sample generation consistent with the final production approach.
- Use the native/built-in image generation backend first. Consider API/CLI fallback only if the native backend is unavailable, cannot attach required visual inputs, lacks a required capability, or the user explicitly authorizes fallback.
- Do not treat a verbal style direction as approved until the client has approved sample images.
- Do not proceed to full deck generation during this skill.
- If client feedback changes the style, layout, text density, image treatment, or template usage, update the plan before generating another sample.

## Sample Strategy

Generate a representative sample set for every order.

Default rule:

- Generate 3 sample slides by default.
- Generate 2 sample slides only when the deck is very short, page types are not varied, or the user explicitly chooses a smaller sample set.
- Do not use a single sample slide as the normal path.
- Choose samples that test the visual system across page types.

If the client provided a clear template, reference image, or template PPT:

- Still generate 3 samples by default.
- Prefer representative page types: cover/opening, standard content, and the most complex page type.
- Use the provided template/reference as visual guidance.
- If the template has multiple page types or the client expects different template pages for different slides, create or verify a reference image for each required page type or per-slide template page.

If the client did not provide a template or only gave a verbal direction:

- Generate 3 samples by default to establish the visual system.
- The samples can be 3 representative page types in one coherent direction, or 3 visual directions applied to the same representative slide if the user explicitly wants style exploration.
- Prefer 3 representative page types once a direction is chosen: cover/opening, standard content, and image/data/complex page.

If the client wants an old PPT beautified or redesigned:

- Select 3 representative pages from the old PPT by default: cover/opening, normal content page, and a complex image/data/process page when available.
- Preserve the original slide text unless the plan allows rewriting.
- Treat the old PPT as content source, not automatically as the new template.

If the client feedback says the direction is completely wrong:

- Revise the style/template plan first.
- Create a new sample round.
- Do not patch only minor details while keeping a rejected visual direction.

If the client feedback is specific and local:

- Update the plan with the requested changes.
- Regenerate the same sample page or direction.

## Files To Create Or Update

### `sample_plan.md`

Create this before generating or coordinating samples.

Required structure:

```markdown
# Sample Plan

## Sample Goal
- What needs approval:
- Why samples are needed:

## Current Template / Style Plan
- Source:
- Description:
- Reference files:
- Open concerns:

## Sample Round
- Round:
- Strategy:
- Number of samples:
- Image backend: native/built-in first; API/CLI fallback only if user-authorized

## Samples To Produce

### Sample A
- Slide:
- Purpose:
- Text source:
- Template/style source:
- Required images:
- Reference images:
- Embedded/source visuals to verify:
- What this sample should prove:

### Sample B
- ...
```

### `sample_feedback.md`

Append each client feedback round.

Use this format:

```markdown
# Sample Feedback

## Round 1
- Samples shown:
- Client decision:
- Approval returned through user:
- Requested changes:
- Rejected elements:
- Approved elements:
- Plan updates needed:
```

### `approved_style_reference.md`

Create this only after the user says the client approved the sample direction.

Required structure:

```markdown
# Approved Style Reference

## Approval
- Approved round:
- Approved sample files:
- Approved by: user-confirmed client approval or user approval
- Date:
- Approved artifact hashes:

## Final Template / Style Description
- Overall direction:
- Palette:
- Background:
- Typography:
- Layout rules:
- Image treatment:
- Decorative elements:
- Text density:
- Do not use:

## Page Type References
- Cover:
- Standard content:
- Image-heavy page:
- Data/process page:
- Closing:

## Production Notes
- How to use these references in full production:
- Required asset preservation rules:
- Text rewrite constraints:
```

### `reference_mapping.md`

Create this after the sample/reference direction is approved. This file is mandatory for full production.

It answers: which approved reference image should each slide use?

Required structure:

```markdown
# Reference Mapping

## Reference Images

| Reference ID | File | Source | Usage |
|---|---|---|---|
| cover_ref | samples/approved/cover_reference.png | approved generated sample | cover pages |
| content_ref | samples/approved/content_reference.png | approved generated sample | standard content pages |
| template_03 | template_renders/page_03.png | client template page | data pages |

## Slide To Reference Mapping

| Slide | Page Type | Reference ID | Reference Image | Notes |
|---:|---|---|---|---|
| 1 | cover | cover_ref | samples/approved/cover_reference.png | Match title treatment and hero composition |
| 2 | content | content_ref | samples/approved/content_reference.png | Reuse content page style |
| 3 | data | template_03 | template_renders/page_03.png | Use chart/card layout language |
```

Rules:

- Every slide in `slide_plan.md` must have a row.
- Every row must point to at least one image file.
- The image path must exist or be explicitly marked as blocked.
- One reference image can be reused by many slides.
- If a slide uses multiple reference images, state each image's role, such as `layout reference`, `style reference`, or `client template page`.
- If a client template supplies different page designs, map slides to the matching rendered template page image.
- If no approved reference image exists for a slide, do not hand off to full production.

Validate the mapping before Stage 3:

```bash
python skills/ppt-sample-iteration/scripts/validate_reference_mapping.py <order_folder>/reference_mapping.md --slide-plan <order_folder>/slide_plan.md --approval-log <order_folder>/approval_log.json
```

The validator blocks missing slide rows, blocked rows, missing local images, reference images placed under `origin_image/`, and stale approvals. Use `--write-normalized-json` when Stage 3 needs a machine-readable mapping summary.

### `slide_plan.md`

Update this file when feedback changes the production plan.

Each slide should eventually point to an approved style or sample reference:

```markdown
### Template / Style Plan
- Source:
- Current description:
- Reference files:
- Page type:
- Sample required:
- Sample strategy:
- Approval status:
- Approved reference:
```

Before full production, `Approval status` should be approved for the deck-level style and every slide's approved reference should be represented in `reference_mapping.md`.

## Sample Image Handling

Store samples under:

```text
samples/
├── round_01/
├── round_02/
└── approved/
```

Recommended names:

```text
samples/round_01/slide_03_direction_a.png
samples/round_01/slide_03_direction_b.png
samples/round_02/slide_03_revised.png
samples/approved/content_reference.png
```

Keep samples separate from final production images. Do not put sample images into `origin_image/` unless full production later intentionally accepts that slide as final.

## Sample Generation Handoff

When creating sample slide images, use the same worker discipline as full production whenever subagents are available. The parent agent prepares the sample plan and image inputs; a sample worker generates one sample image and returns the selected generated file plus a short QA note.

For each sample worker, provide actual bitmap inputs, not just filenames:

- approved or draft reference images for style/layout
- required client images assigned to that sample slide
- rendered source pages when they are needed to understand placement

If a sample worker cannot open, view, or attach a bitmap input to the selected image backend, it must return a blocker. Do not ask the user to upload images that already exist locally unless the current runtime truly cannot hand them to the image backend or worker.

## Feedback Loop

For each round:

1. Read current `slide_plan.md`, `sample_plan.md`, and any new client feedback.
2. Decide whether the feedback is global style feedback, page-type feedback, or local slide feedback.
3. Update `sample_feedback.md`.
4. Update `slide_plan.md` if the production plan changed.
5. If another sample round is needed, update `sample_plan.md`.
6. Once approved, create or update `approved_style_reference.md`.
7. Create or update `reference_mapping.md` so every slide maps to an approved reference image.

Do not call the style approved from your own judgment. Approval must come from the user or client feedback provided by the user.

Do not call the reference mapping approved from your own judgment if the mapping changes the client's plan. If the mapping follows the already approved plan and sample feedback, record it; otherwise ask the user for confirmation.

Every new approval checkpoint must return to the user. The agent does not ask the client directly. The user decides whether to ask the client and then reports the result.

## What To Report

When preparing a sample round, report:

- sample strategy
- sample slide count
- which slides or page types will be sampled
- files that will be used as template/style/image references
- any open questions before sample generation

After feedback, report:

- what changed in the plan
- whether another sample round is needed
- whether `approved_style_reference.md` was created
- whether `reference_mapping.md` now maps every slide to a reference image
- that full deck production has not started
- whether another user/client approval is required before moving on

## Handoff To Full Production

After sample approval, full production should use:

- confirmed `slide_plan.md`
- `approved_style_reference.md`
- `reference_mapping.md`
- approved sample images under `samples/approved/`
- required client assets exactly as planned

The production stage should follow the image-based slide generation approach inspired by `codex-ppt`: one generated image per slide, with each slide using the reference image assigned in `reference_mapping.md`.
