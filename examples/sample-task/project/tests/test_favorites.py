import unittest

from app.favorites import Favorites


class FavoritesTest(unittest.TestCase):
    def test_saved_item_appears_first(self):
        favorites = Favorites()
        favorites.toggle("a")
        favorites.toggle("b")
        self.assertEqual(favorites.items(), ["b", "a"])

    def test_second_tap_removes(self):
        favorites = Favorites()
        favorites.toggle("a")
        self.assertEqual(favorites.toggle("a"), "removed")
        self.assertEqual(favorites.items(), [])

    def test_signed_out_shopper_is_asked_to_sign_in(self):
        favorites = Favorites()
        self.assertEqual(favorites.toggle("a", signed_in=False), "sign-in")
        self.assertEqual(favorites.items(), [])

    def test_removed_item_is_not_saved(self):
        favorites = Favorites()
        self.assertEqual(favorites.toggle("z", available=False), "This item is no longer available")
