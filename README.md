# Factor Research Platform

Equity factor research platform that constructs and evaluates quantitative investment factors using S&P 500 data. The project ingests price and fundamental data into PostgreSQL, computes five canonical factors (momentum, value, size, volatility, quality), and evaluates their predictive power through rigorous statistical testing — Information Coefficient analysis, quintile spread analysis, Newey-West significance testing, and multiple hypothesis correction.

## Key Findings

Evaluated over the full 2021–2026 sample (≈53 months for price factors, ≈64 months for fundamental factors):

- **Size** was the only factor to survive Bonferroni correction (adjusted p = 0.012). It posted the best risk-adjusted performance (Sharpe 1.00, smallest drawdown at −6.4%) and the highest information ratio (0.22). One honest caveat: size is significant *within the S&P 500* but correlates *negatively* with the market-wide Fama-French SMB factor, so it reflects a within-large-cap tilt rather than a replication of the academic size premium.
- **Momentum** delivered the highest total return (68.7%, 12.6% annualized) and the only cleanly monotonic quintile spread, but its mean return did not reach significance even before correction (p = 0.055) — a clean example that economic magnitude and statistical significance are distinct questions.
- **Value** and **quality** were weakly positive but statistically indistinguishable from zero (both p ≈ 0.18).
- **Volatility** ran in reverse — high-volatility stocks outperformed low-volatility stocks — producing a −71% cumulative return and a significantly negative mean (p = 0.007).
- **The broader lesson:** only one of five factors survived honest multiple-testing correction. Extending the fundamental factors from an earlier ~18-month window to the full ~5-year sample deflated every headline number (size's Sharpe fell from 1.47 to 1.00, value's apparent dominance disappeared), underscoring how short samples flatter factor results.

Full analysis and methodology are documented in `notebooks/research_report.ipynb`.

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.12 |
| Database | PostgreSQL |
| ORM / SQL | SQLAlchemy + raw SQL |
| Data sources | yfinance (prices), SEC EDGAR Company Facts API (fundamentals), Kenneth French Data Library (FF factors) |
| Data processing | pandas, NumPy |
| Validation | Pandera |
| Statistics | SciPy, statsmodels |
| Visualization | matplotlib, seaborn |
| Dashboard | Streamlit |

## Project Structure

```
factor-research-platform/
├── config/
│   └── settings.py                  # Lazy DB engine, project root, XBRL extraction helpers
├── data/
│   ├── ingestion/
│   │   ├── fetch_prices.py          # S&P 500 daily price data (yfinance) → PostgreSQL
│   │   ├── fetch_fundamentals.py    # Quarterly fundamentals (SEC EDGAR XBRL) → PostgreSQL
│   │   └── fetch_ff_factors.py      # Fama-French factor returns → PostgreSQL
│   └── quality/
│       └── validate.py              # Data quality validation report
├── factors/
│   ├── base.py                      # Abstract base class (normalize, quintile, store)
│   ├── momentum.py                  # 12-1 month momentum
│   ├── value.py                     # Book-to-market ratio
│   ├── size.py                      # Negated market capitalization
│   ├── volatility.py                # Negated 252-day realized volatility
│   ├── quality.py                   # Return on equity
│   └── run_factors.py               # Compute → normalize → quintile → store, all five factors
├── analysis/
│   ├── factor_evaluation.py         # IC analysis, cross-validation, significance testing
│   ├── correlation_analysis.py      # Factor correlation matrix
│   └── backtest.py                  # Cumulative returns, Sharpe, drawdown, turnover
├── sql/
│   ├── schema.sql                   # Table definitions
│   ├── views.sql                    # Monthly/forward returns, derived fundamentals, universe, FF monthly
│   └── queries/
│       └── backtest_returns.sql     # Long-short portfolio return computation
├── notebooks/
│   └── research_report.ipynb        # Full research walkthrough and results
├── dashboard/
│   ├── app.py                       # Streamlit interactive dashboard
│   └── export_data.py               # Refresh dashboard CSVs from the database
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
- Run `sql/views.sql` to create views (including the `universe` view)

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
python factors/run_factors.py
```

8. Refresh dashboard data and view results:
```bash
python dashboard/export_data.py
jupyter notebook notebooks/research_report.ipynb
streamlit run dashboard/app.py
```

## Data Notes

- **Universe:** S&P 500 constituents as of download date. This introduces survivorship bias — companies removed or delisted from the index are absent. A SQL `universe` view enforces the usable set (≥750 daily price observations *and* presence in fundamentals), yielding 496 tickers; every factor filters against it so the traded set is consistent. Point-in-time constituent data would remove the survivorship bias but requires a paid subscription.
- **Price data:** ~5 years of daily adjusted close prices from yfinance (2021–2026). Tickers with fewer than 750 trading days are excluded — this removes recent spinoffs and IPOs (e.g., FDXF, GEV, SOLV, VLTO) that lack sufficient history.
- **Fundamental data:** Sourced from the SEC EDGAR Company Facts API (XBRL structured filings), providing quarterly history back to ~2007. Year-to-date flow items (income, revenue) are reconstructed into discrete quarters via Q4 differencing, with deduplication by filing date to avoid look-ahead bias. Because this history backfills the price window, the fundamental-dependent factors (value, size, quality) now cover the full ~5-year sample rather than a short recent window — the binding constraint on evaluation length is the price history, not the fundamentals.
- **Data quality:** XBRL share counts are unreliable for dual-class filers (FOX/FOXA, BRK-B) and split-adjusted names (CMG), where the reported share count and the price series can refer to different share classes or adjustment conventions. Market-cap factors (value, size) apply a $1B market-cap floor to exclude these, and all raw scores are winsorized cross-sectionally at the 1st/99th percentile per date. Fully share-class-aware XBRL extraction is left as future work.
- **Look-ahead bias:** Factor scores use only data available at the time of scoring. Fundamental data is aligned via a backward as-of merge (the most recent quarterly report on or before the scoring date), and performance is measured using forward (next-month) returns.
- **Transaction costs:** Reported returns are gross. Portfolio turnover is measured separately as a proxy for implementation cost and ranges from ~5% (size) to ~22% (momentum) monthly; at an assumed 10 bps per trade, the implied cost drag is small relative to the factor returns themselves.
