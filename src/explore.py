from pathlib import Path
import pandas as pd

RAW = Path("data/raw")

for path in sorted(RAW.glob("*.csv")):
    df = pd.read_csv(path)
    print("=" * 60)
    print(path.name)
    print(f"rows: {len(df):,}   columns: {len(df.columns)}")
    print(f"fully duplicated rows: {df.duplicated().sum():,}")
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if missing.empty:
        print("missing values: none")
    else:
        print("missing values per column:")
        print(missing.to_string())