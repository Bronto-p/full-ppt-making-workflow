# Imagegen Repair Prompt 模板

## Clean Background Repair

```text
Use case: high-fidelity-slide-background-repair
Input images: Image 1: current clean background; Image 2: original slide reference
Primary request: repair only the specified problem in the clean background.
Problem to fix: <leftover primary text | ghost mark | bad inpainting | duplicated icon | layout drift | wrong preserved decoration>
Preserve: all unaffected composition, colors, texture, lighting, panels, spacing, background decorative microtext, and slide identity.
Change only: the specified problem area.
Constraints: remove leftover primary text or foreground objects completely. No pseudo text in removed primary text areas, no blur patches, no new objects, no layout redesign, no watermark.
```

## Picture / Screenshot Asset Repair

```text
Use case: high-fidelity-slide-asset-repair
Input images: Image 1: original slide reference; Image 2: previous failed asset
Primary request: regenerate or repair only the specified embedded picture/screenshot/chart/UI asset.
Problem to fix: <wrong text | wrong numbers | layout drift | missing detail | bad crop | style drift>
Preserve exactly: source content, text, numbers, punctuation, chart/UI layout, colors, borders, and proportions.
Constraints: do not substitute similar content, do not simplify labels, do not add watermark.
```

## Art Text Repair

```text
Use case: high-fidelity-art-text-repair
Input images: Image 1: original slide reference; Image 2: previous failed art text asset
Primary request: repair the specified art text asset.
Problem to fix: <wrong letters | plain-font look | missing outline | wrong shadow | bad transparency | clipped glyph>
Preserve exactly: visible letters, handwritten/lettering style, stroke weight, fill, gradient, outline, shadow, glow, texture, rotation, and spacing.
Constraints: transparent output, no extra text, no watermark.
```

## Visual Asset Sheet Repair

```text
Use case: high-fidelity-visual-asset-repair
Input images: Image 1: slide visual reference; Image 2: previous failed asset or sheet
Primary request: regenerate only the specified foreground asset(s) as clean isolated bitmap object(s) on a flat chroma-key background.
Assets to repair: <asset list>
Constraints: each asset must be complete, separated, unclipped, and surrounded by pure chroma-key padding. Keep the visual metaphor and style close to the slide reference. No extra objects, no cross-object shadows, no watermark.
```
