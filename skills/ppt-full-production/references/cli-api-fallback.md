# CLI/API Fallback

Use this reference only after CLI/API fallback has been selected.

## Runtime

Use this skill's local wrapper for fallback image generation when compatible:

```bash
python skills/ppt-full-production/scripts/image_gen.py --help
```

Do not manually recreate image generation logic. Keep generated images under the project output structure and record the selected result through `scripts/record_slide_result.py`.

## Blockers

Return a blocker if the fallback runtime is missing credentials, cannot attach required images, cannot preserve client assets, or produces output that cannot be inspected.
