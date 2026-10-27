# Coding Principles: plugin

These rules hold for the skills, hooks, scripts and templates. The agent reads them before every session.

## Language

- Everything in English: code, comments, skill text, messages, commit messages, specs, decisions.

## Python (hooks and scripts)

- Standard library only. PyYAML is the one optional dependency; when it is missing, say so and
  report the check as not run. A check that did not run is never a pass.
- A script's tests sit beside it as `test_*.py` and run with `python3 -m unittest discover`.
- A hook that cannot decide lets the command through and says why; it blocks only on a red
  verify stage or a malformed declaration.
- Exit codes are part of the contract: document each one in the module docstring.

## Skills

- One `SKILL.md` per user intent, frontmatter `name`, `description`, `user-invocable`.
- `description` stays under 200 characters: it names what the skill does and the phrases that trigger it.
- Describe what the agent can do, not what it must not do.
- A skill that spawns a reviewer or builders says it runs in the main thread.

## Templates and schemas

- A template field the schema does not know is a bug in one of them; change both together.
- Templates hold placeholders and short comments, never project-specific values.
- A change to a template or schema that projects must follow ships with an `update-project` step.

## Versioning

- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `methodology.version` in the
  context template carry the same version.
