import pandas as pd

from db import get_engine

K_VALUES = [0, 0.5, 1, 1.5, 2, 3]   # how much safety buffer to add

engine = get_engine()

# 1. The blend forecasts we already saved, for the same 20 test weeks
base = pd.read_sql("SELECT * FROM features.baseline_backtest",
                   engine, parse_dates=["week"])
boost = pd.read_sql("SELECT * FROM features.model_backtest",
                    engine, parse_dates=["week"])
res = pd.concat([base, boost], ignore_index=True)

fc = res.pivot_table(index=["week", "category"], columns="model",
                     values="forecast")
fc["blend"] = fc[["last_week", "avg_4_weeks", "boosting"]].mean(axis=1)
fc["actual"] = res.groupby(["week", "category"])["actual"].first()
fc = fc.reset_index()[["week", "category", "blend", "actual"]]

# 2. Safety buffer: how much the category swung in the 8 weeks BEFORE each week
hist = pd.read_sql(
    "SELECT category, week, units FROM features.weekly_category_units",
    engine, parse_dates=["week"],
)
wide = hist.pivot(index="week", columns="category", values="units").sort_index()
buffer = wide.shift(1).rolling(8).std()
buf = buffer.melt(ignore_index=False, var_name="category",
                  value_name="buffer").reset_index()

data = fc.merge(buf, on=["week", "category"]).dropna()


def evaluate(frame):
    rows = []
    for k in K_VALUES:
        order = (frame["blend"] + k * frame["buffer"]).clip(lower=0)
        served = order.combine(frame["actual"], min)
        leftover = (order - served).sum()
        rows.append({
            "k": k,
            "fill_rate": served.sum() / frame["actual"].sum(),
            "stockout_share": (order < frame["actual"]).mean(),
            "leftover_units": leftover,
            "leftover_pct_of_order": leftover / order.sum(),
        })
    return pd.DataFrame(rows).round(3)


print("All categories (fill_rate = share of demand served):")
all_res = evaluate(data)
print(all_res.to_string(index=False))

top10 = data.groupby("category")["actual"].sum().nlargest(10).index
print()
print("10 biggest categories only:")
print(evaluate(data[data["category"].isin(top10)]).to_string(index=False))

all_res.to_sql("decision_results", engine, schema="features",
               if_exists="replace", index=False)
print()
print("saved features.decision_results")