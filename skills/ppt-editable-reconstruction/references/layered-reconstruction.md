# Layered Reconstruction

Use this page-level order:

1. Inspect the source page and prior production metadata.
2. Build a semantic layer plan.
3. Generate or edit the clean visual background.
4. Inspect the clean background.
5. Generate or preserve foreground visual assets that must remain separate.
6. Add native editable text boxes.
7. Build the page PPTX.
8. Render preview, compare with source, repair the smallest failing layer.

## Semantic Layer Plan

Before making assets, classify every visible element:

- background / clean base
- embedded client image treatment
- required image that should remain a separate picture layer
- native editable slide text
- image-contained text
- incidental background text
- artistic text / word art
- simple native shape
- generated visual asset
- source-derived raster asset

Record decisions in `manifest.json`. Do not begin final page construction until this plan is explicit.

## Preferred Layer Order

Use this z-order unless the source requires otherwise:

- clean background / integrated generated background: 0
- simple native structural shapes: 10-20
- separate picture assets and generated visual assets: 30
- native editable text boxes: 40+

## Fidelity Priority

For this workflow, visual fidelity and client asset preservation are more important than making every decorative object a native shape.

Use native PPT shapes for simple geometry only: rectangles, lines, circles, table/grid lines, simple arrows, and simple containers.

Use imagegen or source-preserving bitmap assets for complex icons, illustration details, artistic marks, textured decoration, word art, photo treatments, and objects where native shapes would look crude.

## No Full-Slide Screenshot Fallback

Do not use the original full-slide source image as the background with editable text placed over it. That creates duplicate text, uneditable foreground objects, and low reconstruction quality.

The background should be cleaned or regenerated so later editable text and layered assets do not duplicate source elements.
