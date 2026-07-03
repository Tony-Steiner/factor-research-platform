from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from sqlalchemy import text
from config.settings import get_engine
 
 
class Factor(ABC):
    def __init__(self, name):
        self.name = name
        self.engine = get_engine()
 
    @abstractmethod
    def compute(self):
        pass
 
    def normalize(self, data):
        data = data.replace([np.inf, -np.inf], np.nan).dropna(subset=["raw_score"]).copy()
        data["raw_score"] = data.groupby("date")["raw_score"].transform(
        lambda x: x.clip(lower=x.quantile(0.01), upper=x.quantile(0.99))
        )
        data["z_score"] = data.groupby("date")["raw_score"].transform(
        lambda x: (x - x.mean()) / x.std() if x.std() != 0 else 0
        )
        return data
 
    def assign_quintiles(self, data):
        data["quintile"] = data.groupby("date")["z_score"].transform(
            lambda x: pd.qcut(x, 5, labels=[1, 2, 3, 4, 5])
        )
        return data
 
    def store(self, data):
        data["factor_name"] = self.name
        with self.engine.begin() as conn:
            conn.execute(
                text('DELETE FROM factor_scores WHERE factor_name = :name'),
                {'name': self.name}
            )
        data.to_sql("factor_scores", self.engine, if_exists="append", index=False)
