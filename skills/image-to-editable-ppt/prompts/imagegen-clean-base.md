# Clean Background Prompt 模板

## Full-Slide Clean Background

```text
Use case: high-fidelity-slide-background-edit
Input images: Image 1: source slide, edit target, and strict visual reference
Primary request: create a full-slide clean background for a layered editable PowerPoint reconstruction.
Preserve exactly: original canvas ratio, composition, camera angle, perspective, crop, major object positions, panel/card/container layout, embedded background picture areas, colors, lighting direction, contrast, texture/materials, depth of field, brand style, and overall slide identity.
Remove only: main title, subtitle, body text, main labels, editable numeric values, callout text, foreground icons, foreground pictures, art text, badges, stickers, hand-drawn marks, and objects that will be overlaid separately.
Keep allowed decorative background text: tiny texture text, watermark-like microtext, non-editable screen noise, ornamental glyphs, and decorative marks that are part of the background atmosphere and will not be duplicated as editable text.
Constraints: fill removed areas with coherent continuation of the original slide background. Do not invent a new room, new dashboard, new product, new illustration, new camera angle, new object placement, or different lighting. No ghost text, no blur patches, no dark boxes, no pseudo text in removed primary text areas, no watermark.
```

## Dense Report / Dashboard Background

```text
Use case: high-fidelity-slide-background-edit
Input images: Image 1: source slide visual reference
Primary request: create a clean layout background for rebuilding an editable PowerPoint page.
Preserve exactly: broad background fills, gradients, panels, empty cards, empty containers, table/grid lines, chart frames, axis lines, shadows that belong to containers, spacing, brand colors, and overall composition.
Remove: all main readable titles, body copy, editable labels, editable numbers, legends that will be rebuilt, foreground icons, art text, badges, stickers, and reusable foreground objects that will be overlaid separately.
Allowed to keep: decorative microtext, watermark texture, tiny non-editable screen noise, and background ornamentation when it is not part of the main text layer.
Constraints: leave clean blank areas matching surrounding fills. No ghost text, no fake labels, no watermark, no layout redesign.
```
