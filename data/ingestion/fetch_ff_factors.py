import pandas as pd
import requests
from config.settings import get_engine, extract_csv_from_zip
from sqlalchemy import text

try:
    with get_engine().connect() as connection:
        print("Successfully connected")
except Exception as e:
    print(f"Connection failed: {e}")

url1 = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"
url2 = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip"

response1 = requests.get(url1)
response1.raise_for_status()
response2 = requests.get(url2)
response2.raise_for_status()

df_ff5 = extract_csv_from_zip(response1, 3)

df_ff5 = df_ff5.drop(columns = ['CMA', 'RMW'])
df_ff5 = df_ff5.rename(columns = {'Unnamed: 0' : 'date'})
df_ff5 = df_ff5.drop(df_ff5.index[-1])
df_ff5['date'] = pd.to_datetime(df_ff5['date'], format = '%Y%m%d')
df_ff5.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df_ff5.columns]

# Fama-French momentum file has 13 lines of header text before the data
df_mom = extract_csv_from_zip(response2, 13)

df_mom = df_mom.drop(df_mom.index[-1])
df_mom = df_mom.rename(columns = {'Unnamed: 0' : 'date', 'Mom' : 'umd'})
df_mom['date'] = pd.to_datetime(df_mom['date'], format = '%Y%m%d')
df_mom.columns = [col.lower().replace(' ', '_') for col in df_mom.columns]

factors = pd.merge(df_ff5, df_mom, on = 'date', how = 'inner')

with get_engine().begin() as conn:
    conn.execute(text('TRUNCATE TABLE ff_factors'))

factors.to_sql('ff_factors', get_engine(), if_exists = 'append', index = False)