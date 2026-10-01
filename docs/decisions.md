# Project decisions

## Data scope
- Dataset: Olist Brazilian e-commerce (9 CSV files).
- Usable period: 2017-01-01 to 2018-08-31. Before and after that, order counts are near zero.
- Dropped orders with status `canceled` or `unavailable`. They are not real demand.
- Partial first and last weeks are dropped when building weekly data.
- `olist_geolocation_dataset.csv` (261,831 duplicate rows) is not used.

## Known data problems (quality checks must report these)
- 8 orders marked `delivered` have no delivery date.
- 610 products have no category, name, description or photo count.
- 2 products have no weight or size.

## Forecasting level
- 55% of products were sold only once. Only 286 products sold in 20+ weeks.
- Main forecast: weekly units per product category (71 categories).
- Second experiment: the 286 products with 20+ active weeks.
- Rare products: fallback to the category forecast.

## Known risks to test later
- Black Friday (Nov 2017) spike: 7,544 orders vs 4,631 the month before.
- Strong growth during 2017, so the past is not a stable guide to the future.
## Updates after exploring the weekly data
- There are 74 categories, not 71: 2 categories have no English translation, and `unknown` is the 74th.
- The last week of data (from 2018-08-20) is cut. Sales fade out to 16 units on 2018-08-29, so the data is incomplete.
- Weekly table: 85 full weeks (2017-01-02 to 2018-08-19), 74 categories.
- Metrics: MAE and WAPE. MAPE is not used because 31% of the cells are zero.
- Backtest: the last 20 weeks, one week ahead, training only on earlier weeks.
- Unexplained demand drop in the week of 2018-05-21 (about half of the previous week). All models fail there. The cause is not confirmed.
