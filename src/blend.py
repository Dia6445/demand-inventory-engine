import pandas as pd

from db import get_engine

engine = get_engine()

base = pd.read_sql("SELECT * FROM features.baseline_backtest",
                   engine, parse_dates=["week"])
boost = pd.read_sql("SELECT * FROM features.model_backtest",
                    engine, parse_dates=["week"])
res = pd.concat([base, boost], ignore_index=True)

# one column per model, one row per (week, category)
wide = res.pivot_table(index=["week", "category"], columns="model",
                       values="forecast")
actual = res.groupby(["week", "category"])["actual"].first()

wide["blend"] = wide[["last_week", "avg_4_weeks", "boosting"]].mean(axis=1)
wide["actual"] = actual
wide = wide.reset_index()

top10 = wide.groupby("category")["actual"].sum().nlargest(10).index


def score(frame):
    out = {}
    for model in ["last_week", "avg_4_weeks", "boosting", "blend"]:
        err = (frame[model] - frame["actual"]).abs()
        out[model] = {"MAE": err.mean(), "WAPE": err.sum() / frame["actual"].sum()}
    return pd.DataFrame(out).T.round(3)


print("All categories:")
print(score(wide).to_string())
print()
print("10 biggest categories only:")
print(score(wide[wide["category"].isin(top10)]).to_string())