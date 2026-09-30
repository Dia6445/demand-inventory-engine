from sqlalchemy import text

from db import get_engine

CHECKS = {
    "duplicate order ids":
        "SELECT count(*) - count(DISTINCT order_id) FROM raw.orders",
    "delivered orders with no delivery date":
        "SELECT count(*) FROM raw.orders "
        "WHERE order_status = 'delivered' AND order_delivered_customer_date IS NULL",
    "delivery date before purchase date":
        "SELECT count(*) FROM raw.orders "
        "WHERE order_delivered_customer_date::timestamp < order_purchase_timestamp::timestamp",
    "order items with no matching order":
        "SELECT count(*) FROM raw.order_items i "
        "LEFT JOIN raw.orders o ON o.order_id = i.order_id WHERE o.order_id IS NULL",
    "order items with price <= 0":
        "SELECT count(*) FROM raw.order_items WHERE price <= 0",
    "products with no category":
        "SELECT count(*) FROM raw.products WHERE product_category_name IS NULL",
    "products with no weight":
        "SELECT count(*) FROM raw.products WHERE product_weight_g IS NULL",
}

engine = get_engine()
problems = 0

with engine.connect() as conn:
    for name, sql in CHECKS.items():
        found = conn.execute(text(sql)).scalar()
        status = "OK  " if found == 0 else "WARN"
        problems += found > 0
        print(f"[{status}] {name}: {found:,}")

print()
print(f"{problems} of {len(CHECKS)} checks found problems")