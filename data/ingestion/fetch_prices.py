import pandas as pd
import yfinance as yf
import yfinance.shared as shared
from sqlalchemy import text
from config.settings import get_engine, get_tickers

try:
    with get_engine().connect() as connection:
        print("Successfully connected")
except Exception as e:
    print(f"Connection failed: {e}")

tickers = get_tickers()

data = yf.download(tickers, start ='2021-01-01' , end = '2026-06-01', interval = '1d', group_by = 'ticker', auto_adjust = True)
if shared._ERRORS:
    print(f"Failed to download the following tickers: {list(shared._ERRORS.keys())}")

ok = []
failed = []
for t in tickers:
    df = data[t].reset_index()
    df.columns = df.columns.str.lower()
    df['ticker'] = t
    df = df.dropna(subset = ['open','high', 'low', 'close'])
    if df.empty:
        failed.append(t)
    else:
        ok.append(df)

data_clean = pd.concat(ok)
data_clean.columns.name =None

if failed:
    print(f"Empty after dropping NaN prices: {failed}")

with get_engine().begin() as conn:
    conn.execute(text('TRUNCATE TABLE daily_prices;'))

data_clean.to_sql("daily_prices", get_engine(), if_exists = 'append', index = False)