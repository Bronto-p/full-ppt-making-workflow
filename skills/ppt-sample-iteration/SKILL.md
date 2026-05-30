---
name: ppt-sample-iteration
description: Run the sample-slide iteration stage for a client PPT order. Use after ppt-order-planner has created slide_plan.md and before full deck production, to plan 1-3 sample slides, generate or coordinate image-based samples, collect client feedback, update the style/template plan, and produce approved_style_reference.md.
---

# PPT Sample Iteration

## Purpose

This skill handles the second stage of the client PPT workflow: sample slides and style approval.

Use it after `ppt-order-planner` has created a first `slide_plan.md`. This skill turns the initial template/style plan into client-approved visual references before full PPT production.

Final PPT production is out of scope. Do not generate the full deck, `deck_spec.json`, final `origin_image/slide_XX.png` set, `speech.md`, or PPTX files in this skill.

## Workflow Position

The overall workflow is:

1. `ppt-order-planner`: organize client requirements, materials, per-slide text, image assets, and initial template/style plan.
2. `ppt-sample-iteration`: generate sample slides, handle feedback, and lock the approved template/style references.
3. Full production: use the approved plan and references to generate the full image-based PPT workflow.

This skill only performs step 2.

## Required Inputs

The order folder should contain:

- `order_materials.md`
- `slide_plan.md`
- the source files referenced by those plans

If `slide_plan.md` is missing, stop and ask the user to run or provide the output from `ppt-order-planner` first.

If client feedback is provided, read it before planning the next sample round.

## Core Rules

- Samples are used to confirm the visual system before full deck production.
- Whether the client provided a template or not, sample approval is still required before full production.
- Use image-based slide sample generation consistent with the final production approach.
- Do not treat a verbal style direction as approved until the client has approved sample images.
- Do not proceed to full deck generation during this skill.
- If client feedback changes the style, layout, text density, image treatment, or template usage, update the plan before generating another sample.

## Sample Strategy

Choose the smallest useful sample set.

If the client provided a clear template, reference image, or template PPT:

- Default to one representative sample slide.
- Prefer a real content slide over a cover unless the cover is the main buying decision.
- Use the provided template/reference as visual guidance.

If the client did not provide a template or only gave a verbal direction:

- Default to 2-3 visual directions.
- Each direction may use the same representative slide so the client can compare style clearly.
- If the deck has very different page types, use 2-3 sample pages instead: cover, standard content, and image/data page.

If the client wants an old PPT beautified or redesigned:

- Select 2-3 representative pages from the old PPT: cover, normal content page, and a complex image/data/process page when available.
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

## Samples To Produce

### Sample A
- Slide:
- Purpose:
- Text source:
- Template/style source:
- Required images:
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
- Approved by:
- Date:

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

Before full production, `Approval status` should be approved for the deck-level style, or unresolved items should be listed clearly.

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

## Feedback Loop

For each round:

1. Read current `slide_plan.md`, `sample_plan.md`, and any new client feedback.
2. Decide whether the feedback is global style feedback, page-type feedback, or local slide feedback.
3. Update `sample_feedback.md`.
4. Update `slide_plan.md` if the production plan changed.
5. If another sample round is needed, update `sample_plan.md`.
6. Once approved, create or update `approved_style_reference.md`.

Do not call the style approved from your own judgment. Approval must come from the user or client feedback provided by the user.

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
- that full deck production has not started

## Handoff To Full Production

After sample approval, full production should use:

- confirmed `slide_plan.md`
- `approved_style_reference.md`
- approved sample images under `samples/approved/`
- required client assets exactly as planned

The production stage should follow the image-based slide generation approach inspired by `codex-ppt`: one generated image per slide, with approved samples used as style/template references.
