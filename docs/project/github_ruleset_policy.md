# GitHub ruleset policy

The active repository ruleset is `Protect main and dev` (ID `24205350`). It targets `main` and `dev` and is enforced by GitHub.

## Enforced rules

- Require a pull request and one approval from someone other than the latest pusher
- Dismiss stale approvals after new commits
- Require review conversations to be resolved
- Require all listed status checks and require the branch to be up to date
- Block force pushes and deletion of protected branches

## Required status checks

Use the following exact check names in the ruleset requirement list:

- `lint`
- `task-linkage`
- `test (3.10)`
- `test (3.11)`
- `ai-review`

The AI review job uses PR-Agent with Google AI Studio Gemini Flash. Add the Actions repository secret `GEMINI_API_KEY` with a newly created Gemini API key. The workflow intentionally fails when the provider key is absent or the review action fails. Gemini free-tier availability and quotas are controlled by Google and may change. Keys must never be committed or pasted into pull requests or chat.

## Merge policy

- Feature branches merge into `dev` only.
- `dev` merges into `main` only after all status checks are green and review is complete.
- PRs must include a task or issue reference using `Fixes #`, `Closes #`, or `Task:`.
- Any PR touching runtime safety, orchestration, or data execution must include security review plus validation evidence.

The AI review is advisory and does not replace maintainer approval. Reviewers remain responsible for validating findings and resolving conversations.

## Why this follows GitHub best practices

This pattern follows the current GitHub ruleset guidance for protected branches: enforce a review path, require passes from CI, prevent direct pushes, and ensure all merge decisions are backed by traceable signals instead of ad hoc approvals.
