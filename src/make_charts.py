import matplotlib
matplotlib.use("Agg")  # draw to files, no window needed
import matplotlib.pyplot as plt
import pandas as pd

from db import get_engine

engine = get_engine()
OUT = "docs/charts"

# Chart 1: revenue per month
rev = pd.read_sql("""
    SELECT to_char(purchased_at, 'YYYY-MM') AS month,
           sum(price)::float AS revenue
    FROM clean.order_items
    GROUP BY 1 ORDER BY 1
""", engine)

fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(rev["month"], rev["revenue"] / 1000, marker="o")
ax.set_title("Revenue per month")
ax.set_ylabel("Revenue (thousands)")
ax.tick_params(axis="x", rotation=60)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(f"{OUT}/revenue_per_month.png", dpi=120)
plt.close(fig)

# Chart 2: weekly units for the 4 biggest categories (full weeks only)
weekly = pd.read_sql("""
    SELECT p.category,
           date_trunc('week', i.purchased_at)::date AS week,
           count(*) AS units
    FROM clean.order_items i
    JOIN clean.products p ON p.product_id = i.product_id
    WHERE i.purchased_at >= '2017-01-02' AND i.purchased_at < '2018-08-27'
    GROUP BY 1, 2
""", engine)

top = weekly.groupby("category")["units"].sum().nlargest(4).index
pivot = (weekly[weekly["category"].isin(top)]
         .pivot(index="week", columns="category", values="units")
         .fillna(0))

fig, ax = plt.subplots(figsize=(10, 4.5))
pivot.plot(ax=ax)
ax.set_title("Weekly units, top 4 categories")
ax.set_ylabel("Units per week")
ax.set_xlabel("")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(f"{OUT}/weekly_units_top_categories.png", dpi=120)
plt.close(fig)

# Chart 3: average delivery time per month
deliv = pd.read_sql("""
    SELECT to_char(purchased_at, 'YYYY-MM') AS month,
           avg(extract(epoch FROM delivered_at - purchased_at) / 86400)::float AS avg_days
    FROM clean.orders
    WHERE delivered_at IS NOT NULL
    GROUP BY 1 ORDER BY 1
""", engine)

fig, ax = plt.subplots(figsize=(10, 4.5))
ax.bar(deliv["month"], deliv["avg_days"])
ax.set_title("Average delivery time per month")
ax.set_ylabel("Days")
ax.tick_params(axis="x", rotation=60)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(f"{OUT}/delivery_time_per_month.png", dpi=120)
plt.close(fig)

print("saved 3 charts in", OUT)