"""Small command-line demonstration of the Phase 2 proof of concept."""

from inventory_system import (
    DuplicateProductError,
    InsufficientStockError,
    InventoryManager,
    Product,
)


def main() -> None:
    inventory = InventoryManager(
        demand_window=4,
        lead_time_periods=2,
        safety_stock_periods=1,
    )
    sample_products = [
        Product("P100", "Wireless Mouse", "Electronics", "24.99", 12, 4),
        Product("P101", "USB-C Cable", "Electronics", "9.50", 3, 5),
        Product("P200", "Coffee Beans", "Grocery", "14.25", 9, 3),
    ]

    for product in sample_products:
        inventory.add_product(product)

    print("INITIAL SNAPSHOT")
    print(inventory.snapshot())

    found = inventory.search_product("P100")
    print(f"\nSEARCH P100: {found.name} | quantity={found.quantity}")

    for period_demand in (2, 4, 3):
        inventory.record_demand("P100", period_demand)
    recommendation = inventory.restock_recommendation("P100")
    print(
        "DEMAND-AWARE RECOMMENDATION:",
        {
            "average_demand": recommendation.average_period_demand,
            "reorder_point": recommendation.reorder_point,
            "suggested_order_quantity": (
                recommendation.suggested_order_quantity
            ),
        },
    )
    print(f"P100 QUANTITY: {inventory.require_product('P100').quantity}")
    print(f"PENDING RESTOCK REQUESTS: {inventory.pending_restock_count}")

    next_item = inventory.process_restock()
    print(f"NEXT RESTOCK ITEM: {next_item.product_id} ({next_item.name})")

    electronics = inventory.products_in_category("electronics")
    print("ELECTRONICS:", [product.product_id for product in electronics])

    try:
        inventory.add_product(sample_products[0])
    except DuplicateProductError as exc:
        print("EXPECTED DUPLICATE ERROR:", exc)

    try:
        inventory.record_demand("P200", 100)
    except InsufficientStockError as exc:
        print("EXPECTED STOCK ERROR:", exc)

    removed = inventory.remove_product("P101")
    print(f"REMOVED: {removed.product_id}")
    print("FINAL SNAPSHOT")
    print(inventory.snapshot())


if __name__ == "__main__":
    main()
