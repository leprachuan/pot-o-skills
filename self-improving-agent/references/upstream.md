# Upstream Reference

This local skill is an original adaptation inspired by the public skill listed at:

- ClawHub page: https://clawhub.ai/pskoett/self-improving-agent
- Upstream repository: https://github.com/pskoett/pskoett-ai-skills
- Upstream skill path: `skills/self-improvement`
- Observed upstream commit: `636784f35b9bc43b635585f7407a6244c23c7e99`
- Related upstream CI variant: `skills/self-improvement-ci`

## Important Note

The upstream repository did not present a clear license file during import review, so this directory does **not** vendor the upstream text or scripts verbatim.

Instead, this skill is a clean in-house adaptation that preserves:

- the core idea of logging learnings, errors, and feature requests
- local initialization helpers
- promotion and review workflow
- explicit upstream references for future manual comparison

## Refresh Process

When checking for upstream changes later:

1. Compare the current upstream `skills/self-improvement` directory against this skill.
2. Review upstream changes manually.
3. Re-implement useful changes in local wording and local path conventions.
4. Update the upstream commit SHA in this file and in `skill_metadata.json`.
