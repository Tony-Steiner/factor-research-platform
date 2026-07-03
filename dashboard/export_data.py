from analysis.backtest import compute_cumulative_returns, compute_performance_metrics, compute_turnover
from analysis.correlation_analysis import compute_factor_correlations
from analysis.factor_evaluation import compute_ic_series, compute_quintile_spreads, compute_significance
import os

data_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(data_dir, exist_ok=True)

compute_cumulative_returns().to_csv(os.path.join(data_dir, 'cumulative.csv'), index=False)
compute_performance_metrics().to_csv(os.path.join(data_dir, 'metrics.csv'), index=False)
compute_turnover().to_csv(os.path.join(data_dir, 'turnover.csv'), index=False)

corr, overlap = compute_factor_correlations()
corr.to_csv(os.path.join(data_dir, 'corr.csv'))

compute_ic_series().to_csv(os.path.join(data_dir, 'ic.csv'), index=False)
compute_quintile_spreads().to_csv(os.path.join(data_dir, 'qs.csv'))
compute_significance().to_csv(os.path.join(data_dir, 'sig.csv'), index=False)

print("All data exported to dashboard/data/")