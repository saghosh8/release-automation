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
