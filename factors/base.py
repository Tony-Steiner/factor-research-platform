from abc import ABC, abstractmethod
import pandas as pd


class Factor(ABC):
    def __init__(self, name, engine):
        self.name = name
        self.engine = engine

    @abstractmethod
    def compute(self):
        pass

    def normalize(self, data):
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
        data.to_sql("factor_scores", self.engine, if_exists="append", index=False)
