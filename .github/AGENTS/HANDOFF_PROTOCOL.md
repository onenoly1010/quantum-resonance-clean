# Handoff Protocol

**Version:** 1.0  
**Status:** Operational  
**Purpose:** Define the coordination process for all agent and contributor interactions

---

## Purpose

The Handoff Protocol ensures that work can be resumed by any contributor at any time. It prevents context loss, documents decisions, and makes the repository self-maintaining.

## Core Philosophy

**"Work should be resumable by anyone, anytime, without asking the original contributor."**

This means:
- Context is never tribal knowledge
- Decisions are traceable
- Dependencies are explicit
- Risks are acknowledged
- Next steps are clear

## The 5-Step Protocol

Every handoff (agent-to-agent, agent-to-human, human-to-agent) follows this structure:

### Step 1: Context Capture
**"What is the current state?"**

Document:
- **Background** - Why is this work happening?
- **Prior Work** - What has already been done?
- **Current State** - Where are we now?
- **Constraints** - What limitations exist?
- **Requirements** - What must be satisfied?

**Example:**
```markdown
### Context
Background: User requested feature to export quantum data to CSV
Prior Work: Database schema supports export, API endpoint exists
Current State: Backend returns JSON, need frontend UI
Constraints: Must maintain existing API contract
Requirements: Support filters, handle large datasets
```

---

### Step 2: Work Summary
**"What was done?"**

Document:
- **Actions Taken** - Specific work performed
- **Decisions Made** - Choices and their rationale
- **Approach** - Strategy or methodology used
- **Challenges** - Problems encountered and solutions
- **Scope** - What was in/out of scope

**Example:**
```markdown
### Work Completed
Actions: Created ExportButton component, added CSV conversion utility
Decisions: Used PapaParse library for CSV generation (widely used, well-tested)
Approach: Client-side conversion to avoid server load
Challenges: Large datasets caused memory issues, implemented chunking
Scope: Included filters, excluded custom formatting (future work)
```

---

### Step 3: Artifact Listing
**"What files were created or modified?"**

Document:
- **Exact Paths** - Full file paths
- **Change Type** - Created, modified, deleted
- **Purpose** - Why each file was changed
- **Key Changes** - Important modifications within files
- **Dependencies** - New libraries or dependencies added

**Example:**
```markdown
### Files Modified
- `frontend/components/ExportButton.tsx` - NEW - CSV export button component
- `frontend/utils/csvExport.ts` - NEW - CSV conversion utility with chunking
- `frontend/pages/data.tsx` - MODIFIED - Added export button to data table
- `frontend/package.json` - MODIFIED - Added papaparse@5.4.1 dependency
- `frontend/types/export.ts` - NEW - TypeScript types for export functionality
```

---

### Step 4: Next Steps
**"What remains or should happen next?"**

Document:
- **Remaining Work** - Incomplete tasks
- **Recommendations** - Suggested future improvements
- **Blockers** - Dependencies waiting on other work
- **Testing** - What testing is needed
- **Documentation** - What docs should be updated

**Example:**
```markdown
### Next Steps
Remaining: 
- Add progress indicator for large exports
- Implement custom column selection

Recommendations:
- Consider server-side export for very large datasets
- Add export format options (Excel, JSON)

Blockers: None

Testing:
- Test with datasets >10k rows
- Verify filter application in exports
- Cross-browser compatibility check

Documentation:
- Update user guide with export feature
- Add JSDoc comments to export utilities
```

---

### Step 5: Risk Declaration
**"What assumptions or concerns exist?"**

Document:
- **Assumptions** - What is taken for granted
- **Risks** - Potential problems or concerns
- **Technical Debt** - Shortcuts or compromises made
- **Dependencies** - External factors
- **Open Questions** - Unresolved uncertainties

**Example:**
```markdown
### Risks and Assumptions
Assumptions:
- Users have modern browsers supporting Blob API
- CSV is acceptable format (no Excel requirement mentioned)
- Client-side processing is acceptable for current data volumes

Risks:
- Memory usage on very large datasets (>100k rows)
- Performance on low-end devices
- CSV special character escaping edge cases

Technical Debt:
- Chunking implementation is basic, may need optimization
- Error handling is minimal, needs improvement

Dependencies:
- PapaParse library (external, need to monitor for updates)

Open Questions:
- Should we limit export size? If so, what limit?
- Do we need audit logging for exports?
```

---

## Protocol Application

### In Pull Requests

Use the PR template which includes:

```markdown
## Handoff Context

### What Was Done
[Work Summary - Step 2]

### Files Modified
[Artifact Listing - Step 3]

### Next Steps
[Next Steps - Step 4]

### Risks or Assumptions
[Risk Declaration - Step 5]
```

Context Capture (Step 1) comes from the linked issue.

### In Issue Comments

When agents or contributors provide updates:

```markdown
## Handoff Update

**Context:** [Brief context refresh]

**Progress:** [What was done]

**Status:** [Current state]

**Next:** [What remains]

**Notes:** [Any risks or assumptions]
```

### In Code Comments

For complex code requiring context:

```typescript
/**
 * HANDOFF CONTEXT
 * 
 * Why: User data export feature
 * Approach: Client-side CSV generation with chunking
 * Challenge: Memory limits on large datasets
 * Solution: Process in 1000-row chunks
 * Risk: Performance on low-end devices
 * Next: Consider server-side for >100k rows
 */
export function exportToCSV(data: DataRow[]) {
  // Implementation
}
```

## Agent-Specific Application

### GitHub Agent (Coordinator)

When routing work:
```markdown
Routing to: Coding Agent

Context: Feature request for CSV export (see #123)
Scope: Frontend implementation only, backend exists
Handoff: See issue #123 for full requirements
Next: Implementation, then hand to Testing Agent
```

### Coding Agent

When implementing:
```markdown
Implementation complete.

Context: Export feature per issue #123
Work: Created ExportButton and CSV utility
Files: frontend/components/ExportButton.tsx (+3 others)
Next: Testing Agent for validation, Documentation Agent for user guide
Risks: Memory usage on large datasets
```

### Testing Agent

When validating:
```markdown
Testing complete.

Context: Export feature from PR #124
Work: Created unit tests, integration tests, manual testing
Files: frontend/__tests__/export.test.ts (+2 others)
Next: Documentation Agent for test documentation
Risks: Edge cases for special characters need monitoring
```

### Documentation Agent

When documenting:
```markdown
Documentation updated.

Context: Export feature from PR #124
Work: Updated user guide, added API docs, JSDoc comments
Files: docs/user-guide.md, docs/api.md, inline comments
Next: Ready for merge, consider release notes
Risks: None
```

## Quality Standards

### Required Elements

Every handoff **must** include:
- ✅ Clear context (why this work exists)
- ✅ Work summary (what was done)
- ✅ File list (what changed)
- ✅ Next steps (what remains)
- ✅ Risk declaration (what could go wrong)

### Optional Enhancements

Handoffs **may** include:
- 📊 Diagrams or screenshots
- 🔗 Links to related issues/PRs
- 📝 Design decisions documentation
- 🧪 Test coverage reports
- ⚡ Performance measurements

### Anti-Patterns

❌ **Bad Handoff:**
```markdown
Fixed the bug. Updated some files. Should work now.
```

❌ **Bad Handoff:**
```markdown
Implemented the feature as discussed.
```

✅ **Good Handoff:**
```markdown
## Handoff Context

### Context
Fixed null pointer exception in user profile loading (issue #234)

### Work Done
Added null checks in ProfileService.loadUser()
Updated tests to cover null scenarios
Added error logging for debugging

### Files
- src/services/ProfileService.ts - Added null checks
- tests/ProfileService.test.ts - Added null case tests

### Next Steps
Deploy to staging for validation
Monitor error logs for patterns

### Risks
Assumes null is the only edge case
May need additional validation for empty objects
```

## Protocol Enforcement

### Automated Checks

GitHub workflows validate:
- PR template usage
- Required sections present
- File lists included

See `.github/workflows/pr-check.yml`

### Review Guidelines

Reviewers should check:
- [ ] Handoff protocol followed
- [ ] Context is clear and sufficient
- [ ] File changes are listed
- [ ] Next steps are actionable
- [ ] Risks are acknowledged
- [ ] Work is resumable by others

### Non-Compliance

If handoff protocol is not followed:
1. Reviewer comments on PR
2. Requests handoff documentation
3. PR cannot merge until compliant
4. Patterns of non-compliance → governance discussion

## Benefits

Following this protocol ensures:

✅ **Continuity** - Anyone can pick up work  
✅ **Transparency** - All decisions are visible  
✅ **Quality** - Explicit risk acknowledgment  
✅ **Efficiency** - No time wasted asking "what was done?"  
✅ **Learning** - New contributors understand the approach  
✅ **Maintenance** - Future maintainers understand why  

## Examples from the Wild

### Example 1: Feature Implementation

See `docs/examples/handoff-feature-implementation.md`

### Example 2: Bug Fix

See `docs/examples/handoff-bug-fix.md`

### Example 3: Refactoring

See `docs/examples/handoff-refactoring.md`

### Example 4: Multi-Agent Coordination

See `docs/examples/handoff-multi-agent.md`

## Protocol Evolution

This protocol can evolve through:

1. **Feedback** - Contributors suggest improvements
2. **Governance** - Governance Agent reviews proposals
3. **Testing** - Trial changes in practice
4. **Amendment** - Canon amendment process if needed
5. **Documentation** - Update this file

Proposed changes should be discussed in issues labeled `governance`.

## Integration

This protocol integrates with:
- **Canon of Autonomy** - Core principles
- **Agent Instructions** - All agents follow this
- **PR Template** - Enforces structure
- **Issue Templates** - Provides context
- **Workflows** - Automated validation
- **MASTER_HANDOFF_MANIFEST** - System overview

## Quick Reference Card

```markdown
## HANDOFF TEMPLATE

### Context
Why: [Background and purpose]
Prior: [Previous work]
State: [Current situation]

### Work Done
Actions: [What was accomplished]
Decisions: [Choices made and why]

### Files Changed
- path/to/file.ts - [Change type] - [Purpose]

### Next Steps
Remaining: [Incomplete work]
Testing: [What needs validation]
Docs: [Documentation needs]

### Risks
Assumptions: [What we're assuming]
Concerns: [Potential issues]
Questions: [Unresolved items]
```

---

**Remember: A good handoff makes you redundant. That's the goal.**

*Last Updated: December 2025*  
*See MASTER_HANDOFF_MANIFEST.md for complete system architecture*
