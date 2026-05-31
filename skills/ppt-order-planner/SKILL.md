---
name: ppt-order-planner
description: Turn a client PPT order folder into the first-stage production plan for an image-based PPT workflow. Use when the user has a customer requirement document plus PPT, Word/PDF/text, template, image, logo, or old-deck materials and wants to organize each slide's text, image assets, and initial template/style plan before sample-slide iteration.
---

# PPT Order Planner

## Purpose

This skill prepares a customer PPT order for the first stage of an image-based PPT workflow. It reads the client requirement document first, verifies the referenced materials in the order folder, then creates:

- `order_materials.md`: what the client provided and how each material should be used.
- `slide_plan.md`: a concise per-slide plan that locks title/subtitle/body, template/reference, and exact slide image assets.
- `material_manifest.json` or references to existing ingestion outputs when the order contains embedded visuals, scanned pages, Office/PDF/PPT files, archives, or cloud-linked assets.

## Scripts

Use `scripts/ingest_materials.py` before planning when the order has Office/PDF/container files or embedded visuals:

```bash
python skills/ppt-order-planner/scripts/ingest_materials.py <order_folder>
```

It creates `material_manifest.json`, `slide_visual_index.md`, `ingestion_notes.md`, extracted DOCX/PPTX/XLSX media where available, rendered PDF and Office pages when local dependencies are available, linked/external Office asset findings, and a contact sheet for viewable source and derived visuals. This is a visibility check, not a replacement for reading the requirement document.

Use `scripts/lint_slide_plan.py` before handoff when a plan has been drafted:

```bash
python skills/ppt-order-planner/scripts/lint_slide_plan.py <order_folder>/slide_plan.md
```

Use `scripts/approval_log.py` to record and verify approval checkpoints:

```bash
python skills/ppt-order-planner/scripts/approval_log.py add --log <order_folder>/approval_log.json --stage plan --approved-by "user-confirmed client approval" --artifact slide_plan.md --artifact order_materials.md
python skills/ppt-order-planner/scripts/approval_log.py check --log <order_folder>/approval_log.json --stage plan --artifact slide_plan.md
```

Use this before `ppt-sample-iteration` when the user is handling a real client order with mixed materials.

Do not generate slides, sample images, `deck_spec.json`, or PPTX files in this skill. This skill plans the job and prepares the plan for client approval; sample images and final reference mapping are handled by the second-stage sample iteration skill.

## Core Principle

Start from the client's stated requirements. Do not infer the customer's intent primarily from filenames, file extensions, or folder names.

Files still need to be inspected and verified, but the client requirement document is the source of truth for what each material is meant to do.

Text visibility and visual visibility are separate. A DOCX, PDF, PPTX, spreadsheet, or archive may be readable as text while embedded pictures, charts, screenshots, or scanned pages are invisible unless they are extracted or rendered. If embedded visuals matter, create or use rendered page images, extracted image files, or contact sheets before planning image usage.

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

If the requirement document itself is DOCX, PDF, PPT/PPTX, a scan, or contains screenshots/images/tables, verify whether those visuals can be seen. If not, render/extract them or mark the visibility gap in `Unclear Items`.

### 2. Inspect, Render, Extract, And Verify Materials

Review the files that the client requirement references. Also scan the folder for unmentioned files that may be useful or need clarification.

For every non-plain-text container, record:

- whether text was extracted
- whether pages were rendered to images
- whether embedded images/charts/tables were extracted or visibly inspected
- whether the file has comments, tracked changes, speaker notes, animations, videos, linked media, or password protection
- whether the agent can actually see the visuals or only knows their filenames

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

If DOCX/PDF files contain embedded images, tables, scans, charts, signatures, certificates, or screenshots, do not rely on text extraction alone. Render pages or extract the embedded media and assign those visuals to the slide/page where they appear.

When a source document is page-by-page slide content with images pasted below or near each page's text, treat those images as slide-scoped required assets. Do not leave them as a global extracted-media pool. Use `slide_visual_index.md`, rendered pages, paragraph order, nearby captions, filenames, contact sheets, and direct visual inspection to map each extracted image back to its slide. If a visual's slide cannot be determined, put that exact file under the most likely slide's `Open Questions` instead of omitting it.

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

For cloud links, linked Office media, archives, password-protected files, corrupted files, or unsupported formats, ask the user for exported local files or mark them blocked. Do not assume linked assets will still be accessible later.

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
| File | Role In Production | Text Visible | Visuals Visible | Notes |
|---|---|---:|---:|---|
| 客户要求.docx | Requirement document | yes | rendered/extracted | Source of truth |
| 内容.docx | Content source | yes | needs extraction | Needs slide planning |
| 模板.pptx | Template/style reference | partial | rendered pages | Use according to requirement |
| logo.png | Required brand asset | n/a | yes | Preserve exactly |

## Unclear Items
- ...

## Ingestion Outputs
- material_manifest.json:
- slide_visual_index.md:
- rendered pages:
- extracted images:
- contact sheets:
```

Only include conclusions supported by the requirement document or by direct inspection. If something is unclear, put it under `Unclear Items`.

### 4. Create `slide_plan.md`

Create a per-slide production plan in the order folder. This is the main handoff artifact for sample iteration and later full PPT generation.

Every slide should be short and production-ready. Do not create a large nested plan when the client already provided page-by-page content.

Use this format:

```markdown
# Slide Plan

## Slide 1: {Title}

### Content
- Source:
- Rewrite allowed:
- Title:
- Subtitle:
- Body:
  - ...
- Must preserve:
  - ...

### Template / Reference
- Page type:
- Draft reference image:
- Approval status:
- Approved reference:

### Images
- Required:
  - File:
    - Role:
    - Preservation:
    - Placement evidence:
- Optional:
  - File:
    - Role:
- Placement images:
  - File:
    - Role:
- Free image generation/search:

### Open Questions
- ...
```

Keep image prompts/descriptions concise. For requested or generated images, use one short production phrase plus preservation constraints, not long prose prompts. Example: `clean product photo, preserve original logo and labels`.

If the client has already specified every page, preserve that structure. If the client provided long-form content instead of page-by-page content, propose a practical slide breakdown and mark it for confirmation.

If the client provided a template or style reference, map each slide to the relevant template page type when possible: cover, agenda, section divider, content page, image page, data page, closing page, or another visible page type. Set `Approval status` to `not approved` because a sample still needs client confirmation.

If the client did not provide a template or visual reference, still write a clear template/style plan from the requirement document and the deck purpose. Describe the intended visual direction in `Current description`, set `Source` to `client verbal requirement` or `agent-designed draft`, and set `Sample strategy` to `3 representative samples` unless the deck is too short or the user explicitly requests 2 samples.

If the client wants an old PPT beautified or redesigned, treat the old PPT primarily as content source unless the requirement document says its existing visual style should be kept. The initial template/style plan should describe the new direction to test through samples.

If the client provided images, do not leave them as a general pool when their use can be planned. Assign them to slides where appropriate. If a required image placement is unclear, list it in `Open Questions`.

Required image assignment rules:

- Read `slide_visual_index.md` before writing `slide_plan.md` whenever it exists.
- If an image is embedded on the same source page/section as a slide's text, assign it to that slide.
- If multiple images appear under one slide's text, list each image under that slide with a short role.
- If the source has rendered page images, use the rendered page as placement evidence and the extracted image as the strict asset when available.
- If only an extracted image is available, cite its extracted path and note the evidence used to map it.
- Never drop extracted visuals from `slide_plan.md`; every viewable extracted client visual must be either assigned to a slide, marked as a template/style reference, or listed in `Unclear Items`.

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

- Plan 3 sample slides by default for every order, regardless of whether the client provided a template, reference image, verbal direction, old PPT, or redesign request.
- Use 2 samples only when the deck is very short, page types are not varied, or the user explicitly chooses a smaller sample set.
- Choose representative page types, not only the most attractive page.
- Default sample mix: cover/opening page, standard content page, and the most complex page type.
- Complex page type can be image-heavy, data/process, comparison, product screenshot, timeline, case study, or another page that stresses the visual system.
- If the client has a different template page for each slide, choose 3 representative template/page types for samples and preserve the full per-slide template mapping in the draft reference mapping plan.
- Strongly varied deck page types: plan samples by page type rather than one generic slide.

### 7. Ask For Client Plan Confirmation

After creating `order_materials.md` and `slide_plan.md`, report:

- paths to both files
- the planned slide count
- the recommended sample strategy
- the draft reference mapping approach
- which items still need clarification
- that no slide images or PPT files were generated

Ask the user to confirm or edit the full `slide_plan.md` before running `ppt-sample-iteration`. The user is responsible for asking the client when client approval is needed; do not contact the client directly or assume approval. The confirmation must cover:

- every slide's text content
- every slide's image usage and required assets
- every slide's template/style plan
- every slide's draft reference-image mapping
- the sample strategy
- whether any embedded images/tables/charts from container documents were correctly read and assigned
- whether API fallback is allowed if the native image generation backend cannot complete the job later

If the user says the client has not approved the plan yet, stop after reporting the files and questions. Do not begin sample iteration until the plan is approved or the user explicitly authorizes internal sample drafts.

Record each approval in `approval_log.json` when practical, including approved artifact paths and hashes.

## Hard Rules

- Always start from the client requirement document.
- If no requirement document exists, stop and ask for one.
- Verify that files referenced by the requirement document exist.
- Verify that referenced visuals are actually visible to the agent, not only present inside a container file.
- Do not classify an order only from filenames, extensions, or folder names.
- Do not assume a PPT file is a template; inspect it if its role matters.
- Do not assume client-provided images are optional.
- For client-required images, preserve original image content; do not replace, redraw, or approximate it.
- If template usage is unclear, ask whether it is strict template use, style reference, loose direction, or not relevant.
- If image usage is unclear, ask which images are required and where they should appear.
- If text rewrite permission is unclear, ask whether content can be edited, summarized, or only visually arranged.
- The planned final workflow is image-based slide generation. Still record any client editability requirement as a delivery risk or open question.
- The full plan must be approved before sample iteration: slide text, image usage, template/style plan, draft reference-image mapping, and sample strategy.
- Every approval checkpoint must return to the user. The user decides whether to ask the client and then gives the result back to the agent.
- Do not generate sample slides, final slide images, `deck_spec.json`, `speech.md`, or PPTX files during this skill.

## Handoff To Sample Iteration

After the user confirms `slide_plan.md`, use `ppt-sample-iteration` to generate or coordinate sample slides and collect client feedback.

When handing off:

- Use `order_materials.md` and `slide_plan.md` as the source of truth.
- Keep required images as strict input assets.
- Use template files, rendered template pages, reference images, or draft style descriptions as sample references.
- Preserve text rewrite constraints and image preservation rules.
- Do not move to full production until sample images are approved, `approved_style_reference.md` exists, and `reference_mapping.md` maps every slide to an approved reference image.
