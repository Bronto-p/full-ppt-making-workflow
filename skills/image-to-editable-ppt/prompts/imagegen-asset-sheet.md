# Imagegen Asset Prompt 模板

## Picture / Screenshot / Chart Asset

```text
Use case: high-fidelity-slide-asset-reconstruction
Input images: Image 1: source slide strict visual reference
Primary request: reconstruct the specified embedded picture/screenshot/chart/UI panel as an independent raster asset for PowerPoint layering.
Target asset: <describe source region, content, and role>
Preserve exactly: content, layout, text, numbers, punctuation, chart labels, UI labels, icon positions, colors, crop, perspective, borders, shadows, and visual style from the source region.
Output: a clean standalone image asset with the same rectangular/transparent boundary needed for placement on the slide.
Constraints: do not substitute similar content, do not rewrite text, do not simplify labels, do not change the chart/UI/data, do not add watermark.
```

## Art Text Asset

```text
Use case: high-fidelity-decorative-text-asset
Input images: Image 1: source slide strict visual reference
Primary request: reconstruct the specified art text as an independent transparent raster asset.
Target art text: <exact visible text and source region>
Preserve exactly: glyph shapes, handwriting/lettering style, stroke weight, fill, gradient, outline, shadow, glow, texture, perspective, rotation, spacing, and visual energy.
Output: transparent-background PNG-style asset, tightly but safely padded.
Constraints: do not convert to a plain font, do not change letters, do not add extra text, do not add watermark.
```

## Sparse Visual Asset Sheet

```text
Use case: high-fidelity-slide-visual-assets
Input images: Image 1: slide visual reference
Primary request: create one sparse asset sheet containing the reusable foreground visual objects from the slide.
Scene/backdrop: perfectly flat solid <#00ff00 or #ff00ff> chroma-key background.
Subject: icons, pictograms, badges, stickers, hand-drawn marks, decorative arrows, check marks, warning symbols, chart glyphs, underlines, tapes, logo-like marks, art text, and other foreground objects listed below. Use the same count, order, semantic identity, colors, stroke style, rough proportions, and visual style as the source inventory:
<asset list>
Constraints: every object must be fully visible, internally complete, separated from every other object by generous pure chroma-key space, and surrounded by padding. Spacing is more important than asset size. No missing objects, no substituted symbols, no touching, no overlap, no cross-object shadows, no unwanted readable text, no pseudo text, no full cards, no full panels, no full page fragments, no watermark. Do not add objects not present in the reference.
```

使用说明：

- 绿色资产不要用 `#00ff00`，改用 `#ff00ff` 或其他缺席颜色。
- 紫色/洋红资产不要用 `#ff00ff`。
- 含字图片、复杂 UI、复杂图表、证书和精确截图优先单独生成，不要塞进拥挤 sheet。
- asset sheet 拥挤或对象粘连时，应重新生成更稀疏的 sheet，不要强行后处理。
