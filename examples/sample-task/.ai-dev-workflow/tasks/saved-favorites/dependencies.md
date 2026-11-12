# Dependencies: Saved favorites

| ID | Type | Class | Gate | Owner | Summary |
|----|------|-------|------|-------|---------|
| DEP-1 | backend | Verified | - | Backend developer | Favorites endpoints and errors |
| DEP-2 | ui | Not applicable | - | - | Existing item card and list patterns cover the UI |

## Details

### DEP-1 — Favorites endpoints

**Why it matters:** REQ-1 and EC-1 depend on how favorites are saved and what errors come back.
**Who provides it:** Backend developer.
**Message to send:**
```text
Hi! We're adding saved favorites to the shop app: a signed-in user taps a heart on an item to save it,
and sees saved items on a favorites screen, newest first.

To finish the spec we need:
1. Which endpoints save, remove and list favorites (method and path)?
2. Is the list paginated, and how is it sorted?
3. What does the API return when the item no longer exists, or the user is not signed in?

Could you share an example request and response for saving and for listing, including the error bodies?
Thanks!
```
**Answer received:** PUT/DELETE /favorites/{itemId}; GET /favorites?page=n, 20 per page, newest first; 404 when the item is gone; 401 when signed out.
**Resolution:** Contract written into REQ-1, REQ-2, REQ-3 and EC-1; Class changed to Verified.
