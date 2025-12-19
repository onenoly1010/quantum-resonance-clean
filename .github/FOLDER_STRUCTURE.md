# Canonical Folder Structure

**Purpose:** Define the standard folder structure for repositories using the autonomous governance architecture  
**Status:** Reference document  
**Version:** 1.0

---

## Overview

This document defines the canonical folder structure for repositories implementing the 16-file autonomous governance architecture. Following this structure ensures consistency, discoverability, and proper integration of the agent system.

## Complete Structure

```
repository-name/
│
├── .github/                              # GitHub-specific configuration
│   ├── CANON_OF_AUTONOMY.md             # Foundational governance principles
│   ├── GITHUB_AGENT_INSTRUCTIONS.md     # GitHub Agent coordinator role
│   ├── PROJECT_INIT.md                  # Repository initialization guide
│   ├── REPOSITORY_INDEX.md              # Complete navigation map
│   ├── FOLDER_STRUCTURE.md              # This file
│   ├── MULTI_REPO_PROPAGATION.md        # Multi-repo propagation strategy
│   ├── copilot-instructions.md          # GitHub Copilot configuration
│   ├── pull_request_template.md         # PR template with handoff protocol
│   │
│   ├── AGENTS/                          # Agent instruction files
│   │   ├── README.md                    # Agent system overview
│   │   ├── HANDOFF_PROTOCOL.md          # Coordination process
│   │   ├── CODING_AGENT.md              # Code implementation specialist
│   │   ├── TESTING_AGENT.md             # Test coverage specialist
│   │   ├── DOCUMENTATION_AGENT.md       # Documentation specialist
│   │   ├── CREATIVITY_AGENT.md          # Naming and concepts specialist
│   │   ├── DESIGN_AGENT.md              # UI/UX specialist
│   │   ├── STEWARD_AGENT.md             # Repository maintenance specialist
│   │   ├── GOVERNANCE_AGENT.md          # Process and Canon specialist
│   │   └── ONBOARDING_AGENT.md          # New contributor specialist
│   │
│   ├── ISSUE_TEMPLATE/                  # Issue templates for routing
│   │   ├── feature_request.md           # Feature requests → Coding Agent
│   │   ├── documentation_update.md      # Docs → Documentation Agent
│   │   ├── creative_request.md          # Naming → Creativity Agent
│   │   ├── testing_request.md           # Tests → Testing Agent
│   │   └── governance_issue.md          # Process → Governance Agent
│   │
│   └── workflows/                       # GitHub Actions workflows
│       ├── label-routing.yml            # Route issues to agents via labels
│       ├── pr-check.yml                 # Validate PR template usage
│       ├── docs-reminder.yml            # Remind about documentation
│       └── [project-specific].yml       # Project-specific CI/CD workflows
│
├── MASTER_HANDOFF_MANIFEST.md           # Complete system architecture overview
├── README.md                            # Project overview and quick start
├── CONTRIBUTING.md                      # Contribution guidelines
├── CHANGELOG.md                         # Project history
├── LICENSE                              # License information
│
├── [project-specific directories]       # Your actual project code
│   ├── src/                             # Source code (example)
│   ├── tests/                           # Test files (example)
│   ├── docs/                            # Detailed documentation (example)
│   └── ...                              # Other project directories
│
└── [configuration files]                # Project configuration
    ├── .gitignore                       # Git ignore rules
    ├── .env.example                     # Environment variables template
    ├── package.json                     # Node.js dependencies (if applicable)
    ├── requirements.txt                 # Python dependencies (if applicable)
    └── ...                              # Other configuration files
```

## Core Structure Breakdown

### Root Level

**Governance Capstone:**
- `MASTER_HANDOFF_MANIFEST.md` - **REQUIRED** - System architecture overview

**Standard Project Files:**
- `README.md` - **REQUIRED** - Must include agent ecosystem section
- `CONTRIBUTING.md` - **REQUIRED** - Must reference agent system
- `CHANGELOG.md` - Recommended - Track system and project changes
- `LICENSE` - Required for open source
- `.gitignore` - **REQUIRED** - Exclude generated files

**Project-Specific:**
- Source code directories (varies by project)
- Configuration files (varies by tech stack)
- Build/deployment files

---

### .github/ Directory

**Purpose:** GitHub-specific configuration and governance files

**Core Governance (6 files):**
```
.github/
├── CANON_OF_AUTONOMY.md                 # Foundational principles
├── GITHUB_AGENT_INSTRUCTIONS.md         # Coordinator role
├── PROJECT_INIT.md                      # Initialization guide
├── REPOSITORY_INDEX.md                  # Navigation map
├── FOLDER_STRUCTURE.md                  # This file
└── MULTI_REPO_PROPAGATION.md            # Propagation strategy
```

**Templates:**
```
.github/
├── pull_request_template.md             # PR template
└── ISSUE_TEMPLATE/                      # Issue templates
    ├── feature_request.md
    ├── documentation_update.md
    ├── creative_request.md
    ├── testing_request.md
    └── governance_issue.md
```

**Automation:**
```
.github/
└── workflows/                           # GitHub Actions
    ├── label-routing.yml                # Agent routing
    ├── pr-check.yml                     # PR validation
    └── docs-reminder.yml                # Doc reminders
```

**Optional:**
```
.github/
└── copilot-instructions.md              # GitHub Copilot config
```

---

### .github/AGENTS/ Directory

**Purpose:** Agent instruction files

**Structure (10 files):**
```
.github/AGENTS/
├── README.md                            # Agent system overview
├── HANDOFF_PROTOCOL.md                  # 5-step coordination process
├── CODING_AGENT.md                      # Development
├── TESTING_AGENT.md                     # Quality assurance
├── DOCUMENTATION_AGENT.md               # Documentation
├── CREATIVITY_AGENT.md                  # Naming and concepts
├── DESIGN_AGENT.md                      # UI/UX
├── STEWARD_AGENT.md                     # Maintenance
├── GOVERNANCE_AGENT.md                  # Process and Canon
└── ONBOARDING_AGENT.md                  # New contributor support
```

**File Naming:** All agent files follow pattern `[AGENT_NAME]_AGENT.md` in SCREAMING_SNAKE_CASE

---

### .github/ISSUE_TEMPLATE/ Directory

**Purpose:** Route issues to appropriate agents

**Minimum Templates (5 files):**
```
.github/ISSUE_TEMPLATE/
├── feature_request.md                   # General features
├── documentation_update.md              # Documentation
├── creative_request.md                  # Naming/concepts
├── testing_request.md                   # Testing
└── governance_issue.md                  # Governance
```

**Optional Templates:**
- `bug_report.md` - Bug reports
- `design_request.md` - UI/UX requests
- `maintenance.md` - Repository maintenance
- Custom templates as needed

**Template Format:**
Each template must include:
- YAML front matter with `name`, `about`, `labels`
- Clear sections guiding contributor
- Reference to relevant agent

---

### .github/workflows/ Directory

**Purpose:** GitHub Actions automation

**Core Workflows (3 files):**
```
.github/workflows/
├── label-routing.yml                    # Routes labeled issues to agents
├── pr-check.yml                         # Validates PR template usage
└── docs-reminder.yml                    # Reminds about documentation needs
```

**Project-Specific:**
Add your CI/CD workflows:
- `ci.yml` - Continuous integration
- `deploy.yml` - Deployment automation
- `test.yml` - Test automation
- etc.

---

## Structural Principles

### 1. Separation of Concerns

**Governance** (.github/)
- Isolated from project code
- Clear structure
- Easy to update independently

**Project Code** (root or subdirectories)
- Organized by project needs
- Standard patterns for tech stack
- Not mixed with governance

### 2. Discoverability

**Clear Naming:**
- Governance files in SCREAMING_SNAKE_CASE
- Agent files end with `_AGENT.md`
- Templates in `ISSUE_TEMPLATE/` or `pull_request_template.md`

**Logical Grouping:**
- All agents in one directory
- All templates in one directory
- All workflows in one directory

### 3. Consistency

**Same Structure Everywhere:**
- Makes it easy to move between repos
- Reduces learning curve
- Enables automation

**Predictable Locations:**
- Governance always in `.github/`
- Agents always in `.github/AGENTS/`
- Templates always in `.github/ISSUE_TEMPLATE/`

### 4. Extensibility

**Add Without Breaking:**
- New agents → Add to `AGENTS/`
- New templates → Add to `ISSUE_TEMPLATE/`
- New workflows → Add to `workflows/`

**Core 16 Files Always Present:**
- 1 Master Manifest (root)
- 6 Core governance (.github/)
- 10 Agent system (.github/AGENTS/)
- = 16 core files (minimum)

### 5. Integration

**With Existing Repos:**
- Add governance structure alongside code
- Update existing files (README, CONTRIBUTING)
- Don't require restructuring project code

**With GitHub Features:**
- Templates use GitHub's built-in support
- Workflows use GitHub Actions
- Labels use GitHub's label system

---

## Customization Guidelines

### What to Customize

**DO customize:**
- Project-specific examples in agent files
- Tech stack references in agent instructions
- Issue template questions for your domain
- Workflow triggers for your CI/CD
- copilot-instructions.md for your project

**DO NOT change:**
- Core file names (CANON_OF_AUTONOMY.md, etc.)
- Folder structure (.github/AGENTS/, etc.)
- Handoff protocol structure
- Agent names or roles

### Adding Project-Specific Files

Your project code can be organized however makes sense:

**Example 1: Python Project**
```
repository/
├── .github/                  # Governance (standard)
├── MASTER_HANDOFF_MANIFEST.md
├── src/
│   └── myproject/
├── tests/
├── docs/
├── requirements.txt
└── setup.py
```

**Example 2: Web Application**
```
repository/
├── .github/                  # Governance (standard)
├── MASTER_HANDOFF_MANIFEST.md
├── frontend/
│   └── src/
├── backend/
│   └── api/
├── docs/
└── docker-compose.yml
```

**Example 3: Monorepo**
```
repository/
├── .github/                  # Governance (standard)
├── MASTER_HANDOFF_MANIFEST.md
├── packages/
│   ├── package-a/
│   ├── package-b/
│   └── package-c/
├── shared/
└── lerna.json
```

The governance structure is the same; only project code differs.

---

## Validation

### Structure Checklist

Verify your structure with this checklist:

**Root Level:**
- [ ] MASTER_HANDOFF_MANIFEST.md present
- [ ] README.md includes agent ecosystem section
- [ ] CONTRIBUTING.md references agent system

**.github/ Directory:**
- [ ] 6 core governance files present
- [ ] AGENTS/ subdirectory exists
- [ ] ISSUE_TEMPLATE/ subdirectory exists
- [ ] workflows/ subdirectory exists
- [ ] pull_request_template.md present

**.github/AGENTS/:**
- [ ] 10 agent files present (README.md + HANDOFF_PROTOCOL.md + 8 agents)
- [ ] All files named correctly (*_AGENT.md pattern)

**.github/ISSUE_TEMPLATE/:**
- [ ] At least 5 templates present
- [ ] All templates have YAML front matter

**.github/workflows/:**
- [ ] 3 core workflows present
- [ ] All YAML files valid

### Automated Validation

Create a script to validate structure:

```bash
#!/bin/bash
# validate-structure.sh

echo "Validating autonomous governance structure..."

required_files=(
  "MASTER_HANDOFF_MANIFEST.md"
  ".github/CANON_OF_AUTONOMY.md"
  ".github/GITHUB_AGENT_INSTRUCTIONS.md"
  ".github/PROJECT_INIT.md"
  ".github/REPOSITORY_INDEX.md"
  ".github/FOLDER_STRUCTURE.md"
  ".github/MULTI_REPO_PROPAGATION.md"
  ".github/AGENTS/README.md"
  ".github/AGENTS/HANDOFF_PROTOCOL.md"
  ".github/pull_request_template.md"
)

missing=0
for file in "${required_files[@]}"; do
  if [ ! -f "$file" ]; then
    echo "❌ Missing: $file"
    ((missing++))
  fi
done

if [ $missing -eq 0 ]; then
  echo "✅ All core governance files present!"
else
  echo "❌ $missing files missing"
  exit 1
fi
```

---

## Migration

### Adding Structure to Existing Repo

1. **Create governance structure** (preserve existing code)
2. **Update root files** (README, CONTRIBUTING)
3. **Test templates and workflows**
4. **Announce to contributors**
5. **Monitor and iterate**

### Moving Between Versions

If structure changes:
1. Document changes in CHANGELOG.md
2. Provide migration guide
3. Update FOLDER_STRUCTURE.md
4. Communicate to all repos using the system

---

## Resources

- [Master Handoff Manifest](../MASTER_HANDOFF_MANIFEST.md) - Complete system overview
- [Project Init Guide](PROJECT_INIT.md) - How to set up structure
- [Repository Index](REPOSITORY_INDEX.md) - Navigate existing structure
- [Multi-Repo Propagation](MULTI_REPO_PROPAGATION.md) - Apply to multiple repos

---

*Last Updated: December 2025*  
*Maintain this document as structure evolves*
