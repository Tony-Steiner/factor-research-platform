-- Compute monthly long-short portfolio returns for each factor.
-- Joins factor scores with FORWARD returns (month T+1) to avoid look-ahead bias:
-- stocks are ranked at end of month T, then we measure their performance in month T+1.
-- Q5 (top quintile) = long portfolio, Q1 (bottom quintile) = short portfolio.
-- Long-short spread isolates the factor's pure return, hedged against market direction.
WITH quintiles AS (
    SELECT fs.date,
        fs.factor_name,
        fs.quintile,
        AVG(fr.next_month_return) AS avg_return
    FROM factor_scores AS fs
        INNER JOIN forward_returns AS fr ON fs.ticker = fr.ticker
        AND fs.date = fr.month_start
    WHERE fs.quintile IN (1, 5) -- Focus on top and bottom quintiles for long-short strategy
    GROUP BY fs.date,
        fs.factor_name,
        fs.quintile
    ORDER BY fs.factor_name,
        fs.quintile,
        fs.date;
)
SELECT q.date,
    q.factor_name,
    SUM(
        CASE
            WHEN quintile = 5 THEN avg_return
            ELSE 0
        END
    ) AS long_return,
    SUM(
        CASE
            WHEN quintile = 1 THEN avg_return
            ELSE 0
        END
    ) AS short_return,
    SUM(
        CASE
            WHEN quintile = 5 THEN avg_return
            ELSE 0
        END
    ) - SUM(
        CASE
            WHEN quintile = 1 THEN avg_return
            ELSE 0
        END
    ) AS long_short
FROM quintiles AS q
GROUP BY q.date,
    q.factor_name
ORDER BY q.factor_name,
    q.date;