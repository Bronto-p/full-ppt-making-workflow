# Background And Client Images

This workflow differs from generic image-to-editable conversion: previous stages know which client images were required on each slide.

Use that metadata.

## Core Rule

When a slide contains client-required images, do not reconstruct those image regions from the flattened slide screenshot alone.

Provide both:

- the full slide `source.png`
- the original client image asset files listed in `slide_plan.md` or `prompts/slide_XX.json`

The full slide shows placement, crop, lighting, masking, and composition. The original client asset preserves identity.

## Default Client Image Strategy

By default, client-required images should be preserved through imagegen using the original image asset as input and visually integrated into the reconstructed background/scene.

This is preferred over simply pasting a rectangle image layer on top when the source slide visually embeds the image with:

- crop treatment
- perspective
- mask shape
- gradient fade
- soft shadow
- blending
- reflection
- rounded clipping
- paper/photo frame treatment
- partial transparency
- depth or lighting effects

The prompt must explicitly state:

- preserve the original asset identity
- preserve text, logos, UI details, data, faces, certificates, and visual content
- use the source slide for placement and treatment
- do not redraw or substitute the asset

## When To Keep Client Image As Separate Layer

Use a separate picture layer when:

- the image is a simple rectangular photo/screenshot
- it has no complex blending with the background
- the user likely needs to move or replace it later
- preserving exact pixels matters more than integrated visual effects

Even then, match crop, border, shadow, mask, and position as closely as possible.

## Clean Background

The clean background should remove:

- main slide text that will become editable
- foreground icons and assets that will be layered separately
- duplicated labels or callouts that will be native text

The clean background may preserve:

- incidental tiny background text
- image-contained text in preserved client image areas
- visual texture, blurred charts, distant UI, or decorative screen details

Do not ask imagegen to remove all text globally. Specify which text/objects are being reconstructed separately.

## Background Inspection

After generating a clean/integrated background:

- compare it to source
- verify placement and treatment of client images
- verify client image identity was preserved
- verify main editable text is not duplicated
- verify incidental background details are acceptable
- if a client image changed identity, repair using the original asset input again
