# Factor Research Platform

Equity factor research platform that constructs and evaluates quantitative investment factors using S&P 500 data. The project ingests price and fundamental data into PostgreSQL, computes five canonical factors (momentum, value, size, volatility, quality), and evaluates their predictive power through rigorous statistical testing — including Information Coefficient analysis, quintile spread analysis, Newey-West significance testing, and multiple hypothesis correction.

## Key Findings

- **Value** showed the strongest predictive signal (mean IC 0.046, 75% hit rate, Sharpe 1.35) but is estimated from only 18 months of fundamental data.
- **Momentum** delivered the highest cumulative return (37.9% over 49 months) with a clear monotonic quintile spread and a Sharpe ratio of 0.62.
- **Size** was the only factor to survive Bonferroni correction for multiple hypothesis testing (adjusted p=0.035), though also limited to 18 months.
- **Volatility** ran in reverse — high-volatility stocks consistently outperformed low-volatility stocks, producing a -59.7% cumulative return.
- After multiple hypothesis correction, most factors lose statistical significance, underscoring the difficulty of identifying reliable premiums from limited samples.

Full analysis and methodology are documented in `notebooks/research_report.ipynb`.

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.12 |
| Database | PostgreSQL |
| ORM / SQL | SQLAlchemy + raw SQL |
| Data sources | yfinance, Kenneth French Data Library |
| Data processing | pandas, NumPy |
| Statistics | SciPy, statsmodels |
| Visualization | matplotlib, seaborn |
| Dashboard | Streamlit |

## Project Structure

```
factor-research-platform/
├── config/
│   └── settings.py                  # Database engine, project root, shared utilities
├── data/
│   ├── ingestion/
│   │   ├── fetch_prices.py          # S&P 500 daily price data → PostgreSQL
│   │   ├── fetch_fundamentals.py    # Quarterly financial statements → PostgreSQL
│   │   └── fetch_ff_factors.py      # Fama-French factor returns → PostgreSQL
│   └── quality/
│       └── validate.py              # Data quality validation report
├── factors/
│   ├── base.py                      # Abstract base class (normalize, quintile, store)
│   ├── momentum.py                  # 12-1 month momentum
│   ├── value.py                     # Book-to-market ratio
│   ├── size.py                      # Negated market capitalization
│   ├── volatility.py                # Negated 252-day realized volatility
│   └── quality.py                   # Return on equity
├── analysis/
│   ├── factor_evaluation.py         # IC analysis, cross-validation, significance testing
│   ├── correlation_analysis.py      # Factor correlation matrix
│   └── backtest.py                  # Cumulative returns, Sharpe, drawdown, turnover
├── sql/
│   ├── schema.sql                   # Table definitions
│   ├── views.sql                    # Monthly returns, forward returns, derived fundamentals, FF monthly
│   └── queries/
│       └── backtest_returns.sql     # Long-short portfolio return computation
├── notebooks/
│   └── research_report.ipynb        # Full research walkthrough and results
├── dashboard/
│   └── app.py                       # Streamlit interactive dashboard
├── .env.example                     # Database connection template
├── requirements.txt                 # Pinned dependencies
└── README.md
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/Tony-Steiner/factor-research-platform.git
cd factor-research-platform
```

2. Create and activate a virtual environment:
```bash
python -m venv factor-research
source factor-research/bin/activate        # macOS/Linux
factor-research\Scripts\activate           # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL:
- Create a database named `factor_research`
- Copy `.env.example` to `.env` and fill in your credentials
- Run `sql/schema.sql` to create tables
- Run `sql/views.sql` to create views

5. Ingest data:
```bash
python data/ingestion/fetch_prices.py
python data/ingestion/fetch_fundamentals.py
python data/ingestion/fetch_ff_factors.py
```

6. Validate data:
```bash
python data/quality/validate.py
```

7. Compute factors:
```bash
python -c "
from config.settings import engine
from factors.momentum import Momentum
from factors.size import Size
from factors.value import Value
from factors.volatility import Volatility
from factors.quality import Quality

for FactorClass, name in [(Momentum, 'momentum'), (Size, 'size'), (Value, 'value'), (Volatility, 'volatility'), (Quality, 'quality')]:
    f = FactorClass(name, engine)
    raw = f.compute()
    norm = f.normalize(raw.dropna())
    q = f.assign_quintiles(norm)
    f.store(q)
    print(f'{name} stored: {len(q)} rows')
"
```

8. View results:
```bash
jupyter notebook notebooks/research_report.ipynb
```

## Data Notes

- **Universe:** S&P 500 constituents as of download date. This introduces survivorship bias — companies removed or delisted from the index are absent. Point-in-time constituent data would address this but requires a paid subscription.
- **Price data:** ~5 years of daily adjusted close prices. Tickers with fewer than 750 trading days are excluded from analysis.
- **Fundamental data:** Limited to 5–6 quarters via yfinance. Price-only factors (momentum, volatility) use the full history; fundamental-dependent factors (value, size, quality) are limited to this shorter window (~18 months of evaluation).
- **Look-ahead bias:** Factor scores use only data available at the time of scoring. Fundamental data is aligned using the most recent quarterly report on or before the scoring date. Performance is measured using forward (next-month) returns.
- **Transaction costs:** Modeled at 10 basis points per trade. Turnover ranges from 5.8% (volatility) to 22.1% (momentum) monthly.