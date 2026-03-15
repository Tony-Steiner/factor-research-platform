create or replace view monthly_returns as -- Step 1: Identify the last trading day of each month per ticker.
   -- ROW_NUMBER with DESC order assigns rn=1 to the most recent date in each month.
   with last_day_prices as (
      select ticker,
         date_trunc(
            'month',
            date
         )::date as month_start,
         date as last_trade_date,
         close,
         row_number() over(
            partition by ticker,
            date_trunc(
               'month',
               date
            )::date
            order by date desc
         ) as rn
      from daily_prices
   ) -- Step 2: Keep only the last trading day (rn=1), then compute monthly return.
   -- LAG(close) gets the previous month's close for the same ticker (default offset = 1).
   -- NULLIF prevents division-by-zero errors (returns NULL instead of crashing).
   -- (current / previous) - 1 converts a price ratio into a simple return.
select ticker,
   month_start,
   last_trade_date,
   close,
   lag(close) over(
      partition by ticker
      order by month_start
   ) as prev_close,
   (
      close / nullif(
         lag(close) over(
            partition by ticker
            order by month_start
         ),
         0
      )
   ) - 1 as monthly_return
from last_day_prices
where rn = 1
order by ticker,
   month_start;
create or replace view forward_returns as
select ticker,
   month_start,
   monthly_return,
   lead(monthly_return) over(
      partition by ticker
      order by month_start
   ) as next_month_return
from monthly_returns;
create or replace view derived_fundamentals as -- Compute derived financial metrics from raw fundamental data.
   -- ROE and debt-to-equity use only the fundamentals table.
   -- Market cap requires joining with daily_prices to get the closing price
   -- on (or nearest trading day before) the quarter-end report date.
select f.ticker,
   f.report_date,
   f.ordinary_shares_number,
   f.stockholders_equity,
   f.total_debt,
   f.net_income,
   f.total_revenue,
   -- Return on Equity: how efficiently the company generates profit from equity
   f.net_income / nullif(f.stockholders_equity, 0) as roe,
   -- Leverage ratio: how much debt relative to equity
   f.total_debt / nullif(f.stockholders_equity, 0) as debt_to_equity,
   -- Market cap = share price × shares outstanding
   -- Subquery finds the closest trading day on or before report_date,
   -- since quarter-end dates may fall on weekends/holidays.
   (
      select dp.close
      from daily_prices dp
      where dp.ticker = f.ticker
         and dp.date = (
            select max(dp2.date)
            from daily_prices dp2
            where dp2.ticker = f.ticker
               and dp2.date <= f.report_date
         )
   ) * f.ordinary_shares_number as market_cap
from fundamentals f
order by f.ticker,
   f.report_date;
-- Compound Fama-French daily factor returns into monthly returns.
-- Uses EXP(SUM(LN(1+r))) - 1 as the SQL equivalent of (1+r).prod() - 1
-- since PostgreSQL has no native PROD() aggregate.
CREATE OR REPLACE VIEW ff_monthly_factors AS
SELECT DATE_TRUNC('month', date)::date AS month_start,
   EXP(SUM(LN(1 + mkt_rf / 100))) - 1 AS mkt_rf,
   EXP(SUM(LN(1 + smb / 100))) - 1 AS smb,
   EXP(SUM(LN(1 + hml / 100))) - 1 AS hml,
   EXP(SUM(LN(1 + rf / 100))) - 1 AS rf,
   EXP(SUM(LN(1 + umd / 100))) - 1 AS umd
FROM ff_factors
GROUP BY month_start
ORDER BY month_start;