import numpy as np
import pandas as pd

from db import get_engine

MODELS = ["last_week", "avg_4_weeks", "boosting", "blend"]
K_VALUES = [round(0.25 * i, 2) for i in range(0, 17)]   # 0, 0.25, ... 4
TARGET = 0.95   # the fill rate we want to reach

engine = get_engine()

# 1. Saved forecasts of all four models for the same 20 test weeks
base = pd.read_sql("SELECT * FROM features.baseline_backtest",
                   engine, parse_dates=["week"])
boost = pd.read_sql("SELECT * FROM features.model_backtest",
                    engine, parse_dates=["week"])
res = pd.concat([base, boost], ignore_index=True)

fc = res.pivot_table(index=["week", "category"], columns="model",
                     values="forecast")
fc["blend"] = fc[["last_week", "avg_4_weeks", "boosting"]].mean(axis=1)
fc["actual"] = res.groupby(["week", "category"])["actual"].first()
fc = fc.reset_index()

# 2. Same safety buffer as before: swing of the 8 weeks BEFORE each week
hist = pd.read_sql(
    "SELECT category, week, units FROM features.weekly_category_units",
    engine, parse_dates=["week"],
)
wide = hist.pivot(index="week", columns="category", values="units").sort_index()
buf = (wide.shift(1).rolling(8).std()
       .melt(ignore_index=False, var_name="category", value_name="buffer")
       .reset_index())
data = fc.merge(buf, on=["week", "category"]).dropna()

# 3. Replay every model at every k
rows = []
for model in MODELS:
    for k in K_VALUES:
        order = (data[model] + k * data["buffer"]).clip(lower=0)
        served = np.minimum(order, data["actual"])
        rows.append({
            "model": model,
            "k": k,
            "fill_rate": served.sum() / data["actual"].sum(),
            "leftover_pct": (order - served).sum() / order.sum(),
        })
grid = pd.DataFrame(rows)

print("Same safety setting (k = 1) for every model:")
print(grid[grid["k"] == 1.0].round(3).to_string(index=False))

print()
print(f"Smallest k that reaches a fill rate of {TARGET:.0%} (fair comparison):")
best = []
for model in MODELS:
    ok = grid[(grid["model"] == model) & (grid["fill_rate"] >= TARGET)]
    best.append(ok.iloc[0] if len(ok) else None)
out = pd.DataFrame([b for b in best if b is not None]).round(3)
print(out.to_string(index=False))

grid.to_sql("policy_comparison", engine, schema="features",
            if_exists="replace", index=False)
print()
print("saved features.policy_comparison")