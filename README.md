# Factor Research Platform

Equity factor research platform that constructs and evaluates quantitative investment factors using S&P 500 data. The project ingests price and fundamental data into PostgreSQL, computes canonical factors (momentum, value, size, volatility, quality), evaluates their predictive power through rigorous statistical testing, and presents results via an interactive dashboard.

## Current Status

**Week 1 complete** — data foundation built and validated.

- [x] PostgreSQL database schema and data layer
- [x] S&P 500 daily price ingestion (5 years, ~500 tickers)
- [x] Quarterly fundamental data ingestion (income statement + balance sheet)
- [x] Fama-French factor data download (MKT-RF, SMB, HML, RF, UMD)
- [x] Data quality validation report (completeness, outliers, cross-table alignment)
- [x] SQL views: monthly returns, forward returns, derived fundamentals (ROE, debt-to-equity, market cap)
- [ ] Factor construction (momentum, value, size, volatility, quality)
- [ ] Statistical evaluation (IC analysis, quintile spreads, significance testing)
- [ ] Backtesting (long-short portfolios, transaction costs, performance metrics)
- [ ] Research notebook and Streamlit dashboard

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.12 |
| Database | PostgreSQL |
| ORM / SQL | SQLAlchemy + raw SQL |
| Data source | yfinance, Kenneth French Data Library |
| Data processing | pandas, NumPy |
| Statistics | scipy, statsmodels (upcoming) |
| Visualization | matplotlib, seaborn, Plotly (upcoming) |
| Dashboard | Streamlit (upcoming) |

## Project Structure

```
factor-research-platform/
├── data/
│   ├── ingestion/
│   │   ├── fetch_prices.py          # S&P 500 daily price data → PostgreSQL
│   │   ├── fetch_fundamentals.py    # Quarterly financial statements → PostgreSQL
│   │   └── fetch_ff_factors.py      # Fama-French factor returns → PostgreSQL
│   └── quality/
│       └── validate.py              # Data quality validation report
├── sql/
│   ├── schema.sql                   # Table definitions
│   └── views.sql                    # Monthly returns, forward returns, derived fundamentals
├── .env.example                     # Database connection template
├── requirements.txt                 # Pinned dependencies
├── LICENSE
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

## Data Notes

- **Universe:** S&P 500 constituents as of download date. This introduces survivorship bias, which is acknowledged as a limitation — proper point-in-time constituent data requires a paid data subscription.
- **Price data:** ~5 years of daily adjusted close prices. Tickers with fewer than 750 trading days are excluded from analysis.
- **Fundamental data:** Limited to 5–6 quarters via yfinance's free data. Price-only factors (momentum, volatility) use the full history; fundamental-dependent factors (value, quality) are limited to this shorter window.
- **Look-ahead bias:** Fundamental data uses period-end dates. A lag is applied in the analysis layer to approximate actual filing dates.