import pandas as pd
import time
import requests
from tqdm import tqdm
from config.settings import get_tickers, get_engine, extract_flow_item, extract_stock_item, find_raw_data
 
try:
    with get_engine().connect() as connection:
        print("Successfully connected")
except Exception as e:
    print(f"Connection failed: {e}")
 
url_sp500 = 'https://www.sec.gov/files/company_tickers.json'
 
headers = {"User-Agent": "John Doe john.doe@example.com"}
 
response = requests.get(url_sp500, headers = headers)
response.raise_for_status()
 
data = response.json()
 
tickers = get_tickers()
 
sp500_tickers = {}
valid_tickers = set(tickers)
 
for info in data.values():
    current_ticker = info.get('ticker')
    if current_ticker in valid_tickers:
        sp500_tickers[current_ticker] = info.get('cik_str')
 
results = {}
 
for ticker, cik in tqdm(sp500_tickers.items()):
        num = str(cik).zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{num}.json"
        response = requests.get(url, headers = headers)
        report = response.json()
 
        results[ticker] = {
                'net_income' : extract_flow_item(report, ['us-gaap', 'dei'], ['NetIncomeLoss'], ['USD', 'shares']),
                'revenue' : extract_flow_item(report, ['us-gaap', 'dei'], ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'InterestAndDividendIncomeOperating'], ['USD', 'shares']),
                'debt' : extract_stock_item(report, ['us-gaap', 'dei'], ['LongTermDebt', 'LongTermDebtNoncurrent', 'DebtInstrumentCarryingAmount'], ['USD', 'shares']),
                'equity' : extract_stock_item(report, ['us-gaap', 'dei'], ['StockholdersEquity'], ['USD', 'shares']),
                'shares' : extract_stock_item(report, ['us-gaap', 'dei'], ['EntityCommonStockSharesOutstanding'], ['USD', 'shares'])
        }
 
        time.sleep(0.1)
 
keep_cols = ['end', 'val']
full = []
 
for ticker in tqdm(results):
    ok = []
    for factor in results[ticker]:
        df = pd.DataFrame(results[ticker][factor])
        if 'end' not in df:
            continue
        df['end'] = pd.to_datetime(df['end'])
        df = df[keep_cols]
sp500_tickers = {}
valid_tickers = set(tickers)
 
for info in data.values():
    current_ticker = info.get('ticker')
    if current_ticker in valid_tickers:
        sp500_tickers[current_ticker] = info.get('cik_str')
 
results = {}
 
for ticker, cik in tqdm(sp500_tickers.items()):
        num = str(cik).zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{num}.json"
        response = requests.get(url, headers = headers)
        report = response.json()
 
        results[ticker] = {
                'net_income' : extract_flow_item(report, ['us-gaap', 'dei'], ['NetIncomeLoss'], ['USD', 'shares']),
                'revenue' : extract_flow_item(report, ['us-gaap', 'dei'], ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'InterestAndDividendIncomeOperating'], ['USD', 'shares']),
                'debt' : extract_stock_item(report, ['us-gaap', 'dei'], ['LongTermDebt', 'LongTermDebtNoncurrent', 'DebtInstrumentCarryingAmount'], ['USD', 'shares']),
                'equity' : extract_stock_item(report, ['us-gaap', 'dei'], ['StockholdersEquity'], ['USD', 'shares']),
                'shares' : extract_stock_item(report, ['us-gaap', 'dei'], ['EntityCommonStockSharesOutstanding'], ['USD', 'shares'])
        }
 
        time.sleep(0.1)
 
keep_cols = ['end', 'val']
full = []
 
for ticker in tqdm(results):
    ok = []
    for factor in results[ticker]:
        df = pd.DataFrame(results[ticker][factor])
        if 'end' not in df:
            continue
        df['end'] = pd.to_datetime(df['end'])
        df = df[keep_cols]
        df['ticker'] = ticker
        df = df.rename(columns = {'val' : factor})
 
        ok.append(df)

    if len(ok) < 2:
        counts = {f: len(results[ticker][f]) for f in results[ticker]}
        print(f'SKIP {ticker}: only {len(ok)} factor(s) with data - {counts}')
        continue
 
    merged = pd.merge_asof(ok[0], ok[1], on = 'end', by = 'ticker', direction = 'backward')
 
    for num in range(2, len(ok)):
        merged = pd.merge_asof(merged, ok[num], on = 'end', by = 'ticker', direction = 'backward')
 
    full.append(merged)
 
data = pd.concat(full).reset_index()
data = data.rename(columns = {'end' : 'report_date', 'shares' : 'ordinary_shares_number', 'equity' : 'stockholders_equity', 'debt' : 'total_debt', 'revenue' : 'total_revenue'})
data['report_date'] = pd.to_datetime(data['report_date']).dt.date
 
existing = pd.read_sql('SELECT DISTINCT ticker, report_date FROM fundamentals', get_engine())
 
new_data = data.merge(existing, on = ['ticker', 'report_date'], how = 'left', indicator = True)
new_records = new_data[new_data['_merge'] == 'left_only'].drop(columns=['_merge', 'index'])
new_records = new_records.drop_duplicates(subset = ['ticker', 'report_date'], keep = 'first')
 
new_records.to_sql('fundamentals', get_engine(), if_exists = 'append', index = False)
print(f'Added {len(new_records)} new rows, skipped {len(data) - len(new_records)} existing rows')
