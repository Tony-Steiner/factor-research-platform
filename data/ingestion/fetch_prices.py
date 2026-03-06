import pandas as pd
import yfinance as yf
import requests
from io import StringIO
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
from config.settings import engine

try:
    with engine.connect() as connection:
        print("Successfully connected to the PostgreSQL database.")
except Exception as e:
    print(f"Connection failed: {e}")

# 1. Get S&P 500 tickers from Wikipedia
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

resp = requests.get(url, headers=headers, timeout=30)
resp.raise_for_status()  # Check if the request was successful

tables = pd.read_html(StringIO(resp.text))
sp500 = tables[0]  # The first table contains the S&P 500 companies
tickers = (
    sp500["Symbol"].str.replace(".", "-", regex=False).tolist()
)  # Convert to list and replace '.' with '-' for yfinance compatibility
print(tickers[:10], len(tickers))

# 2. Fetch historical price data for each ticker
ok = []
failed = {}

for t in tickers:
    try:
        df = yf.download(t, period="5y", interval="1d", progress=False)
        if df.empty:
            failed[t] = "empty"
            continue

        if isinstance(
            df.columns, pd.MultiIndex
        ):  # Built-in Python function that checks the data type of an object. Here, it verifies whether the columns are formatted as a pd.MultiIndex instead of a standard flat index.
            df.columns = df.columns.get_level_values(
                0
            )  # .get_level_values(0) is a method used to extract the first level of column names from a MultiIndex. This effectively flattens the columns, making them easier to work with.
        # require core columns
        required = {
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        }  # This is a Python set. Sets are unordered collections of unique elements.
        if not required.issubset(
            df.columns
        ):  # .issubset() is a built-in Python set method. It checks if every single element in the 'required' set is present in the df.columns iterable.
            failed[t] = f"missing columns: {required - set(df.columns)}"
            continue

        # drop rows with all NaNs in price columns
        df = df.dropna(subset=["Open", "High", "Low", "Close"])
        if df.empty:
            failed[t] = "all NaNs"
            continue
        df["ticker"] = t
        ok.append(df)
    except Exception as e:
        failed[t] = str(e)

data = pd.concat(ok) if ok else pd.DataFrame()

# 3. Insert data into PostgreSQL
data.reset_index(inplace=True)
data.columns = data.columns.str.lower()

with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE daily_prices;"))  # Clear existing data

data.to_sql("daily_prices", engine, if_exists="append", index=False)
