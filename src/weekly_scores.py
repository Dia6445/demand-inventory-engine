import pandas as pd

from db import get_engine

engine = get_engine()

base = pd.read_sql("SELECT * FROM features.baseline_backtest",
                   engine, parse_dates=["week"])
boost = pd.read_sql("SELECT * FROM features.model_backtest",
                    engine, parse_dates=["week"])
res = pd.concat([base, boost], ignore_index=True)

wide = res.pivot_table(index=["week", "category"], columns="model",
                       values="forecast")
wide["blend"] = wide[["last_week", "avg_4_weeks", "boosting"]].mean(axis=1)
wide["actual"] = res.groupby(["week", "category"])["actual"].first()
wide = wide.reset_index()

MODELS = ["last_week", "avg_4_weeks", "boosting", "blend"]

# WAPE per week: total miss in that week / total units sold in that week
rows = []
for week, g in wide.groupby("week"):
    row = {"week": week.date()}
    for m in MODELS:
        row[m] = (g[m] - g["actual"]).abs().sum() / g["actual"].sum()
    rows.append(row)

weekly = pd.DataFrame(rows).set_index("week")

print("WAPE per week (lower is better):")
print(weekly.round(3).to_string())

print()
print("weeks won (lowest WAPE of the 4 models):")
print(weekly.idxmin(axis=1).value_counts().to_string())

print()
print("blend vs last_week:")
better = (weekly["blend"] < weekly["last_week"]).sum()
print(f"  blend beat last_week in {better} of {len(weekly)} weeks")