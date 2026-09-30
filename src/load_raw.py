from pathlib import Path
import pandas as pd
from sqlalchemy import text

from db import get_engine

RAW = Path("data/raw")
SKIP = {"olist_geolocation_dataset.csv"}  # not used, see docs/decisions.md

engine = get_engine()

with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))

for path in sorted(RAW.glob("*.csv")):
    if path.name in SKIP:
        print(f"skipped {path.name}")
        continue
    table = path.stem.replace("olist_", "").replace("_dataset", "")
    df = pd.read_csv(path)
    df.to_sql(table, engine, schema="raw", if_exists="replace",
              index=False, chunksize=10_000)
    print(f"loaded raw.{table}: {len(df):,} rows")