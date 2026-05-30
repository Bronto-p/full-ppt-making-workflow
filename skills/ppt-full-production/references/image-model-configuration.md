# Image Model Configuration

Use this reference only when the API/CLI fallback is needed and the runtime configuration is missing or invalid.

Do not manually parse `.env` files. Run the local fallback wrapper first and follow the error it reports.

The selected configuration must support the deck's required image inputs, aspect ratio, and quality constraints. If it cannot receive the mapped reference images or required client assets as visual inputs, stop before production and report a blocker.
