from functools import reduce

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from db import get_engine

TEST_WEEKS = 20  # same last 20 weeks as the baselines

engine = get_engine()
df = pd.read_sql(
    "SELECT category, week, units FROM features.weekly_category_units",
    engine, parse_dates=["week"],
)
wide = df.pivot(index="week", columns="category", values="units").sort_index()

# Hints for each (week, category). Every hint uses only weeks BEFORE that week.
hints = {
    "lag1": wide.shift(1),
    "lag2": wide.shift(2),
    "lag3": wide.shift(3),
    "lag4": wide.shift(4),
    "avg4": wide.shift(1).rolling(4).mean(),
    "avg8": wide.shift(1).rolling(8).mean(),
    "size": wide.shift(1).expanding().mean(),  # category's average size so far
    "actual": wide,
}


def to_long(frame, name):
    out = frame.melt(ignore_index=False, var_name="category", value_name=name)
    return out.reset_index()


data = reduce(
    lambda a, b: a.merge(b, on=["week", "category"]),
    [to_long(f, n) for n, f in hints.items()],
).dropna()

FEATURES = ["lag1", "lag2", "lag3", "lag4", "avg4", "avg8", "size"]

rows = []
for week in wide.index[-TEST_WEEKS:]:
    train = data[data["week"] < week]   # only the past
    test = data[data["week"] == week]   # the week we predict
    model = HistGradientBoostingRegressor(
        loss="poisson", max_iter=200, learning_rate=0.05, random_state=0
    )
    model.fit(train[FEATURES], train["actual"])
    pred = model.predict(test[FEATURES]).clip(min=0)
    rows.append(pd.DataFrame({
        "model": "boosting", "week": week, "category": test["category"].values,
        "actual": test["actual"].values, "forecast": pred,
    }))

boost = pd.concat(rows, ignore_index=True)
boost["abs_error"] = (boost["forecast"] - boost["actual"]).abs()
boost.to_sql("model_backtest", engine, schema="features",
             if_exists="replace", index=False)

base = pd.read_sql("SELECT * FROM features.baseline_backtest",
                   engine, parse_dates=["week"])
res = pd.concat([base, boost], ignore_index=True)


def summarize(frame):
    s = frame.groupby("model").agg(
        MAE=("abs_error", "mean"),
        error_sum=("abs_error", "sum"),
        actual_sum=("actual", "sum"),
    )
    s["WAPE"] = s["error_sum"] / s["actual_sum"]
    return s[["MAE", "WAPE"]].round(3)


print(f"test weeks: {res['week'].min().date()} to {res['week'].max().date()}")
print()
print("All categories:")
print(summarize(res).to_string())

top10 = res.groupby("category")["actual"].sum().nlargest(10).index
print()
print("10 biggest categories only:")
print(summarize(res[res["category"].isin(top10)]).to_string())

print()
print("saved features.model_backtest")