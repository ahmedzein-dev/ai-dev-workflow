# Feature Spec: [Feature Name]

---

## 1. Requirements

**Goal (one sentence):**
[What the user can do after this ships.]

**User story:**
As a [buyer / seller / rider / driver], I want to [action] so that [outcome].

**Functional requirements:**
- **FR-1:** [Specific, testable behavior]
- **FR-2:**
- **FR-3:**

**Out of scope (do NOT build):**
- [ ]

---

## 2. Edge Cases

| ID | Scenario | Expected Behavior |
|----|----------|-------------------|
| EC-1 | [e.g. User double-taps submit] | [e.g. Second tap ignored; button disabled while loading] |
| EC-2 | [e.g. No internet connection] | [ ] |
| EC-3 | [e.g. Server error / timeout] | [ ] |
| EC-4 | [e.g. Empty result] | [ ] |
| EC-5 | [e.g. App killed mid-operation] | [ ] |
| EC-6 | [e.g. Empty / null / max-length input] | [ ] |

---

## 3. Constraints (must NOT change)

- **Protected files / modules:** [e.g. core/network/, auth flow]
- **Public contracts:** [e.g. existing repository interfaces, API response shapes]
- **Allowed packages:** [e.g. flutter_bloc, dio, get_it, freezed]. No new packages without approval.
- **Architecture:** Clean Architecture. Dependencies flow UI → Logic → Domain ← Data. Widgets never import data sources or models; cubits never import models or data sources.
- **Scope:** Only touch files related to this feature. No refactoring outside it.
- **If anything is unclear:** stop and ask. Do not guess.

---

## 4. Acceptance Criteria

- **AC-1:** Given [context], when [action], then [result].
- **AC-2:** Given [context], when [action], then [result].
- **AC-3:** Given [context], when [action], then [result].

**Done when:**
- [ ] All requirements implemented
- [ ] All edge cases handled as specified
- [ ] Required tests pass
- [ ] `flutter analyze` has zero warnings
