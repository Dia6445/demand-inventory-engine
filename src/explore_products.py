from pathlib import Path
import pandas as pd

RAW = Path("data/raw")

orders = pd.read_csv(
    RAW / "olist_orders_dataset.csv",
    parse_dates=["order_purchase_timestamp"],
)
items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
products = pd.read_csv(RAW / "olist_products_dataset.csv")
names = pd.read_csv(RAW / "product_category_name_translation.csv")

# keep real sales in the usable date range
orders = orders[~orders["order_status"].isin(["canceled", "unavailable"])]
orders = orders[
    (orders["order_purchase_timestamp"] >= "2017-01-01")
    & (orders["order_purchase_timestamp"] < "2018-09-01")
]

df = items.merge(orders[["order_id", "order_purchase_timestamp"]], on="order_id")
df["week"] = df["order_purchase_timestamp"].dt.to_period("W")

total_weeks = df["week"].nunique()
print(f"rows kept: {len(df):,}   weeks in range: {total_weeks}")

units = df.groupby("product_id").size()
active_weeks = df.groupby("product_id")["week"].nunique()

print()
print("products with sales in at least N weeks:")
for n in (5, 10, 20, 40):
    good = active_weeks[active_weeks >= n].index
    share = units[good].sum() / units.sum()
    print(f"  {n:>2} weeks: {len(good):>5,} products, {share:.0%} of all units sold")

print()
df = df.merge(products[["product_id", "product_category_name"]], on="product_id")
df = df.merge(names, on="product_category_name", how="left")
print(f"categories: {df['product_category_name_english'].nunique()}")
print("top 10 categories by units sold:")
print(df["product_category_name_english"].value_counts().head(10).to_string())
