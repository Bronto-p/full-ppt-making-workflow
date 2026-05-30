---
name: ppt-order-planner
description: Turn a client PPT order folder into the first-stage production plan for an image-based PPT workflow. Use when the user has a customer requirement document plus PPT, Word/PDF/text, template, image, logo, or old-deck materials and wants to organize each slide's text, image assets, and initial template/style plan before sample-slide iteration.
---

# PPT Order Planner

## Purpose

This skill prepares a customer PPT order for the first stage of an image-based PPT workflow. It reads the client requirement document first, verifies the referenced materials in the order folder, then creates:

- `order_materials.md`: what the client provided and how each material should be used.
- `slide_plan.md`: the per-slide plan that locks text, image assets, initial template/style plan, and draft reference-image mapping.

Use this before `ppt-sample-iteration` when the user is handling a real client order with mixed materials.

Do not generate slides, sample images, `deck_spec.json`, or PPTX files in this skill. This skill plans the job and prepares the plan for client approval; sample images and final reference mapping are handled by the second-stage sample iteration skill.

## Core Principle

Start from the client's stated requirements. Do not infer the customer's intent primarily from filenames, file extensions, or folder names.

Files still need to be inspected and verified, but the client requirement document is the source of truth for what each material is meant to do.

## Required Input

The order folder must contain a client requirement document, such as:

- `客户要求.docx`
- `需求说明.md`
- `聊天记录整理.txt`
- `order_brief.pdf`
- another clearly named document that explains the customer's request

If no client requirement document is present, stop and ask the user to add one or identify which file contains the client's requirements.

## Workflow

### 1. Locate And Read The Client Requirement

Inspect the order folder and identify the requirement document. Read it before interpreting other materials.

Extract:

- goal and use case
- target audience
- desired page count, if stated
- required deadline or delivery format, if stated
- content source
- template or style reference
- image/material usage requirements
- whether text rewriting is allowed
- whether final PPT must be object-editable
- any fixed brand, logo, color, font, or layout requirements

If the requirement document mentions attached files, verify that those files exist in the order folder.

### 2. Inspect And Verify Materials

Review the files that the client requirement references. Also scan the folder for unmentioned files that may be useful or need clarification.

For PPT/PPTX files, do not assume the role from the extension. Inspect representative pages or render them when needed, then describe how the requirement document says to use them:

- template to apply
- style reference
- old PPT to redesign
- old PPT to polish
- content deck to preserve
- page-by-page brief
- unclear, needs question

For DOCX/PDF/TXT/MD files, inspect whether they contain:

- client requirements
- source content
- page-by-page slide text
- brand/style guide
- embedded images or tables
- mixed content that needs splitting

For images, visually inspect important or referenced files when possible. Identify likely use:

- logo or brand asset
- product image
- screenshot
- chart/data figure
- certificate/document proof
- portrait/team photo
- background/decorative image
- template/style reference image
- unknown

Treat real logos, product screenshots, certificates, data charts, portraits, and brand assets as requiring explicit preservation unless the requirement document says otherwise.

### 3. Create `order_materials.md`

Write a concise material summary in the order folder.

Required sections:

```markdown
# Order Materials

## Client Requirement Summary
- Goal:
- Use case:
- Audience:
- Page count:
- Content source:
- Template/style source:
- Image/material policy:
- Text rewrite policy:
- Editability requirement:
- Special requirements:

## Materials
| File | Role In Production | Notes |
|---|---|---|
| 客户要求.docx | Requirement document | Source of truth |
| 内容.docx | Content source | Needs slide planning |
| 模板.pptx | Template/style reference | Use according to requirement |
| logo.png | Required brand asset | Preserve exactly |

## Unclear Items
- ...
```

Only include conclusions supported by the requirement document or by direct inspection. If something is unclear, put it under `Unclear Items`.

### 4. Create `slide_plan.md`

Create a per-slide production plan in the order folder. This is the main handoff artifact for sample iteration and later full PPT generation.

Every slide should lock four things:

1. Text content
2. Initial template/style plan
3. Image assets and image policy
4. Draft reference-image plan

Use this format:

```markdown
# Slide Plan

## Slide 1: {Title}

### Text
- Source:
- Rewrite allowed:
- Title:
- Body:
  - ...
- Must preserve:
  - ...

### Template / Style Plan
- Source:
- Current description:
- Reference files:
- Page type:
- Sample required:
- Sample strategy:
- Draft reference image:
- Reference mapping status:
- Approval status:
- Approved reference:

### Images
- Required:
  - File:
    - Role:
    - Preservation:
- Optional:
  - File:
    - Role:
- Free image generation/search:

### Open Questions
- ...
```

If the client has already specified every page, preserve that structure. If the client provided long-form content instead of page-by-page content, propose a practical slide breakdown and mark it for confirmation.

If the client provided a template or style reference, map each slide to the relevant template page type when possible: cover, agenda, section divider, content page, image page, data page, closing page, or another visible page type. Set `Approval status` to `not approved` because a sample still needs client confirmation.

If the client did not provide a template or visual reference, still write a clear template/style plan from the requirement document and the deck purpose. Describe the intended visual direction in `Current description`, set `Source` to `client verbal requirement` or `agent-designed draft`, and set `Sample strategy` to `2-3 directions` or `2-3 page type samples`.

If the client wants an old PPT beautified or redesigned, treat the old PPT primarily as content source unless the requirement document says its existing visual style should be kept. The initial template/style plan should describe the new direction to test through samples.

If the client provided images, do not leave them as a general pool when their use can be planned. Assign them to slides where appropriate. If a required image placement is unclear, list it in `Open Questions`.

### 5. Add Draft Reference Mapping Plan

Add a deck-level section to `slide_plan.md`:

```markdown
## Draft Reference Mapping Plan

| Slide | Page Type | Planned Reference Source | Planned Reference Image | Status | Notes |
|---:|---|---|---|---|---|
| 1 | cover | client template page | template_renders/page_01.png | needs client approval | Use as cover reference |
| 2 | content | pending generated sample | samples/approved/content_reference.png | pending sample | Reuse for standard content pages |
```

This section is a plan, not final approval. It must make every slide's intended visual reference explicit before sample iteration.

Rules:

- A reference image can be reused by many slides.
- If the client provided a template PPT or reference image, use rendered/visible template pages or reference images as planned reference images when available.
- If the client did not provide a template, mark the planned reference image as pending sample output, such as `samples/approved/content_reference.png`.
- If the client has a different template page for each slide, preserve that one-slide-to-one-reference mapping.
- If a slide has no clear planned reference source, list it in `Open Questions`.

### 6. Recommend The Sample Strategy

Add a deck-level section to `slide_plan.md`:

```markdown
## Sample Strategy
- Reason samples are needed:
- If client provided template/reference:
- If no template/reference was provided:
- Recommended sample count:
- Recommended sample slides:
- What the client must approve:
```

Use these defaults:

- Clear client template/reference: plan one representative sample slide.
- No template/reference, only verbal direction: plan 2-3 visual directions.
- Old PPT beautification/redesign: plan 2-3 representative samples, such as cover, standard content, and complex image/data/process page.
- Strongly varied deck page types: plan samples by page type rather than one generic slide.

### 7. Ask For Client Plan Confirmation

After creating `order_materials.md` and `slide_plan.md`, report:

- paths to both files
- the planned slide count
- the recommended sample strategy
- the draft reference mapping approach
- which items still need clarification
- that no slide images or PPT files were generated

Ask the user to confirm or edit the full `slide_plan.md` before running `ppt-sample-iteration`. The confirmation must cover:

- every slide's text content
- every slide's image usage and required assets
- every slide's template/style plan
- every slide's draft reference-image mapping
- the sample strategy

If the user says the client has not approved the plan yet, stop after reporting the files and questions. Do not begin sample iteration until the plan is approved or the user explicitly authorizes internal sample drafts.

## Hard Rules

- Always start from the client requirement document.
- If no requirement document exists, stop and ask for one.
- Verify that files referenced by the requirement document exist.
- Do not classify an order only from filenames, extensions, or folder names.
- Do not assume a PPT file is a template; inspect it if its role matters.
- Do not assume client-provided images are optional.
- For client-required images, preserve original image content; do not replace, redraw, or approximate it.
- If template usage is unclear, ask whether it is strict template use, style reference, loose direction, or not relevant.
- If image usage is unclear, ask which images are required and where they should appear.
- If text rewrite permission is unclear, ask whether content can be edited, summarized, or only visually arranged.
- The planned final workflow is image-based slide generation. Still record any client editability requirement as a delivery risk or open question.
- The full plan must be approved before sample iteration: slide text, image usage, template/style plan, draft reference-image mapping, and sample strategy.
- Do not generate sample slides, final slide images, `deck_spec.json`, `speech.md`, or PPTX files during this skill.

## Handoff To Sample Iteration

After the user confirms `slide_plan.md`, use `ppt-sample-iteration` to generate or coordinate sample slides and collect client feedback.

When handing off:

- Use `order_materials.md` and `slide_plan.md` as the source of truth.
- Keep required images as strict input assets.
- Use template files, rendered template pages, reference images, or draft style descriptions as sample references.
- Preserve text rewrite constraints and image preservation rules.
- Do not move to full production until sample images are approved, `approved_style_reference.md` exists, and `reference_mapping.md` maps every slide to an approved reference image.
