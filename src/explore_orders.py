from pathlib import Path
import pandas as pd

RAW = Path("data/raw")

orders = pd.read_csv(
    RAW / "olist_orders_dataset.csv",
    parse_dates=["order_purchase_timestamp"],
)
items = pd.read_csv(RAW / "olist_order_items_dataset.csv")

print("order status counts:")
print(orders["order_status"].value_counts().to_string())

print()
print("first order:", orders["order_purchase_timestamp"].min())
print("last order: ", orders["order_purchase_timestamp"].max())

print()
print("orders per month:")
monthly = orders.groupby(orders["order_purchase_timestamp"].dt.to_period("M")).size()
print(monthly.to_string())

print()
print("missing delivery date, by order status:")
no_delivery = orders[orders["order_delivered_customer_date"].isna()]
print(no_delivery["order_status"].value_counts().to_string())

print()
print("items sold per product:")
per_product = items.groupby("product_id").size()
print(per_product.describe().to_string())
print(f"products sold only once: {(per_product == 1).sum():,}")