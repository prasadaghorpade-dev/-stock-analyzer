import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Risk Analyzer", layout="wide")
st.title("Stock History, Profit-Loss & Anomaly Analyzer")
st.caption("Historical data analysis only. Not a prediction tool. Decision is yours.")

st.sidebar.header("Select Stock")
ticker_input = st.sidebar.text_input(
    "Enter Stock Symbol (add .NS for NSE stocks)",
    value="RELIANCE.NS",
    help="Example: RELIANCE.NS, TCS.NS, INFY.NS, TATAMOTORS.NS"
)

years = st.sidebar.slider("Years of historical data", 1, 10, 5)
threshold = st.sidebar.slider(
    "Big monthly move threshold (%)", 5, 30, 10,
    help="Months with change above this percentage will be flagged"
)
volume_threshold = st.sidebar.slider(
    "Volume spike threshold (x average)", 2, 10, 3,
    help="Days where volume is this many times the average will be flagged"
)

analyze_btn = st.sidebar.button("Run Analysis")


def fetch_data(ticker, years):
    end = datetime.today()
    start = end - timedelta(days=years * 365)
    data = yf.download(ticker, start=start, end=end, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data


def find_big_moves(data, threshold_pct):
    monthly = data["Close"].resample("ME").last()
    monthly_returns = monthly.pct_change().dropna() * 100

    big_moves = []
    for date, ret in monthly_returns.items():
        if abs(ret) >= threshold_pct:
            move_type = "PROFIT" if ret > 0 else "LOSS"
            big_moves.append({
                "Month": date.strftime("%B %Y"),
                "Type": move_type,
                "Change %": round(ret, 2)
            })
    return pd.DataFrame(big_moves)


def find_volume_anomalies(data, spike_multiplier):
    avg_volume = data["Volume"].rolling(window=20, min_periods=5).mean()
    spikes = data[data["Volume"] > (avg_volume * spike_multiplier)]

    anomalies = []
    for date, row in spikes.iterrows():
        avg_at_that_time = avg_volume.loc[date]
        if pd.notna(avg_at_that_time) and avg_at_that_time > 0:
            times_avg = row["Volume"] / avg_at_that_time
            anomalies.append({
                "Date": date.strftime("%d %b %Y"),
                "Volume": int(row["Volume"]),
                "Times Average": round(times_avg, 1),
                "Price Change %": round(
                    ((row["Close"] - row["Open"]) / row["Open"]) * 100, 2
                ) if row["Open"] != 0 else 0
            })
    return pd.DataFrame(anomalies)


def generate_summary(ticker, data, big_moves_df, volume_anomalies_df):
    total_return = ((data["Close"].iloc[-1] - data["Close"].iloc[0]) / data["Close"].iloc[0]) * 100
    profit_months = len(big_moves_df[big_moves_df["Type"] == "PROFIT"]) if not big_moves_df.empty else 0
    loss_months = len(big_moves_df[big_moves_df["Type"] == "LOSS"]) if not big_moves_df.empty else 0
    volume_spikes = len(volume_anomalies_df) if not volume_anomalies_df.empty else 0

    high = data["Close"].max()
    low = data["Close"].min()

    summary = f"""
    **{ticker} Summary (last {years} years):**

    - Total return: **{total_return:.2f}%**
    - Highest price: Rs {float(high):.2f}
    - Lowest price: Rs {float(low):.2f}
    - Big PROFIT months: {profit_months}
    - Big LOSS months: {loss_months}
    - Unusual volume spike days: {volume_spikes}

    This is a summary of **past data only**. No one can guarantee the future
    will follow the same pattern. Please do your own research before making
    any decision.
    """
    return summary


if analyze_btn:
    with st.spinner("Fetching data..."):
        try:
            data = fetch_data(ticker_input, years)
        except Exception as e:
            st.error(f"Could not fetch data. Error: {e}")
            data = None

    if data is not None and not data.empty:
        st.subheader(f"{ticker_input} - Price History")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Closing Price"))
        fig.update_layout(xaxis_title="Date", yaxis_title="Price (Rs)", height=450)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Big Profit / Loss Events")
        big_moves_df = find_big_moves(data, threshold)
        if not big_moves_df.empty:
            st.dataframe(big_moves_df, use_container_width=True)
        else:
            st.info("No months found above the selected threshold.")

        st.subheader("Volume Anomaly Detection")
        st.caption("Days where trading volume was unusually high compared to the recent average.")
        volume_anomalies_df = find_volume_anomalies(data, volume_threshold)
        if not volume_anomalies_df.empty:
            st.dataframe(volume_anomalies_df, use_container_width=True)
        else:
            st.info("No unusual volume spikes found at this threshold.")

        st.subheader("Analysis Summary")
        st.markdown(generate_summary(ticker_input, data, big_moves_df, volume_anomalies_df))

    elif data is not None and data.empty:
        st.warning("No data found for this symbol. Please check the symbol (e.g. TCS.NS)")

else:
    st.info("Enter a stock symbol in the sidebar and click 'Run Analysis'.")
