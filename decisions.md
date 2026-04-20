# Decision Log

<!--
For every phase, log the decisions that shaped the implementation.
Format: [Category] Decision -- rationale

Categories: Architecture, Tooling, Implementation, TradeOff, Security
-->

## p-sfad-plugin: Claude Code Plugin

- [Architecture] Plugin lives in specification-first-agentic-development repo, not in agent-smith -- the plugin IS the methodology packaged. Agent Smith just happens to use Spec-First. Right owner matters.
- [Architecture] Skills over Commands -- commands/ is legacy per Anthropic docs. Skills with SKILL.md frontmatter are the current standard.
- [Architecture] 6 skills: workflow, bootstrap-project, create-phase, execute-phase, log-decision, update-project -- covers the full lifecycle. update-project included in v1.0 because methodology evolution without sync strands early adopters.
- [Implementation] Skills reference existing templates/ instead of duplicating -- single source of truth. bootstrap-project reads templates as structural guide, adapts to each project.
- [Implementation] methodology.version field in context.yaml -- user's own file is the single source of truth for which version they bootstrapped with. Plugin version in plugin.json is the comparison target.
- [TradeOff] Manual install via git clone + --plugin-dir for MVP -- marketplace listing is a separate effort. Git clone works today, zero dependencies.
- [TradeOff] No automated tests -- plugin quality is trigger-description quality, verified by manual testing. SKILL.md files are prose, not code.
