import yfinance as yf
import pandas as pd
import os
import requests
from io import StringIO
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from config.settings import engine, fetch_financial_statements

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


# 2. Fetch quarterly income statements and balance sheets for each ticker
required_stmt = {"Total Revenue", "Net Income"}
ok_stmt, failed_stmt = fetch_financial_statements(
    tickers, required_stmt, "quarterly_income_stmt"
)
data_stmt = pd.concat(ok_stmt) if ok_stmt else pd.DataFrame()

required_sheet = {"Stockholders Equity", "Total Debt", "Ordinary Shares Number"}
ok_sheet, failed_sheet = fetch_financial_statements(
    tickers, required_sheet, "quarterly_balance_sheet"
)
data_sheet = pd.concat(ok_sheet) if ok_sheet else pd.DataFrame()

# 3. Merge the two datasets on ticker and report_date
data = pd.merge(data_stmt, data_sheet, on=["ticker", "report_date"], how="inner")

# 4. Write the merged dataset to the PostgreSQL database OR update existing records
existing = pd.read_sql('SELECT DISTINCT ticker, report_date FROM fundamentals', engine)

new_data = data.merge(existing, on = ['ticker', 'report_date'], how = 'left', indicator = True)
new_records = new_data[new_data['_merge'] == 'left_only'].drop(columns='_merge')

new_records.to_sql('fundamentals', engine, if_exists = 'append', index = False)
print(f'Added {len(new_records)} new rows, skipped {len(data) - len(new_records)} existing rows')
