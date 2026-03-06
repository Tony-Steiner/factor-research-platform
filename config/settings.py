from sqlalchemy import create_engine
from dotenv import load_dotenv
import yfinance as yf
import os

load_dotenv()

DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)


def fetch_financial_statements(tickers, required_columns, function):
    ok = []
    failed = {}

    for t in tickers:
        ticker_obj = yf.Ticker(t)
        try:
            df = getattr(ticker_obj, function)
            if df.empty:
                failed[t] = "empty"
                continue

            if not required_columns.issubset(df.index):

                failed[t] = f"missing rows: {required_columns - set(df.index)}"
                continue

            df = df.loc[list(required_columns)].T

            df = df.dropna(subset=list(required_columns))

            df = df.reset_index()
            df = df.rename(columns={"index": "report_date"})

            df.columns = [col.lower().replace(" ", "_") for col in df.columns]

            df["ticker"] = t
            ok.append(df)

        except Exception as e:
            failed[t] = str(e)

    return ok, failed
