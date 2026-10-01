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
}

engine = get_engine()

for title, sql in QUESTIONS.items():
    print("=" * 70)
    print(title)
    print(pd.read_sql(sql, engine).to_string(index=False))
    print()