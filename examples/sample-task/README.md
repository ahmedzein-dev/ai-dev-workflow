# Sample task: saved favorites

A complete, finished AIDevWorkflow task, produced by running the real engine from start to finish in a small
example project. Nothing here was written by hand afterwards: the hashes, snapshots, evidence and history are what
`workflow.py` recorded.

What it shows:

- **Dependencies** — a backend contract was Blocking at the spec gate; the ready-to-send message, the answer and the
  resolution are in [`dependencies.md`](.ai-dev-workflow/tasks/saved-favorites/dependencies.md).
- **Specification** — the example template filled in, with coverage and edge-case decisions recorded in the review
  (`spec_review` in `state.json`).
- **Approvals** — the user's words, bound to each document's hash, with frozen copies in
  [`approved/`](.ai-dev-workflow/tasks/saved-favorites/approved/).
- **Cross-agent handoff** — specified and planned in Claude Code, implemented and tested in Codex (see `history` in
  `state.json`), audited in a separate session by another agent.
- **Evidence** — the `unit` check recorded with a fingerprint of the code; the acceptance matrix in
  [`verification.md`](.ai-dev-workflow/tasks/saved-favorites/verification.md).
- **Honest status** — EC-2 was only verified by inspection and an Important finding was accepted rather than fixed,
  so `workflow.py outcome` capped the result at **Completed with Limitations**
  ([`report.md`](.ai-dev-workflow/tasks/saved-favorites/report.md)).

`project/` holds the code the task produced, for reference.
