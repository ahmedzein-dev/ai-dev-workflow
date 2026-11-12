# Feature Specification: [Feature name]

## Summary

**Problem:** [The problem this solves, and for whom.]
**Outcome:** [What a user can do once this ships.]

## Requirements

- **REQ-1:** [A specific, testable behavior]
- **REQ-2:** [Another behavior]

**Not included:**
- [Something a reader might assume is part of this, but is not]

## Edge Cases

| ID | Situation | Expected behavior |
|----|-----------|-------------------|
| EC-1 | [e.g. The network drops during the request] | [e.g. Show "No connection" with a Retry button; nothing is saved] |

## Constraints

- **Must not change:** [Modules, public APIs or behavior that stay as they are]
- **Structures:** [Classes, components or modules to add or change, and the existing code each one follows]
- **New dependencies:** [Libraries or services to add, or "None"]

## Acceptance Criteria

- **AC-1:** Given [situation], when [action], then [result].

**Definition of done:**
- [ ] Every requirement and edge case behaves as specified
- [ ] The tests named in the plan pass
- [ ] The project's required checks pass
