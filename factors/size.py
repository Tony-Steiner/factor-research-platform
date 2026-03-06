import pandas as pd
from config.settings import engine
from factors.base import Factor


class Size(Factor):
    def compute(self):
        derived_df = pd.read_sql("SELECT * FROM derived_fundamentals", self.engine)
        derived_df = derived_df.rename(columns={"report_date": "date"})
        derived_df["date"] = pd.to_datetime(derived_df["date"])
        monthly_df = pd.read_sql("SELECT * FROM monthly_returns", self.engine)
        monthly_df = monthly_df.rename(columns={"month_start": "date"})
        monthly_df["date"] = pd.to_datetime(monthly_df["date"])
        data = pd.merge_asof(
            monthly_df.sort_values("date"),
            derived_df.sort_values("date"),
            on="date",
            by="ticker",
            direction="backward",
        )
        data["raw_score"] = -data["market_cap"] / 1e9
        return data[["date", "ticker", "raw_score"]]
