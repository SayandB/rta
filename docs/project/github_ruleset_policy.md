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

The AI review job uses GitHub's Copilot inference action. The Actions repository secret `COPILOT_PAT` must contain a token authorized for Copilot CLI inference; the workflow intentionally fails closed when the secret is absent or the model returns no review. The current repository has no such secret configured, so AI review checks will fail until an administrator adds it.

## Merge policy

- Feature branches merge into `dev` only.
- `dev` merges into `main` only after all status checks are green and review is complete.
- PRs must include a task or issue reference using `Fixes #`, `Closes #`, or `Task:`.
- Any PR touching runtime safety, orchestration, or data execution must include security review plus validation evidence.

The AI review is advisory and does not replace maintainer approval. Reviewers remain responsible for validating findings and resolving conversations.

## Why this follows GitHub best practices

This pattern follows the current GitHub ruleset guidance for protected branches: enforce a review path, require passes from CI, prevent direct pushes, and ensure all merge decisions are backed by traceable signals instead of ad hoc approvals.
