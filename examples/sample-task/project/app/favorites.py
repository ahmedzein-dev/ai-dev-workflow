class Favorites:
    """Saved item IDs for one shopper, newest first."""

    def __init__(self):
        self._ids = []

    def toggle(self, item_id, signed_in=True, available=True):
        if not signed_in:
            return "sign-in"
        if not available:
            return "This item is no longer available"
        if item_id in self._ids:
            self._ids.remove(item_id)
            return "removed"
        self._ids.insert(0, item_id)
        return "saved"

    def items(self):
        return list(self._ids)
