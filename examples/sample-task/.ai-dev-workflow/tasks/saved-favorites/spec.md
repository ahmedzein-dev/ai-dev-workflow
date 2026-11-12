# Feature Specification: Saved favorites

## Summary

**Problem:** Returning shoppers cannot find items they liked without searching again.
**Outcome:** A signed-in shopper can save an item with a heart and see saved items, newest first, on a favorites screen.

## Requirements

- **REQ-1:** Each item card shows a heart; tapping it saves the item with `PUT /favorites/{itemId}`, tapping again removes it with `DELETE /favorites/{itemId}`.
- **REQ-2:** The favorites screen lists saved items newest first, from `GET /favorites?page=n` (20 per page).
- **REQ-3:** A shopper who is not signed in sees a sign-in prompt instead of saving.

**Not included:**
- Sharing favorites with other people
- Multiple lists or collections
- Price-drop alerts

## Edge Cases

| ID | Situation | Expected behavior |
|----|-----------|-------------------|
| EC-1 | The item was removed from the shop (API returns 404) | The heart reverts and "This item is no longer available" appears. |
| EC-2 | No network connection when tapping the heart | The heart reverts and "No connection" appears with a Retry button. |
| EC-3 | The shopper has no favorites | The screen shows "No favorites yet" with a "Browse items" button. |

## Constraints

- **Must not change:** The item card layout apart from the heart, and the existing `app/items.py` data.
- **Structures:** A new `app/favorites.py` module with a `Favorites` class, following the one-responsibility module layout of `app/items.py` (AGENTS.md).
- **New dependencies:** None

## Acceptance Criteria

- **AC-1:** Given a signed-in shopper, when they tap an empty heart, then the item is saved and appears first on the favorites screen.
- **AC-2:** Given a saved item, when the shopper taps its heart again, then it disappears from the favorites screen.
- **AC-3:** Given a shopper who is not signed in, when they tap a heart, then a sign-in prompt appears and nothing is saved.

**Definition of done:**
- [ ] Every requirement and edge case behaves as specified
- [ ] Unit tests for `Favorites` (save, remove, order, signed-out) pass
- [ ] The project's required checks pass
