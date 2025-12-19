# Agent System Overview

**Purpose:** Multi-agent autonomous coordination for repository operations  
**Status:** Operational  
**Version:** 1.0

---

## Introduction

This directory contains the instruction sets for all autonomous agents operating within this repository. Each agent is a specialist with clear responsibilities, boundaries, and coordination protocols.

The agent system implements the principles defined in the [Canon of Autonomy](../.github/CANON_OF_AUTONOMY.md).

## The Agent Ecosystem

### Coordination Layer

#### GitHub Agent
**File:** See `.github/GITHUB_AGENT_INSTRUCTIONS.md` (parent directory)  
**Role:** Coordinator and facilitator  
**Responsibilities:**
- Route work to appropriate specialist agents
- Ensure handoff protocols are followed
- Maintain system coherence
- Bridge between contributors and specialist agents

**Does NOT:**
- Merge pull requests
- Approve deployments
- Override contributor decisions
- Command other agents

### Specialist Agents

#### 1. Coding Agent
**File:** `CODING_AGENT.md`  
**Domain:** Code implementation, refactoring, technical solutions  
**When to Use:**
- Implementing new features
- Refactoring existing code
- Bug fixes
- Code optimization
- Technical problem-solving

**Labels:** `coding-agent`, `enhancement`, `bug`

---

#### 2. Testing Agent
**File:** `TESTING_AGENT.md`  
**Domain:** Test creation, coverage analysis, validation  
**When to Use:**
- Writing unit tests
- Integration testing
- Test coverage analysis
- Validation strategies
- Test refactoring

**Labels:** `testing-agent`, `testing`

---

#### 3. Documentation Agent
**File:** `DOCUMENTATION_AGENT.md`  
**Domain:** Documentation creation, maintenance, clarity  
**When to Use:**
- Writing/updating README files
- API documentation
- Code comments
- Architecture documents
- Usage guides

**Labels:** `documentation-agent`, `documentation`

---

#### 4. Creativity Agent
**File:** `CREATIVITY_AGENT.md`  
**Domain:** Naming, concepts, narrative, branding  
**When to Use:**
- Naming variables, functions, projects
- Conceptual framework design
- Narrative consistency
- Terminology development
- Branding decisions

**Labels:** `creativity-agent`, `creativity`

---

#### 5. Design Agent
**File:** `DESIGN_AGENT.md`  
**Domain:** UI/UX, visual design, user experience  
**When to Use:**
- User interface design
- User experience optimization
- Visual consistency
- Accessibility improvements
- Design systems

**Labels:** `design-agent`, `design`, `ui/ux`

---

#### 6. Steward Agent
**File:** `STEWARD_AGENT.md`  
**Domain:** Repository health, maintenance, optimization  
**When to Use:**
- Dependency updates
- Repository cleanup
- Performance optimization
- Technical debt management
- Infrastructure maintenance

**Labels:** `steward-agent`, `maintenance`

---

#### 7. Governance Agent
**File:** `GOVERNANCE_AGENT.md`  
**Domain:** Process, Canon interpretation, conflict resolution  
**When to Use:**
- Canon interpretation questions
- Process clarification
- Conflict resolution
- Governance amendments
- Policy decisions

**Labels:** `governance-agent`, `governance`

---

#### 8. Onboarding Agent
**File:** `ONBOARDING_AGENT.md`  
**Domain:** New contributor support, learning paths  
**When to Use:**
- New contributor onboarding
- Repository navigation help
- Learning resource curation
- First-time contribution guidance
- System explanation

**Labels:** `onboarding-agent`, `onboarding`, `good first issue`

---

## How Agents Work Together

### Agent Coordination Principles

1. **Peer Collaboration** - Agents work as equals, not in hierarchy
2. **Clear Boundaries** - Each agent has a defined domain
3. **Handoff Protocol** - All coordination follows documented protocol
4. **Transparency** - All agent actions are visible and documented
5. **Autonomy** - Agents make decisions within their domains

### Common Patterns

#### Pattern 1: Single Agent
Simple tasks handled by one agent:
```
Issue → Routing → Coding Agent → PR → Review → Merge
```

#### Pattern 2: Sequential Handoff
Complex work passed between agents:
```
Issue → Creativity Agent (naming) → 
Coding Agent (implementation) → 
Testing Agent (validation) → 
Documentation Agent (docs) → PR
```

#### Pattern 3: Parallel Work
Independent tasks by multiple agents:
```
Issue → Coding Agent (feature A) + Design Agent (UI) → 
        Merge coordination → Integration
```

#### Pattern 4: Governance Escalation
Questions requiring process interpretation:
```
Issue → Initial Agent → Governance Agent (interpretation) → 
        Resolution → Original Agent (completion)
```

## The Handoff Protocol

Every agent interaction follows the 5-step handoff process defined in `HANDOFF_PROTOCOL.md`:

1. **Context Capture** - Current state and background
2. **Work Summary** - What was accomplished
3. **Artifact Listing** - Files created/modified
4. **Next Steps** - Remaining work or recommendations
5. **Risk Declaration** - Assumptions, concerns, dependencies

See [HANDOFF_PROTOCOL.md](HANDOFF_PROTOCOL.md) for complete details.

## Using the Agent System

### For Contributors

**Opening an Issue:**
1. Choose appropriate issue template (routes to correct agent)
2. Provide clear context and requirements
3. Let automation assign agent labels
4. Agent will respond and coordinate work

**During Work:**
1. Agents document all work using handoff protocol
2. Check PR descriptions for agent involvement
3. Review handoff context before continuing work
4. Add to handoff documentation if you modify agent work

**For Reviews:**
1. Verify handoff protocol was followed
2. Check alignment with Canon of Autonomy
3. Ensure work is documented for resumability
4. Confirm no single-person dependencies created

### For Agents

**Receiving Work:**
1. Read issue/PR context thoroughly
2. Check for existing handoff documentation
3. Identify dependencies on other agents
4. Begin work within your domain

**Performing Work:**
1. Follow Canon of Autonomy principles
2. Stay within your domain boundaries
3. Document as you work
4. Coordinate with other agents as needed

**Completing Work:**
1. Use handoff protocol for documentation
2. List all modified files
3. Identify next steps or remaining work
4. Declare any risks or assumptions

## Agent Activation

### GitHub Agent
Always active - monitors all issues and PRs

### Specialist Agents
Activated by:
- Issue template selection
- Manual label assignment
- Cross-agent handoff
- Automated workflow routing

## System Health

### Monitoring
- Handoff protocol compliance
- Agent coordination quality
- Response times
- Work quality

### Maintenance
Regular review of:
- Agent instruction effectiveness
- Coordination patterns
- Process improvements
- Canon alignment

### Evolution
The agent system can evolve through:
- Agent instruction updates
- New coordination patterns
- Handoff protocol refinements
- Canon amendments

## Quick Reference

| Need | Agent | Label | Template |
|------|-------|-------|----------|
| Code implementation | Coding Agent | `coding-agent` | feature_request |
| Tests | Testing Agent | `testing-agent` | testing_request |
| Documentation | Documentation Agent | `documentation-agent` | documentation_update |
| Naming/concepts | Creativity Agent | `creativity-agent` | creative_request |
| UI/UX | Design Agent | `design-agent` | feature_request |
| Repository health | Steward Agent | `steward-agent` | maintenance |
| Process questions | Governance Agent | `governance-agent` | governance_issue |
| Getting started | Onboarding Agent | `onboarding-agent` | help |

## Integration Points

This agent system integrates with:
- **Canon of Autonomy** - Foundational principles
- **GitHub Agent Instructions** - Coordinator role
- **Handoff Protocol** - Coordination process
- **Issue Templates** - Agent routing
- **PR Template** - Handoff documentation
- **GitHub Workflows** - Automation
- **MASTER_HANDOFF_MANIFEST** - System overview

## Resources

- [Canon of Autonomy](../CANON_OF_AUTONOMY.md)
- [GitHub Agent Instructions](../GITHUB_AGENT_INSTRUCTIONS.md)
- [Handoff Protocol](HANDOFF_PROTOCOL.md)
- [Master Handoff Manifest](../../MASTER_HANDOFF_MANIFEST.md)
- [Repository Index](../REPOSITORY_INDEX.md)

---

**The agent system exists to empower contributors, not replace them.**  
**Agents coordinate work; humans make decisions.**  
**The Canon governs all; no agent is above it.**

*Last Updated: December 2025*
