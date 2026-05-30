# User-Supplied Assets

Read this before using logos, screenshots, product images, charts, certificates, portraits, UI screenshots, or other client-provided assets that must appear in the deck.

Treat required client assets as source assets, not loose inspiration.

## Preservation

Preserve business-critical details: logos, UI text, data labels, chart values, faces, certificates, product details, and client branding. Do not redraw, approximate, replace, or hallucinate required images.

If the image generation backend cannot preserve a required asset reliably as an actual input image, record a blocker. Do not silently switch to a similar generated image or manual overlay.

## Worker Handoff

For each slide, list required assets in `required_images` with absolute path, role, and preservation rule. The parent must make the actual image available to the worker. If the image cannot be opened, viewed, or attached to the backend, record a blocker.

Keep `reference_images` separate from `required_images`: reference images guide style/layout, while required images are strict content assets.
