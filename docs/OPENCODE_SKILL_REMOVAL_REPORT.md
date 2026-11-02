# OpenCode Expert Skill Removal Report

**Repository:** https://github.com/BluHExH/hex-cli  
**Branch:** main  

## Summary

Removed the accidentally uploaded **OpenCode Expert Skill** tree that was introduced on remote `main` in commit `b519623` (`docs: add OpenCode Expert knowledge skill`).

HEX CLI product code, tests, config, and the in-app skills loader (`hex_cli/skills/`) were **not** deleted.

## Files and directories removed

- `skills/opencode-expert/` (entire tree)
  - `SKILL.md`, `README.md`, `CHANGELOG.md`
  - `architecture/*` (Mermaid/docs flows)
  - `hex-mapping/*`
  - `references/01`–`28`*.md
  - `sources/*` including `source-manifest.json`
- `docs/OPENCODE_EXPERT_SKILL_REPORT.md`

## Original project preserved

| Path | Status |
|------|--------|
| `hex_cli/**` | Preserved |
| `hex_cli/skills/loader.py` | Preserved (product Skills feature) |
| `tests/**` | Preserved |
| `docs/OPENCODE_TUI_GAP_ANALYSIS.md` and stage reports | Preserved (HEX UX docs, not Expert Skill) |
| `pyproject.toml`, `README.md`, `config.example.json` | Preserved |
| Version | Unchanged |

## Modified original files restored

None required — the Skill commit only **added** files; it did not modify existing HEX sources.

## Validation

- Git status reviewed: only Skill deletions + this report.
- Confirmed `skills/opencode-expert` absent after removal.
- Confirmed `hex_cli/skills/loader.py` still present.
- Full pytest suite: run after staging if environment allows; product code untouched so risk is low.

## Remaining references

Mentions of “OpenCode” in HEX stage docs remain as **external UX reference** only, not Expert Skill package content.

## Git

- Cleanup commit message: `chore: remove accidentally uploaded OpenCode Expert Skill`
- No force-push; no history rewrite of prior commits.
