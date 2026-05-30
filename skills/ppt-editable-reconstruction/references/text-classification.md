# Text Classification

Not all visible text should become native editable text. Classify text before reconstruction.

## Editable Slide Text

Use native PowerPoint text boxes for:

- slide titles
- subtitles
- body bullets
- labels and captions that belong to the designed slide content
- callouts
- section titles
- buttons or tags that are intended as slide text

Use prior production metadata when available: `slide_plan.md` and `prompts/slide_XX.json` are more reliable than OCR alone.

## Image-Contained Text

Keep text inside its image treatment when it belongs to:

- product screenshots
- UI screenshots
- charts or dashboard images
- certificates
- document screenshots
- portraits or photos containing signs/screens
- client-required image assets

This text should not be recreated as editable PPT text unless the user explicitly requests it. Preserving the original image identity is more important.

## Incidental Background Text

May remain inside the generated background when it is:

- tiny
- blurred
- decorative
- part of a distant screen, chart texture, newspaper texture, or background poster
- not meant to be read as main slide content

Do not remove all text blindly. Remove only text that will be reconstructed as native editable slide text or separate foreground assets.

## Artistic Text / Word Art

Artistic text may become an image asset when native text would break the design, such as:

- logo-like title marks
- heavily distorted lettering
- 3D/extruded text
- textured text integrated into an illustration
- ornamental typography where the exact visual treatment matters more than editability

Record why it is not native text.

## Font And Layout Calibration

For native text:

- estimate font size from source glyph height, container height, line spacing, and density
- use prior approved text content as the exact text source
- render preview and compare
- if preview text is larger or more crowded than source, reduce size first
- avoid hidden/off-canvas/transparent text as fake editability
