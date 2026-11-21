# ORE security and threat model (proposal)

ORE inherits the project's threat model (../RISK_REGISTER.md §3): agents run with the user's permissions, so ORE
prevents mistakes and makes tampering detectable; it does not claim to stop a malicious agent with full permissions.

## Principles

1. **Models are data.** A JSON document validated against a schema; expressions are a small allow-listed AST
   (constants, parameters, variables, sums, constant scaling, comparisons, logical operators). No `eval`, `exec`,
   pickle or code generation from model content.
2. **Only trusted adapters run.** Adapters ship with ORE or come from plugins the user trusted (pinned by hash in the
   local trust store); a model cannot name an arbitrary executable.
3. **Solvers run in a separate process** with time, memory and thread limits, killed as a process group.
4. **Classification belongs to the verifier.** The agent proposes models and explains results; it cannot record
   `PROVEN_OPTIMAL` or any classification.
5. **Evidence is fingerprinted** and its events are part of the hash-chained event log (Phase 2).

## Threats

| ID | Threat | Mitigation | Prevents / detects |
|---|---|---|---|
| O-01 | Malicious model content (code injection through expressions or names) | Schema + allow-listed AST; identifiers restricted to a safe pattern; no evaluation of strings | Prevents |
| O-02 | Resource exhaustion (huge domains, pathological models) | Pre-checks (search-space size, sizes), process limits, cancellation | Prevents runaway runs; cannot predict all hard instances |
| O-03 | Invalid or contradictory constraints | Validation; infeasibility reported as such, with explanation when available | Detects |
| O-04 | Numerical overflow / precision loss | Exact fractions; bounded integer scaling; `NUMERICAL_UNCERTAINTY` instead of rounding | Prevents silent error |
| O-05 | Unsafe solver plugins | Plugin trust (Phase 15): manifest, permissions, hash pinning, never auto-enabled | Gated |
| O-06 | Data leakage (customer or business data in models and evidence) | Sensitive data stored by reference and hash, not copied into committed records; secret scanning on evidence; nothing sent to external services without consent | Reduces |
| O-07 | Model tampering after approval | Approval snapshot + fingerprint; changed model → stale results and invalid approval | Detects |
| O-08 | Result tampering or fake solver output | Independent exact verification of feasibility and objective; evidence fingerprints; event chain | Detects |
| O-09 | Fake optimality claims (by an agent or a misconfigured solver) | Classification computed only by the verifier from evidence meeting the policy level | Prevents through the engine |
| O-10 | Unauthorized changes to hard constraints or weights | Hard constraints and weights are part of the approved model; changes need renewed approval | Prevents through the engine |
| O-11 | Supply-chain change in a solver | Pinned versions, binary hash in evidence, trust store re-confirmation on change | Detects |
| O-12 | Prompt injection through data files feeding models | Data is parsed as values with provenance, never as instructions | Reduces |
