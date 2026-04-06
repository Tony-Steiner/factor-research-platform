import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

data_dir = os.path.join(os.path.dirname(__file__), 'data')

st.set_page_config(page_title="Factor Research Dashboard", layout="wide")

@st.cache_data()
def load_all_data():
    cumulative = pd.read_csv(os.path.join(data_dir, 'cumulative.csv'))
    metrics = pd.read_csv(os.path.join(data_dir, 'metrics.csv'))
    turnover = pd.read_csv(os.path.join(data_dir, 'turnover.csv'))
    corr = pd.read_csv(os.path.join(data_dir, 'corr.csv'))
    ic = pd.read_csv(os.path.join(data_dir, 'ic.csv'))
    qs = pd.read_csv(os.path.join(data_dir, 'qs.csv'))
    sig = pd.read_csv(os.path.join(data_dir, 'sig.csv'))
    return cumulative, metrics, turnover, corr, None, ic, qs, sig

cumulative, metrics, turnover, corr, overlap, ic, qs, sig = load_all_data()

with st.sidebar:
    st.write("Select factors to display:")
    quality = st.checkbox("Quality")
    value = st.checkbox("Value")
    momentum = st.checkbox("Momentum")
    volatility = st.checkbox("Low Volatility")
    size = st.checkbox("Size")

selected = []
if quality:
    selected.append("quality")
if value:
    selected.append("value")
if momentum:            
    selected.append("momentum")
if volatility:
    selected.append("volatility")
if size:
    selected.append("size")

if not selected:
    selected = ['quality', 'value', 'momentum', 'volatility', 'size']

st.title("Factor Research Dashboard")
st.caption("Equity factor construction and evaluation · S&P 500 · 2021–2026")
cumulative_filtered = cumulative[cumulative['factor_name'].isin(selected)]
cum_plot = cumulative_filtered.rename(columns={"factor_name": "Factor name"})
st.subheader("Cumulative Returns by Factor")
st.line_chart(cum_plot, 
              x = 'date', 
              y = 'cumulative', 
              color = 'Factor name', 
              x_label = 'Date', 
              y_label = 'Cumulative Returns'
              )

metrics_filtered = metrics[metrics['factor_name'].isin(selected)]

turnover_filtered = turnover[turnover['factor_name'].isin(selected)]

col1, col2 = st.columns(2)
with col1:
    st.subheader("Performance Metrics")
    st.dataframe(
        metrics_filtered, 
        hide_index=True, 
        width = 'stretch'
        )

with col2:
    st.subheader("Average Monthly Turnover")
    st.dataframe(
        turnover_filtered, 
        hide_index=True, 
        width = 'stretch'
        )

st.subheader("Factor Correlations")
corr = corr.set_index('factor_name')
corr.index.name = 'Factor name'
corr.columns.name = 'Factor name'
corr_matrix = corr.loc[selected, selected]
if len(selected) < 2:
    st.write("Not enough factors selected for correlation analysis. Select at least 2 factors to view the correlation matrix.")
else:
    fig, ax = plt.subplots()
    sns.heatmap(corr_matrix, ax=ax, annot=True, cmap="RdBu_r")
    plt.title("Factor Correlation Matrix")
    plt.tight_layout()
    st.pyplot(fig)

st.subheader("Information Coefficient (IC) Series")
ic_filtered = ic[ic['factor_name'].isin(selected)]
st.dataframe(
    ic_filtered.groupby('factor_name')['ic'].agg(
    ['mean', 'std', 'count']
    ).assign(
        ir = lambda x: x['mean'] / x['std'], 
        hit_rate = ic_filtered.groupby('factor_name')['ic'].apply(
            lambda x: (x > 0).mean()
            )
            ), 
        width = 'stretch'
        )

st.subheader("Quintile Spread")
qs_filtered = qs[qs['factor_name'].isin(selected)]
fig, ax = plt.subplots()
sns.barplot(
    data = qs_filtered.melt(
        id_vars = 'factor_name', 
        var_name = 'quintile', 
        value_name = 'avg_return'
        ),
        x = 'quintile',
        hue = 'factor_name',
        y = 'avg_return'
        )
plt.xlabel("Quintile")
plt.ylabel("Average Return")
plt.legend(title="Factor")
plt.grid()
st.pyplot(fig)

st.subheader("Significance Results Table")
sig_filtered = sig[sig['factor_name'].isin(selected)]
st.dataframe(
    sig_filtered, 
    hide_index=True, 
    width = 'stretch'
    )