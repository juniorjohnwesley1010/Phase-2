"""Core data structures for the Dynamic Inventory Management System PoC."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Deque, Dict, Optional, Set


class InventoryError(Exception):
    """Base exception for inventory operations."""


class DuplicateProductError(InventoryError):
    """Raised when a Product ID already exists."""


class ProductNotFoundError(InventoryError):
    """Raised when a Product ID cannot be found."""


class InsufficientStockError(InventoryError):
    """Raised when an update would make quantity negative."""


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _money(value: object) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("price must be numeric.") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("price must be a finite, non-negative value.")
    return amount.quantize(Decimal("0.01"))


def _nonnegative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer.")
    return value


@dataclass(slots=True)
class Product:
    """A validated inventory record."""

    product_id: str
    name: str
    category: str
    price: Decimal
    quantity: int
    reorder_level: int = 5

    def __post_init__(self) -> None:
        self.product_id = _required_text(self.product_id, "product_id")
        self.name = _required_text(self.name, "name")
        self.category = _required_text(self.category, "category")
        self.price = _money(self.price)
        self.quantity = _nonnegative_integer(self.quantity, "quantity")
        self.reorder_level = _nonnegative_integer(
            self.reorder_level, "reorder_level"
        )

    @property
    def needs_restock(self) -> bool:
        return self.quantity <= self.reorder_level


class InventoryManager:
    """Coordinates the product index, category index, and restock queue."""

    def __init__(self) -> None:
        self._products: Dict[str, Product] = {}
        self._category_index: Dict[str, Set[str]] = defaultdict(set)
        self._restock_queue: Deque[str] = deque()
        self._queued_restock_ids: Set[str] = set()

    @staticmethod
    def _category_key(category: str) -> str:
        return _required_text(category, "category").casefold()

    def add_product(self, product: Product) -> None:
        if not isinstance(product, Product):
            raise TypeError("product must be a Product instance.")
        if product.product_id in self._products:
            raise DuplicateProductError(
                f"Product ID '{product.product_id}' already exists."
            )

        self._products[product.product_id] = product
        self._category_index[self._category_key(product.category)].add(
            product.product_id
        )
        self._sync_restock_status(product)

    def search_product(self, product_id: str) -> Optional[Product]:
        return self._products.get(_required_text(product_id, "product_id"))

    def require_product(self, product_id: str) -> Product:
        normalized_id = _required_text(product_id, "product_id")
        product = self._products.get(normalized_id)
        if product is None:
            raise ProductNotFoundError(
                f"Product ID '{normalized_id}' was not found."
            )
        return product

    def update_quantity(self, product_id: str, change: int) -> Product:
        if isinstance(change, bool) or not isinstance(change, int):
            raise ValueError("change must be an integer.")

        product = self.require_product(product_id)
        new_quantity = product.quantity + change
        if new_quantity < 0:
            raise InsufficientStockError(
                f"Cannot reduce '{product.product_id}' below zero units."
            )

        product.quantity = new_quantity
        self._sync_restock_status(product)
        return product

    def remove_product(self, product_id: str) -> Product:
        product = self.require_product(product_id)
        del self._products[product.product_id]

        category_key = self._category_key(product.category)
        product_ids = self._category_index[category_key]
        product_ids.discard(product.product_id)
        if not product_ids:
            del self._category_index[category_key]

        # The deque is cleaned lazily when process_restock is called.
        self._queued_restock_ids.discard(product.product_id)
        return product

    def products_in_category(self, category: str) -> list[Product]:
        product_ids = self._category_index.get(self._category_key(category), set())
        return [self._products[pid] for pid in sorted(product_ids)]

    def process_restock(self) -> Optional[Product]:
        while self._restock_queue:
            product_id = self._restock_queue.popleft()
            if product_id not in self._queued_restock_ids:
                continue
            self._queued_restock_ids.remove(product_id)
            product = self._products.get(product_id)
            if product is not None and product.needs_restock:
                return product
        return None

    def _sync_restock_status(self, product: Product) -> None:
        if product.needs_restock:
            if product.product_id not in self._queued_restock_ids:
                self._restock_queue.append(product.product_id)
                self._queued_restock_ids.add(product.product_id)
        else:
            # Removing from the membership set invalidates any stale deque entry.
            self._queued_restock_ids.discard(product.product_id)

    @property
    def product_count(self) -> int:
        return len(self._products)

    @property
    def pending_restock_count(self) -> int:
        return len(self._queued_restock_ids)

    def snapshot(self) -> dict[str, object]:
        """Return a serializable summary for demonstrations and future APIs."""
        return {
            "product_count": self.product_count,
            "pending_restock_count": self.pending_restock_count,
            "categories": {
                key: sorted(product_ids)
                for key, product_ids in sorted(self._category_index.items())
            },
        }
