# ORE mathematical model schema (proposal)

A declarative, solver-independent and LLM-independent model format. Models are **data** validated against a JSON
Schema; nothing in a model is ever executed (no `eval`, no code). Version 1 deliberately covers what can be proven
(finite or bounded integer and Boolean variables, linear expressions, logical constraints); later versions add
classes only together with a solver that can honour the policy for them.

## 1. Shape

```json
{
  "schema": "ore/1",
  "id": "OPT-3",
  "title": "MVP feature selection",
  "template": "feature-selection",
  "sense": "lexicographic",
  "parameters": {
    "budget": {"value": "120", "unit": "person-day", "source": "user-provided", "ref": "Q-14", "collected": "2026-11-22"},
    "value_search": {"value": "40", "unit": "score", "source": "estimate", "ref": "ASM-6", "note": "PM estimate, 1–100 scale"}
  },
  "variables": {
    "pick": {"type": "bool", "index": ["search", "favorites", "offline", "sync", "share"]},
    "start_week": {"type": "int", "lb": "0", "ub": "12", "unit": "week", "index": ["search", "favorites"]}
  },
  "constraints": [
    {"id": "C1", "kind": "hard", "expr": {"le": [{"sum": {"over": "pick", "coef": "effort"}}, {"param": "budget"}]},
     "source": "CON-2", "text": "Total effort within the budget"},
    {"id": "C2", "kind": "hard", "expr": {"implies": [{"var": ["pick", "sync"]}, {"var": ["pick", "offline"]}]},
     "source": "REQ-9", "text": "Sync needs offline storage"},
    {"id": "C3", "kind": "soft", "expr": {"ge": [{"sum": {"over": "pick"}}, "3"]}, "penalty": "W1",
     "text": "Prefer at least three features"}
  ],
  "objectives": [
    {"id": "O1", "sense": "max", "expr": {"sum": {"over": "pick", "coef": "value"}}, "unit": "score", "priority": 1},
    {"id": "O2", "sense": "min", "expr": {"sum": {"over": "pick", "coef": "effort"}}, "unit": "person-day", "priority": 2}
  ],
  "weights": {"W1": {"value": "5", "approved_by": "user", "evidence": "approval quote ref"}},
  "policy": {"required_guarantee": "exact", "time_limit_s": 60, "memory_mb": 1024, "threads": 1},
  "not_represented": ["Team morale", "Marketing timing"],
  "refs": ["OBJ-1", "REQ-9", "CON-2", "ADR-0007"]
}
```

## 2. Elements

| Element | v1 support | Notes |
|---|---|---|
| Variables | `bool`, `int` with finite `lb`/`ub`, indexed families; `categorical` compiled to one-hot booleans | Continuous variables arrive with the first solver/verifier pair that can prove LP results (Phase 10) |
| Higher-level types | `assignment`, `interval` (scheduling) from templates, compiled to primitives | Compilation is deterministic and shown in the human rendering |
| Expressions | Linear: constants, `param`, `var`, `sum`, `scale` (constant × expression); comparisons `le`, `ge`, `eq` | Products of variables are rejected in v1 (`UNSUPPORTED_PROBLEM`), never silently linearised |
| Logical | `and`, `or`, `not`, `implies`, `all_different`, `exactly_one`, `at_most_one`; interval `no_overlap` | Compiled to linear or native constraints per adapter |
| Objectives | `min`/`max`; several with `priority` (lexicographic) or `pareto`; weighted sums only with approved `weights` | No weights → no weighted sum |
| Hard constraints | Must hold in every reported solution | Never relaxed automatically |
| Soft constraints | Only with an approved penalty weight or as a separate objective | Otherwise they are listed as unmodelled preferences |
| Numbers | Decimal strings parsed as exact fractions | Floats in input are rejected |

## 3. Data provenance and units

- Every parameter has `source` ∈ {`verified`, `measured`, `user-provided`, `approved-assumption`, `estimate`,
  `unknown`}, a `ref` to the record that justifies it (`Q`, `ASM`, `RES`, eval run, check run), `collected` and, where
  relevant, `valid_until`.
- `unknown` values block solving (`INSUFFICIENT_DATA`); `estimate` values are allowed but every result built on them is
  labelled "conditional on estimates" with the list of estimated inputs.
- Units: each parameter, variable and objective has a unit; the validator checks that sums and comparisons combine
  compatible units (a small built-in unit algebra; unknown units are rejected rather than guessed).

## 4. Integrity

- **Model fingerprint** = SHA-256 of the canonical JSON (sorted keys, normalised numbers).
- **Data fingerprint** = SHA-256 of the canonical parameter values.
- **Run identity** = model fingerprint + data fingerprint + solver name/version/binary hash + configuration.
- Any change to the model, data, policy or solver makes earlier results **stale**; an approved model is frozen like an
  approved spec (approval snapshot).

## 5. Human rendering (for model review)

The engine renders, without the agent: "This model decides **which of 5 features to build and when to start them**.
It maximises **total value (estimated, ASM-6)**, then minimises **effort**. It must never: exceed **120 person-days
(you, Q-14)**; build sync without offline storage (REQ-9). It prefers at least three features (penalty 5, approved).
It does **not** represent: team morale, marketing timing. Estimated inputs: value of all features."

## 6. Validation checks (before any solver runs)

Schema · referenced IDs exist · domains finite and non-empty · units compatible · every parameter has provenance and
no `unknown` value · linearity · soft constraints have approved weights or are objectives · exact integer scaling of
rational coefficients stays within the adapter's integer range (else `NUMERICAL_UNCERTAINTY` or `UNSUPPORTED_PROBLEM`)
· search-space size for enumeration computed exactly (product of domain sizes) and compared with the policy limit ·
the required guarantee can be met by at least one trusted adapter (else `UNSUPPORTED_PROBLEM`).
