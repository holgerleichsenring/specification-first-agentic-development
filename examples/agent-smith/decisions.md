# Decision Log (Extract)

This is an extract from 70+ phases of real decision logging.

## p01: Core Infrastructure
- [Architecture] Command Pattern (MediatR-style) as central pattern -- strict separation of "What" (context) from "How" (handler)
- [Architecture] Single generic handler interface `ICommandHandler<TContext>` instead of multiple handler types -- enables DI-based dispatch
- [Tooling] YamlDotNet for configuration -- chosen for simplicity, avoids overengineering (no JSON schema validation at this stage)
- [Implementation] Lazy environment variable resolution in config loader -- unset vars aren't errors during loading, only at usage time
- [TradeOff] No validation of all environment variables upfront -- accepted incomplete config to gain flexibility

## p04: Pipeline Execution
- [Architecture] Regex-based intent parser instead of LLM call -- chosen for determinism, cost, and speed
- [Architecture] CommandContextFactory maps command names to contexts -- avoids massive switch statement in PipelineExecutor
- [TradeOff] Intent parser intentionally simple -- can be swapped for Claude-based parser later without interface changes

## p14: GitHub Action & Webhook
- [Architecture] Both GitHub Action (zero infrastructure) and webhook listener (self-hosted) variants -- choice for user deployment model
- [Tooling] HttpListener for webhook (no ASP.NET dependency) -- minimal overhead for simple HTTP requirements
- [Implementation] Each webhook request spawns async Task -- non-blocking, server returns 202 Accepted immediately

## p18: Chat Gateway
- [Architecture] Redis Streams as message bus (progress/question/done/error) with persistent consumer groups -- decouples agent from dispatcher, enables multi-platform routing
- [Architecture] Separate `IProgressReporter` implementations: Console for CLI, Redis for K8s -- single interface, pluggable output
- [Implementation] K8s Job per request with ephemeral agent containers -- isolation, resource limits, TTL cleanup

## p34: Multi-Skill Architecture
- [Architecture] Skills define HOW, not WHAT -- role-based rules loaded into context, not separate agents
- [Architecture] `CommandResult.InsertNext` enables cascading command execution -- PipelineExecutor manages dynamic insertion
- [TradeOff] Convergence check uses LLM -- accepted token cost for deterministic loop termination

## p59: PR Comment Webhook
- [Architecture] Shared `CommentIntentParser` across all platforms (GitHub/GitLab/AzDO) -- same regex, different webhook handlers
- [Security] `author_association` guard on GitHub -- only OWNER/MEMBER/COLLABORATOR/CONTRIBUTOR can trigger pipelines
- [Architecture] Pipeline allowlist (`fix-bug`, `security-scan`, `pr-review`) -- prevents arbitrary pipeline execution via PR comments
- [TradeOff] No rate limiting in MVP -- accepted risk, mitigated by access control
