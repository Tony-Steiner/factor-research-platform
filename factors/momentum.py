import pandas as pd
from sqlalchemy import create_engine, text
from factors.base import Factor
from config.settings import engine


class Momentum(Factor):
    def compute(self):
        data = pd.read_sql(text("SELECT * FROM monthly_returns"), self.engine)
        data["raw_score"] = (
            data.groupby("ticker")["monthly_return"]
            .apply(
                lambda g: g.shift(1)
                .rolling(window=11)
                .apply(lambda x: (1 + x).prod() - 1)
            )
            .reset_index(level=0, drop=True)
        )
        data = data.rename(columns={"month_start": "date"})
        return data[["date", "ticker", "raw_score"]]
