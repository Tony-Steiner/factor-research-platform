import pandas as pd
import seaborn as sns
import os
import matplotlib.pyplot as plt
from config.settings import engine
from config.settings import PROJECT_ROOT

sql_path = os.path.join(PROJECT_ROOT, "sql", "queries", "backtest_returns.sql")


def compute_factor_correlations(engine):
    backtest_query = open(sql_path).read()
    df_backtest = pd.read_sql(backtest_query, engine)

    pivoted = df_backtest.pivot(
        index="date", columns="factor_name", values="long_short"
    )
    corr_matrix = pivoted.corr()

    overlap_counts = pivoted.notna().astype(int).T.dot(pivoted.notna().astype(int))
    return corr_matrix, overlap_counts


def plot_correlation_heatmap(corr_matrix):
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap="RdBu_r")
    plt.title("Factor Correlation Matrix")
    plt.tight_layout()
    return plt.gcf()
