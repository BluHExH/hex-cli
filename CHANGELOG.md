# Changelog

## 2.1.1 — Three-column workspace TUI

- Left / center / right layout matching professional coding-agent structure
- Tool execution cards, changes & activity rails, context meter
- Composer toolbar + Enter submit
- SVG screenshots under docs/screenshots/

# Changelog

## 2.1.0 — TUI/UX redesign

- Professional layout: header, sidebar, home, timeline, composer, status
- Design tokens theme system
- Command palette (Ctrl+P)
- Responsive sidebar
- Multiline composer (Ctrl+Enter)
- Backend unchanged from 2.0.1

## 2.0.1 — Release stabilization

- Fix console entry point: `hex_cli.main:main`
- Align package/runtime version to **2.0.1**
- Rewrite README for actual 2.0 architecture
- Shell: default `shell=False` argv execution; explicit `use_shell`; cancel/timeout
- Cooperative agent cancellation + shell process terminate
- TUI: threaded workers; Ctrl+C cancels in-flight turn
- Textual moved to optional `[tui]` / `[dev]` extra
- Version consistency regression test

## 2.0.0 — Clean architecture rebuild

- Modular agent, providers, tools, permissions, sessions, changes, TUI core
