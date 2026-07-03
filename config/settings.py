from sqlalchemy import create_engine
from dotenv import load_dotenv
from io import StringIO
import pandas as pd
import requests
import zipfile
import io
import os
 
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
 
_engine = None 
 
def get_engine():
    global _engine
    
    if _engine is None:
        load_dotenv()
        DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        _engine = create_engine(DATABASE_URL)
    return _engine
 
def get_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
 
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers = headers, timeout = 30)
    response.raise_for_status()
 
    tables = pd.read_html(StringIO(response.text))
 
    sp500_df = tables[0]
 
    tickers = (sp500_df['Symbol'].str.replace('.', '-', regex = False).tolist())
 
    return tickers
 
def find_raw_data(report, facts, tags, units):
    for fact in facts:
        if fact in report['facts']:
            for tag in tags:
                if tag in report['facts'][fact]:
                    for unit in units:
                        if unit in report['facts'][fact][tag]['units']:
                                          return report['facts'][fact][tag]['units'][unit]
    return None
 
def extract_stock_item(report, facts, tags, units):
 
    raw_report = find_raw_data(report, facts, tags, units)
 
    if raw_report is None:
        return []
 
    entries = []
    seen = set()
 
    raw_report.sort(key = lambda x: x['filed'], reverse = False)
 
    for item in raw_report:
        if 'end' not in item:
            continue
        
        date_key = item['end']
 
        if date_key not in seen:
            seen.add(date_key)
            entries.append({
                'end' : item['end'],
                'val' : item['val'],
                'form' : item['form'],
                'fp' : item['fp']
            })
 
    entries = sorted(entries, key = lambda x: x['end'], reverse = False)
 
    return entries
 
def extract_flow_item(report, facts, tags, units):
 
    raw_report = find_raw_data(report, facts, tags, units)
 
    if raw_report is None:
        return []
        
    min_q = 85
    max_q = 95
 
    min_y = 350
    max_y = 380
 
    entries = []
    seen = set()
 
    raw_report.sort(key = lambda x: x['filed'], reverse = False)
 
    for item in raw_report:
        if 'start' not in item:
            continue
        
        date_keys = (item['start'], item['end'])
            
        duration = (pd.to_datetime(item['end']) - pd.to_datetime(item['start'])).days
 
        if date_keys not in seen and (min_q <= duration <= max_q or min_y <= duration <= max_y):
            seen.add(date_keys)
            entries.append({
                'start' : item['start'],
                'end' : item['end'],
                'val' : item['val'],
                'form' : item['form'],
                'fp' : item['fp']
            })
 
    entries = sorted(entries, key = lambda x: x['end'], reverse = False)
 
    quarterly = []
    annual = []
 
    for item in entries:
        duration = (pd.to_datetime(item['end']) - pd.to_datetime(item['start'])).days
        if (min_y <= duration <= max_y):
            annual.append(item)
        else:
            quarterly.append(item)
 
    final_quarters = []
 
    for x in annual:
                
        for y in quarterly:
            duration = (pd.to_datetime(x['end']) - pd.to_datetime(y['end'])).days
            if (min_q <= duration <= max_q):
                final_quarters.append({
                    'start' : y['end'],
                    'end' : x['end'],
                    'val' : x['val'] - y['val'],
                    'form' : x['form'],
                    'fp' : x['fp']
                })
    
    return sorted(quarterly + final_quarters, key = lambda x : x['end'])  
 
def extract_csv_from_zip(response, skiprow):
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        with z.open(z.namelist()[0]) as f:
            df = pd.read_csv(f, skiprows = skiprow)
 
    return df
