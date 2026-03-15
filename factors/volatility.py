import pandas as pd
from config.settings import engine
from factors.base import Factor


class Volatility(Factor):
    def compute(self):
        df = pd.read_sql("SELECT * FROM daily_prices", self.engine)
        df["date"] = pd.to_datetime(df["date"])
        df["returns"] = df.groupby("ticker")["close"].pct_change()
        df["volatility"] = (
            df.groupby("ticker")["returns"]
            .rolling(window=252)
            .std()
            .reset_index(level=0, drop=True)
        )
        df["raw_score"] = -df["volatility"]
        df["month"] = df["date"].dt.to_period("M")
        df["rn"] = df.groupby(["ticker", "month"])["date"].rank(
            method="first", ascending=False
        )
        monthly = df[df["rn"] == 1].copy()
        monthly["date"] = monthly["date"].dt.to_period("M").dt.to_timestamp()

        return monthly[["date", "ticker", "raw_score"]]
