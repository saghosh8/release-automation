# release-automation

Automates multi-repository release branch creation and release note / GitHub Release generation using GitHub Actions.

## Table of contents
- About
- Features
- How it works
- Files
- Prerequisites
- Usage
  - Create Release Branches
  - Create Release Notes & Publish Releases
- Inputs & required secrets
- Security notes
- Troubleshooting
- Suggested CV / interview bullets
- Contributing
- License

## About
This repository contains reusable GitHub Actions workflows to:
- create release branches across a set of application repositories, and
- generate tags, release notes, and publish GitHub Releases for applications.

## Features
- Create a release branch (pattern: `release/<name>-<number>`) across multiple repositories.
- Generate a versioned tag (e.g. `1.0.1-release-<commit-short>`).
- Auto-generate release notes using GitHub's release notes generator.
- Publish GitHub Releases for each application repository.
- Validate automation token and produce an Actions job summary for visibility.

## How it works (high level)
1. Trigger a workflow via the Actions UI or `gh` CLI.
2. The workflow validates `RELEASE_AUTOMATION_TOKEN`.
3. Branch creation workflow clones target repos, creates a release branch from `main`, and pushes it.
4. Release workflow finds the release branch commit, creates a tag, generates release notes (since previous tag if present), and publishes a GitHub Release.
5. Each job writes a summary to the GitHub Actions job summary.

## Files
- .github/workflows/create-release-branch.yml — Create release branches across multiple app repositories.
- .github/workflows/create-release-notes.yml — Create tags, generate release notes, and publish releases.
- README.md — (this file)

## Prerequisites
- Workflows run on GitHub Actions.
- Store a GitHub Personal Access Token (classic or fine-grained) in secrets as `RELEASE_AUTOMATION_TOKEN`.
- Token must have access to each target repository listed in workflow inputs.

## Usage

### Create Release Branches
Workflow: `.github/workflows/create-release-branch.yml`

Inputs (workflow_dispatch):
- `release_name` — release name
- `release_number` — release number
- `app_repos` — comma-separated list of repository names (e.g., `app-one,app-two`)

Behavior:
- Generates branch: `release/<release_name>-<release_number>`
- Clones each repo and pushes the new branch

Example (gh CLI):
gh workflow run "Create Release Branches" -f release_name="SG" -f release_number="2026-08-22" -f app_repos="app-one,app-two"

### Create Release Notes & Publish Releases
Workflow: `.github/workflows/create-release-notes.yml`

Inputs (workflow_dispatch):
- `release_version` — version string (e.g., `1.0.1`)
- `applications` — comma-separated list of repository names

Behavior:
- Locates release branch `release/SG_RELEASE_<release_version>`
- Creates tag: `<release_version>-release-<short-commit>`
- Generates release notes (compares to previous tag when present)
- Publishes a GitHub Release with generated notes

Example (gh CLI):
gh workflow run "Create Release Notes" -f release_version="1.0.1" -f applications="app-one,app-two"

## Inputs & required secrets
Workflow inputs:
- `release_name`, `release_number`, `app_repos`, `release_version`, `applications`

Secrets:
- `RELEASE_AUTOMATION_TOKEN` — PAT or fine-grained token with access to target repositories.

Recommended token permissions:
- Fine-grained token scoped to required repositories with: Contents (read/write), Releases (write), Metadata (read).

## Security notes
- Store `RELEASE_AUTOMATION_TOKEN` in GitHub Secrets — never hard-code secrets.
- Prefer fine-grained tokens limited to required repositories and permissions.
- Review audit logs when running automation that pushes branches or creates releases.

## Troubleshooting
- Token errors: confirm `RELEASE_AUTOMATION_TOKEN` is configured and has access to target repos.
- Clone failures: workflows clone `main`; ensure the branch exists or update the workflow to use a different source branch.
- Tag exists: the workflow checks for existing tags and skips tag creation if present.
- Check workflow logs and the GitHub Actions job summary for diagnostics.

## Suggested CV / interview bullets
- Built automated release orchestration using GitHub Actions to create release branches, generate release notes, and publish GitHub Releases across multiple repositories.
- Implemented token validation, resilient clone/push logic, and job summaries to improve release visibility and reduce manual work.
- Designed reusable, input-driven workflows that centralize multi-repo release operations.
- Leveraged the GitHub CLI and API to programmatically generate release notes and manage tags/releases.

## Contributing
- Copy the workflows into your repo under `.github/workflows/` to reuse.
- Update secret names and token scopes as required.
- Test on a staging repository before running on production repositories.

## License
This repository is licensed under the MIT License.