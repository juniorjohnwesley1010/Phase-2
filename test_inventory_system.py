"""Automated correctness and edge-case tests for the inventory PoC."""

import unittest
from decimal import Decimal

from inventory_system import (
    DuplicateProductError,
    InsufficientStockError,
    InventoryManager,
    Product,
    ProductNotFoundError,
)


class InventoryManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = InventoryManager()
        self.mouse = Product("P100", "Mouse", "Electronics", "24.99", 10, 3)
        self.cable = Product("P101", "Cable", "Electronics", "9.50", 2, 4)

    def test_add_and_search_product(self) -> None:
        self.inventory.add_product(self.mouse)
        self.assertIs(self.inventory.search_product("P100"), self.mouse)
        self.assertEqual(self.inventory.product_count, 1)

    def test_duplicate_product_id_is_rejected(self) -> None:
        self.inventory.add_product(self.mouse)
        with self.assertRaises(DuplicateProductError):
            self.inventory.add_product(
                Product("P100", "Keyboard", "Electronics", 30, 8)
            )

    def test_missing_search_returns_none(self) -> None:
        self.assertIsNone(self.inventory.search_product("UNKNOWN"))

    def test_update_quantity_enqueues_low_stock_once(self) -> None:
        self.inventory.add_product(self.mouse)
        self.inventory.update_quantity("P100", -7)
        self.inventory.update_quantity("P100", 0)
        self.assertEqual(self.inventory.pending_restock_count, 1)

    def test_negative_result_is_rejected_without_mutation(self) -> None:
        self.inventory.add_product(self.mouse)
        with self.assertRaises(InsufficientStockError):
            self.inventory.update_quantity("P100", -11)
        self.assertEqual(self.inventory.require_product("P100").quantity, 10)

    def test_category_lookup_is_case_insensitive_and_sorted(self) -> None:
        self.inventory.add_product(self.cable)
        self.inventory.add_product(self.mouse)
        ids = [p.product_id for p in self.inventory.products_in_category("ELECTRONICS")]
        self.assertEqual(ids, ["P100", "P101"])

    def test_remove_updates_primary_and_category_indexes(self) -> None:
        self.inventory.add_product(self.mouse)
        self.inventory.remove_product("P100")
        self.assertIsNone(self.inventory.search_product("P100"))
        self.assertEqual(self.inventory.products_in_category("Electronics"), [])

    def test_remove_missing_product_raises_error(self) -> None:
        with self.assertRaises(ProductNotFoundError):
            self.inventory.remove_product("UNKNOWN")

    def test_restock_queue_preserves_fifo_order(self) -> None:
        self.inventory.add_product(self.cable)
        second = Product("P102", "Adapter", "Electronics", 12, 1, 2)
        self.inventory.add_product(second)
        self.assertEqual(self.inventory.process_restock().product_id, "P101")
        self.assertEqual(self.inventory.process_restock().product_id, "P102")

    def test_stale_queue_entry_is_skipped_after_recovery(self) -> None:
        self.inventory.add_product(self.cable)
        self.inventory.update_quantity("P101", 10)
        self.assertIsNone(self.inventory.process_restock())

    def test_product_validation(self) -> None:
        with self.assertRaises(ValueError):
            Product("", "Bad", "Other", 1, 1)
        with self.assertRaises(ValueError):
            Product("P1", "Bad", "Other", -1, 1)
        with self.assertRaises(ValueError):
            Product("P1", "Bad", "Other", 1, -1)

    def test_price_is_stored_as_decimal(self) -> None:
        self.assertEqual(self.mouse.price, Decimal("24.99"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
