# Multi-Repository Propagation Strategy

**Purpose:** Guide for applying the autonomous governance architecture across multiple repositories  
**Audience:** Repository maintainers, organization administrators  
**Version:** 1.0

---

## Overview

This document outlines strategies for propagating the 16-file autonomous governance architecture across multiple repositories within an organization or project ecosystem. It addresses how to maintain consistency, handle customization, and ensure long-term sustainability.

## Why Propagate?

### Benefits of Multi-Repo Governance

**Consistency:**
- Same process across all repositories
- Contributors move between repos easily
- Reduced cognitive load

**Efficiency:**
- Proven patterns reused
- Lessons learned shared
- Collective improvement

**Sustainability:**
- No single repo depends on one person
- Knowledge preserved across organization
- System self-maintains

**Quality:**
- Consistent quality standards
- Shared best practices
- Coordinated improvements

## Propagation Patterns

### Pattern 1: Template Repository

**Best for:** Organizations creating many similar repos

**Approach:**
Create a template repository with the governance architecture, then create new repos from the template.

**Setup:**

1. **Create Template Repository:**
```bash
# Create new repo
gh repo create org/governance-template --template --public

# Add governance structure
cd governance-template
# Copy all 16 core files
# Customize README with placeholder text
# Commit and push
```

2. **Mark as Template:**
- GitHub → Repository Settings
- Check "Template repository"
- Save

3. **Use Template:**
```bash
# Create new repo from template
gh repo create org/new-project --template org/governance-template

# Customize for new project
cd new-project
# Update README with project specifics
# Customize agent examples
# Update technology references
```

**Pros:**
- Quick setup for new repos
- Ensures all files present
- GitHub built-in feature

**Cons:**
- Not for existing repos
- Customization needed per repo
- Updates don't propagate automatically

---

### Pattern 2: Manual Propagation

**Best for:** Adding governance to existing repositories one at a time

**Approach:**
Follow [PROJECT_INIT.md](PROJECT_INIT.md) for each repository manually.

**Process:**

1. **Prepare:**
   - Read PROJECT_INIT.md thoroughly
   - Gather repository-specific information
   - Plan customization needs

2. **Initialize:**
   - Follow PROJECT_INIT.md step-by-step
   - Create all 16 core files
   - Customize for repository context

3. **Integrate:**
   - Update existing README, CONTRIBUTING
   - Test templates and workflows
   - Announce to contributors

4. **Document:**
   - Note customizations made
   - Document lessons learned
   - Share with other repos

**Pros:**
- Full control over customization
- Learn system deeply
- Careful integration

**Cons:**
- Time-consuming
- Potential for inconsistency
- Manual labor

---

### Pattern 3: Script-Assisted Propagation

**Best for:** Organizations with many existing repos to update

**Approach:**
Create scripts to automate file copying and basic customization.

**Conceptual Script:**

```bash
#!/bin/bash
# propagate-governance.sh
# Usage: ./propagate-governance.sh /path/to/target/repo

TARGET_REPO=$1
SOURCE_TEMPLATE="./governance-template"

echo "Propagating governance to $TARGET_REPO..."

# Create directories
mkdir -p "$TARGET_REPO/.github/AGENTS"
mkdir -p "$TARGET_REPO/.github/ISSUE_TEMPLATE"
mkdir -p "$TARGET_REPO/.github/workflows"

# Copy core files
cp "$SOURCE_TEMPLATE/.github/CANON_OF_AUTONOMY.md" "$TARGET_REPO/.github/"
cp "$SOURCE_TEMPLATE/.github/GITHUB_AGENT_INSTRUCTIONS.md" "$TARGET_REPO/.github/"
# ... copy all 16 core files

echo "✅ Files copied. Now customize for repository context."
echo "📝 Update: README.md, CONTRIBUTING.md"
echo "🔧 Customize: Agent examples, technology references"
```

**Advanced Script Features:**
- Detect technology stack
- Auto-customize placeholders
- Validate structure
- Generate checklist

**Pros:**
- Faster than manual
- Consistent file structure
- Batch processing possible

**Cons:**
- Still needs customization
- Script maintenance required
- Not fully automatic

---

## Governance of Propagation

### Who Decides?

**Organization Level:**
- CTO or technical leadership decides to adopt
- Engineering team implements
- Repository maintainers customize

**Project Level:**
- Project maintainers decide to adopt
- Contributors implement
- Community provides feedback

**Repository Level:**
- Maintainer decides to adopt
- Follows propagation pattern
- Announces to contributors

### Decision Framework

```markdown
## Should We Propagate?

Ask these questions:

### Repository Needs
- [ ] Is this a collaborative repository?
- [ ] Do we want long-term sustainability?
- [ ] Do we value transparency?
- [ ] Do contributors need clearer processes?

### Organization Readiness
- [ ] Can we support the system?
- [ ] Do we have resources for setup?
- [ ] Are we committed to principles?
- [ ] Will we maintain it?

### Timing
- [ ] Is now the right time?
- [ ] Are we between major releases?
- [ ] Can we handle the transition?
- [ ] Do contributors have capacity?

If mostly yes → Propagate
If mostly no → Wait or start with pilot
If mixed → Pilot in one repo first
```

## Customization Strategy

### What to Standardize

**Same across all repos:**
- Core file names and locations
- Handoff protocol structure
- Agent names and roles
- Canon of Autonomy principles
- Template structure

**Benefits:**
- Contributors move between repos easily
- System improvements apply broadly
- Shared understanding

### What to Customize

**Different per repo:**
- Technology stack examples
- Code style references
- Specific processes
- Domain terminology
- Repository-specific constraints

**Examples:**

```markdown
# Standardized (same everywhere)
## Agent System
- 8 specialist agents
- Handoff protocol
- Canon principles

# Customized (per repo)
## Technology Context
- Python repo: pytest examples
- JavaScript repo: Jest examples
- Go repo: Go testing examples
```

### Customization Guidelines

**DO customize:**
- Examples in agent instructions
- Technology references
- Build/test commands
- Repository-specific patterns

**DON'T customize:**
- Agent names or roles
- Handoff protocol structure
- Canon principles
- Core file structure

## Maintenance Strategy

### Centralized vs. Distributed

**Centralized Maintenance:**
- One team maintains governance files
- Updates pushed to all repos
- Consistency enforced

**Distributed Maintenance:**
- Each repo maintains its own
- Improvements shared via best practices
- Flexibility prioritized

**Hybrid Approach (Recommended):**
- Core governance centrally maintained
- Customizations locally maintained
- Improvements flow both directions

### Update Propagation

When governance improves:

1. **Document Change:**
   ```markdown
   ## Change Proposal
   
   File: AGENTS/CODING_AGENT.md
   Change: Add section on error handling
   Rationale: Common pattern needs documentation
   Impact: All repos should add this
   ```

2. **Test in Pilot:**
   - Apply to one repository
   - Gather feedback
   - Refine based on learning

3. **Communicate:**
   ```markdown
   To: All repo maintainers
   Subject: Governance Update Available
   
   Update: Coding Agent instructions improved
   File: .github/AGENTS/CODING_AGENT.md
   Action: Review and apply if relevant
   Timeline: Next maintenance cycle
   ```

4. **Propagate:**
   - Maintainers apply to their repos
   - Document in CHANGELOG.md
   - Share lessons learned

5. **Monitor:**
   - Check adoption across repos
   - Collect feedback
   - Iterate if needed

### Version Management

**Option 1: Governance Version Tags**

```markdown
# In MASTER_HANDOFF_MANIFEST.md
Governance System Version: 1.2.0

Changelog:
- 1.2.0: Added error handling section to Coding Agent
- 1.1.0: Improved Handoff Protocol examples
- 1.0.0: Initial autonomous governance system
```

**Option 2: Template Repository Releases**

Create releases in template repository:
- v1.0.0: Initial system
- v1.1.0: First improvement
- v1.2.0: Second improvement

Repos track which version they're using.

**Option 3: Living Documents**

No formal versions, continuous improvement:
- Update documentation in place
- Note update date at bottom of files
- Repos pull updates as needed

## Organization Patterns

### Small Organization (2-5 repos)

**Strategy:** Manual propagation

**Process:**
1. Set up in one repo (pilot)
2. Learn and refine (1-2 months)
3. Manually apply to other repos
4. Share lessons learned

**Maintenance:**
- Coordinate improvements informally
- Update repos opportunistically
- Keep systems roughly aligned

---

### Medium Organization (5-20 repos)

**Strategy:** Template + coordination

**Process:**
1. Create template repository
2. Pilot in 2-3 repos
3. Refine based on feedback
4. Create new repos from template
5. Gradually migrate existing repos

**Maintenance:**
- Designate governance coordinator
- Monthly review of improvements
- Quarterly propagation of updates
- Maintain template repository

---

### Large Organization (20+ repos)

**Strategy:** Centralized governance + automation

**Process:**
1. Establish governance working group
2. Create template repository
3. Pilot in representative repos
4. Build automation tools
5. Phased rollout across organization

**Maintenance:**
- Dedicated governance team
- Formal RFC process for changes
- Automated update checking
- Regular governance reviews

---

## Phased Rollout

### Phase 1: Pilot (1-2 months)

**Goals:**
- Validate system in real usage
- Identify issues and improvements
- Train initial adopters

**Repos:** 1-3 pilot repositories

**Activities:**
- Full setup following PROJECT_INIT.md
- Active usage and feedback collection
- Documentation of lessons learned
- Refinement of templates

**Success Metrics:**
- Handoff protocol followed consistently
- Contributors find system helpful
- Issues routed correctly
- No major blockers identified

---

### Phase 2: Early Adoption (2-4 months)

**Goals:**
- Expand to more repos
- Refine based on pilot feedback
- Build community of practice

**Repos:** 5-10 repositories

**Activities:**
- Apply to high-value repos
- Document customization patterns
- Train additional maintainers
- Create FAQ from common questions

**Success Metrics:**
- Multiple repos using system successfully
- Improvements identified and implemented
- Contributors moving between repos smoothly
- Maintainers confident in system

---

### Phase 3: Broad Rollout (6-12 months)

**Goals:**
- Apply across organization
- Standardize on practices
- Achieve consistency

**Repos:** Remaining repositories

**Activities:**
- Systematic propagation
- Automated updates where possible
- Comprehensive documentation
- Organization-wide training

**Success Metrics:**
- All active repos using system
- Consistent governance across org
- Reduced onboarding time
- Improved contribution quality

---

## Success Indicators

You'll know propagation is working when:

✅ Contributors move between repos without confusion  
✅ Handoff protocol followed consistently  
✅ Issues routed to appropriate agents  
✅ No repos have single points of failure  
✅ Quality and consistency improved  
✅ System self-maintains  

## Common Challenges

### Challenge: Resistance to Change

**Symptoms:**
- "We don't need this"
- "Too much overhead"
- "Our way works fine"

**Solutions:**
- Start with willing pilot repos
- Show concrete benefits
- Make adoption optional initially
- Demonstrate value with success stories

---

### Challenge: Customization Sprawl

**Symptoms:**
- Each repo diverges significantly
- No shared understanding
- Hard to maintain

**Solutions:**
- Define what must be standardized
- Document acceptable customizations
- Regular alignment reviews
- Share customization patterns

---

### Challenge: Stale Documentation

**Symptoms:**
- Governance docs outdated
- Broken links
- Inaccurate examples

**Solutions:**
- Assign Steward Agent responsibility
- Regular review cycles
- Automated link checking
- Make updates easy

---

### Challenge: Update Fatigue

**Symptoms:**
- Repos stop pulling updates
- Versions drift apart
- Improvements don't propagate

**Solutions:**
- Batch updates (quarterly)
- Clear communication of value
- Low-friction update process
- Only push valuable changes

---

## Best Practices

### Do's

✅ Start with pilot before wide rollout  
✅ Customize examples for each repo  
✅ Document lessons learned  
✅ Share improvements across repos  
✅ Make updates easy  
✅ Celebrate successes  

### Don'ts

❌ Force adoption on unwilling repos  
❌ Customize core structure  
❌ Let repos drift too far apart  
❌ Update too frequently  
❌ Ignore feedback  
❌ Neglect maintenance  

## Long-Term Sustainability

### Governance Working Group

**Purpose:** Maintain and evolve the system

**Responsibilities:**
- Review proposed improvements
- Coordinate updates
- Support repo maintainers
- Ensure consistency

**Composition:**
- Representative from each major repo
- Governance Agent practitioners
- Technical leadership liaison

**Cadence:**
- Monthly meetings
- Quarterly reviews
- Annual strategic planning

### Evolution Process

1. **Identify Improvement**
   - From usage feedback
   - From new patterns
   - From challenges encountered

2. **Propose Change**
   - Document clearly
   - Show examples
   - Explain rationale

3. **Pilot**
   - Test in 1-2 repos
   - Gather feedback
   - Refine

4. **Approve**
   - Governance working group reviews
   - Maintainers provide input
   - Decision documented

5. **Propagate**
   - Communicate change
   - Support adoption
   - Monitor results

6. **Learn**
   - Collect outcomes
   - Document lessons
   - Feed into next cycle

## Resources

- [Project Init Guide](PROJECT_INIT.md) - How to set up one repository
- [Folder Structure](FOLDER_STRUCTURE.md) - Canonical structure
- [Repository Index](REPOSITORY_INDEX.md) - Navigation
- [Master Handoff Manifest](../MASTER_HANDOFF_MANIFEST.md) - System overview

## Conclusion

Propagating autonomous governance across multiple repositories creates a sustainable, consistent, high-quality ecosystem. Start small, learn continuously, and expand thoughtfully. The system will grow stronger as it spreads.

**The goal isn't perfection, it's sustainable autonomy.**

---

*Last Updated: December 2025*  
*This strategy evolves with your organization*
