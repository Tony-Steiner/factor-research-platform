import pandas as pd
import urllib.request
import zipfile
import io
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

load_dotenv()

connection_url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(connection_url)

try:
    with engine.connect() as connection:
        print("Successfully connected to the PostgreSQL database.")
except Exception as e:
    print(f"Connection failed: {e}")

# 1. The direct URL to the daily 5-factor CSV zip file
url1 = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"
url2 = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip"

# 2. Download the zip file into memory
request1 = urllib.request.urlopen(url1)
request2 = urllib.request.urlopen(url2)

# 3. Extract and read the CSV
with zipfile.ZipFile(io.BytesIO(request1.read())) as z:
    with z.open(z.namelist()[0]) as f:
        # Fama-French CSVs have 3 lines of text at the top we must skip
        df1 = pd.read_csv(f, skiprows=3)

df1 = df1.rename(columns={"Unnamed: 0": "date"})
df1 = df1.drop(df1.index[-1])
df1 = df1.drop(columns=["CMA", "RMW"])
df1["date"] = pd.to_datetime(df1["date"], format="%Y%m%d")
df1.columns = [col.lower().replace(" ", "_").replace("-", "_") for col in df1.columns]

with zipfile.ZipFile(io.BytesIO(request2.read())) as z:
    with z.open(z.namelist()[0]) as f:
        # Fama-French CSVs have 3 lines of text at the top we must skip
        df2 = pd.read_csv(f, skiprows=13)

df2 = df2.rename(columns={"Unnamed: 0": "date", "Mom": "umd"})
df2 = df2.drop(df2.index[-1])
df2["date"] = pd.to_datetime(df2["date"], format="%Y%m%d")
df2.columns = [col.lower().replace(" ", "_") for col in df2.columns]

# 4. Merge the two datasets on date
factors = pd.merge(df1, df2, on="date", how="inner")

# 5. Write the merged dataset to the PostgreSQL database
with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE ff_factors"))

factors.to_sql("ff_factors", engine, if_exists="append", index=False)
