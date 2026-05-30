---
name: ppt-order-planner
description: Turn a client PPT order folder into a production-ready plan. Use when the user has a customer requirement document plus PPT, Word/PDF/text, template, image, logo, or old-deck materials and wants to organize what each slide should contain before using codex-ppt or another PPT production skill.
---

# PPT Order Planner

## Purpose

This skill prepares a customer PPT order for production. It reads the client requirement document first, verifies the referenced materials in the order folder, then creates:

- `order_materials.md`: what the client provided and how each material should be used.
- `slide_plan.md`: the per-slide plan that locks text, template/style reference, and image assets.

Use this before `codex-ppt` when the user is handling a real client order with mixed materials.

Do not generate slides, sample images, `deck_spec.json`, or PPTX files in this skill.

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

Create a per-slide production plan in the order folder. This is the main handoff artifact for later PPT generation.

Every slide should lock three things:

1. Text content
2. Template or style reference
3. Image assets and image policy

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

### Template / Style Reference
- File:
- Reference page/image:
- Usage:
- Strictness:

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

If the client provided a template or style reference, map each slide to the relevant template page type when possible: cover, agenda, section divider, content page, image page, data page, closing page, or another visible page type.

If the client provided images, do not leave them as a general pool when their use can be planned. Assign them to slides where appropriate. If a required image placement is unclear, list it in `Open Questions`.

### 5. Ask For Confirmation

After creating `order_materials.md` and `slide_plan.md`, report:

- paths to both files
- the planned slide count
- which items still need clarification
- that no slide images or PPT files were generated

Ask the user to confirm or edit `slide_plan.md` before handing off to `codex-ppt` or another production skill.

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
- If editability is unclear, ask whether image-based PPT output is acceptable or object-level editability is required.
- Do not generate sample slides, final slide images, `deck_spec.json`, `speech.md`, or PPTX files during this skill.

## Handoff To Codex PPT

After the user confirms `slide_plan.md`, use `codex-ppt` for visual production when image-based PPT output is acceptable.

When handing off:

- Convert `slide_plan.md` into the approved `outline.md` / `deck_spec.json` structure expected by `codex-ppt`.
- Carry required images as strict input assets.
- Carry template images or rendered PPT pages as style/template references.
- Preserve text rewrite and editability constraints.
- Keep unresolved questions out of production until answered.
