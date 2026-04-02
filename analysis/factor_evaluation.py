import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import statsmodels.api as sm
import os
from config.settings import engine
from config.settings import PROJECT_ROOT
from scipy.stats import spearmanr, false_discovery_control

sql_path = os.path.join(PROJECT_ROOT, "sql", "queries", "backtest_returns.sql")


def cross_validation(engine):
    backtest_query = open(sql_path).read()
    df_backtest = pd.read_sql(backtest_query, engine)

    df_ff = pd.read_sql("SELECT * FROM ff_monthly_factors", engine)

    mom_ls = df_backtest[df_backtest["factor_name"] == "momentum"][
        ["date", "long_short"]
    ]
    value_ls = df_backtest[df_backtest["factor_name"] == "value"][
        ["date", "long_short"]
    ]
    size_ls = df_backtest[df_backtest["factor_name"] == "size"][["date", "long_short"]]

    mom_compare = mom_ls.merge(
        df_ff[["month_start", "umd"]], left_on="date", right_on="month_start"
    )
    size_compare = size_ls.merge(
        df_ff[["month_start", "smb"]], left_on="date", right_on="month_start"
    )
    value_compare = value_ls.merge(
        df_ff[["month_start", "hml"]], left_on="date", right_on="month_start"
    )

    results = {
        "momentum": {
            "correlation": mom_compare["long_short"].corr(mom_compare["umd"]),
            "months": len(mom_compare),
            "mean": mom_compare["long_short"].mean(),
            "ff_mean": mom_compare["umd"].mean(),
        },
        "size": {
            "correlation": size_compare["long_short"].corr(size_compare["smb"]),
            "months": len(size_compare),
        },
        "value": {
            "correlation": value_compare["long_short"].corr(value_compare["hml"]),
            "months": len(value_compare),
        },
    }
    return results


def compute_ic_series(engine):
    df_fs = pd.read_sql("SELECT * FROM factor_scores", engine)

    df_fr = pd.read_sql("SELECT * FROM forward_returns", engine)
    df_fr = df_fr.rename(columns={"month_start": "date"})

    df = pd.merge(df_fs, df_fr, on=["date", "ticker"])

    results = []
    for (factor, date), group in df.groupby(["factor_name", "date"]):
        clean = group.dropna(subset=["raw_score", "next_month_return"])
        if len(clean) < 10:
            continue
        coef, p = spearmanr(clean["raw_score"], clean["next_month_return"])
        results.append({"date": date, "factor_name": factor, "ic": coef, "p_value": p})
    df_ic = pd.DataFrame(results)
    return df_ic


def plot_ic_series(df_ic):
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df_ic, x="date", y="ic", hue="factor_name")
    plt.title("Information Coefficient (IC) Over Time")
    plt.xlabel("Date")
    plt.ylabel("IC")
    plt.legend(title="Factor")
    plt.grid()
    plt.show()


def compute_quintile_spreads(engine):
    query = """
        SELECT fs.date, fs.factor_name, fs.quintile, AVG(fr.next_month_return) AS avg_return
        FROM factor_scores AS fs
        INNER JOIN forward_returns AS fr ON fs.ticker = fr.ticker
        AND fs.date = fr.month_start
        GROUP BY fs.date, fs.factor_name, fs.quintile
        ORDER BY fs.factor_name, fs.quintile, fs.date;
    """
    df_raw = pd.read_sql(query, engine)
    df = df_raw.groupby(["factor_name", "quintile"])["avg_return"].mean().unstack()
    return df


def plot_quintile_spreads(df_quintiles):
    plt.figure(figsize=(12, 6))
    sns.barplot(
        data=df_quintiles.reset_index().melt(
            id_vars="factor_name", var_name="quintile", value_name="avg_return"
        ),
        x="quintile",
        hue="factor_name",
        y="avg_return",
    )
    plt.title("Average Return by Quintile")
    plt.xlabel("Quintile")
    plt.ylabel("Average Return")
    plt.legend(title="Factor")
    plt.grid()
    plt.show()


def compute_significance(engine):
    backtest_query = open(sql_path).read()
    df_backtest = pd.read_sql(backtest_query, engine)

    results = []
    for factor, group in df_backtest.groupby("factor_name"):
        returns = group["long_short"].dropna()

        if len(returns) < 12:
            continue

        X = sm.add_constant(np.ones(len(returns)))

        model = sm.OLS(returns.values, X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})

        results.append(
            {
                "factor_name": factor,
                "mean_return": returns.mean(),
                "nw_tstat": model.tvalues[0],
                "nw_pvalue": model.pvalues[0],
                "n_months": len(returns),
                "significant": model.pvalues[0] < 0.05,
            }
        )

    p_values = [r["nw_pvalue"] for r in results]
    bonferroni = [min(p * 5, 1.0) for p in p_values]
    bh_adjusted = false_discovery_control(p_values, method="bh")

    df = pd.DataFrame(results)
    df["bonferroni_p"] = bonferroni
    df["bh_p"] = bh_adjusted

    return df