from config.settings import engine
from analysis.backtest import compute_cumulative_returns, compute_performance_metrics, compute_turnover
from analysis.correlation_analysis import compute_factor_correlations
from analysis.factor_evaluation import compute_ic_series, compute_quintile_spreads, compute_significance
import os

data_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(data_dir, exist_ok=True)

compute_cumulative_returns(engine).to_csv(os.path.join(data_dir, 'cumulative.csv'), index=False)
compute_performance_metrics(engine).to_csv(os.path.join(data_dir, 'metrics.csv'), index=False)
compute_turnover(engine).to_csv(os.path.join(data_dir, 'turnover.csv'), index=False)

corr, overlap = compute_factor_correlations(engine)
corr.to_csv(os.path.join(data_dir, 'corr.csv'))

compute_ic_series(engine).to_csv(os.path.join(data_dir, 'ic.csv'), index=False)
compute_quintile_spreads(engine).to_csv(os.path.join(data_dir, 'qs.csv'))
compute_significance(engine).to_csv(os.path.join(data_dir, 'sig.csv'), index=False)

print("All data exported to dashboard/data/")


# python dashboard/export_data.py
# git add dashboard/data/
# git commit -m "data: refresh dashboard exports"
# git push