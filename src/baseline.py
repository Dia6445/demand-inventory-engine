import pandas as pd

from db import get_engine

TEST_WEEKS = 20  # how many of the most recent weeks we predict, one at a time

engine = get_engine()
df = pd.read_sql(
    "SELECT category, week, units FROM features.weekly_category_units",
    engine, parse_dates=["week"],
)
wide = df.pivot(index="week", columns="category", values="units").sort_index()

results = []
for t in range(len(wide) - TEST_WEEKS, len(wide)):
    history = wide.iloc[:t]   # only the past: weeks before week t
    actual = wide.iloc[t]     # what really sold in week t
    forecasts = {
        "last_week": history.iloc[-1],
        "avg_4_weeks": history.iloc[-4:].mean(),
    }
    for name, f in forecasts.items():
        results.append(pd.DataFrame({
            "model": name,
            "week": wide.index[t],
            "category": wide.columns,
            "actual": actual.values,
            "forecast": f.values,
        }))

res = pd.concat(results, ignore_index=True)
res["abs_error"] = (res["forecast"] - res["actual"]).abs()

print(f"test weeks: {res['week'].min().date()} to {res['week'].max().date()}")
print()


def summarize(frame):
    s = frame.groupby("model").agg(
        MAE=("abs_error", "mean"),
        error_sum=("abs_error", "sum"),
        actual_sum=("actual", "sum"),
    )
    s["WAPE"] = s["error_sum"] / s["actual_sum"]
    return s[["MAE", "WAPE"]].round(3)


print("All 74 categories:")
print(summarize(res).to_string())

top10 = res.groupby("category")["actual"].sum().nlargest(10).index
print()
print("10 biggest categories only:")
print(summarize(res[res["category"].isin(top10)]).to_string())

res.to_sql("baseline_backtest", engine, schema="features",
           if_exists="replace", index=False)
print()
print("saved features.baseline_backtest")