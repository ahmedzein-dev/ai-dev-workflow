# Verification: Saved favorites

## Check runs

Written by `workflow.py run`; do not edit between the markers.

<!-- aidw:checks:start -->
| Check | Status | Summary | Code fingerprint | When | Agent |
|---|---|---|---|---|---|
| unit | passed | OK | `ca05faf7ef` | 2026-11-12T06:10:54Z | codex |
<!-- aidw:checks:end -->

## Acceptance matrix

One row for every AC and EC in the approved spec and every "Done when" item, numbered DW-1, DW-2, … in
order. Status is Passed, Failed, Blocked or Not Verified. Evidence names the test, command or inspection;
for Blocked and Not Verified it says why. A check that did not run is never Passed.

| Item | Status | Evidence |
|------|--------|----------|
| AC-1 | Passed | test_saved_item_appears_first (check `unit`) |
| AC-2 | Passed | test_second_tap_removes (check `unit`) |
| AC-3 | Passed | test_signed_out_shopper_is_asked_to_sign_in (check `unit`) |
| EC-1 | Passed | test_removed_item_is_not_saved (check `unit`) |
| EC-2 | Not Verified | revert path inspected; no network-failure test double exists yet |
| EC-3 | Passed | `items()` returns an empty list; empty state inspected |
| DW-1 | Passed | all REQ and EC items above, EC-2 by inspection |
| DW-2 | Passed | four tests in tests/test_favorites.py pass |
| DW-3 | Passed | check `unit` passed on the current code |

## Behavioral checks

Saved, removed and re-saved items in a scratch session; ran the existing items test unchanged.

## Limitations

EC-2 (no network) has no automated test; verified by reading the revert path.
