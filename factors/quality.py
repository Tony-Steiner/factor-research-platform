import pandas as pd
from config.settings import engine
from factors.base import Factor


class Quality(Factor):
    def compute(self):
        df_fund = pd.read_sql("SELECT * FROM derived_fundamentals", self.engine)
        df_fund = df_fund.rename(columns={"report_date": "date"})
        df_fund["date"] = pd.to_datetime(df_fund["date"])

        df_monthly = pd.read_sql("SELECT * FROM monthly_returns", self.engine)
        df_monthly = df_monthly.rename(columns={"month_start": "date"})
        df_monthly["date"] = pd.to_datetime(df_monthly["date"])

        data = pd.merge_asof(
            df_monthly.sort_values("date"),
            df_fund.sort_values("date"),
            on="date",
            by="ticker",
            direction="backward",
        )

        data["raw_score"] = data["roe"]

        return data[["date", "ticker", "raw_score"]]
