import pandas as pd

from db import get_engine

QUESTIONS = {
    "1. Revenue per month (price only, without shipping)": """
        SELECT to_char(purchased_at, 'YYYY-MM') AS month,
               count(DISTINCT order_id) AS orders,
               round(sum(price)::numeric, 0) AS revenue
        FROM clean.order_items
        GROUP BY 1 ORDER BY 1
    """,
    "2. Top 10 categories by revenue": """
        SELECT p.category,
               count(*) AS units,
               round(sum(i.price)::numeric, 0) AS revenue
        FROM clean.order_items i
        JOIN clean.products p ON p.product_id = i.product_id
        GROUP BY 1 ORDER BY revenue DESC LIMIT 10
    """,
    "3. Top 10 products by units sold": """
        SELECT i.product_id, p.category,
               count(*) AS units,
               round(sum(i.price)::numeric, 0) AS revenue
        FROM clean.order_items i
        JOIN clean.products p ON p.product_id = i.product_id
        GROUP BY 1, 2 ORDER BY units DESC LIMIT 10
    """,
    "4. Most unstable categories (weekly units, variability = std / average)": """
        WITH weekly AS (
            SELECT p.category,
                   date_trunc('week', i.purchased_at) AS week,
                   count(*) AS units
            FROM clean.order_items i
            JOIN clean.products p ON p.product_id = i.product_id
            WHERE i.purchased_at >= '2017-01-02' AND i.purchased_at < '2018-08-27'
            GROUP BY 1, 2
        )
        SELECT category,
               count(*) AS active_weeks,
               round(avg(units), 1) AS avg_weekly_units,
               round((stddev(units) / avg(units))::numeric, 2) AS variability
        FROM weekly
        GROUP BY 1
        HAVING count(*) >= 40
        ORDER BY variability DESC LIMIT 10
    """,
    "5. Average delivery time per month (days)": """
        SELECT to_char(purchased_at, 'YYYY-MM') AS month,
               count(*) AS delivered_orders,
               round(avg(extract(epoch FROM delivered_at - purchased_at) / 86400)::numeric, 1) AS avg_days
        FROM clean.orders
        WHERE delivered_at IS NOT NULL
        GROUP BY 1 ORDER BY 1
    """,
    "6. Top 10 sellers by revenue and their share of the total": """
        SELECT seller_id,
               count(*) AS units,
               round(sum(price)::numeric, 0) AS revenue,
               round((100 * sum(price) / sum(sum(price)) OVER ())::numeric, 1) AS pct_of_total
        FROM clean.order_items
        GROUP BY 1 ORDER BY revenue DESC LIMIT 10
    """,
}

engine = get_engine()

for title, sql in QUESTIONS.items():
    print("=" * 70)
    print(title)
    print(pd.read_sql(sql, engine).to_string(index=False))
    print()