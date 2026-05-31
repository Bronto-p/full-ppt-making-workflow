---
name: ppt-plan-order
description: Create a consistent PPT production plan from a client order folder. Use when the user provides client requirements, source documents, PPT/PPTX files, PDFs, Word files, images, templates, screenshots, logos, or other assets and wants a deck-wide requirement summary plus a page-by-page plan before making samples or producing the final PowerPoint.
---

# PPT Plan Order

## Purpose

Turn messy client materials into one predictable planning file: `ppt_plan.md`.

This skill does not create sample slides, final slide images, or PPTX files. It only reads the order folder and writes the plan that a human or later PPT skill can use.

## Input

Accept any order folder that contains client requirements and production materials, including:

- Word, PDF, PPT/PPTX, TXT, Markdown, spreadsheet, or chat-log requirement files
- source content documents
- old PPT decks to redesign or use as content
- template PPT files or rendered template images
- style references
- logos, product images, screenshots, charts, portraits, certificates, or other client images

Start from the client requirements when they are identifiable. Then inspect the rest of the folder and connect each file to the plan.

## Output

Always create or update this file in the order folder:

```text
ppt_plan.md
```

Use the same structure every time.

```markdown
# PPT Plan

## Deck Requirements
- Goal:
- Audience:
- Slide count:
- Overall theme:
- Overall template/style:
- Main source files:
- Template/reference files:
- Image asset files:

## Slide Plan

### Slide 1: {slide title}
- Content:
- Template/theme:
- Page layout/structure:
- Template/reference path:
- Images:
  - Path:
  - Role:
  - Use on slide:

### Slide 2: {slide title}
- Content:
- Template/theme:
- Page layout/structure:
- Template/reference path:
- Images:
  - Path:
  - Role:
  - Use on slide:
```

## Planning Rules

- Keep the plan concise and production-ready.
- Use local paths for every referenced source file, template file, reference image, and slide image asset.
- If a slide has no client image asset, write `Images: none` for that slide.
- If a slide uses a general deck template or style reference, repeat that path in the slide's `Template/reference path` field.
- If a template/reference is only a verbal style direction, write the direction in `Template/theme` and use `Template/reference path: none`.
- If the client supplied page-by-page content, preserve that page order.
- If the client supplied long-form content, create a practical slide breakdown.
- If the client supplied images near specific source-page content, assign those images to the matching slide.
- Do not leave client images as a loose asset pool when their slide use is clear.
- Do not add optional notes or open-question sections unless the user explicitly asks for them.

## Hard Constraints

- Always output `ppt_plan.md` with the exact top-level sections `Deck Requirements` and `Slide Plan`.
- Every planned slide must have `Content`, `Template/theme`, `Page layout/structure`, `Template/reference path`, and `Images`.
- Every referenced template, reference, or image must include a local path when a file exists.
- Do not invent file paths. If no matching file exists, write `none`.
- Do not skip client-provided images that clearly belong to a slide.
- Do not generate sample images, final slide images, or PPTX files.
- Do not add approval gates, approval logs, status tracking, worker instructions, or production job files.
- Do not stop to ask questions during planning unless the folder contains no identifiable client requirement or source content at all.

## Meaning Of Key Fields

- `Overall theme`: the deck's visual direction in plain language, such as modern corporate, medical academic, luxury product, investor pitch, or education/training.
- `Overall template/style`: the template, reference deck, visual style, color/font/layout direction, or client brand direction used across the deck.
- `Template/theme`: the slide-specific layout or visual treatment, such as cover page, title-and-bullets, image-heavy page, comparison, timeline, process, data/chart, case study, or closing page.
- `Page layout/structure`: the concrete arrangement of the slide, such as title position, content blocks, image placement, chart/table area, section balance, visual hierarchy, and whether the page should be full-bleed, split layout, grid, cards, timeline, process flow, or centered statement.
- `Template/reference path`: the local file path to the template PPT, rendered template page, reference image, old deck page, or other visual reference for that slide.
- `Images`: the exact client image files planned for that slide, with each image's purpose and placement/use.

## Final Response

After writing `ppt_plan.md`, report:

- the path to `ppt_plan.md`
- the planned slide count
- the main template/reference files used
- the main image asset files assigned
- that no PPT has been generated
