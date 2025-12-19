# Handoff Protocol

**Standardized Work Transfer Between Agents and Contributors**

## Purpose

This protocol ensures seamless transfer of work between agents and contributors by establishing a consistent format for documenting context, decisions, and next steps. Proper handoffs enable the repository to remain maintainable without relying on any individual's memory.

## When to Perform a Handoff

Perform a formal handoff when:

- **Work is complete** in your domain and requires expertise from another agent
- **You've reached your scope boundary** and cannot proceed further
- **A task requires multiple agent specialties** working in sequence
- **You're blocked** and need input from another perspective
- **Context is complex** and must be preserved for future work

## Required Handoff Elements

Every handoff must include these six elements:

### 1. Work Summary

**What to include:**
- High-level description of what was accomplished
- Key decisions made during the work
- Problems solved or identified
- Scope of changes (what was changed vs. what wasn't)

**Example:**
```
Implemented authentication middleware for the ledger API endpoints.
Added JWT token validation, role-based access control, and audit logging.
Did NOT modify the frontend authentication flow—that remains unchanged.
```

### 2. Affected Files

**What to include:**
- Complete list of files created, modified, or deleted
- Line ranges for significant changes (optional but helpful)
- Dependencies added or updated

**Example:**
```
Created:
- ledger-api/src/middleware/auth.py
- ledger-api/tests/test_auth_middleware.py

Modified:
- ledger-api/src/main.py (lines 15-18, 45-52)
- ledger-api/requirements.txt (added python-jose[cryptography])

Deleted:
- (none)
```

### 3. Context Preservation

**What to include:**
- Why specific approaches were chosen
- Alternatives considered and rejected (with reasons)
- Constraints that influenced decisions
- References to similar patterns in the codebase

**Example:**
```
Chose JWT over session-based auth because:
1. API is stateless and deployed across multiple containers
2. Aligns with existing authentication in server/main.py
3. Simplifies scaling without shared session storage

Considered OAuth2 but rejected due to:
- Adds external dependency complexity
- Current requirements don't need third-party authentication
- Can add later if needed without breaking changes
```

### 4. Risks and Assumptions

**What to include:**
- Known limitations or edge cases
- Assumptions made during implementation
- Potential security considerations
- Performance implications
- Backward compatibility concerns

**Example:**
```
Assumptions:
- JWT_SECRET_KEY is properly secured in environment variables
- Token expiration is set to 24 hours (may need adjustment based on use case)
- All users have a valid email field in the database

Risks:
- Token invalidation before expiry not yet implemented (requires Redis or similar)
- High-frequency token refresh could impact database performance
- No rate limiting on authentication endpoints yet

Edge Cases:
- Concurrent token refresh during expiration window
- User role changes don't invalidate existing tokens until expiry
```

### 5. Next Steps

**What to include:**
- Specific actions recommended for next phase
- Which agent should handle which task
- Priority or sequencing of actions
- Open questions requiring decisions

**Example:**
```
For Testing Agent:
1. Add integration tests for authentication flow
2. Test token expiration and refresh scenarios
3. Validate role-based access control with different user types
4. Load test authentication endpoints (target: 1000 req/sec)

For Documentation Agent:
1. Document authentication setup in API README
2. Add authentication section to Swagger/OpenAPI spec
3. Create migration guide for existing API consumers

Open Questions:
- Should we implement token blacklisting for logout?
- What's the desired token expiration time for production?
- Do we need separate tokens for API vs. web interface?
```

### 6. Testing Status

**What to include:**
- Tests that were run and their results
- Coverage metrics if available
- Known test failures or gaps
- Manual testing performed

**Example:**
```
Completed:
✓ Unit tests for JWT encoding/decoding (100% coverage)
✓ Middleware integration tests (8 scenarios)
✓ Manual testing with Postman collection
✓ Verified against existing auth patterns in server/

Pending:
⧗ Load testing under concurrent requests
⧗ Security scan with CodeQL
⧗ Integration tests with frontend authentication

Known Issues:
✗ Test for expired token refresh fails intermittently (timing-dependent)
✗ Mock auth in tests doesn't match production Guardian implementation
```

## Handoff Templates

### Template 1: Standard Handoff

```markdown
## Handoff: [From Agent] → [To Agent]

### Work Summary
[Describe what was accomplished]

### Affected Files
Created:
- [file paths]

Modified:
- [file paths with optional line ranges]

Deleted:
- [file paths]

### Context Preservation
**Why this approach:**
[Rationale for decisions]

**Alternatives considered:**
[What else was evaluated and why rejected]

### Risks and Assumptions
**Assumptions:**
- [List assumptions made]

**Risks:**
- [Known risks or limitations]

**Edge Cases:**
- [Unusual scenarios to consider]

### Next Steps
**For [Recipient Agent]:**
1. [Specific action]
2. [Specific action]

**Open Questions:**
- [Questions requiring decisions]

### Testing Status
**Completed:**
- [What was tested]

**Pending:**
- [What still needs testing]

**Known Issues:**
- [Any test failures or gaps]
```

### Template 2: Quick Handoff (for minor changes)

```markdown
## Quick Handoff: [Task Name]

**Changed:** [Brief description]
**Files:** [List files]
**Next:** [What's needed] → [Which agent]
**Tested:** [Yes/No + what was validated]
```

### Template 3: Blocked Handoff

```markdown
## Blocked Handoff: [Issue Description]

**What I tried:**
[Approaches attempted]

**Why blocked:**
[Specific obstacle preventing progress]

**Need:**
[Specific help or decision required]

**Context:**
[Relevant background for problem-solving]

**Handoff to:** [Agent/Contributor who can help]
```

## Agent-Specific Handoff Patterns

### Coding Agent → Testing Agent

**Focus on:**
- New functionality that needs test coverage
- Changed behavior requiring test updates
- Edge cases discovered during implementation
- Performance characteristics to validate

### Testing Agent → Documentation Agent

**Focus on:**
- Test scenarios that should be documented
- API changes requiring doc updates
- New features needing user guides
- Breaking changes requiring migration docs

### Documentation Agent → Steward Agent

**Focus on:**
- Documentation completeness for review
- Consistency with existing docs
- Accuracy of technical details
- Clarity for target audience

### Steward Agent → Governance Agent

**Focus on:**
- Pattern violations detected
- Policy questions requiring clarification
- Conflict resolution needs
- Community standard updates

### Any Agent → Onboarding Agent

**Focus on:**
- New contributors needing guidance
- Setup steps that were confusing
- Missing documentation for common tasks
- Learning path improvements

## Handoff Best Practices

### Do:
- ✅ Be comprehensive but concise
- ✅ Use specific file paths and line numbers
- ✅ Link to related issues, PRs, or documentation
- ✅ Acknowledge uncertainty when present
- ✅ Provide enough context for someone unfamiliar with the work
- ✅ Use consistent formatting for readability

### Don't:
- ❌ Assume the recipient has context you haven't shared
- ❌ Leave implicit assumptions undocumented
- ❌ Skip testing status (even if tests are pending)
- ❌ Handoff without clear next steps
- ❌ Use vague language ("might need", "probably works")
- ❌ Forget to specify which agent should receive the handoff

## Handoff Storage

Handoffs should be documented in:

1. **Pull Request Descriptions** - For work submitted for review
2. **Issue Comments** - For ongoing work tracking
3. **Commit Messages** - For context preservation in git history
4. **README Updates** - For significant architectural changes

Choose the storage location based on:
- **Visibility needs** - Who needs to see this information?
- **Longevity** - How long must this context be preserved?
- **Discoverability** - Where will future contributors look for it?

## Example: Complete Handoff

```markdown
## Handoff: Coding Agent → Testing Agent

### Work Summary
Implemented quantum resonance calculation service for the ledger API.
Added three new endpoints for resonance analysis, pattern detection,
and frequency harmonization. All endpoints follow FastAPI async patterns
and include proper error handling with audit logging.

### Affected Files
Created:
- ledger-api/src/services/quantum_resonance.py (235 lines)
- ledger-api/src/schemas/resonance.py (89 lines)
- ledger-api/src/routers/resonance.py (142 lines)

Modified:
- ledger-api/src/main.py (lines 34-36: added resonance router)
- ledger-api/requirements.txt (added scipy==1.11.4 for quantum calculations)

### Context Preservation
**Why this approach:**
Implemented resonance calculations using scipy's FFT (Fast Fourier Transform)
because it provides proven, optimized quantum frequency analysis. This aligns
with the existing pattern in workflow_patch_agent.py which uses similar
mathematical analysis approaches.

**Alternatives considered:**
1. NumPy-only implementation - Rejected because scipy provides higher-level
   abstractions that make the code more maintainable
2. Custom FFT implementation - Rejected because scipy is battle-tested and
   significantly faster
3. External quantum computing API - Rejected due to latency and dependency
   on third-party availability

**Similar patterns:**
- Error handling matches allocation.py service pattern
- Async structure mirrors reconciliation.py
- Audit logging follows workflow_patch_agent.py approach

### Risks and Assumptions
**Assumptions:**
- Input frequency data is normalized to 0-1 range
- Users understand quantum resonance terminology (documented in API)
- scipy is acceptable dependency (adds ~50MB to container)

**Risks:**
- FFT calculations could be CPU-intensive for large datasets (>10k points)
- Memory usage scales linearly with input size
- No caching yet—repeated identical calculations recompute

**Edge Cases:**
- Empty input arrays return 400 error with clear message
- Single-point input returns warning but processes
- Very high frequency inputs (>1MHz) may produce numerical instability

### Next Steps
**For Testing Agent:**
1. Create unit tests for quantum_resonance.py (target: 90%+ coverage)
   - Test resonance calculation with known input/output pairs
   - Test error handling for invalid inputs
   - Test edge cases (empty, single-point, extreme values)

2. Add integration tests for resonance API endpoints
   - Test authentication requirements
   - Test audit log creation
   - Test response format compliance with OpenAPI spec

3. Performance testing
   - Benchmark calculation times for various input sizes (100, 1k, 10k points)
   - Verify memory usage stays within acceptable bounds
   - Test concurrent request handling (target: 50 req/sec)

4. Validate against existing workflow_patch_agent tests
   - Ensure new tests follow same pytest patterns
   - Use similar mocking approaches for database
   - Match assertion style and organization

**For Documentation Agent (after testing):**
- Document resonance API endpoints in README
- Add quantum resonance concepts to technical glossary
- Create example usage guide with sample data

**Open Questions:**
- Should resonance calculations be cached? (Trade-off: memory vs. CPU)
- What's the maximum acceptable calculation time? (Current: ~500ms for 10k points)
- Do we need to support real-time streaming resonance analysis?

### Testing Status
**Completed:**
✓ Manual testing with Postman using sample quantum data
✓ Validated against Pi Network test environment
✓ Checked resonance output matches expected mathematical properties
✓ Verified audit logs are created correctly
✓ Confirmed error responses follow API conventions

**Pending:**
⧗ Automated unit tests (this is the primary handoff task)
⧗ Integration test suite
⧗ Performance benchmarking
⧗ Security scan with CodeQL

**Known Issues:**
✗ scipy import adds noticeable startup time (~2 seconds)
✗ No rate limiting on compute-intensive resonance endpoints yet
✗ Error messages could be more user-friendly for non-technical users

---

**Handoff Date:** 2025-12-19  
**From:** Coding Agent  
**To:** Testing Agent  
**Priority:** High (blocks resonance feature release)
```

## Handoff Checklist

Before completing a handoff, verify:

- [ ] All six required elements are included
- [ ] File paths are absolute and accurate
- [ ] Next steps are specific and actionable
- [ ] Risks are honestly assessed
- [ ] Context is sufficient for someone unfamiliar with the work
- [ ] Recipient agent/contributor is clearly identified
- [ ] Testing status is accurately reported
- [ ] Related documentation is linked

## Continuous Improvement

This handoff protocol should evolve based on:
- Feedback from agents and contributors
- Identified gaps in handoff quality
- New agent types or workflows
- Lessons learned from failed handoffs

Suggest improvements via pull request to this document.

---

**Version:** 1.0  
**Last Updated:** 2025-12-19  
**Status:** Active
