# Phase 59: PR Comment Webhook (GitHub)

## Goal

PR comments become full-fledged inputs for Agent Smith.
Two scenarios, one shared foundation:

**Scenario A -- New job via comment:**
Reviewer writes `/agent-smith fix this` in a PR comment.
-> New pipeline job starts with the PR as context.

**Scenario B -- Dialogue answer via comment:**
Agent asked in the PR: "Should I proceed?"
-> Reviewer answers `/approve` or `/reject [reason]`.
-> Running job picks up the answer and continues.

**MVP scope: GitHub only.** GitLab -> p59b. Azure DevOps -> p59c.

## Scope

- `CommentIntentParser` -- regex-based, `/agent-smith <cmd>` and `/approve`/`/reject`
- `GitHubPrCommentWebhookHandler` -- handles `issue_comment` + `pull_request_review_comment`
- `GitHubPrCommentReplyService` -- posts replies via Octokit
- `IConversationLookup` -- finds active job for a PR channel
- Access control: `author_association` must be OWNER/MEMBER/COLLABORATOR/CONTRIBUTOR
- Pipeline guard: only `fix-bug`, `security-scan`, `pr-review` allowed

## Definition of Done

- [x] `CommentIntentParser` handles all command variants
- [x] `GitHubPrCommentWebhookHandler` handles both scenarios
- [x] `GitHubPrCommentReplyService` posts replies
- [x] `IConversationLookup` routes dialogue answers
- [x] Access control via `author_association`
- [x] Pipeline allowlist guard
- [x] Unit tests for parser (16 tests)
- [x] Unit tests for handler (10 tests)
- [x] All existing tests green (749 total)
