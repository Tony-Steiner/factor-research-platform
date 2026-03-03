"""
Data Quality Validation Report
==============================
Runs all validation checks against daily_prices, fundamentals, and ff_factors
tables, then prints a structured report summarizing data health and issues.

Usage: python data/quality/validate.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ── Connection ────────────────────────────────────────────────────────────────

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

connection_url = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(connection_url)

# ── Configuration ─────────────────────────────────────────────────────────────

MIN_PRICE_ROWS = 750  # ~3 years of trading days; tickers below this are excluded

# ── Helper ────────────────────────────────────────────────────────────────────


def section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── Load tables ───────────────────────────────────────────────────────────────

df_prices = pd.read_sql("SELECT * FROM daily_prices", engine)
df_fundamentals = pd.read_sql("SELECT * FROM fundamentals", engine)
df_ff = pd.read_sql("SELECT * FROM ff_factors", engine)

# ══════════════════════════════════════════════════════════════════════════════
#  1. OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

section("1. TABLE OVERVIEW")

for name, df in [
    ("daily_prices", df_prices),
    ("fundamentals", df_fundamentals),
    ("ff_factors", df_ff),
]:
    print(f"\n  {name}:")
    print(f"    Rows:    {len(df):,}")
    print(f"    Columns: {list(df.columns)}")
    print(f"    NaNs:    {df.isna().sum().sum()}")

# ══════════════════════════════════════════════════════════════════════════════
#  2. DAILY PRICES — COMPLETENESS
# ══════════════════════════════════════════════════════════════════════════════

section("2. DAILY PRICES — COMPLETENESS")

counts_prices = df_prices.groupby("ticker").size().sort_values()
mode_count = counts_prices.mode().iloc[0]
incomplete = counts_prices[counts_prices < MIN_PRICE_ROWS]
short_but_ok = counts_prices[
    (counts_prices < mode_count) & (counts_prices >= MIN_PRICE_ROWS)
]

print(f"\n  Total tickers:        {counts_prices.nunique()}")
print(f"  Expected row count:   {mode_count} (mode)")
print(f"  Min threshold:        {MIN_PRICE_ROWS}")
print(f"  Tickers below threshold ({MIN_PRICE_ROWS}): {len(incomplete)}")

if len(incomplete) > 0:
    print(f"\n  EXCLUDED (< {MIN_PRICE_ROWS} rows):")
    for ticker, count in incomplete.items():
        print(f"    {ticker:<8} {count:>5} rows")

if len(short_but_ok) > 0:
    print(f"\n  KEPT but incomplete (>= {MIN_PRICE_ROWS}, < {mode_count}):")
    for ticker, count in short_but_ok.items():
        print(f"    {ticker:<8} {count:>5} rows")

# ══════════════════════════════════════════════════════════════════════════════
#  3. DAILY PRICES — OUTLIERS
# ══════════════════════════════════════════════════════════════════════════════

section("3. DAILY PRICES — OUTLIERS")

df_p = df_prices.sort_values(["ticker", "date"]).copy()
df_p["daily_return"] = df_p.groupby("ticker")["close"].pct_change()

zero_close = df_p[df_p["close"] == 0]
extreme_returns = df_p[df_p["daily_return"].abs() > 5]  # > 500%

print(f"\n  Zero close prices:      {len(zero_close)}")
print(f"  Extreme returns (>500%): {len(extreme_returns)}")

if len(zero_close) > 0:
    print("\n  Zero close rows:")
    print(zero_close[["ticker", "date", "close"]].to_string(index=False))

if len(extreme_returns) > 0:
    print("\n  Extreme return rows:")
    print(
        extreme_returns[["ticker", "date", "close", "daily_return"]].to_string(
            index=False
        )
    )

# ══════════════════════════════════════════════════════════════════════════════
#  4. FUNDAMENTALS — COMPLETENESS
# ══════════════════════════════════════════════════════════════════════════════

section("4. FUNDAMENTALS — COMPLETENESS")

counts_fund = df_fundamentals.groupby("ticker").size().sort_values()
mode_fund = counts_fund.mode().iloc[0]
mismatched_fund = counts_fund[counts_fund != mode_fund]

print(f"\n  Total tickers:        {len(counts_fund)}")
print(f"  Expected quarters:    {mode_fund} (mode)")
print(f"  Tickers with fewer:   {len(mismatched_fund)}")

if len(mismatched_fund) > 0:
    print(f"\n  Incomplete fundamental data:")
    for ticker, count in mismatched_fund.items():
        print(f"    {ticker:<8} {count:>2} quarters")

# date range
min_date = df_fundamentals["report_date"].min()
max_date = df_fundamentals["report_date"].max()
print(f"\n  Date range: {min_date} to {max_date}")

# ══════════════════════════════════════════════════════════════════════════════
#  5. FUNDAMENTALS — SUSPICIOUS VALUES
# ══════════════════════════════════════════════════════════════════════════════

section("5. FUNDAMENTALS — SUSPICIOUS VALUES")

neg_revenue = df_fundamentals[df_fundamentals["total_revenue"] < 0]

print(f"\n  Negative revenue rows: {len(neg_revenue)}")

if len(neg_revenue) > 0:
    print()
    for _, row in neg_revenue.iterrows():
        print(
            f"    {row['ticker']:<8} {row['report_date']}  revenue = {row['total_revenue']:>15,.2f}"
        )

# ══════════════════════════════════════════════════════════════════════════════
#  6. CROSS-TABLE ALIGNMENT
# ══════════════════════════════════════════════════════════════════════════════

section("6. CROSS-TABLE ALIGNMENT")

price_tickers = set(df_prices["ticker"].str.upper().str.strip().unique())
fund_tickers = set(df_fundamentals["ticker"].str.upper().str.strip().unique())

in_both = price_tickers & fund_tickers
only_prices = price_tickers - fund_tickers
only_fund = fund_tickers - price_tickers

print(f"\n  Tickers in both tables:          {len(in_both)}")
print(f"  Only in daily_prices:            {len(only_prices)}")
print(f"  Only in fundamentals:            {len(only_fund)}")

if only_prices:
    print(f"\n  Missing from fundamentals: {sorted(only_prices)}")
if only_fund:
    print(f"\n  Missing from daily_prices: {sorted(only_fund)}")

# ══════════════════════════════════════════════════════════════════════════════
#  7. FAMA-FRENCH FACTORS
# ══════════════════════════════════════════════════════════════════════════════

section("7. FAMA-FRENCH FACTORS")

print(f"\n  Rows:       {len(df_ff):,}")
print(f"  Date range: {df_ff['date'].min()} to {df_ff['date'].max()}")
print(f"  NaNs:       {df_ff.isna().sum().sum()}")

# ══════════════════════════════════════════════════════════════════════════════
#  8. USABLE UNIVERSE SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

section("8. USABLE UNIVERSE SUMMARY")

# Tickers that pass price completeness AND exist in fundamentals
usable_price_tickers = set(counts_prices[counts_prices >= MIN_PRICE_ROWS].index)
usable_universe = usable_price_tickers & fund_tickers

print(
    f"\n  Tickers passing price threshold ({MIN_PRICE_ROWS}): {len(usable_price_tickers)}"
)
print(f"  Of those, also in fundamentals:            {len(usable_universe)}")
print(f"\n  FINAL USABLE UNIVERSE: {len(usable_universe)} tickers")
print(f"\n  NOTE: Price-only factors (momentum, volatility, size) can use")
print(f"  the full {len(usable_price_tickers)} tickers. Fundamental-dependent factors")
print(f"  (value, quality) are limited to {len(usable_universe)} tickers with")
print(f"  {mode_fund} quarters of data ({min_date} to {max_date}).")

# ══════════════════════════════════════════════════════════════════════════════

section("VALIDATION COMPLETE")
print()
