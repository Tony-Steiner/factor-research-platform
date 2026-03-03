import yfinance as yf
import pandas as pd
import os
import requests
from io import StringIO
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

connection_url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(connection_url)

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
ok_stmt = []
failed_stmt = {}

ok_sheet = []
failed_sheet = {}

for t in tickers:
    ticker_obj = yf.Ticker(t)
    try:
        stmt_df = ticker_obj.quarterly_income_stmt
        if stmt_df.empty:
            failed_stmt[t] = "empty"
            continue

        required = {"Total Revenue", "Net Income"}
        if not required.issubset(stmt_df.index):

            failed_stmt[t] = f"missing rows: {required - set(stmt_df.index)}"
            continue

        df_stmt = stmt_df.loc[list(required)].T

        df_stmt = df_stmt.dropna(subset=["Total Revenue", "Net Income"])

        df_stmt = (
            df_stmt.reset_index()
        )  # Move the index (quarter-end dates) into a column
        df_stmt = df_stmt.rename(
            columns={"index": "report_date"}
        )  # Rename the new column to 'date'

        # standardize column names (lowercase, underscores)
        df_stmt.columns = [col.lower().replace(" ", "_") for col in df_stmt.columns]

        # Add ticker column
        df_stmt["ticker"] = t
        ok_stmt.append(df_stmt)

    except Exception as e:
        failed_stmt[t] = str(e)

    try:
        sheet_df = ticker_obj.quarterly_balance_sheet
        if sheet_df.empty:
            failed_sheet[t] = "empty"
            continue

        required = {"Stockholders Equity", "Total Debt", "Ordinary Shares Number"}
        if not required.issubset(sheet_df.index):

            failed_sheet[t] = f"missing rows: {required - set(sheet_df.index)}"
            continue

        df_sheet = sheet_df.loc[list(required)].T

        df_sheet = df_sheet.dropna(
            subset=["Stockholders Equity", "Total Debt", "Ordinary Shares Number"]
        )

        df_sheet = df_sheet.reset_index()
        df_sheet = df_sheet.rename(columns={"index": "report_date"})

        df_sheet.columns = [col.lower().replace(" ", "_") for col in df_sheet.columns]

        df_sheet["ticker"] = t
        ok_sheet.append(df_sheet)

    except Exception as e:
        failed_sheet[t] = str(e)

data_stmt = pd.concat(ok_stmt) if ok_stmt else pd.DataFrame()
data_sheet = pd.concat(ok_sheet) if ok_sheet else pd.DataFrame()

# 3. Merge the two datasets on ticker and report_date
data = pd.merge(data_stmt, data_sheet, on=["ticker", "report_date"], how="inner")

# 4. Write the merged dataset to the PostgreSQL database
with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE fundamentals;"))

data.to_sql("fundamentals", engine, if_exists="append", index=False)
