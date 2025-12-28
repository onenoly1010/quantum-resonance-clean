# Project Initialization Guide

**Purpose:** Step-by-step guide to initialize a new repository with the autonomous governance architecture  
**Audience:** Repository creators, maintainers setting up new projects  
**Version:** 1.0

---

## Overview

This guide walks through setting up the complete 16-file autonomous governance architecture in a new repository. Following these steps will create a self-governing, agent-coordinated repository aligned with the Canon of Autonomy.

## Prerequisites

Before starting:
- [ ] GitHub repository created
- [ ] Git installed locally
- [ ] Repository cloned to local machine
- [ ] Basic understanding of Git and GitHub
- [ ] Text editor ready

## Initialization Sequence

### Phase 1: Core Governance (30 minutes)

**Goal:** Establish foundational principles

#### Step 1.1: Create Canon of Autonomy

```bash
# Create .github directory if it doesn't exist
mkdir -p .github

# Create Canon
touch .github/CANON_OF_AUTONOMY.md
```

**Content:** Copy the Canon of Autonomy template, customizing:
- Repository-specific examples
- Technology stack references
- Community norms

**Verify:**
```bash
cat .github/CANON_OF_AUTONOMY.md | head -20
```

#### Step 1.2: Create Agent Directory

```bash
# Create agents directory
mkdir -p .github/AGENTS
```

#### Step 1.3: Create Agent System Files

```bash
# Create agent instruction files
touch .github/AGENTS/README.md
touch .github/AGENTS/HANDOFF_PROTOCOL.md
touch .github/AGENTS/CODING_AGENT.md
touch .github/AGENTS/TESTING_AGENT.md
touch .github/AGENTS/DOCUMENTATION_AGENT.md
touch .github/AGENTS/CREATIVITY_AGENT.md
touch .github/AGENTS/DESIGN_AGENT.md
touch .github/AGENTS/STEWARD_AGENT.md
touch .github/AGENTS/GOVERNANCE_AGENT.md
touch .github/AGENTS/ONBOARDING_AGENT.md
```

**Content:** Copy agent templates, customizing:
- Technology-specific examples
- Repository-specific patterns
- Domain-specific guidance

**Verify:**
```bash
ls -la .github/AGENTS/
# Should show 10 files
```

### Phase 2: Coordination Layer (20 minutes)

**Goal:** Set up GitHub Agent and operational docs

#### Step 2.1: GitHub Agent Instructions

```bash
touch .github/GITHUB_AGENT_INSTRUCTIONS.md
```

**Content:** Copy GitHub Agent template

#### Step 2.2: Operational Framework

```bash
touch .github/PROJECT_INIT.md          # This file!
touch .github/REPOSITORY_INDEX.md      # Navigation
touch .github/FOLDER_STRUCTURE.md      # Structure definition
touch .github/MULTI_REPO_PROPAGATION.md  # Propagation strategy
```

**Content:** Copy operational framework templates

**Verify:**
```bash
ls -la .github/*.md
# Should show 6 .md files in .github/
```

### Phase 3: Templates & Automation (30 minutes)

**Goal:** Enable automated routing and enforcement

#### Step 3.1: Pull Request Template

```bash
touch .github/pull_request_template.md
```

**Content:**
```markdown
## Summary
<!-- Brief description of changes -->

## Agent Involvement
<!-- Which agents were involved? Coding, Testing, Documentation, etc. -->

## Handoff Context

### What Was Done
<!-- Summarize the work completed -->

### Files Modified
<!-- List exact file paths -->

### Next Steps
<!-- What remains or what should happen next? -->

### Risks or Assumptions
<!-- Any concerns or dependencies? -->

## Alignment with Canon
- [ ] Changes align with Canon of Autonomy principles
- [ ] Work is documented and resumable by others
- [ ] No single-person dependencies created
```

#### Step 3.2: Issue Templates

```bash
mkdir -p .github/ISSUE_TEMPLATE
touch .github/ISSUE_TEMPLATE/feature_request.md
touch .github/ISSUE_TEMPLATE/documentation_update.md
touch .github/ISSUE_TEMPLATE/creative_request.md
touch .github/ISSUE_TEMPLATE/testing_request.md
touch .github/ISSUE_TEMPLATE/governance_issue.md
```

**Content:** Copy issue template examples (see complete templates in problem statement)

**Verify:**
```bash
ls -la .github/ISSUE_TEMPLATE/
# Should show 5 template files
```

#### Step 3.3: Workflows

```bash
mkdir -p .github/workflows
touch .github/workflows/label-routing.yml
touch .github/workflows/pr-check.yml
touch .github/workflows/docs-reminder.yml
```

**Content:** Copy workflow YAML files (see complete workflows in problem statement)

**Verify:**
```bash
ls -la .github/workflows/
# Should show 3 .yml files (+ any existing CI/CD)
```

### Phase 4: Master Manifest (15 minutes)

**Goal:** Create system capstone document

#### Step 4.1: Master Handoff Manifest

```bash
touch MASTER_HANDOFF_MANIFEST.md
```

**Content:** Copy Master Handoff Manifest template, ensuring:
- All 16 files are indexed
- File paths are correct for your repo
- Repository-specific context included

**Verify:**
```bash
cat MASTER_HANDOFF_MANIFEST.md | grep "##"
# Should show clear section structure
```

### Phase 5: Integration (20 minutes)

**Goal:** Connect system to existing repository

#### Step 5.1: Update README

Add agent ecosystem section to your README.md:

```markdown
## 🤖 Autonomous Agent Ecosystem

This repository uses a multi-agent system governed by the [Canon of Autonomy](CANON_OF_AUTONOMY.md).

### Quick Start
- **New contributors**: See `.github/AGENTS/ONBOARDING_AGENT.md`
- **Need help?**: Open an issue with the appropriate template
- **Understanding the system**: Read `MASTER_HANDOFF_MANIFEST.md`

### Agent System
- **GitHub Agent** - Coordinates all agents (`.github/GITHUB_AGENT_INSTRUCTIONS.md`)
- **8 Specialist Agents** - Coding, Testing, Documentation, Creativity, Design, Steward, Governance, Onboarding
- **Complete map**: `.github/AGENTS/README.md`

The system is designed to be sovereign, transparent, and self-sustaining.
```

#### Step 5.2: Update CONTRIBUTING.md

Add reference to agent system:

```markdown
## Agent-Assisted Contributions

This repository uses an autonomous agent system. When opening issues:
- Choose the appropriate issue template
- The system will route to the relevant agent
- Follow the handoff protocol in PR template

See [Canon of Autonomy](CANON_OF_AUTONOMY.md) for governance principles.
```

#### Step 5.3: Create/Update CHANGELOG.md

```markdown
# Changelog

## [Unreleased]

### Added
- Autonomous agent ecosystem with 8 specialist agents
- Canon of Autonomy governance framework
- Handoff protocol for coordination
- Issue templates for agent routing
- PR template with handoff documentation
- Automated workflows for agent coordination

### System Files
- Complete 16-file governance architecture
- Master Handoff Manifest
- See MASTER_HANDOFF_MANIFEST.md for complete system map
```

## Git Initialization

### Commit Strategy

Commit the files in logical groups:

```bash
# Commit 1: Core governance
git add .github/CANON_OF_AUTONOMY.md
git add .github/AGENTS/
git commit -m "Add Canon of Autonomy and agent system"

# Commit 2: Coordination layer
git add .github/GITHUB_AGENT_INSTRUCTIONS.md
git add .github/PROJECT_INIT.md
git add .github/REPOSITORY_INDEX.md
git add .github/FOLDER_STRUCTURE.md
git add .github/MULTI_REPO_PROPAGATION.md
git commit -m "Add GitHub Agent instructions and operational framework"

# Commit 3: Templates and automation
git add .github/pull_request_template.md
git add .github/ISSUE_TEMPLATE/
git add .github/workflows/
git commit -m "Add templates and automation workflows"

# Commit 4: Master manifest
git add MASTER_HANDOFF_MANIFEST.md
git commit -m "Add Master Handoff Manifest"

# Commit 5: Integration
git add README.md CONTRIBUTING.md CHANGELOG.md
git commit -m "Integrate agent ecosystem with existing documentation"

# Push all
git push origin main
```

## GitHub Agent Initialization

### Setting Up Agent Labels

Create labels in GitHub repository:

```bash
# Using GitHub CLI (if installed)
gh label create "coding-agent" --color "0E8A16" --description "For Coding Agent"
gh label create "testing-agent" --color "1D76DB" --description "For Testing Agent"
gh label create "documentation-agent" --color "0075CA" --description "For Documentation Agent"
gh label create "creativity-agent" --color "D876E3" --description "For Creativity Agent"
gh label create "design-agent" --color "F9D0C4" --description "For Design Agent"
gh label create "steward-agent" --color "FFA500" --description "For Steward Agent"
gh label create "governance-agent" --color "5319E7" --description "For Governance Agent"
gh label create "onboarding-agent" --color "FBCA04" --description "For Onboarding Agent"
```

Or manually through GitHub UI:
- Go to repository Settings → Labels
- Create each label with appropriate color

### Enabling Workflows

Ensure GitHub Actions are enabled:
1. Go to repository Settings → Actions
2. Select "Allow all actions and reusable workflows"
3. Save

### Testing Automation

Create a test issue to verify routing:
1. Open new issue
2. Select "Feature Request" template
3. Submit
4. Verify label-routing workflow adds comment
5. Close test issue

## Verification Checklist

After initialization, verify:

### File Structure
- [ ] 16 core files present (see MASTER_HANDOFF_MANIFEST.md for list)
- [ ] .github/AGENTS/ contains 10 files
- [ ] .github/ISSUE_TEMPLATE/ contains 5 templates
- [ ] .github/workflows/ contains 3 workflows
- [ ] MASTER_HANDOFF_MANIFEST.md at root

### Content Quality
- [ ] All files have content (not empty)
- [ ] Repository-specific customization done
- [ ] Cross-references are accurate
- [ ] File paths in documentation are correct

### Integration
- [ ] README mentions agent ecosystem
- [ ] CONTRIBUTING references agent system
- [ ] CHANGELOG documents system addition
- [ ] Labels created in GitHub
- [ ] Workflows enabled

### Functionality
- [ ] Issue templates appear when creating issue
- [ ] PR template appears when creating PR
- [ ] Workflows run on test issue/PR
- [ ] Labels route correctly

## Post-Initialization

### Announce to Contributors

Create an announcement issue:

```markdown
Title: 🤖 Autonomous Agent Ecosystem Now Active

Body:
We've implemented an autonomous agent ecosystem governed by the Canon of Autonomy!

**What this means:**
- 8 specialist agents coordinate work
- Clear processes via handoff protocol
- Issue templates route to appropriate agents
- Transparent, inclusive governance

**Getting started:**
1. Read [MASTER_HANDOFF_MANIFEST.md](MASTER_HANDOFF_MANIFEST.md)
2. Check [Canon of Autonomy](.github/CANON_OF_AUTONOMY.md)
3. Use issue templates for new work
4. Follow PR template for submissions

**New contributors:**
See [Onboarding Agent](.github/AGENTS/ONBOARDING_AGENT.md) for guidance!

Questions? Open an issue with the governance template.
```

### Monitor and Iterate

For the first few weeks:
- Monitor how contributors use the system
- Collect feedback on agent effectiveness
- Refine agent instructions based on usage
- Document lessons learned
- Iterate on templates and workflows

### Maintenance Schedule

Set reminders:
- **Weekly:** Review agent coordination quality
- **Monthly:** Update agent instructions if needed
- **Quarterly:** Review Canon for potential amendments

## Troubleshooting

### Common Issues

**Issue:** Workflows not running
- **Solution:** Check Actions enabled, YAML syntax valid, permissions set

**Issue:** Templates not appearing
- **Solution:** Verify files in correct location, GitHub cache may take a few minutes

**Issue:** Labels not routing
- **Solution:** Check label names match workflow YAML exactly

**Issue:** Contributors confused about system
- **Solution:** Create more examples, improve onboarding documentation

## Success Indicators

You'll know initialization was successful when:

✅ All 16 files committed and pushed  
✅ Issue templates appear in GitHub UI  
✅ PR template auto-populates  
✅ Workflows run automatically  
✅ Labels route issues correctly  
✅ Contributors start using the system  
✅ Handoff protocol is being followed  

## Next Steps

After successful initialization:

1. **Propagate** - Apply to other repositories (see MULTI_REPO_PROPAGATION.md)
2. **Refine** - Iterate based on real usage
3. **Evangelize** - Share with other projects
4. **Maintain** - Keep system healthy and current
5. **Evolve** - Improve governance over time

## Resources

- [Master Handoff Manifest](../MASTER_HANDOFF_MANIFEST.md) - Complete system map
- [Canon of Autonomy](CANON_OF_AUTONOMY.md) - Governance principles
- [Agent System Overview](AGENTS/README.md) - Agent ecosystem details
- [Folder Structure](FOLDER_STRUCTURE.md) - Canonical structure
- [Multi-Repo Propagation](MULTI_REPO_PROPAGATION.md) - Scaling strategy

---

**Congratulations! You've initialized an autonomous, self-governing repository.**

*Last Updated: December 2025*
