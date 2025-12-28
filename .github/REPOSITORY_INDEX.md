# Repository Index

**Purpose:** Complete navigation map for the Quantum Resonance Clean repository  
**Status:** Living document - update as structure changes  
**Version:** 1.0

---

## Quick Navigation

| Need | Go To |
|------|-------|
| **Get Started** | [README.md](../README.md) |
| **Understand System** | [MASTER_HANDOFF_MANIFEST.md](../MASTER_HANDOFF_MANIFEST.md) |
| **Governance** | [Canon of Autonomy](#core-governance) |
| **Agent Help** | [Agent System](#agent-system) |
| **Contribute** | [CONTRIBUTING.md](../CONTRIBUTING.md) |
| **Templates** | [Issue/PR Templates](#templates--automation) |

---

## Core Governance

The foundational documents that establish how this repository governs itself.

### Primary Documents

| File | Purpose | When to Read |
|------|---------|--------------|
| [MASTER_HANDOFF_MANIFEST.md](../MASTER_HANDOFF_MANIFEST.md) | Complete system architecture overview | First time, or when confused about system |
| [CANON_OF_AUTONOMY.md](CANON_OF_AUTONOMY.md) | Foundational governance principles | Before contributing, when questions arise |
| [GITHUB_AGENT_INSTRUCTIONS.md](GITHUB_AGENT_INSTRUCTIONS.md) | GitHub Agent coordinator role | Understanding coordination |

### Operational Framework

| File | Purpose | When to Read |
|------|---------|--------------|
| [PROJECT_INIT.md](PROJECT_INIT.md) | How to initialize new repository | Setting up new repo |
| [REPOSITORY_INDEX.md](REPOSITORY_INDEX.md) | This file - navigation map | When lost or looking for something |
| [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) | Canonical folder structure | Understanding organization |
| [MULTI_REPO_PROPAGATION.md](MULTI_REPO_PROPAGATION.md) | How to propagate system | Applying to multiple repos |

---

## Agent System

The multi-agent coordination system that facilitates autonomous governance.

### Agent Overview

| File | Purpose | Route When |
|------|---------|------------|
| [AGENTS/README.md](AGENTS/README.md) | Agent ecosystem overview | Understanding agent system |
| [AGENTS/HANDOFF_PROTOCOL.md](AGENTS/HANDOFF_PROTOCOL.md) | Coordination process (5 steps) | Before any contribution |

### Specialist Agents

#### Development Agents

| Agent | Domain | File | Use When |
|-------|--------|------|----------|
| **Coding Agent** | Code implementation | [CODING_AGENT.md](AGENTS/CODING_AGENT.md) | Feature implementation, bug fixes, refactoring |
| **Testing Agent** | Test coverage | [TESTING_AGENT.md](AGENTS/TESTING_AGENT.md) | Writing tests, coverage analysis |
| **Design Agent** | UI/UX | [DESIGN_AGENT.md](AGENTS/DESIGN_AGENT.md) | Interface design, user experience |

#### Content Agents

| Agent | Domain | File | Use When |
|-------|--------|------|----------|
| **Documentation Agent** | Documentation | [DOCUMENTATION_AGENT.md](AGENTS/DOCUMENTATION_AGENT.md) | Writing docs, guides, API documentation |
| **Creativity Agent** | Naming, concepts | [CREATIVITY_AGENT.md](AGENTS/CREATIVITY_AGENT.md) | Naming challenges, terminology |

#### System Agents

| Agent | Domain | File | Use When |
|-------|--------|------|----------|
| **Steward Agent** | Maintenance | [STEWARD_AGENT.md](AGENTS/STEWARD_AGENT.md) | Dependencies, performance, tech debt |
| **Governance Agent** | Process, Canon | [GOVERNANCE_AGENT.md](AGENTS/GOVERNANCE_AGENT.md) | Process questions, conflicts |
| **Onboarding Agent** | New contributors | [ONBOARDING_AGENT.md](AGENTS/ONBOARDING_AGENT.md) | Getting started, learning paths |

---

## Contributor Experience

Resources for contributing to this repository.

### Getting Started

| File | Purpose | Audience |
|------|---------|----------|
| [README.md](../README.md) | Project overview and quick start | Everyone |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contribution guidelines | All contributors |
| [AGENTS/ONBOARDING_AGENT.md](AGENTS/ONBOARDING_AGENT.md) | Onboarding guide | New contributors |

### Contribution Process

| File | Purpose | When to Use |
|------|---------|-------------|
| [pull_request_template.md](pull_request_template.md) | PR template with handoff | Creating pull request |
| [ISSUE_TEMPLATE/](ISSUE_TEMPLATE/) | Issue templates | Opening new issue |
| [AGENTS/HANDOFF_PROTOCOL.md](AGENTS/HANDOFF_PROTOCOL.md) | Handoff documentation process | All contributions |

---

## Templates & Automation

GitHub templates and automated workflows.

### Issue Templates

Located in `.github/ISSUE_TEMPLATE/`

| Template | Agent | Purpose |
|----------|-------|---------|
| [feature_request.md](ISSUE_TEMPLATE/feature_request.md) | Coding Agent | Request new features |
| [documentation_update.md](ISSUE_TEMPLATE/documentation_update.md) | Documentation Agent | Request doc improvements |
| [creative_request.md](ISSUE_TEMPLATE/creative_request.md) | Creativity Agent | Naming, concepts |
| [testing_request.md](ISSUE_TEMPLATE/testing_request.md) | Testing Agent | Test coverage requests |
| [governance_issue.md](ISSUE_TEMPLATE/governance_issue.md) | Governance Agent | Process questions |

### Pull Request Template

| File | Purpose |
|------|---------|
| [pull_request_template.md](pull_request_template.md) | Ensures handoff protocol in all PRs |

### Workflows

Located in `.github/workflows/`

| Workflow | File | Purpose |
|----------|------|---------|
| **Label Routing** | [label-routing.yml](workflows/label-routing.yml) | Routes issues to agents via labels |
| **PR Template Check** | [pr-check.yml](workflows/pr-check.yml) | Validates PR template usage |
| **Docs Reminder** | [docs-reminder.yml](workflows/docs-reminder.yml) | Reminds about documentation |
| **Ledger API CI** | [ledger-api-ci.yml](workflows/ledger-api-ci.yml) | Runs ledger API tests |

---

## Project Artifacts

Key project documentation and resources.

### Project Documentation

| File | Purpose |
|------|---------|
| [CHANGELOG.md](../CHANGELOG.md) | Project history and changes |
| [ROADMAP.md](../ROADMAP.md) | Future plans and direction (if exists) |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | How to contribute |

### Technical Documentation

| File | Purpose |
|------|---------|
| [IMPLEMENTATION_SUMMARY.md](../IMPLEMENTATION_SUMMARY.md) | Implementation details |
| [SECURITY_SUMMARY.md](../SECURITY_SUMMARY.md) | Security considerations |
| [docs/](../docs/) | Detailed technical documentation |

### Ledger API

| Location | Purpose |
|----------|---------|
| [ledger-api/](../ledger-api/) | Ledger API implementation |
| [ledger-api/WORKFLOW_PATCH_AGENT.md](../ledger-api/WORKFLOW_PATCH_AGENT.md) | Example autonomous agent |
| [ledger-api/tests/](../ledger-api/tests/) | Ledger API tests |

---

## Codebase Structure

The actual project code and implementation.

### Backend (Python/FastAPI)

| Location | Purpose |
|----------|---------|
| [server/](../server/) | Python/FastAPI backend application |
| [server/main.py](../server/main.py) | Main application entry point |
| [requirements.txt](../requirements.txt) | Python dependencies |

### Frontend (Next.js/React)

| Location | Purpose |
|----------|---------|
| [frontend/](../frontend/) | Next.js/React/TypeScript frontend |
| [frontend/package.json](../frontend/package.json) | Node.js dependencies |
| [frontend/pages/](../frontend/pages/) | Next.js pages |
| [frontend/components/](../frontend/components/) | React components |

### Ledger API

| Location | Purpose |
|----------|---------|
| [ledger-api/](../ledger-api/) | Ledger API with database migrations |
| [ledger-api/alembic/](../ledger-api/alembic/) | Alembic database migrations |
| [ledger-api/tests/](../ledger-api/tests/) | Test suite |

### Infrastructure

| File | Purpose |
|------|---------|
| [Dockerfile](../Dockerfile) | Docker container configuration |
| [docker-compose.yml](../docker-compose.yml) | Docker Compose setup |
| [docker-compose.test.yml](../docker-compose.test.yml) | Testing environment |
| [railway.toml](../railway.toml) | Railway deployment config |

### Installation

| File | Purpose |
|------|---------|
| [install.sh](../install.sh) | Linux/macOS installation script |
| [install.ps1](../install.ps1) | Windows PowerShell installation |
| [run.ps1](../run.ps1) | Windows run script |

---

## Configuration

Configuration and environment files.

| File | Purpose |
|------|---------|
| [.env.example](../.env.example) | Environment variables template |
| [.gitignore](../.gitignore) | Git ignore rules |
| [.github/copilot-instructions.md](copilot-instructions.md) | GitHub Copilot configuration |

---

## Search Strategies

### Finding Something Specific

**Looking for governance?**
→ Start with [CANON_OF_AUTONOMY.md](CANON_OF_AUTONOMY.md)

**Looking for agent instructions?**
→ Check [AGENTS/](AGENTS/) directory

**Looking for how to contribute?**
→ Read [CONTRIBUTING.md](../CONTRIBUTING.md) and [AGENTS/ONBOARDING_AGENT.md](AGENTS/ONBOARDING_AGENT.md)

**Looking for code?**
→ Backend in [server/](../server/), Frontend in [frontend/](../frontend/)

**Looking for tests?**
→ [ledger-api/tests/](../ledger-api/tests/) for Python

**Looking for documentation?**
→ [docs/](../docs/) for detailed docs

**Looking for examples?**
→ [ledger-api/WORKFLOW_PATCH_AGENT.md](../ledger-api/WORKFLOW_PATCH_AGENT.md) shows autonomous patterns

### Using This Index

1. **Ctrl+F** (or Cmd+F) to search this page
2. Follow links to relevant files
3. Each file has internal navigation
4. Return here when you need to find something else

### File Naming Patterns

- **ALL_CAPS.md** - Important project-wide documentation
- **AGENTS/*.md** - Agent instruction files
- **lowercase.yml** - Workflow automation
- **lowercase.md** - Templates
- **lowercase/** - Code directories

---

## Maintenance

### Keeping This Index Current

When you add/remove/move files:
1. Update this index
2. Update [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md)
3. Update [MASTER_HANDOFF_MANIFEST.md](../MASTER_HANDOFF_MANIFEST.md) if governance files change
4. Commit changes together

### Who Maintains This

- **Steward Agent** - Regular maintenance
- **Documentation Agent** - Structure improvements
- **Any Contributor** - Spot fixes welcome!

---

## Quick Reference

### Common Workflows

| Task | Path |
|------|------|
| Create issue | Use [ISSUE_TEMPLATE/](ISSUE_TEMPLATE/) |
| Submit PR | Use [pull_request_template.md](pull_request_template.md) |
| Understand agent | Read agent's .md file in [AGENTS/](AGENTS/) |
| Learn governance | Read [CANON_OF_AUTONOMY.md](CANON_OF_AUTONOMY.md) |
| Get started | Read [AGENTS/ONBOARDING_AGENT.md](AGENTS/ONBOARDING_AGENT.md) |

### Key Concepts

| Concept | Where to Learn |
|---------|---------------|
| **Canon of Autonomy** | [CANON_OF_AUTONOMY.md](CANON_OF_AUTONOMY.md) |
| **Handoff Protocol** | [AGENTS/HANDOFF_PROTOCOL.md](AGENTS/HANDOFF_PROTOCOL.md) |
| **Agent System** | [AGENTS/README.md](AGENTS/README.md) |
| **System Architecture** | [MASTER_HANDOFF_MANIFEST.md](../MASTER_HANDOFF_MANIFEST.md) |

---

## Help

**Still can't find what you're looking for?**

1. Check [MASTER_HANDOFF_MANIFEST.md](../MASTER_HANDOFF_MANIFEST.md) for complete system overview
2. Search the repository with GitHub search
3. Open an issue and tag @Onboarding-Agent
4. Ask in discussions (if enabled)

**Found an issue with this index?**

Please open an issue or submit a PR to improve it!

---

*Last Updated: December 2025*  
*This is a living document - keep it current!*
