# OpenCode Expert

This Skill gives Grok an evidence-linked reference for OpenCode architecture and native HEX
CLI implementation decisions.

## Use with Grok

No native loading workflow has been established for every Grok client. If a client supports
skill attachment, attach this directory. Otherwise use the manual workflow:

1. Provide `SKILL.md` and the relevant reference files.
2. Ask Grok to follow the mandatory workflow in `SKILL.md`.
3. Require source links and commit/release citations for behavior that can change.
4. Ask Grok to inspect the current HEX implementation before proposing changes.
5. Ask Grok to update the relevant reference and parity row after implementation.

## Refreshing research

1. Record the date, OpenCode release/tag or commit, and documentation URLs.
2. Re-clone or fetch the official repository.
3. Inspect changed paths named by the source map.
4. Update or add `source-manifest.json` entries.
5. Revise modules from source, not documentation alone.
6. Re-evaluate each affected HEX parity row.

## Directory guide

- `references/`: detailed system modules.
- `architecture/`: original Mermaid diagrams.
- `hex-mapping/`: HEX architecture, gaps, roadmap, and compatibility rules.
- `sources/`: official links and versioned source evidence.

## Evidence labels

- `DOCUMENTED`: explicitly stated in official docs.
- `SOURCE VERIFIED`: inspected in a pinned official source revision.
- `PARTIAL`: evidence exists but lifecycle details remain unknown.
- `UNVERIFIED`: no sufficient evidence yet; do not use as implemented fact.
