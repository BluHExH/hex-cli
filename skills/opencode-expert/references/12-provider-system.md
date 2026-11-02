# Provider System

## Overview

Provider/model services live in `packages/core/src/provider.ts`, `model.ts`,
`model-resolver.ts`, `models-dev.ts`, and the AI package.

## Responsibilities

- Discover and load provider implementations.
- Resolve provider/model IDs.
- Read credentials/configuration.
- Discover supported models and capabilities.
- Adapt request, stream, tool, and error protocols.
- Surface provider-specific failures safely.

## Authentication

Credentials should be separate from ordinary project configuration. Provider selection should
not mutate user files unless explicitly requested.

## HEX implications

HEX uses provider specs and OpenAI-compatible transports. Native implementations should stay
protocol-compatible while provider capabilities remain explicit. Provider retries and streaming
must not be assumed uniform across adapters.
