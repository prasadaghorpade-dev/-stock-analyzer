import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock History Analyzer", layout="wide")
st.title("📊 Stock History & Profit-Loss Analyzer")
st.caption("Fakt past data cha analysis. Prediction nahi. Nirnay tumcha!")

st.sidebar.header("Stock Nivda")
ticker_input = st.sidebar.text_input(
    "Stock Symbol taka (NSE sathi .NS lava)",
    value="RELIANCE.NS",
    help="Example: RELIANCE.NS, TCS.NS, INFY.NS, TATAMOTORS.NS"
)

years = st.sidebar.slider("Kiti varsh cha data baghaycha?", 1, 10, 5)
threshold = st.sidebar.slider(
    "Mothi halchal (%) kiti mhanaychi?", 5, 30, 10,
    help="Ya percentage peksha jast mahinyacha badal 'mothi ghatna' mhanun dakhavla jail"
)

analyze_btn = st.sidebar.button("Analysis Suru Kara")


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


def generate_summary(ticker, data, big_moves_df):
    total_return = ((data["Close"].iloc[-1] - data["Close"].iloc[0]) / data["Close"].iloc[0]) * 100
    profit_months = len(big_moves_df[big_moves_df["Type"] == "PROFIT"]) if not big_moves_df.empty else 0
    loss_months = len(big_moves_df[big_moves_df["Type"] == "LOSS"]) if not big_moves_df.empty else 0

    high = data["Close"].max()
    low = data["Close"].min()

    summary = f"""
    **{ticker} cha Summary (nivडलेल्या {years} varshasathi):**

    - Ekun return: **{total_return:.2f}%**
    - Sarvat jasti kimmat: ₹{float(high):.2f}
    - Sarvat kami kimmat: ₹{float(low):.2f}
    - Mothi PROFIT months: {profit_months}
    - Mothi LOSS months: {loss_months}

    Ha fakt past data cha summary aahe. Future madhe asach hoil
    yachi koni guarantee deu shakat nahi. Nirnay ghenyapurvi swataha research kara.
    """
    return summary


if analyze_btn:
    with st.spinner("Data ghetla jaat aahe..."):
        try:
            data = fetch_data(ticker_input, years)
        except Exception as e:
            st.error(f"Data milala nahi. Chuk: {e}")
            data = None

    if data is not None and not data.empty:
        st.subheader(f"{ticker_input} - Price History")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Closing Price"))
        fig.update_layout(xaxis_title="Date", yaxis_title="Price (₹)", height=450)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Mothya Profit / Loss chya Ghatna")
        big_moves_df = find_big_moves(data, threshold)
        if not big_moves_df.empty:
            st.dataframe(big_moves_df, use_container_width=True)
        else:
            st.info("Nivडलelya threshold peksha mothi halchal sapadli nahi.")

        st.subheader("Analysis Summary")
        st.markdown(generate_summary(ticker_input, data, big_moves_df))

    elif data is not None and data.empty:
        st.warning("Ya symbol sathi data sapadla nahi. Symbol tapasun baga (e.g. TCS.NS)")

else:
    st.info("Sidebar madhe stock symbol taka ani 'Analysis Suru Kara' button daba.")
