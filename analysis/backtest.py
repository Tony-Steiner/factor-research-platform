import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

from config.settings import engine
from config.settings import PROJECT_ROOT

sql_path = os.path.join(PROJECT_ROOT, "sql", "queries", "backtest_returns.sql")


def compute_performance_metrics(engine):
    backtest_query = open(sql_path).read()
    df = pd.read_sql(backtest_query, engine)

    results = []
    for factor, group in df.groupby("factor_name"):
        r = group["long_short"].dropna()
        cumulative = (1 + r).cumprod()

        # Annualized Sharpe: mean monthly return / std, scaled to annual
        sharpe = (r.mean() / r.std()) * np.sqrt(12) if r.std() > 0 else np.nan

        # Max drawdown: largest peak-to-through decline
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        max_dd = drawdown.min()

        results.append(
            {
                "factor_name": factor,
                "total_return": cumulative.iloc[-1] - 1,
                "annual_return": (cumulative.iloc[-1] ** (12 / len(r))) - 1,
                "annual_sharpe": sharpe,
                "max_drawdown": max_dd,
                "n_months": len(r),
            }
        )

    return pd.DataFrame(results)


def compute_turnover(engine):
    df = pd.read_sql(
        "SELECT ticker, date, factor_name, quintile FROM factor_scores", engine
    )

    results = []
    for factor, group in df.groupby("factor_name"):
        dates = sorted(group["date"].unique())
        turnovers = []

        for i in range(1, len(dates)):
            prev = set(
                group[
                    (group["date"] == dates[i - 1]) & (group["quintile"].isin([1, 5]))
                ]["ticker"]
            )
            curr = set(
                group[(group["date"] == dates[i]) & (group["quintile"].isin([1, 5]))][
                    "ticker"
                ]
            )

            if len(prev) == 0:
                continue

            # turnover = fraction of holdings that changed
            turnover = len(curr.symmetric_difference(prev)) / (len(prev) + len(curr))
            turnovers.append(turnover)

        results.append(
            {
                "factor_name": factor,
                "avg_monthly_turnover": np.mean(turnovers) if turnovers else np.nan,
            }
        )

    return pd.DataFrame(results)


def compute_cumulative_returns(engine):
    backtest_query = open(sql_path).read()
    df_backtest = pd.read_sql(backtest_query, engine)

    returns = df_backtest.sort_values(["factor_name", "date"]).copy()

    returns["cumulative"] = (
        (1 + returns["long_short"]).groupby([returns["factor_name"]]).cumprod()
    )

    return returns


def plot_cumulative_returns(returns):
    plt.figure(figsize=(12, 6))
    sns.lineplot(x=returns["date"], y=returns["cumulative"], hue=returns["factor_name"])
    plt.title("Cumulative Returns by Factor")
    plt.xlabel("Date")
    plt.ylabel("Cumulative Return")
    plt.grid()
    plt.show()
