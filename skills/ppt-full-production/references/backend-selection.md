# Backend Selection

Read this before confirming the image backend or generating final slide images.

## Rule

Use one image backend for the whole production run. Use the native/built-in image generation/editing tool first. Use CLI/API fallback only when the built-in backend is unavailable, cannot attach required visual inputs, lacks a required capability, or the user explicitly authorizes fallback.

If CLI/API fallback may send client materials outside the native tool path, stop and ask the user before continuing.

## Record The Decision

Record the backend in `deck_spec.json` and every slide job. Workers must use the selected backend only. If the backend is unavailable for a worker, the worker returns a blocker instead of switching tools.

## Image Inputs

The selected backend must be able to receive the mapped reference images and required client image assets as actual visual inputs. If it cannot, report the limitation before production starts.

If a required client asset needs exact preservation and the backend cannot preserve it reliably, record a blocker instead of approximating or replacing the asset.
