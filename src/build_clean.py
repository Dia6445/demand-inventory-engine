from sqlalchemy import text

from db import get_engine

STEPS = [
    "CREATE SCHEMA IF NOT EXISTS clean",
    "DROP TABLE IF EXISTS clean.order_items",
    "DROP TABLE IF EXISTS clean.orders",
    "DROP TABLE IF EXISTS clean.products",
    """
    CREATE TABLE clean.orders AS
    SELECT order_id, customer_id, order_status,
           order_purchase_timestamp::timestamp AS purchased_at,
           order_delivered_customer_date::timestamp AS delivered_at
    FROM raw.orders
    WHERE order_status NOT IN ('canceled', 'unavailable')
      AND order_purchase_timestamp::timestamp >= '2017-01-01'
      AND order_purchase_timestamp::timestamp < '2018-09-01'
    """,
    """
    CREATE TABLE clean.products AS
    SELECT p.product_id,
           COALESCE(t.product_category_name_english,
                    p.product_category_name, 'unknown') AS category,
           p.product_weight_g
    FROM raw.products p
    LEFT JOIN raw.product_category_name_translation t
           ON t.product_category_name = p.product_category_name
    """,
    """
    CREATE TABLE clean.order_items AS
    SELECT i.order_id, i.order_item_id, i.product_id, i.seller_id,
           i.price, i.freight_value, o.purchased_at
    FROM raw.order_items i
    JOIN clean.orders o ON o.order_id = i.order_id
    """,
]

engine = get_engine()

with engine.begin() as conn:
    for sql in STEPS:
        conn.execute(text(sql))

with engine.connect() as conn:
    for table in ("orders", "products", "order_items"):
        n = conn.execute(text(f"SELECT count(*) FROM clean.{table}")).scalar()
        print(f"clean.{table}: {n:,} rows")