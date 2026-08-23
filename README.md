# Release Automation

Automates multi-repository release branch creation, version tagging, release note generation, and GitHub Release publishing using GitHub Actions.

## Table of Contents

- [About](#about)
- [Features](#features)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Workflows](#workflows)
- [Release Naming Convention](#release-naming-convention)
- [Configuration](#configuration)
- [Release Process Example](#release-process-example)
- [Failure Handling](#failure-handling)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## About

This repository contains reusable GitHub Actions workflows that automate the release process across multiple application repositories.

The automation handles:

- Release branch creation
- Release branch validation
- Repository validation
- Commit SHA retrieval
- Release tag creation
- Existing tag validation
- Previous release identification
- Release comparison
- GitHub Release note generation
- GitHub Release publishing
- Release verification
- Failure handling

## Features

- Create release branches across multiple application repositories
- Standardized release branch naming
- Support for multiple repositories in a single workflow execution
- Validate that repositories exist and are accessible
- Validate that release branches exist before creating a release
- Retrieve the exact commit SHA from the release branch
- Generate release tags containing the release version and short commit SHA
- Detect existing release tags
- Prevent an existing tag from pointing to an unexpected commit
- Identify the previous release tag
- Compare the previous release against the new release
- Automatically generate GitHub Release notes
- Publish GitHub Releases
- Verify tags and releases
- Fail the workflow when a required step fails
- Use `RELEASE_AUTOMATION_TOKEN` for cross-repository access

## How It Works

### 1. Create Release Branch

The release branch workflow receives a release name, version, and application repositories.

For example:

```text
Release name: SG_RELEASE
Version: 1.0.0
Repositories: application-one,application-two
```

It creates:

```text
release/SG_RELEASE_1.0.0
```

in each target repository.

### 2. Create and Publish Release Notes

The release publishing workflow receives the release identifier and application repositories.

For:

```text
SG_RELEASE_1.0.0
```

the workflow resolves the branch:

```text
release/SG_RELEASE_1.0.0
```

It then:

1. Resolves the repository to its full `owner/repository` name.
2. Verifies that the repository exists and is accessible.
3. Verifies that the release branch exists.
4. Gets the exact commit SHA at the HEAD of the release branch.
5. Gets the short commit SHA.
6. Builds the release tag.
7. Checks whether the tag already exists.
8. Creates the tag if required.
9. Verifies that an existing tag points to the expected commit.
10. Identifies the previous release.
11. Generates release notes from the comparison.
12. Publishes the GitHub Release.
13. Verifies the published release.

If a required step fails, the workflow fails.

## Project Structure

```text
release-automation/
├── .github/
│   └── workflows/
│       ├── create-release-branch.yml
│       └── publish-release-notes.yml
├── README.md
└── LICENSE
```

## Workflows

### Create Release Branches

Workflow:

[create-release-branch.yml](https://github.com/saghosh8/release-automation/blob/main/.github/workflows/create-release-branch.yml)

Purpose:

Creates release branches in one or more application repositories.

Trigger:

```yaml
workflow_dispatch
```

Inputs:

| Input | Required | Example | Description |
|---|---|---|---|
| `release_name` | Yes | `SG_RELEASE` | Release identifier |
| `version` | Yes | `1.0.0` | Release version |
| `app_repos` | Yes | `application-one,application-two` | Comma-separated application repositories |

Example:

```text
release_name = SG_RELEASE
version      = 1.0.0
app_repos    = application-one,application-two
```

Result:

```text
release/SG_RELEASE_1.0.0
```

### Create and Publish Release Notes

Workflow:

[create-and-publish-release-notes.yml](https://github.com/saghosh8/release-automation/blob/main/.github/workflows/publish-release-notes.yml)

Purpose:

Creates the release tag, generates release notes, and publishes the GitHub Release for the specified application repositories.

Trigger:

```yaml
workflow_dispatch
```

Inputs:

| Input | Required | Example | Description |
|---|---|---|---|
| `release_branch` | Yes | `SG_RELEASE_1.0.0` | Release identifier used to resolve the release branch |
| `repositories` | Yes | `application-one,application-two` | Comma-separated application repositories |

Example:

```text
release_branch = SG_RELEASE_1.0.0
repositories   = application-one,application-two
```

The workflow converts:

```text
SG_RELEASE_1.0.0
```

to:

```text
release/SG_RELEASE_1.0.0
```

## Release Naming Convention

### Release Branch

Input:

```text
SG_RELEASE_1.0.0
```

Branch:

```text
release/SG_RELEASE_1.0.0
```

### Release Version

The semantic version is extracted from the release identifier:

```text
SG_RELEASE_1.0.0
```

becomes:

```text
1.0.0
```

### Commit SHA

The workflow gets the exact commit at the HEAD of the release branch.

Example:

```text
Full SHA:
81269a628a1d3929817439102b65cecd0d1af545

Short SHA:
81269a6
```

### Release Tag

The release tag format is:

```text
<version>-release-<short-commit-sha>
```

Example:

```text
1.0.0-release-81269a6
```

The tag therefore identifies both the release version and the exact release commit.

## Repository Resolution

Application repositories are supplied by repository name:

```text
application-two
```

The workflow resolves this to the full repository:

```text
saghosh8/application-two
```

and uses the full repository path for API and Git operations.

This avoids attempting to clone an incomplete URL such as:

```text
https://github.com/application-two.git
```

## Release Branch Validation

The release publishing workflow expects the release branch to already exist.

For:

```text
SG_RELEASE_1.0.0
```

it checks:

```text
release/SG_RELEASE_1.0.0
```

If the branch does not exist, the workflow fails.

Example:

```text
Error: Release branch does not exist.
Repository: saghosh8/application-two
Branch: release/SG_RELEASE_1.0.0
```

## Tag Validation

Before creating a release, the workflow checks whether the generated tag already exists.

### Tag does not exist

The workflow creates:

```text
1.0.0-release-81269a6
```

at the release branch commit.

### Tag already exists

The workflow checks that the existing tag points to the same commit as the release branch.

Expected:

```text
81269a628a1d3929817439102b65cecd0d1af545
```

If the existing tag points to another commit, the workflow fails.

Example:

```text
Error: Tag already exists but points to a different commit.
Expected: 81269a628a1d3929817439102b65cecd0d1af545
Actual:   <different SHA>
```

The workflow does not silently move or overwrite an existing tag.

## Previous Release and Comparison

After the current release tag is available, the workflow identifies the previous release tag and uses it as the starting point for the release comparison.

Example:

```text
Previous:
0.9.0-release-cfb154b

Current:
1.0.0-release-81269a6
```

The changes between the previous and current releases are then used to generate the GitHub Release notes.

## Release Notes

GitHub generates the release notes from the changes between the previous release and the current release.

The published release contains the generated:

- What's Changed section
- Pull requests
- Contributors
- Full changelog comparison

Example:

```text
What's Changed

• Update values-prod.yaml by @saghosh8 in #3

Full Changelog:
0.9.0-release-cfb154b...1.0.0-release-81269a6
```

## GitHub Release

The GitHub Release title is the generated release tag.

Example:

```text
1.0.0-release-81269a6
```

The release is associated with the same tag:

```text
1.0.0-release-81269a6
```

and that tag points to the commit at:

```text
release/SG_RELEASE_1.0.0
```

## Configuration

### Required Secret

The workflows use:

```text
RELEASE_AUTOMATION_TOKEN
```

Store this as a GitHub Actions secret.

Go to:

```text
Repository
→ Settings
→ Secrets and variables
→ Actions
```

Create:

```text
RELEASE_AUTOMATION_TOKEN
```

The token must have access to all target application repositories and the permissions required by the workflows.

Do not hard-code the token in a YAML file.

## Example Release Process

Assume the application repository is:

```text
saghosh8/application-two
```

### Step 1 — Create the release branch

Run:

```text
Create Release Branches
```

Inputs:

```text
Release name: SG_RELEASE
Version:      1.0.0
Repository:   application-two
```

The workflow creates:

```text
release/SG_RELEASE_1.0.0
```

### Step 2 — Application changes

Changes are committed to the release branch.

The branch eventually points to:

```text
81269a628a1d3929817439102b65cecd0d1af545
```

Short SHA:

```text
81269a6
```

### Step 3 — Publish the release

Run:

```text
Create and Publish Release Notes
```

Inputs:

```text
Release branch: SG_RELEASE_1.0.0
Repository:     application-two
```

### Step 4 — Tag

The workflow creates or validates:

```text
1.0.0-release-81269a6
```

### Step 5 — Generate release notes

The workflow compares the previous release against:

```text
1.0.0-release-81269a6
```

and generates the GitHub Release notes.

### Step 6 — Publish

The GitHub Release is published using:

```text
1.0.0-release-81269a6
```

## Multi-Repository Example

Multiple repositories can be supplied:

```text
application-one,application-two,application-three
```

Each repository is processed independently.

Example:

```text
application-one
    ↓
release/SG_RELEASE_1.0.0
    ↓
1.0.0-release-abc1234
    ↓
GitHub Release

application-two
    ↓
release/SG_RELEASE_1.0.0
    ↓
1.0.0-release-81269a6
    ↓
GitHub Release

application-three
    ↓
release/SG_RELEASE_1.0.0
    ↓
1.0.0-release-def5678
    ↓
GitHub Release
```

If a required operation fails for a repository, the workflow fails.

## Failure Handling

The workflows are intentionally fail-fast.

They use:

```bash
set -euo pipefail
```

The workflow fails for conditions such as:

- Repository does not exist
- Repository cannot be accessed
- Release branch does not exist
- Invalid release input
- Commit SHA cannot be resolved
- Tag creation fails
- Existing tag points to a different commit
- Previous release cannot be determined
- Release comparison fails
- Release note generation fails
- GitHub Release creation fails
- GitHub Release verification fails

Errors identify the affected repository and branch/tag where possible.

## Security Considerations

- Store `RELEASE_AUTOMATION_TOKEN` only as a GitHub Actions secret.
- Never commit tokens to the repository.
- Use the minimum required repository permissions.
- Prefer a fine-grained token where possible.
- Limit the token to the repositories used by the automation.
- Do not print credentials in workflow logs.
- Rotate tokens periodically.
- Keep application `main` branches protected.
- Do not automatically overwrite existing release tags.

## Troubleshooting

### Repository Not Found

Verify:

1. The repository name is correct.
2. The repository exists.
3. `RELEASE_AUTOMATION_TOKEN` has access.
4. The workflow resolves the repository to the correct `owner/repository`.

### Release Branch Not Found

For input:

```text
SG_RELEASE_1.0.0
```

the expected branch is:

```text
release/SG_RELEASE_1.0.0
```

Verify the branch exists in the target repository.

### Tag Already Exists With a Different Commit

Do not delete or move the tag automatically.

Verify the existing tag and the release branch commit before deciding how to proceed.

### GitHub Release Already Exists

Verify the existing GitHub Release before rerunning the workflow.

The workflow should not create duplicate releases.

## Workflow URLs

### Create Release Branches

https://github.com/saghosh8/release-automation/blob/main/.github/workflows/create-release-branch.yml

### Create and Publish Release Notes

https://github.com/saghosh8/release-automation/blob/main/.github/workflows/publish-release-notes.yml

### Repository

https://github.com/saghosh8/release-automation

## Contributing

1. Fork the repository.
2. Create a feature branch.

```bash
git checkout -b feature/improvement
```

3. Make the changes.
4. Test the workflows.
5. Commit the changes.

```bash
git commit -m "Add release automation improvement"
```

6. Push the branch.

```bash
git push origin feature/improvement
```

7. Open a Pull Request.

## License

This project is licensed under the MIT License.

See the `LICENSE` file for details.

## Release Flow Summary

```text
Create Release Branch
        ↓
release/SG_RELEASE_1.0.0
        ↓
Application changes
        ↓
Validate release branch
        ↓
Get release branch commit
        ↓
Get short commit SHA
        ↓
Generate release tag
        ↓
1.0.0-release-81269a6
        ↓
Create or validate tag
        ↓
Find previous release
        ↓
Compare releases
        ↓
Generate release notes
        ↓
Publish GitHub Release
        ↓
Verify release
```
