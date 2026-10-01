import pandas as pd

from db import get_engine

engine = get_engine()

RANGES = {
    "Around week 2018-05-21": ("2018-05-14", "2018-06-04"),
    "Around week 2018-08-20": ("2018-08-13", "2018-09-01"),
}

for title, (start, end) in RANGES.items():
    daily = pd.read_sql(f"""
        SELECT purchased_at::date AS day,
               to_char(purchased_at, 'Dy') AS weekday,
               count(*) AS units
        FROM clean.order_items
        WHERE purchased_at >= '{start}' AND purchased_at < '{end}'
        GROUP BY 1, 2 ORDER BY 1
    """, engine)
    print("=" * 40)
    print(title)
    print(daily.to_string(index=False))
    print()