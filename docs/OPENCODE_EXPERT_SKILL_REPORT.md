# OpenCode Expert Skill Research Report

## Scope

Created `skills/opencode-expert/` as a modular, source-linked reference for applying verified
OpenCode concepts to HEX CLI without changing HEX branding or architecture.

## Research versions

- HEX CLI baseline: `v1.5.1`, commit
  `ed3807ec2d48ffb21a093e7a50f94ba7bbf3af3c`.
- OpenCode inspected: commit `ff90ed91607cabf420a369e9009539c1aa0932af`
  on 2026-11-02.
- Official documentation reviewed at https://opencode.ai/docs/ and official repository paths.

## Modules

All 28 requested reference modules are included. Some runtime areas are marked partial or
unverified because the shallow/current source snapshot and documentation revision do not
fully establish behavior.

## Important discoveries

- OpenCode is a multi-package TypeScript runtime with CLI, TUI, core, server, protocol, AI,
  schema, SDK, desktop/app, plugin, and provider implementations.
- Source references a structured session runner, session store/projector, tool registry,
  permission service, provider/model services, and server protocol groups.
- HEX has native implementations of its agent loop, JSON sessions, Textual TUI, tools,
  permissions, providers, ChangeTracker, MCP client support, LSP client support, subagents,
  skills, and custom commands.
- Several advanced HEX capabilities are library/UI partial integrations rather than complete
  model-loop wiring: notably MCP, LSP, skills, and subagents.

## HEX parity status

The parity matrix records implemented, partial, missing, not-applicable, and unverified
areas. It distinguishes real behavior from module names.

## Unverified areas

- Deep provider retry semantics that depend on each adapter.
- Compaction/pruning algorithms if not pinned to a source implementation.
- Every documented keyboard binding in the pinned source snapshot.
- Full MCP HTTP parity and server lifecycle details.
- Complete desktop/API parity outside the terminal core.
- Historical OpenCode releases; only the inspected current snapshot is guaranteed.

## Validation

Run the repository validation script/checks described in
`skills/opencode-expert/sources/source-code-map.md` before delivery:

- `source-manifest.json` parses as JSON.
- Every 28-reference file exists.
- Internal Markdown links resolve.
- Mermaid blocks are syntactically plausible.
- No expected documentation file is empty.
- HEX and OpenCode SHAs are recorded exactly.
- Existing application files are unchanged.
- Structure check: 28 reference files, valid manifest JSON, no empty reference/module files.
- Full HEX test run: 145 passed, 1 skipped, 8 failed in the baseline checkout:
  six agent-tool tests call a CLI hook signature incompatible with the loop's expanded status
  arguments, and two TUI sidebar tests observe the default sidebar state as closed.
- These failures do not arise from documentation changes and are recorded as pre-existing
  baseline validation findings. Existing application code remains unchanged per task scope.

## Known limitations

Official behavior changes independently of source revisions. Treat source and documentation
links as points-in-time evidence, then re-run focused source verification before implementation.
