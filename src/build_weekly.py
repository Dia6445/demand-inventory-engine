from sqlalchemy import text

from db import get_engine

FIRST_WEEK = "2017-01-02"   # a Monday
LAST_WEEK = "2018-08-13"    # last reliable week (data fades out after 2018-08-19)

STEPS = [
    "CREATE SCHEMA IF NOT EXISTS features",
    "DROP TABLE IF EXISTS features.weekly_category_units",
    f"""
    CREATE TABLE features.weekly_category_units AS
    WITH weeks AS (
        SELECT generate_series('{FIRST_WEEK}'::date, '{LAST_WEEK}'::date,
                               interval '7 days')::date AS week
    ),
    cats AS (
        SELECT DISTINCT p.category
        FROM clean.order_items i
        JOIN clean.products p ON p.product_id = i.product_id
    ),
    sales AS (
        SELECT p.category,
               date_trunc('week', i.purchased_at)::date AS week,
               count(*) AS units
        FROM clean.order_items i
        JOIN clean.products p ON p.product_id = i.product_id
        WHERE i.purchased_at >= '{FIRST_WEEK}'
          AND i.purchased_at < '2018-08-20'
        GROUP BY 1, 2
    )
    SELECT c.category, w.week, COALESCE(s.units, 0) AS units
    FROM cats c
    CROSS JOIN weeks w
    LEFT JOIN sales s ON s.category = c.category AND s.week = w.week
    ORDER BY c.category, w.week
    """,
]

engine = get_engine()

with engine.begin() as conn:
    for sql in STEPS:
        conn.execute(text(sql))

with engine.connect() as conn:
    rows, weeks, cats, zeros, total = conn.execute(text("""
        SELECT count(*), count(DISTINCT week), count(DISTINCT category),
               count(*) FILTER (WHERE units = 0), sum(units)
        FROM features.weekly_category_units
    """)).one()
    expected = conn.execute(text(f"""
        SELECT count(*) FROM clean.order_items
        WHERE purchased_at >= '{FIRST_WEEK}' AND purchased_at < '2018-08-20'
    """)).scalar()

print(f"rows: {rows:,}   weeks: {weeks}   categories: {cats}")
print(f"cells with zero sales: {zeros:,} ({zeros / rows:.0%})")
print(f"units in weekly table: {total:,}   units in clean.order_items for the same dates: {expected:,}")
print("units match" if total == expected else "WARNING: units do not match")