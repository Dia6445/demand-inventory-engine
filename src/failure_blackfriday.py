from functools import reduce

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from db import get_engine

TEST_START, TEST_END = "2017-10-30", "2017-12-25"

engine = get_engine()
df = pd.read_sql(
    "SELECT category, week, units FROM features.weekly_category_units",
    engine, parse_dates=["week"],
)
wide = df.pivot(index="week", columns="category", values="units").sort_index()

hints = {
    "lag1": wide.shift(1),
    "lag2": wide.shift(2),
    "lag3": wide.shift(3),
    "lag4": wide.shift(4),
    "avg4": wide.shift(1).rolling(4).mean(),
    "avg8": wide.shift(1).rolling(8).mean(),
    "size": wide.shift(1).expanding().mean(),
    "buf": wide.shift(1).rolling(8).std(),
    "actual": wide,
}


def to_long(frame, name):
    return frame.melt(ignore_index=False, var_name="category",
                      value_name=name).reset_index()


data = reduce(lambda a, b: a.merge(b, on=["week", "category"]),
              [to_long(f, n) for n, f in hints.items()]).dropna()
FEATURES = ["lag1", "lag2", "lag3", "lag4", "avg4", "avg8", "size"]

weeks = wide.index[(wide.index >= TEST_START) & (wide.index <= TEST_END)]
rows = []
for week in weeks:
    train = data[data["week"] < week]
    test = data[data["week"] == week]
    model = HistGradientBoostingRegressor(
        loss="poisson", max_iter=200, learning_rate=0.05, random_state=0)
    model.fit(train[FEATURES], train["actual"])
    boost = model.predict(test[FEATURES]).clip(min=0)

    fc = {"last_week": test["lag1"].values,
          "avg_4_weeks": test["avg4"].values,
          "boosting": boost}
    fc["blend"] = (fc["last_week"] + fc["avg_4_weeks"] + fc["boosting"]) / 3

    actual = test["actual"].values
    row = {"week": week.date(), "units": int(actual.sum())}
    for name, f in fc.items():
        row[name] = np.abs(f - actual).sum() / actual.sum()
    order = fc["blend"] + 1.0 * test["buf"].values
    row["fill_k1"] = np.minimum(order, actual).sum() / actual.sum()
    row["stockout_share"] = (order < actual).mean()
    rows.append(row)

out = pd.DataFrame(rows).set_index("week")
print("WAPE per week (lower is better), plus the order rule with k = 1:")
print(out.round(3).to_string())