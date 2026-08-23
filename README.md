# Release Automation

Automates multi-repository release branch creation and release note / GitHub Release generation using GitHub Actions.

## Table of Contents
- [About](#about)  
- [Features](#features)  
- [How It Works](#how-it-works)  
- [Project Structure](#project-structure)  
- [Prerequisites](#prerequisites)  
- [Getting Started](#getting-started)  
- [Workflows](#workflows)  
  - [Create Release Branches](#create-release-branches)  
  - [Create Release Notes & Publish Releases](#create-release-notes--publish-releases)  
- [Configuration](#configuration)  
  - [Workflow Inputs](#workflow-inputs)  
  - [Required Secrets](#required-secrets)  
- [Security Considerations](#security-considerations)  
- [Troubleshooting](#troubleshooting)  
- [Contributing](#contributing)  
- [License](#license)

## About

This repository contains reusable GitHub Actions workflows designed to streamline the release process across multiple application repositories. It automates:

- **Release branch creation** across multiple repositories with consistent naming conventions
- **Version tagging** with automatic commit hash inclusion
- **Release notes generation** using GitHub's built-in generator with changelog comparison
- **GitHub Release publishing** with automated metadata

## Features

✅ Create release branches with standardized naming (`release/<name>-<number>`)  
✅ Generate versioned tags with commit short hash (e.g., `1.0.1-release-abc123f`)  
✅ Auto-generate release notes comparing against previous releases  
✅ Publish GitHub Releases across multiple repositories  
✅ Token validation and security checks  
✅ Detailed Actions job summary reports for audit and visibility  
✅ Support for both classic and fine-grained PATs  

## How It Works

### Release Branch Creation Flow
1. Trigger the **Create Release Branches** workflow via GitHub Actions UI or `gh` CLI
2. Workflow validates the `RELEASE_AUTOMATION_TOKEN`
3. For each specified repository:
   - Clones the repository
   - Creates a release branch from `main`
   - Pushes the branch back to the remote
4. Job summary documents all actions taken

### Release Publishing Flow
1. Trigger the **Create Release Notes** workflow
2. Workflow validates the `RELEASE_AUTOMATION_TOKEN`
3. For each specified repository:
   - Locates the corresponding release branch
   - Creates an annotated tag with versioning and commit hash
   - Generates release notes (automatically compares with previous tag)
   - Publishes a GitHub Release
4. Job summary documents all releases created

## Project Structure

```
release-automation/
├── .github/
│   └── workflows/
│       ├── create-release-branch.yml          # Workflow: Creates release branches
│       └── publish-release-notes.yml          # Workflow: Creates tags & publishes releases
├── README.md                                  # This file
└── LICENSE                                    # MIT License
```

### Workflow Files

#### `.github/workflows/create-release-branch.yml`
Creates release branches across multiple repositories.

**Inputs:**
- `release_name` — Release identifier (e.g., `SG_RELEASE`)
- `version` — Semantic version (e.g., `1.0.0`)
- `app_repos` — Comma-separated repository names

**Process:**
1. Validates authentication token
2. Generates release branch name: `release/<release_name>_<version>`
3. Clones each repository from `main`
4. Creates and pushes the release branch
5. Generates job summary with results

#### `.github/workflows/publish-release-notes.yml`
Creates tags and publishes GitHub Releases with auto-generated notes.

**Inputs:**
- `release_branch` — Release branch name (e.g., `SG_RELEASE_1.0.0`)
- `repositories` — Comma-separated repository names

**Process:**
1. Validates inputs and authentication
2. Resolves each repository
3. Verifies release branch exists
4. Creates versioned tag with commit hash
5. Finds previous release tag for comparison
6. Generates and publishes release notes
7. Verifies release was created

## Prerequisites

### Required
- **GitHub Organization or Personal Account** with multiple repositories
- **GitHub Personal Access Token (PAT)** with appropriate permissions
- **Application repositories** set up with a `main` branch
- **Previous release tags** (for release notes generation)

### Recommended
- **Standardized release naming** across teams
- **Semantic versioning** (e.g., `1.0.0`, `2.3.1`)
- **Branch protection rules** on `main` branch

## Getting Started

### 1. Create a GitHub Personal Access Token

#### Classic PAT
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (full control of private repositories)
   - `workflow` (Update GitHub Actions workflows)
4. Copy the token and store it securely

#### Fine-Grained PAT (Recommended)
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Set **Resource owner** to your organization
4. Set **Repository access** to "Only select repositories" (select all app repos)
5. Grant **Repository permissions**:
   - `Contents` — Read & Write
   - `Releases` — Read & Write
   - `Workflows` — Read & Write
6. Copy the token and store it securely

### 2. Add the Token as a Repository Secret

1. Go to this repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `RELEASE_AUTOMATION_TOKEN`
4. Value: Paste your PAT
5. Click "Add secret"

### 3. Trigger the Workflows

#### Create Release Branches
1. Go to **Actions** tab
2. Select **Create Release Branches** workflow
3. Click "Run workflow"
4. Fill in:
   - **Release name** (e.g., `SG_RELEASE`)
   - **Release version** (e.g., `1.0.0`)
   - **Application repositories** (comma-separated: `repo1,repo2,repo3`)
5. Click "Run workflow"

#### Create Release Notes & Publish Releases
1. Go to **Actions** tab
2. Select **Create Release Notes & Publish Releases** workflow
3. Click "Run workflow"
4. Fill in:
   - **Release branch** (e.g., `SG_RELEASE_1.0.0`)
   - **Repositories** (comma-separated: `repo1,repo2,repo3`)
5. Click "Run workflow"

## Workflows

### Create Release Branches

**File:** `.github/workflows/create-release-branch.yml`

**Purpose:** Creates standardized release branches across multiple repositories.

**Trigger:** Manual (`workflow_dispatch`)

**Workflow Inputs:**

| Input | Required | Example | Description |
|-------|----------|---------|-------------|
| `release_name` | Yes | `SG_RELEASE` | Release identifier |
| `version` | Yes | `1.0.0` | Semantic version number |
| `app_repos` | Yes | `app1,app2,app3` | Comma-separated repository names |

**Output:**
- GitHub Actions job summary with per-repository status
- Release branches created on all specified repositories
- Format: `release/<release_name>_<version>`

**Example:**
```bash
# Via GitHub CLI
gh workflow run create-release-branch.yml \
  -f release_name=SG_RELEASE \
  -f version=1.0.0 \
  -f app_repos=payment-service,auth-service,api-gateway
```

### Create Release Notes & Publish Releases

**File:** `.github/workflows/publish-release-notes.yml`

**Purpose:** Creates annotated tags and publishes GitHub Releases with auto-generated notes.

**Trigger:** Manual (`workflow_dispatch`)

**Workflow Inputs:**

| Input | Required | Example | Description |
|-------|----------|---------|-------------|
| `release_branch` | Yes | `SG_RELEASE_1.0.0` | Release branch identifier |
| `repositories` | Yes | `app1,app2,app3` | Comma-separated repository names |

**Output:**
- Versioned tags with commit hash (e.g., `1.0.0-release-abc123f`)
- GitHub Releases with auto-generated release notes
- Comparison against previous release

**Example:**
```bash
# Via GitHub CLI
gh workflow run publish-release-notes.yml \
  -f release_branch=SG_RELEASE_1.0.0 \
  -f repositories=payment-service,auth-service,api-gateway
```

## Configuration

### Workflow Inputs

#### Release Branch Workflow Inputs

```yaml
release_name:
  description: "Release name (e.g. SG_RELEASE)"
  required: true
  type: string

version:
  description: "Release version (e.g. 1.0.0)"
  required: true
  type: string

app_repos:
  description: "Comma-separated list of application repository names"
  required: true
  type: string
```

#### Release Notes Workflow Inputs

```yaml
release_branch:
  description: "Release branch name, e.g. SG_RELEASE_1.0.0"
  required: true
  type: string

repositories:
  description: "Application repository name(s), comma-separated"
  required: true
  type: string
```

### Required Secrets

#### RELEASE_AUTOMATION_TOKEN

A GitHub Personal Access Token with the following permissions:

**Classic PAT Scopes:**
- `repo` — Full control of private repositories
- `workflow` — Update GitHub Actions workflows

**Fine-Grained PAT Permissions (per repository):**
- `Contents` — Read & Write (for branches, tags, and commits)
- `Releases` — Read & Write (for publishing releases)
- `Workflows` — Read & Write (for updating workflows)

**Setup:**
1. Create or select an existing PAT
2. Add as secret `RELEASE_AUTOMATION_TOKEN` to this repository
3. Ensure the token has access to all target repositories

## Security Considerations

### Token Security
- 🔒 **Never commit tokens** to version control
- 🔒 **Use fine-grained PATs** with minimal required permissions
- 🔒 **Rotate tokens regularly** (recommended: every 90 days)
- 🔒 **Scope tokens to specific repositories** when possible
- 🔒 **Use organization-level secrets** for multi-repo releases

### Workflow Security
- ✅ **Workflows validate all inputs** before processing
- ✅ **Token validation** is performed at the start of each job
- ✅ **No credentials logged** — sensitive data is masked
- ✅ **Branch protection** should be enabled on `main` branches
- ✅ **Audit logs** are generated in GitHub Actions job summaries

### Branch Protection
Recommended settings for application repositories:
- Require pull request reviews before merging
- Require status checks to pass before merging
- Restrict direct pushes to `main`
- Enforce branch naming conventions

### Best Practices
1. **Limit token access** to required repositories
2. **Monitor workflow runs** for failures or anomalies
3. **Review job summaries** after each release
4. **Test with a single repository** before releasing multiple
5. **Maintain release notes** for audit and compliance

## Troubleshooting

### Release Branch Creation Fails

**Problem:** `Failed to clone repository`

**Solutions:**
1. Verify `RELEASE_AUTOMATION_TOKEN` is configured correctly
2. Check that the token has `repo` scope
3. Verify repositories are accessible to the token owner
4. Ensure `main` branch exists in the target repositories

**Problem:** `Failed to push release branch`

**Solutions:**
1. Check branch protection rules on target repository
2. Verify token has write access to repository
3. Ensure branch name is valid (no special characters)
4. Check for naming conflicts with existing branches

### Release Notes Generation Fails

**Problem:** `Release branch does not exist`

**Solutions:**
1. Verify release branch was created successfully
2. Run "Create Release Branches" workflow first
3. Check branch name format: `release/<name>_<version>`
4. Ensure no typos in repository or branch names

**Problem:** `No previous release tag found`

**Solutions:**
1. Ensure at least one previous release exists with tags
2. Verify tag format follows pattern: `X.Y.Z-release-<hash>`
3. Create initial release manually if none exist
4. Check that `main` branch has release tags

**Problem:** `Tag already exists but points to different commit`

**Solutions:**
1. Use different version number for new release
2. Delete existing tag and retry (use caution)
3. Verify release branch is based on correct commit

### Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `RELEASE_AUTOMATION_TOKEN is not configured` | Secret not added | Add `RELEASE_AUTOMATION_TOKEN` secret to repository |
| `Repository does not exist or token has no access` | Invalid credentials | Verify token has correct permissions and access |
| `Invalid release branch format` | Wrong naming pattern | Use format: `SG_RELEASE_X.Y.Z` |
| `main branch does not exist` | Repository missing main | Ensure target repo has `main` branch |
| `GitHub Release already exists` | Release tag already created | Use different version or delete existing release |

### Debugging Tips

1. **Check Actions Logs:** Review the full workflow logs for detailed error messages
2. **Review Job Summaries:** Each workflow generates a summary with per-repository status
3. **Verify Permissions:** Test token access with `gh auth status`
4. **Test Single Repository:** Run workflows on one repository first to debug
5. **Check Repository Settings:** Verify branch protection rules and permissions

## Contributing

Contributions are welcome! Please:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/improvement`)
3. **Make changes** and test thoroughly
4. **Commit with clear messages** (`git commit -am 'Add new feature'`)
5. **Push to your branch** (`git push origin feature/improvement`)
6. **Open a Pull Request** with detailed description

### Areas for Contribution
- Workflow improvements and optimizations
- Additional documentation and examples
- Bug reports and fixes
- Performance enhancements
- New features (e.g., rollback, multi-org support)

## License

This project is licensed under the **MIT License** — see the `LICENSE` file for details.

---

**Questions?** Open an issue or review the [troubleshooting section](#troubleshooting).

**Found a bug?** Submit an issue with details about the error and steps to reproduce.

**Have a feature request?** Create an issue describing your use case and desired functionality.
