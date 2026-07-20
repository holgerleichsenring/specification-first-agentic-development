<!--
  EXAMPLE — not a template to copy verbatim.

  This is a filled-in `coding-principles.md` for ONE stack: a layered .NET /
  MediatR web API. It exists to show the SHAPE the bootstrap skill must produce:
  prescriptive rules an agent can write new code from, architecture ("red
  thread") first, observed build facts last.

  Your project's file will have different specifics — a TypeScript, Python, or
  Go stack looks nothing like this. Derive the CONTENT from the actual codebase;
  keep the STRUCTURE. Domain names below (Orders, OrderHub, Sample.Common.*) are
  placeholders.
-->

# Coding principles — API

This document captures the enforceable conventions for the solution, centred on
the **API component** and the request flow that runs through it. It is
**prescriptive**: new code must follow the architecture ("red thread") and the
hard limits below. Observed build/middleware facts are documented last, so
existing behaviour is preserved when extending the system.

---

## Language rule (NON-NEGOTIABLE)

- **All text in code MUST be in English** — comments, doc-comments, exception and
  log messages, identifiers, commit messages, PR titles, test names. No exceptions.

## The red thread — request flow architecture

Every feature follows the **same path** from HTTP request to persistence and back.
Do not invent alternative flows.

```
HTTP request
   ▼
Controller (API/Controllers)              ← thin, only IMediator.Send(...)
   │  *Request : IRequest<*Response>
   ▼
RequestHandler (Application/…/Handlers)    ← orchestration only, no work
   ├─► I*Adapter   (Infrastructure.Persistence)   ← data access, never raw DbContext
   └─► IMessageSender (Infrastructure.Messaging)  ← cross-service work
   ▼ (async completion)
mediator.Publish(*Notification)  ─►  INotificationHandler  ─►  OrderHub ─► client
```

| Concern | Type / naming | Project · folder | Contract |
|---|---|---|---|
| Endpoint | `*Controller` | `API/Controllers` | thin, `[ApiController]` |
| Request / Response | `*Request` / `*Response` | `Domain/Models` | `IRequest<*Response>` / DTO |
| Handler | `*RequestHandler` | `Application/…/Handlers` | `IRequestHandler<TReq,TRes>` |
| Persistence | `I*Adapter` / `*Adapter` | `Infrastructure.Persistence` | generic CRUD |
| Notification | `*Notification` / `*Handler` | `Domain/Notifications`, `Application/…` | `INotification` |
| Cross-service | `*Message` | `Domain/Messages` | via `IMessageFactory` |

**Controllers are thin.** Inject `IMediator`, do nothing but bind, `Send`, return.
No business logic, data access, or mapping in a controller.

**RequestHandlers orchestrate, they do not contain the work.** One handler per
request type, its own file. `Handle` wires injected services together — extract
real logic into a focused service.

**Persistence goes through an Adapter, never raw DbContext in a handler.** Add
operation-specific query methods to the adapter interface.

**Mapping is manual and explicit — no AutoMapper.** Map in dedicated factories or
a generic `IConverter<TIn,TOut>`.

## Hard limits

- **Max 20 lines per method** — extract a helper instead.
- **Max 120 lines per class** (80 = warning); a large class means too many responsibilities.
- **Max 30 lines for a base class** — scaffolding only, never business logic.
- **One type per file.**

## Design principles

- **One responsibility per class.** Can't describe it in one sentence without "and" → split.
  The class **name IS the documentation** — never `*Helper` / `*Utils` / `*Manager`.
- **Composition over inheritance (non-negotiable)** — inject small, focused services.
- **SOLID**, especially Single Responsibility and Dependency Inversion (every injected
  service has an interface).
- **No manual `new`** for services/handlers/adapters — constructor injection only.

## Naming conventions

- `PascalCase` types/methods/properties; `camelCase` params/locals; `_camelCase` private fields.
- Interfaces `I`-prefixed; async methods `Async`-suffixed; booleans `Is`/`Has`/`Can`.
- Flow types carry their role as a suffix: `*Request`, `*RequestHandler`, `*Adapter`, `*Message`.

## Error handling

- Centralised via middleware; specific exceptions map to HTTP status codes.
- **Never an empty `catch`.** Every catch logs with the exception object (stack trace survives).
- Catch the narrowest type; classify on exception **type**, never by parsing `.Message`.

## Testing

- AAA (Arrange-Act-Assert); mock only external dependencies.
- Class naming `{Class}Tests`; method naming `{Method}_{Scenario}_{Expected}`.

## What NOT to do

- No god classes (>120 lines) or fat base classes (>30 lines).
- No static services; no `*Helper` / `*Utils` / `*Manager` names.
- No business logic in controllers; no raw DbContext access in handlers.
- No AutoMapper; no magic strings; no `Console.WriteLine`; no empty catch blocks.
- No non-English text anywhere.

---

## Build facts to preserve

*(Observations, not principles — kept last. New code must not break these.)*

- Target framework `net9.0`; ASP.NET Core Web SDK; NRT **disabled**; warnings-as-errors in Debug and Release.
- Dependencies point inward: `Domain` references no infrastructure; `Application` holds handlers;
  `Infrastructure.*` holds adapters/messaging/EF Core; nothing references the API.
- Middleware order (do not reorder): HttpsRedirection → Routing → CORS → Authentication →
  ExceptionMiddleware → Localization → Authorization → endpoint mapping.
