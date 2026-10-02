import pandas as pd

from db import get_engine

TEST_WEEKS = 20     # same last 20 weeks as before
MIN_ACTIVE = 15     # product must have sold in at least 15 of the training weeks

engine = get_engine()
sales = pd.read_sql("""
    SELECT i.product_id, p.category,
           date_trunc('week', i.purchased_at)::date AS week,
           count(*) AS units
    FROM clean.order_items i
    JOIN clean.products p ON p.product_id = i.product_id
    WHERE i.purchased_at >= '2017-01-02' AND i.purchased_at < '2018-08-20'
    GROUP BY 1, 2, 3
""", engine, parse_dates=["week"])

weeks = pd.date_range("2017-01-02", "2018-08-13", freq="7D")
wide = (sales.pivot_table(index="week", columns="product_id",
                          values="units", aggfunc="sum")
        .reindex(weeks).fillna(0))
cat_of = sales.drop_duplicates("product_id").set_index("product_id")["category"]
cat_of = cat_of.reindex(wide.columns)
cat_wide = wide.T.groupby(cat_of).sum().T   # weekly units per category

# Choose products using TRAINING weeks only, so the test stays honest.
train_end = len(weeks) - TEST_WEEKS
active = (wide.iloc[:train_end] > 0).sum()
selected = active[active >= MIN_ACTIVE].index
sel_cats = cat_of[selected].values

test_units = wide.iloc[train_end:].sum()
print(f"products selected: {len(selected)} of {wide.shape[1]:,}")
print(f"share of test-period units they cover: "
      f"{test_units[selected].sum() / test_units.sum():.0%}")
print()

rows = []
for t in range(train_end, len(weeks)):
    hist = wide.iloc[:t][selected]
    actual = wide.iloc[t][selected]
    cat_hist = cat_wide.iloc[:t]

    # fallback idea: category forecast x the product's share of its category
    share = hist.sum().values / cat_hist.sum().reindex(sel_cats).values
    cat_fc = cat_hist.iloc[-4:].mean().reindex(sel_cats).values

    forecasts = {
        "last_week": hist.iloc[-1].values,
        "avg_4_weeks": hist.iloc[-4:].mean().values,
        "avg_12_weeks": hist.iloc[-12:].mean().values,
        "category_share": cat_fc * share,
        "always_zero": 0 * actual.values,
    }
    for name, f in forecasts.items():
        rows.append(pd.DataFrame({
            "model": name, "week": weeks[t],
            "product_id": selected, "actual": actual.values, "forecast": f,
        }))

res = pd.concat(rows, ignore_index=True)
res["abs_error"] = (res["forecast"] - res["actual"]).abs()

s = res.groupby("model").agg(MAE=("abs_error", "mean"),
                             err=("abs_error", "sum"),
                             act=("actual", "sum"))
s["WAPE"] = s["err"] / s["act"]
print("Product-level backtest (lower is better):")
print(s[["MAE", "WAPE"]].round(3).sort_values("WAPE").to_string())

res.to_sql("product_backtest", engine, schema="features",
           if_exists="replace", index=False)
print()
print("saved features.product_backtest")