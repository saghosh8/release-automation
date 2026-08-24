# Release Automation

Automates multi-repository release branch creation, version tagging, release note generation, GitHub Release publishing, and new application repository scaffolding using GitHub Actions.

## Table of Contents

- [About](#about)
- [Features](#features)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Workflows](#workflows)
- [Triggering CI and CD - Prod Pipelines](#triggering-ci-and-cd---prod-pipelines)
- [Release Naming Convention](#release-naming-convention)
- [Application Repository Configuration](#application-repository-configuration)
- [Configuration](#configuration)
- [Release Process Example](#release-process-example)
- [Failure Handling](#failure-handling)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## About

This repository contains reusable GitHub Actions workflows that automate the release process across multiple application repositories, and the creation of new application repositories from a standard template.

The automation handles:

- New application repository creation from a shared template
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
- Triggering downstream CI pipelines in application repositories
- Triggering downstream CD - Prod pipelines in application repositories
- Failure handling

## Features

- Create one or more new application repositories in a single workflow run
- Generate a standard Spring Boot + Helm project structure for each new repository
- Derive the application name, Java package, and Java class name automatically from the repository name
- Refuse to overwrite a repository that already exists
- Create release branches across multiple application repositories
- Standardized release branch naming
- Support for multiple repositories in a single workflow execution
- Validate that repositories exist and are accessible
- Validate that release branches exist before creating a release
- Retrieve the exact commit SHA from the release branch
- Generate release tags containing the release version and short commit SHA
- Detect existing release tags
- Prevent an existing tag from pointing to an unexpected commit
- Identify the previous release tag from a maintained mapping file
- Compare the previous release against the new release
- Automatically generate GitHub Release notes
- Publish GitHub Releases
- Verify tags and releases
- Fail the workflow when a required step fails
- Trigger an application repository's `CI` workflow remotely on a given branch
- Trigger an application repository's `CD - Prod` workflow remotely with a specific release tag
- Verify that the target `CI` / `CD - Prod` workflow exists in the application repository before triggering it
- Use `RELEASE_AUTOMATION_TOKEN` for cross-repository access

## How It Works

### 1. Create Application Repository

The application repository workflow receives one or more repository names.

For example:

```
Repositories: application-one,application-two
```

For each name, it:

1. Verifies the repository does not already exist (fails if it does, to avoid overwriting anything).
2. Creates a new public GitHub repository under the `saghosh8` account.
3. Generates the project files from `input_files/app_config.yaml` — a Spring Boot application skeleton and a matching Helm chart.
4. Derives `APP_NAME`, the Java package, and the Java class name from the repository name itself, so every repository gets correctly named, compilable Java code.
5. Commits and pushes the generated files to the new repository's `main` branch.

### 2. Create Release Branch

The release branch workflow receives a release name, version, and application repositories.

For example:

```
Release name: SG_RELEASE
Version: 1.0.0
Repositories: application-one,application-two
```

It creates:

```
release/SG_RELEASE_1.0.0
```

in each target repository.

### 3. Create and Publish Release Notes

The release publishing workflow receives a single **release identifier** input, `release_branch`, formatted as `SG_RELEASE_<version>` (for example `SG_RELEASE_1.0.0`). The `SG_RELEASE_` prefix is required — the workflow validates the input against that exact format and fails if it doesn't match.

Unlike the other two workflows, this one does **not** take a comma-separated list of repositories as a workflow input. Instead, it reads the list of repositories to process — along with the previous release tag for each one — from a file checked into this repository:

```
input_files/prod_Old_tag.txt
```

Each non-empty, non-comment line has the format:

```
<repository-name>:<previous-release-tag>
```

For example:

```
application-one:0.9.0-release-cfb154b
application-two:0.8.2-release-1a2b3c4
```

This file must be kept up to date before each run — any repository missing from it, or with a blank tag, will cause the workflow to fail for that entry.

For the release identifier:

```
SG_RELEASE_1.0.0
```

the workflow resolves the branch:

```
release/SG_RELEASE_1.0.0
```

It then, for each repository listed in `prod_Old_tag.txt`:

1. Resolves the repository to its full `owner/repository` name.
2. Verifies that the repository exists and is accessible.
3. Verifies that the release branch exists.
4. Gets the exact commit SHA at the HEAD of the release branch.
5. Gets the short commit SHA.
6. Builds the release tag.
7. Checks whether the tag already exists.
8. Creates the tag if required.
9. Verifies that an existing tag points to the expected commit.
10. Validates that the previous release tag (from `prod_Old_tag.txt`) exists.
11. Compares the previous release against the new release and fails if there are zero commits between them.
12. Skips release creation if a GitHub Release for the new tag already exists; otherwise generates release notes and publishes the GitHub Release.
13. Verifies the published release.

If a required step fails for a repository, the workflow fails.

### 4. Trigger CI Pipeline

The CI trigger workflow receives a branch and one or more application repositories.

For example:

```
Branch: release/SG_RELEASE_1.0.0
Repositories: application-one,application-two
```

For each repository, it:

1. Resolves the repository to its full `owner/repository` name.
2. Verifies that the given branch exists in that repository.
3. Verifies that a workflow named `CI` exists in that repository.
4. Triggers the `CI` workflow on that branch via `gh workflow run`.

This does not wait for the CI run to complete — it only submits the trigger request and reports success once the request is accepted.

### 5. Trigger CD - Prod Pipeline

The CD - Prod trigger workflow receives a release branch and reads the repositories to deploy, along with the image tag for each, from a file checked into this repository:

```
input_files/prod_New_tag.txt
```

Each non-empty, non-comment line has the format:

```
<repository-name>:<image-tag>
```

For example:

```
application-one:1.0.0-release-abc1234
application-two:1.0.0-release-81269a6
```

For each line, the workflow:

1. Resolves the repository to its full `owner/repository` name.
2. Verifies that a workflow named `CD - Prod` exists in that repository.
3. Triggers the `CD - Prod` workflow on the given release branch, passing the image tag as the `release_tag` input.

Like the CI trigger, this only submits the request — it does not wait for the deployment to finish.

## Project Structure

```
release-automation/
├── .github/
│   └── workflows/
│       ├── create-app-repos.yml
│       ├── create-release-branch.yml
│       ├── publish-release-notes.yml
│       ├── prod_ci.yml
│       └── prod_cd.yml
├── input_files/
│   ├── app_config.yaml
│   ├── prod_Old_tag.txt
│   └── prod_New_tag.txt
├── README.md
└── LICENSE
```

## Workflows

### Create Application Repository

Workflow: [create-app-repos.yml](https://github.com/saghosh8/release-automation/blob/main/.github/workflows/create-app-repos.yml)

[![Run Create Application Repository](https://img.shields.io/badge/▶-Run%20workflow-2ea44f)](https://github.com/saghosh8/release-automation/actions/workflows/create-app-repos.yml)

Purpose:

Creates one or more new application repositories from a shared template, and generates a Spring Boot project with a matching Helm chart in each.

Trigger:

```
workflow_dispatch
```

Inputs:

| Input         | Required | Example                           | Description                                    |
| ------------- | -------- | --------------------------------- | ---------------------------------------------- |
| `repo_names`  | Yes      | `application-one,application-two` | Comma-separated repository names to create     |
| `description` | No       | `Application repository`          | Description applied to each created repository |

Example:

```
repo_names  = application-three
description = Billing service
```

Result:

A new public repository named `application-three` is created under the `saghosh8` account, containing a generated Spring Boot application (package `com.example.applicationthree`, class `ApplicationThreeApplication`) and a Helm chart at `helm/application-three/`.

Notes:

- The repository owner is always `${GITHUB_REPOSITORY_OWNER}` — i.e. whoever owns this `release-automation` repository (`saghosh8`). It is not a workflow input, so repositories can only ever be created under that account.
- The workflow fails without creating anything if a target repository already exists, to avoid overwriting it.
- `APP_NAME` is never read from configuration — it is always taken from the repository name being created, so every repository in a multi-repository run gets its own correct name, Java package, and Helm chart, even though they share the same `app_config.yaml`.
- `input_files/app_config.yaml` is staged to a temporary location before the loop starts, since each repository's working directory is wiped and rebuilt during generation.

### Create Release Branches

Workflow: [create-release-branch.yml](https://github.com/saghosh8/release-automation/blob/main/.github/workflows/create-release-branch.yml)

[![Run Create Release Branches](https://img.shields.io/badge/▶-Run%20workflow-2ea44f)](https://github.com/saghosh8/release-automation/actions/workflows/create-release-branch.yml)

Purpose:

Creates release branches in one or more application repositories.

Trigger:

```
workflow_dispatch
```

Inputs:

| Input          | Required | Example                           | Description                              |
| -------------- | -------- | --------------------------------- | ----------------------------------------- |
| `release_name` | Yes      | `SG_RELEASE`                      | Release identifier                       |
| `version`      | Yes      | `1.0.0`                           | Release version                          |
| `app_repos`    | Yes      | `application-one,application-two` | Comma-separated application repositories |

Example:

```
release_name = SG_RELEASE
version      = 1.0.0
app_repos    = application-one,application-two
```

Result:

```
release/SG_RELEASE_1.0.0
```

> Note: this workflow accepts any `release_name` value, but the publishing workflow below currently only accepts release identifiers starting with `SG_RELEASE_`. In practice, use `SG_RELEASE` as the release name if you plan to publish the release with the workflow below.

### Create and Publish Release Notes

Workflow: [publish-release-notes.yml](https://github.com/saghosh8/release-automation/blob/main/.github/workflows/publish-release-notes.yml)

[![Run Create and Publish Release Notes](https://img.shields.io/badge/▶-Run%20workflow-2ea44f)](https://github.com/saghosh8/release-automation/actions/workflows/publish-release-notes.yml)

Purpose:

Creates the release tag, generates release notes, and publishes the GitHub Release for the application repositories listed in `input_files/prod_Old_tag.txt`.

Trigger:

```
workflow_dispatch
```

Inputs:

| Input            | Required | Example             | Description                                                                 |
| ---------------- | -------- | -------------------- | ----------------------------------------------------------------------------|
| `release_branch` | Yes      | `SG_RELEASE_1.0.0`   | Release identifier, must match `SG_RELEASE_<major>.<minor>.<patch>`         |

The list of repositories to process, and each one's previous release tag, comes from `input_files/prod_Old_tag.txt` — **not** from a workflow input. Update that file before running this workflow. See [Create and Publish Release Notes](#3-create-and-publish-release-notes) above for the file format.

Example:

```
release_branch = SG_RELEASE_1.0.0
```

```
input_files/prod_Old_tag.txt:
application-one:0.9.0-release-cfb154b
application-two:0.8.2-release-1a2b3c4
```

The workflow converts:

```
SG_RELEASE_1.0.0
```

to:

```
release/SG_RELEASE_1.0.0
```

and processes every repository listed in `prod_Old_tag.txt` against that branch.

### Trigger CI Pipeline

Workflow: [prod_ci.yml](https://github.com/saghosh8/release-automation/blob/main/.github/workflows/prod_ci.yml)

[![Run Trigger CI Pipeline](https://img.shields.io/badge/▶-Run%20workflow-2ea44f)](https://github.com/saghosh8/release-automation/actions/workflows/prod_ci.yml)

Purpose:

Remotely triggers the `CI` workflow in one or more application repositories, on a given branch.

Trigger:

```
workflow_dispatch
```

Inputs:

| Input          | Required | Example                           | Description                                          |
| -------------- | -------- | ---------------------------------- | ----------------------------------------------------- |
| `branch`       | Yes      | `release/SG_RELEASE_1.0.0`         | Branch to run CI from                                 |
| `repositories` | Yes      | `application-one,application-two`  | Comma-separated application repository names          |

Example:

```
branch       = release/SG_RELEASE_1.0.0
repositories = application-one,application-two
```

Result:

The `CI` workflow is triggered in `application-one` and `application-two` on `release/SG_RELEASE_1.0.0`.

Notes:

- The target repository must have a workflow whose `name:` is exactly `CI`; the trigger workflow looks it up by name via `gh workflow list` and fails that repository if it isn't found.
- The workflow verifies the branch exists in the target repository before attempting to trigger anything.
- Triggering is fire-and-forget — the workflow reports the trigger request as successful once GitHub accepts it, and does not wait for or report on the triggered run's outcome.

### Trigger CD - Prod Pipeline

Workflow: [prod_cd.yml](https://github.com/saghosh8/release-automation/blob/main/.github/workflows/prod_cd.yml)

[![Run Trigger CD - Prod Pipeline](https://img.shields.io/badge/▶-Run%20workflow-2ea44f)](https://github.com/saghosh8/release-automation/actions/workflows/prod_cd.yml)

Purpose:

Remotely triggers the `CD - Prod` workflow in the application repositories listed in `input_files/prod_New_tag.txt`, passing each repository's image tag along.

Trigger:

```
workflow_dispatch
```

Inputs:

| Input            | Required | Example                     | Description                    |
| ---------------- | -------- | ---------------------------- | -------------------------------|
| `release_branch` | Yes      | `release/SG_RELEASE_1.0.0`   | Release branch to deploy from  |

The list of repositories to deploy, and the image tag to deploy for each, comes from `input_files/prod_New_tag.txt` — not from a workflow input. Update that file before running this workflow.

Format (same style as `prod_Old_tag.txt`):

```
<repository-name>:<image-tag>
```

Example:

```
release_branch = release/SG_RELEASE_1.0.0
```

```
input_files/prod_New_tag.txt:
application-one:1.0.0-release-abc1234
application-two:1.0.0-release-81269a6
```

Result:

The `CD - Prod` workflow is triggered in `application-one` and `application-two` on `release/SG_RELEASE_1.0.0`, each with its own `release_tag` input value taken from `prod_New_tag.txt`.

Notes:

- The target repository must have a workflow whose `name:` is exactly `CD - Prod`; the trigger workflow looks it up by name and fails that repository if it isn't found.
- Unlike `prod_ci.yml`, this workflow does not verify that `release_branch` exists before triggering — the target `CD - Prod` workflow is expected to fail on its own if the ref is invalid.
- Triggering is fire-and-forget, same as the CI trigger workflow above.

## Release Naming Convention

### Release Branch

Input:

```
SG_RELEASE_1.0.0
```

Branch:

```
release/SG_RELEASE_1.0.0
```

### Release Version

The semantic version is extracted from the release identifier:

```
SG_RELEASE_1.0.0
```

becomes:

```
1.0.0
```

### Commit SHA

The workflow gets the exact commit at the HEAD of the release branch.

Example:

```
Full SHA:
81269a628a1d3929817439102b65cecd0d1af545

Short SHA:
81269a6
```

### Release Tag

The release tag format is:

```
<version>-release-<short-commit-sha>
```

Example:

```
1.0.0-release-81269a6
```

The tag therefore identifies both the release version and the exact release commit.

## Repository Resolution

Application repositories are supplied by repository name, e.g.:

```
application-two
```

The workflow resolves this to the full repository:

```
saghosh8/application-two
```

and uses the full repository path for API and Git operations.

This avoids attempting to clone an incomplete URL such as:

```
https://github.com/application-two.git
```

## Release Branch Validation

The release publishing workflow expects the release branch to already exist.

For:

```
SG_RELEASE_1.0.0
```

it checks:

```
release/SG_RELEASE_1.0.0
```

If the branch does not exist, the workflow fails.

Example:

```
Error: Release branch does not exist.
Repository: saghosh8/application-two
Branch: release/SG_RELEASE_1.0.0
```

## Tag Validation

Before creating a release, the workflow checks whether the generated tag already exists.

### Tag does not exist

The workflow creates:

```
1.0.0-release-81269a6
```

at the release branch commit.

### Tag already exists

The workflow checks that the existing tag points to the same commit as the release branch.

Expected:

```
81269a628a1d3929817439102b65cecd0d1af545
```

If the existing tag points to another commit, the workflow fails.

Example:

```
Error: Tag already exists but points to a different commit.
Expected: 81269a628a1d3929817439102b65cecd0d1af545
Actual:   <different SHA>
```

The workflow does not silently move or overwrite an existing tag.

## Previous Release and Comparison

The previous release tag for each repository is read from `input_files/prod_Old_tag.txt` rather than being auto-detected, and is used as the starting point for the release comparison.

Example:

```
Previous (from prod_Old_tag.txt):
0.9.0-release-cfb154b

Current:
1.0.0-release-81269a6
```

The changes between the previous and current releases are then used to generate the GitHub Release notes. The workflow fails if there are zero commits between the previous and current tags.

## Release Notes

GitHub generates the release notes from the changes between the previous release (from `prod_Old_tag.txt`) and the current release.

The published release contains the generated:

- What's Changed section
- Pull requests
- Contributors
- Full changelog comparison

Example:

```
What's Changed

• Update values-prod.yaml by @saghosh8 in #3

Full Changelog:
0.9.0-release-cfb154b...1.0.0-release-81269a6
```

## GitHub Release

The GitHub Release title is the generated release tag.

Example:

```
1.0.0-release-81269a6
```

The release is associated with the same tag:

```
1.0.0-release-81269a6
```

and that tag points to the commit at:

```
release/SG_RELEASE_1.0.0
```

## Triggering CI and CD - Prod Pipelines

Once a release branch exists and has commits, the CI and CD - Prod trigger workflows let this repository kick off pipelines in the application repositories remotely, instead of requiring someone to go trigger them by hand in each repo.

Typical order relative to the rest of the release process:

```
release/SG_RELEASE_1.0.0 created
        ↓
Application changes committed
        ↓
Trigger CI Pipeline (prod_ci.yml)
    branch = release/SG_RELEASE_1.0.0
        ↓
CI passes in each application repository
        ↓
Create and Publish Release Notes (publish-release-notes.yml)
    → release tag created, e.g. 1.0.0-release-81269a6
        ↓
Update input_files/prod_New_tag.txt with the new tag per repository
        ↓
Trigger CD - Prod Pipeline (prod_cd.yml)
    release_branch = release/SG_RELEASE_1.0.0
        ↓
CD - Prod deploys the tagged image in each application repository
```

Both workflows expect the corresponding workflow (`CI` or `CD - Prod`) to already exist, by that exact name, in each target application repository — this automation only triggers them, it does not create or modify them.

## Application Repository Configuration

New application repositories are generated from a single file:

```
input_files/app_config.yaml
```

The file has two top-level sections:

```
values:
  IMAGE_REPOSITORY: my-registry/my-image
  IMAGE_TAG: "1.0.0"
  DEV_REPLICA_COUNT: 1
  UAT_REPLICA_COUNT: 2
  PROD_REPLICA_COUNT: 3
  CONTAINER_PORT: 8080
  SERVICE_PORT: 80
  SERVICE_TYPE: ClusterIP
  INGRESS_ENABLED: true
  INGRESS_HOST: my-app.example.com
  HPA_ENABLED: true
  HPA_MIN_REPLICAS: 2
  HPA_MAX_REPLICAS: 5
  HPA_CPU_TARGET: 70

files:
  - path: "pom.xml"
    content: |
      ...
```

- **`values`** — settings shared by every repository created in a run (image, ports, replica counts, ingress, HPA). `APP_NAME` is intentionally not set here; it is injected automatically from the repository name being created.
- **`files`** — the template. Each entry's `path` and `content` may reference any key from `values` using `${KEY_NAME}` placeholders, plus three keys the workflow derives automatically:

| Placeholder            | Derived from `APP_NAME` (repository name) | Example (`billing-service`)  |
| ---------------------- | ----------------------------------------- | ----------------------------- |
| `${JAVA_PACKAGE}`      | dots, no hyphens                          | `com.example.billingservice` |
| `${JAVA_PACKAGE_PATH}` | same, as a folder path                    | `com/example/billingservice` |
| `${JAVA_CLASS_NAME}`   | PascalCase + `Application` suffix         | `BillingServiceApplication`  |

This derivation exists because Java package and class names cannot contain hyphens, while repository, Helm chart, and Maven artifact names commonly do.

The generated repository includes:

- A Spring Boot application skeleton (`src/main/java`, `src/main/resources`, `src/test/java`)
- Environment-specific Spring profiles (`application-dev.yml`, `application-uat.yml`, `application-prod.yml`)
- `Dockerfile` and `.dockerignore`
- `pom.xml`
- A Helm chart under `helm/<repo-name>/`, with per-environment values files (`values-dev.yaml`, `values-uat.yaml`, `values-prod.yaml`) and templates for Deployment, Service, Ingress, HPA, ConfigMap, and `.helmignore`

## Configuration

### Required Secret

The workflows use:

```
RELEASE_AUTOMATION_TOKEN
```

Store this as a GitHub Actions secret.

Go to:

```
Repository
→ Settings
→ Secrets and variables
→ Actions
```

Create:

```
RELEASE_AUTOMATION_TOKEN
```

The token must have access to all target application repositories, permission to create new repositories under the organization/owner, and the permissions required by the workflows.

Do not hard-code the token in a YAML file.

## Example Release Process

Assume the application repository is:

```
saghosh8/application-two
```

### Step 0 — Create the application repository (once, when the app is new)

Run:

```
Create Application Repository
```

Inputs:

```
repo_names:  application-two
description: Application repository
```

The workflow creates `saghosh8/application-two` with a generated Spring Boot + Helm project.

### Step 1 — Create the release branch

Run:

```
Create Release Branches
```

Inputs:

```
Release name: SG_RELEASE
Version:      1.0.0
Repository:   application-two
```

The workflow creates:

```
release/SG_RELEASE_1.0.0
```

### Step 2 — Application changes

Changes are committed to the release branch.

The branch eventually points to:

```
81269a628a1d3929817439102b65cecd0d1af545
```

Short SHA:

```
81269a6
```

### Step 3 — Update the previous-tag mapping file

Before publishing, make sure `input_files/prod_Old_tag.txt` in this repository contains an up-to-date line for the app, for example:

```
application-two:0.9.0-release-cfb154b
```

### Step 4 — Publish the release

Run:

```
Create and Publish Release Notes
```

Inputs:

```
Release branch: SG_RELEASE_1.0.0
```

The workflow processes every repository listed in `prod_Old_tag.txt`, including `application-two`.

### Step 5 — Tag

The workflow creates or validates:

```
1.0.0-release-81269a6
```

### Step 6 — Generate release notes

The workflow compares the previous release (`application-two:0.9.0-release-cfb154b` from `prod_Old_tag.txt`) against:

```
1.0.0-release-81269a6
```

and generates the GitHub Release notes.

### Step 7 — Publish

The GitHub Release is published using:

```
1.0.0-release-81269a6
```

## Multi-Repository Example

Multiple repositories can be supplied to the creation and release-branch workflows as a comma-separated list:

```
application-one,application-two,application-three
```

For the publishing workflow, multiple repositories are instead supplied as multiple lines in `input_files/prod_Old_tag.txt`:

```
application-one:0.9.0-release-abc0000
application-two:0.9.0-release-cfb154b
application-three:0.9.0-release-def0000
```

Each repository is processed independently.

Example (release branch and publish flow):

```
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

```
set -euo pipefail
```

The workflow fails for conditions such as:

- Target application repository already exists (repository creation workflow)
- `app_config.yaml` is missing, malformed, or missing a required value
- `release_branch` input does not match `SG_RELEASE_<major>.<minor>.<patch>` (publishing workflow)
- `input_files/prod_Old_tag.txt` is missing, empty, or missing an entry/tag for a repository (publishing workflow)
- Repository does not exist
- Repository cannot be accessed
- Release branch does not exist
- Invalid release input
- Commit SHA cannot be resolved
- Tag creation fails
- Existing tag points to a different commit
- Old (previous) tag from `prod_Old_tag.txt` does not exist in the repository
- Zero commits between the previous and new release
- Release note generation fails
- GitHub Release creation fails
- GitHub Release verification fails
- `branch` or `repositories` input is empty (CI trigger workflow)
- Target branch does not exist in the repository (CI trigger workflow)
- A workflow named `CI` is not found in the target repository (CI trigger workflow)
- `input_files/prod_New_tag.txt` is missing, empty, or missing a tag for a repository (CD - Prod trigger workflow)
- A workflow named `CD - Prod` is not found in the target repository (CD - Prod trigger workflow)

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
- Do not automatically overwrite an existing application repository.

## Troubleshooting

### Application Repository Already Exists

The creation workflow refuses to modify an existing repository. Choose a different `repo_names` value, or delete/rename the existing repository first if it was created in error.

### `app_config.yaml` Not Found Mid-Run

If this occurs partway through a multi-repository creation run, confirm the "Stage input files" step ran before the repository loop and that `input_files/app_config.yaml` exists in the automation repository at the commit being run.

### `release_branch` Input Rejected

The publishing workflow only accepts release identifiers of the form `SG_RELEASE_<major>.<minor>.<patch>` (e.g. `SG_RELEASE_1.0.0`). Any other prefix or format will fail validation before any repository is touched.

### `prod_Old_tag.txt` Errors

Verify:

1. `input_files/prod_Old_tag.txt` exists and is not empty.
2. Every repository you expect to publish has a `repo:old_tag` line.
3. The `old_tag` value on each line actually exists as a tag in that repository — the workflow validates this and fails if it doesn't.

### Repository Not Found

Verify:

1. The repository name is correct.
2. The repository exists.
3. `RELEASE_AUTOMATION_TOKEN` has access.
4. The workflow resolves the repository to the correct `owner/repository`.

### Release Branch Not Found

For input:

```
SG_RELEASE_1.0.0
```

the expected branch is:

```
release/SG_RELEASE_1.0.0
```

Verify the branch exists in the target repository.

### Tag Already Exists With a Different Commit

Do not delete or move the tag automatically.

Verify the existing tag and the release branch commit before deciding how to proceed.

### GitHub Release Already Exists

Verify the existing GitHub Release before rerunning the workflow.

The workflow should not create duplicate releases.

### `CI` Workflow Not Found

The CI trigger workflow (`prod_ci.yml`) looks for a workflow named exactly `CI` in the target application repository. Confirm the application repository has a workflow file whose `name:` field is `CI`, not just a filename that contains "ci".

### `CD - Prod` Workflow Not Found

Same as above, but for a workflow named exactly `CD - Prod` in the target repository, triggered by `prod_cd.yml`.

### `prod_New_tag.txt` Errors

Verify:

1. `input_files/prod_New_tag.txt` exists and is not empty.
2. Every repository you expect to deploy has a `repo:image_tag` line.
3. The image tag matches what you expect `CD - Prod` to deploy — the trigger workflow passes it through as-is and does not validate that the tag exists as a release or image.

## Workflow URLs

### Create Application Repository

<https://github.com/saghosh8/release-automation/blob/main/.github/workflows/create-app-repos.yml>

### Create Release Branches

<https://github.com/saghosh8/release-automation/blob/main/.github/workflows/create-release-branch.yml>

### Create and Publish Release Notes

<https://github.com/saghosh8/release-automation/blob/main/.github/workflows/publish-release-notes.yml>

### Trigger CI Pipeline

<https://github.com/saghosh8/release-automation/blob/main/.github/workflows/prod_ci.yml>

### Trigger CD - Prod Pipeline

<https://github.com/saghosh8/release-automation/blob/main/.github/workflows/prod_cd.yml>

### Repository

<https://github.com/saghosh8/release-automation>

## Contributing

1. Fork the repository.
2. Create a feature branch.

```
git checkout -b feature/improvement
```

3. Make the changes.
4. Test the workflows.
5. Commit the changes.

```
git commit -m "Add release automation improvement"
```

6. Push the branch.

```
git push origin feature/improvement
```

7. Open a Pull Request.

## License

This project is licensed under the MIT License.

See the `LICENSE` file for details.

## Release Flow Summary

```
Create Application Repository
        ↓
New repo: application-two
        ↓
Create Release Branch
        ↓
release/SG_RELEASE_1.0.0
        ↓
Application changes
        ↓
Trigger CI Pipeline (prod_ci.yml)
        ↓
Update input_files/prod_Old_tag.txt
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
Read previous release from prod_Old_tag.txt
        ↓
Compare releases
        ↓
Generate release notes
        ↓
Publish GitHub Release
        ↓
Verify release
        ↓
Update input_files/prod_New_tag.txt
        ↓
Trigger CD - Prod Pipeline (prod_cd.yml)
```
