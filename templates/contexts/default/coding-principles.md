# Coding Principles

These rules are non-negotiable. The AI agent reads them before every session.

## Language

- All code, comments, docs, exceptions, logs, prompts, commit messages in **English**.
- No mixed languages, no translations, no locale-dependent strings in code.

## Hard Limits

| Rule | Limit |
|------|-------|
| Method body | max 20 lines |
| Class body | max 120 lines |
| Types per file | 1 |
| Constructor parameters | max 5 |

If a method exceeds the limit, extract a helper. If a class exceeds the limit, split responsibilities.

## Naming

- Classes: `PascalCase`
- Interfaces: `I` prefix (`ITicketProvider`)
- Booleans: `Is`/`Has`/`Can` prefix (`IsValid`, `HasPermission`)
- Async methods: `Async` suffix (`GetTicketAsync`)
- Private fields: `_camelCase`
- Constants: `PascalCase`

## Principles

- **SOLID** -- especially Single Responsibility and Dependency Inversion
- **Guard Clauses** -- validate early, fail fast
- **Tell, Don't Ask** -- pass data to methods, don't query state then act
- **DRY** -- but three similar lines are better than a premature abstraction

## Error Handling

- Throw specific exceptions at system boundaries (user input, external APIs)
- Trust internal code -- don't validate what you just constructed
- No empty catch blocks, no `catch (Exception)` without logging

## Testing

- **AAA pattern**: Arrange, Act, Assert
- **Naming**: `{Method}_{Scenario}_{Expected}` (e.g., `Parse_EmptyInput_ReturnsUnknown`)
- One assertion per test (or closely related assertions)
- No test interdependencies

## What NOT To Do

- Don't add features beyond the current phase spec
- Don't refactor code you didn't change
- Don't add comments for self-evident logic
- Don't create abstractions for one-time operations
- Don't add error handling for impossible scenarios
