# Model Management

## Overview

Models are resolved through provider/model services and catalog metadata.

## Verified source areas

- `packages/core/src/model.ts`
- `packages/core/src/model-resolver.ts`
- `packages/core/src/models-dev.ts`
- provider packages under `packages/ai/src/providers/**`

## Catalog metadata should include

- Stable provider/model ID.
- Display name.
- Context limit and capabilities when verified.
- Tool support.
- Vision/image support where applicable.
- Default/fallback policy.

## HEX implications

HEX has provider catalog specs in `hex_cli/providers/registry.py`, credentials, and model
selection dialogs. Keep model capability checks separate from provider transport support.
