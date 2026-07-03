import pandas as pd
import pandera.pandas as pa
from config.settings import get_engine, get_tickers

# ── Configuration ─────────────────────────────────────────────────────────────
MIN_PRICE_ROWS = 750  # ~3 years of trading days

# ── Helper ────────────────────────────────────────────────────────────────────
def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ── Load tables ───────────────────────────────────────────────────────────────
df_prices = pd.read_sql('SELECT * FROM daily_prices', get_engine())
df_fundamentals = pd.read_sql('SELECT * FROM fundamentals', get_engine())
df_factors = pd.read_sql('SELECT * FROM ff_factors', get_engine())

# ═════════════════════════════════════════════════════════════════════════════
section("1. TABLE OVERVIEW")
# ═════════════════════════════════════════════════════════════════════════════

for name, df in [('daily_prices', df_prices), ('fundamentals', df_fundamentals), ('ff_factors', df_factors)]:
    print(f"\n  {name}:")
    print(f"    Rows:    {len(df):,}")
    print(f"    Columns: {list(df.columns)}")
    print(f"    NaNs:    {df.isna().sum().sum():,}")

# ═════════════════════════════════════════════════════════════════════════════
section("2. DAILY PRICES — COMPLETENESS")
# ═════════════════════════════════════════════════════════════════════════════

counts_prices = df_prices.groupby('ticker').size().sort_values()
mode_count = counts_prices.mode().iloc[0]
low_row_count = counts_prices[counts_prices <= MIN_PRICE_ROWS].index.tolist()
kept_but_incomplete = counts_prices[(counts_prices > MIN_PRICE_ROWS) & (counts_prices < mode_count)].index.tolist()

print(f"\n  Most common row count:           {mode_count:,}")
print(f"  Tickers below threshold ({MIN_PRICE_ROWS}):  {len(low_row_count)}")
print(f"  Kept but incomplete:             {len(kept_but_incomplete)}")
if low_row_count:
    print(f"\n  Excluded tickers: {low_row_count}")

# ═════════════════════════════════════════════════════════════════════════════
section("3. DAILY PRICES — OUTLIERS (Pandera)")
# ═════════════════════════════════════════════════════════════════════════════

df_prices = df_prices.sort_values(['ticker', 'date']).reset_index(drop=True)
df_prices['daily_return'] = df_prices.groupby('ticker')['close'].pct_change()

schema_prices = pa.DataFrameSchema({
    'close': pa.Column(float, pa.Check.gt(0)),
    'daily_return': pa.Column(float, pa.Check(lambda x: x.abs() < 5), nullable=True),
})

try:
    schema_prices.validate(df_prices[['close', 'daily_return']], lazy=True)
    print("\n  Validation passed: no zero closes or extreme returns.")
except pa.errors.SchemaErrors as e:
    print(f"\n  {len(e.failure_cases)} violations found:")
    print(e.failure_cases)

# ═════════════════════════════════════════════════════════════════════════════
section("4. FUNDAMENTALS — COMPLETENESS")
# ═════════════════════════════════════════════════════════════════════════════

counts_fund = df_fundamentals.groupby('ticker').size()
fund_mode = counts_fund.mode().iloc[0]

print(f"\n  Most common quarter count:       {fund_mode}")
print(f"  Tickers with < 8 quarters:       {(counts_fund < 8).sum()}")
print(f"  Tickers with < 20 quarters:      {(counts_fund < 20).sum()}")
print(f"  Date range:                      {df_fundamentals['report_date'].min()} to {df_fundamentals['report_date'].max()}")

# ═════════════════════════════════════════════════════════════════════════════
section("5. FUNDAMENTALS — SUSPICIOUS VALUES (Pandera)")
# ═════════════════════════════════════════════════════════════════════════════

schema_fund = pa.DataFrameSchema({
    'total_revenue': pa.Column(float, pa.Check.ge(0), nullable=True),
})

try:
    schema_fund.validate(df_fundamentals[['total_revenue']], lazy=True)
    print("\n  Validation passed: no negative revenue.")
except pa.errors.SchemaErrors as e:
    print(f"\n  {len(e.failure_cases)} negative revenue rows found:")
    print(e.failure_cases)

# ═════════════════════════════════════════════════════════════════════════════
section("6. CROSS-TABLE ALIGNMENT")
# ═════════════════════════════════════════════════════════════════════════════

price_tickers = set(df_prices['ticker'].unique())
fund_tickers = set(df_fundamentals['ticker'].unique())

print(f"\n  Tickers in both tables:          {len(price_tickers & fund_tickers)}")
print(f"  Only in daily_prices:            {len(price_tickers - fund_tickers)}")
print(f"  Only in fundamentals:            {len(fund_tickers - price_tickers)}")

# ═════════════════════════════════════════════════════════════════════════════
section("7. FAMA-FRENCH FACTORS (Pandera)")
# ═════════════════════════════════════════════════════════════════════════════

df_factors['date'] = pd.to_datetime(df_factors['date'])

schema_factors = pa.DataFrameSchema({
    'date': pa.Column(pa.DateTime, unique=True),
    'mkt_rf': pa.Column(float, pa.Check.in_range(-30, 30)),
    'smb':    pa.Column(float, pa.Check.in_range(-30, 30)),
    'hml':    pa.Column(float, pa.Check.in_range(-30, 30)),
    'rf':     pa.Column(float, pa.Check.in_range(-30, 30)),
    'umd':    pa.Column(float, pa.Check.in_range(-30, 30)),
})

print(f"\n  Rows: {len(df_factors):,}")

try:
    schema_factors.validate(df_factors, lazy=True)
    print("  Validation passed: all factors in expected range.")
except pa.errors.SchemaErrors as e:
    print(f"\n  {len(e.failure_cases)} violations found:")
    print(e.failure_cases)

# ═════════════════════════════════════════════════════════════════════════════
section("8. USABLE UNIVERSE SUMMARY")
# ═════════════════════════════════════════════════════════════════════════════

price_ok_tickers = set(counts_prices[counts_prices >= MIN_PRICE_ROWS].index)
usable_universe = price_ok_tickers & fund_tickers

print(f"\n  Tickers passing price threshold:  {len(price_ok_tickers)}")
print(f"  Also in fundamentals:             {len(usable_universe)}")
print(f"\n  FINAL USABLE UNIVERSE:            {len(usable_universe)} tickers")
print(f"  Price-only factors can use:       {len(price_ok_tickers)}")
print(f"  Fundamental factors limited to:   {len(usable_universe)}")

section("VALIDATION COMPLETE")