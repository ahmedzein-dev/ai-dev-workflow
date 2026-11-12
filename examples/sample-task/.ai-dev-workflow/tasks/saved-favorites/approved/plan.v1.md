# Implementation Plan: Saved favorites

> Spec: v1 (approved)
> Frozen once approved. Progress is recorded with `workflow.py step`, never by editing this plan.

## 1. Goal

Let signed-in shoppers save items and list them newest first (REQ-1 to REQ-3).

## 2. Current Behavior

`app/items.py` holds the item catalogue; there is no saved state. Tests live in `tests/`.

## 3. Proposed Solution

Add `app/favorites.py` with a `Favorites` class that keeps saved item IDs in insertion order and exposes
`toggle(item_id, signed_in)` and `items()`. It follows the small single-purpose module style of `app/items.py`
required by AGENTS.md. The HTTP calls are represented by the class boundary so they can be swapped for the API client.

## 4. Affected Areas

`app/favorites.py` (new), `tests/test_favorites.py` (new). No existing file changes.

## 5. Implementation Steps

- **S1:** Add `Favorites` with toggle, newest-first listing and the signed-out guard (REQ-1, REQ-2, REQ-3, EC-1, EC-3).
- **S2:** Add unit tests for save, remove, order and the signed-out prompt (AC-1, AC-2, AC-3).

## 6. Important Technical Decisions

Keep order with a list rather than a set so "newest first" needs no timestamps; the backend remains the source of
truth on reload.

## 7. Edge Cases

EC-1 and EC-2 revert the toggle when the save fails; EC-3 is the empty list state.

## 8. Testing Plan

`unit` check: `tests/test_favorites.py` covers AC-1, AC-2, AC-3, EC-1 and EC-3; EC-2 is verified by inspection of
the revert path.

## 9. Risks and Dependencies

None — new module only, no shared code touched.

## 10. Expected Result

Shoppers can save, remove and list favorites; signed-out shoppers are asked to sign in.
