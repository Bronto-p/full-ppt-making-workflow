# Slide Worker Prompt

Use this template when dispatching a slide subagent after the plan, sample direction, and reference mapping are approved.

```text
Generate slide <N> for this approved client PPT deck.

Deck dir: <absolute deck dir>
Slide job file: <absolute deck dir>/prompts/slide_<NN>.json
Output target owned by parent: <absolute deck dir>/origin_image/slide_<NN>.png
Selected image backend: <native/built-in image tool OR user-authorized CLI/API fallback>

Mandatory payload:
- text_content: approved text from slide_plan.md
- reference_images: actual approved reference image inputs prepared by parent
- required_images: actual client asset image inputs prepared by parent, if any

Input images prepared by parent:
- <absolute path> - approved reference image; use for style/layout/template reference
- <absolute path> - strict required client asset; preserve original content

Read the JSON job file. Open/view every listed reference image and required image before generation. Use the selected image backend only.

Use the native/built-in image generation backend first. Use CLI/API fallback only if the parent says the user authorized it or the native backend is unavailable/insufficient. If fallback would require sending client assets outside the native path and authorization is not stated, return blocker=<reason>.

Forbidden for final slide image creation:
- local drawing or rendering scripts
- Pillow-generated slides
- SVG, HTML/CSS, or canvas screenshots
- python-pptx/PptxGenJS/native PPT layout screenshots
- manually composited text, card, chart, or image overlays

If any reference image or required image cannot be accessed, viewed, or attached to the image backend, stop and return blocker=<reason>.
If the selected image backend is unavailable, stop and return blocker=<reason>.
If a strict client asset cannot be preserved reliably by the selected backend, stop and return blocker=<reason>; do not create a similar replacement.
Do not edit slide job files, origin_image, speech.md, or assemble the PPT.

Before returning, visually check:
- approved text is present and readable
- Chinese text is not garbled
- style matches the mapped reference image
- required source images are visibly included and not replaced by similar redraws
- no overlapping or truncated important content

Return only:
backend_used=<backend>
selected_source=<absolute path to generated image>
qa_note=<one sentence>
```
