create table daily_prices (
   ticker varchar(10) not null,
   date date not null,
   open numeric(12, 4),
   high numeric(12, 4),
   low numeric(12, 4),
   close numeric(12, 4),
   volume bigint,
   primary key (ticker, date)
);
create table fundamentals (
   ticker varchar(10) not null,
   report_date date not null,
   ordinary_shares_number numeric(18, 2),
   stockholders_equity numeric(18, 2),
   total_debt numeric(18, 2),
   net_income numeric(18, 2),
   total_revenue numeric(18, 2),
   primary key (ticker, report_date)
);
create table factor_scores (
   ticker varchar(10) not null,
   date date not null,
   factor_name varchar(30) not null,
   raw_score numeric(14, 6),
   z_score numeric(8, 4),
   quintile smallint,
   primary key (
      ticker,
      date,
      factor_name
   )
);
create table ff_factors (
   date date not null,
   mkt_rf numeric(10, 6),
   smb numeric(10, 6),
   hml numeric(10, 6),
   rf numeric(10, 6),
   umd numeric(10, 6)
);