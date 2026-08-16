import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Risk Analyzer", layout="wide")
st.title("Stock Risk & Anomaly Analyzer")
st.caption(
    "Historical data analysis only. This is NOT a prediction tool and NOT investment advice. "
    "It does not confirm fraud - it only flags unusual patterns in public price and volume data."
)

st.info(
    "Disclaimer: Risk detection only - not fraud confirmation or investment advice. "
    "Always do your own research before making any financial decision."
)

COMPANIES = {
    "Reliance Industries": "RELIANCE.NS",
    "Tata Consultancy Services": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "State Bank of India": "SBIN.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Wipro": "WIPRO.NS",
    "ITC": "ITC.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
}

st.sidebar.header("Settings")

mode = st.sidebar.radio("Mode", ["Single Company Analysis", "Compare Companies"])

years = st.sidebar.slider("Years of history", 1, 10, 5)
price_threshold = st.sidebar.slider(
    "Big monthly price move threshold (%)", 5, 30, 10,
    help="Monthly moves above this percentage are flagged as anomalies"
)
volume_multiplier = st.sidebar.slider(
    "Volume spike sensitivity (x average)", 1.5, 5.0, 2.5, step=0.5,
    help="Days where volume is this many times the average are flagged"
)


def fetch_data(ticker, years):
    end = datetime.today()
    start = end - timedelta(days=years * 365)
    data = yf.download(ticker, start=start, end=end, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data


def find_big_monthly_moves(data, threshold_pct):
    monthly = data["Close"].resample("ME").last()
    monthly_returns = monthly.pct_change().dropna() * 100

    rows = []
    for date, ret in monthly_returns.items():
        if abs(ret) >= threshold_pct:
            move_type = "PROFIT" if ret > 0 else "LOSS"
            rows.append({
                "Month": date.strftime("%B %Y"),
                "Type": move_type,
                "Change %": round(ret, 2)
            })
    return pd.DataFrame(rows)


def detect_volume_anomalies(data, multiplier):
    avg_volume = data["Volume"].rolling(window=30, min_periods=10).mean()
    data = data.copy()
    data["Volume_Avg_30d"] = avg_volume
    data["Volume_Spike"] = data["Volume"] > (avg_volume * multiplier)
    spikes = data[data["Volume_Spike"] == True]
    return data, spikes


def detect_price_anomalies(data, daily_threshold=7):
    data = data.copy()
    data["Daily_Return_%"] = data["Close"].pct_change() * 100
    data["Price_Anomaly"] = data["Daily_Return_%"].abs() >= daily_threshold
    anomalies = data[data["Price_Anomaly"] == True]
    return data, anomalies


def calculate_risk_score(volume_spikes_count, price_anomaly_count, total_days):
    if total_days == 0:
        return 0
    volume_ratio = min(volume_spikes_count / total_days * 100, 1) * 50
    price_ratio = min(price_anomaly_count / total_days * 100, 1) * 50
    score = round(volume_ratio + price_ratio, 1)
    return min(score, 100)


def build_audit_trail(volume_spikes, price_anomalies, volume_multiplier):
    trail = []
    for date, row in volume_spikes.iterrows():
        trail.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Alert Type": "Volume Anomaly",
            "Reason": f"Volume {int(row['Volume']):,} exceeded {volume_multiplier}x average",
            "Generated At": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    for date, row in price_anomalies.iterrows():
        trail.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Alert Type": "Price Anomaly",
            "Reason": f"Daily move of {row['Daily_Return_%']:.2f}% exceeded threshold",
            "Generated At": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    if not trail:
        return pd.DataFrame(columns=["Date", "Alert Type", "Reason", "Generated At"])
    df = pd.DataFrame(trail).sort_values("Date", ascending=False)
    return df


def generate_summary(ticker, data, big_moves_df, risk_score):
    total_return = ((data["Close"].iloc[-1] - data["Close"].iloc[0]) / data["Close"].iloc[0]) * 100
    profit_months = len(big_moves_df[big_moves_df["Type"] == "PROFIT"]) if not big_moves_df.empty else 0
    loss_months = len(big_moves_df[big_moves_df["Type"] == "LOSS"]) if not big_moves_df.empty else 0
    high = data["Close"].max()
    low = data["Close"].min()

    summary = f"""
    **Summary for {ticker}:**

    - Total return over period: **{total_return:.2f}%**
    - Highest price: Rs {float(high):.2f}
    - Lowest price: Rs {float(low):.2f}
    - Months with large profit moves: {profit_months}
    - Months with large loss moves: {loss_months}
    - Early Warning Risk Score: **{risk_score}/100**

    This is a historical summary only. No guarantee is made about future performance.
    Do your own research before making any investment decision.
    """
    return summary


def risk_label(score):
    if score < 20:
        return "Low", "green"
    elif score < 50:
        return "Moderate", "orange"
    else:
        return "High", "red"


if mode == "Single Company Analysis":
    st.sidebar.subheader("Select Company")
    company_name = st.sidebar.selectbox("Company", list(COMPANIES.keys()))
    custom_ticker = st.sidebar.text_input("Or enter a custom ticker (optional, e.g. TATAPOWER.NS)", value="")
    ticker_input = custom_ticker.strip() if custom_ticker.strip() else COMPANIES[company_name]

    analyze_btn = st.sidebar.button("Run Analysis")

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
            fig.update_layout(xaxis_title="Date", yaxis_title="Price (Rs)", height=400)
            st.plotly_chart(fig, use_container_width=True)

            data_vol, volume_spikes = detect_volume_anomalies(data, volume_multiplier)
            data_price, price_anomalies = detect_price_anomalies(data)

            risk_score = calculate_risk_score(len(volume_spikes), len(price_anomalies), len(data))
            label, color = risk_label(risk_score)

            st.subheader("Early Warning Risk Score")
            col1, col2 = st.columns([1, 3])
            with col1:
                st.metric("Risk Score", f"{risk_score}/100", label)
            with col2:
                st.progress(int(risk_score))

            st.subheader("Company Risk Timeline")
            timeline_fig = go.Figure()
            timeline_fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Price", line=dict(color="lightblue")))
            if not volume_spikes.empty:
                timeline_fig.add_trace(go.Scatter(
                    x=volume_spikes.index, y=volume_spikes["Close"],
                    mode="markers", name="Volume Anomaly",
                    marker=dict(color="orange", size=9, symbol="triangle-up")
                ))
            if not price_anomalies.empty:
                timeline_fig.add_trace(go.Scatter(
                    x=price_anomalies.index, y=price_anomalies["Close"],
                    mode="markers", name="Price Anomaly",
                    marker=dict(color="red", size=9, symbol="x")
                ))
            timeline_fig.update_layout(xaxis_title="Date", yaxis_title="Price (Rs)", height=450)
            st.plotly_chart(timeline_fig, use_container_width=True)

            st.subheader("Volume Anomaly Detection")
            if not volume_spikes.empty:
                st.dataframe(
                    volume_spikes[["Close", "Volume", "Volume_Avg_30d"]].tail(20),
                    use_container_width=True
                )
            else:
                st.info("No significant volume anomalies detected at this sensitivity level.")

            st.subheader("Price Anomaly Detection (Daily)")
            if not price_anomalies.empty:
                st.dataframe(
                    price_anomalies[["Close", "Daily_Return_%"]].tail(20),
                    use_container_width=True
                )
            else:
                st.info("No significant single-day price anomalies detected.")

            st.subheader("Historical Event Backtesting (Monthly Big Moves)")
            big_moves_df = find_big_monthly_moves(data, price_threshold)
            if not big_moves_df.empty:
                st.dataframe(big_moves_df, use_container_width=True)
            else:
                st.info("No monthly moves exceeded the selected threshold.")

            st.subheader("Analysis Summary")
            st.markdown(generate_summary(ticker_input, data, big_moves_df, risk_score))

            st.subheader("Audit Trail - Every Alert and Why It Was Generated")
            audit_df = build_audit_trail(volume_spikes, price_anomalies, volume_multiplier)
            if not audit_df.empty:
                st.dataframe(audit_df, use_container_width=True)
            else:
                st.info("No alerts generated for this period.")

            st.subheader("Export Report")
            csv_data = data.to_csv().encode("utf-8")
            st.download_button(
                "Download Price Data (CSV)",
                data=csv_data,
                file_name=f"{ticker_input}_data.csv",
                mime="text/csv"
            )
            if not audit_df.empty:
                audit_csv = audit_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download Audit Trail (CSV)",
                    data=audit_csv,
                    file_name=f"{ticker_input}_audit_trail.csv",
                    mime="text/csv"
                )

        elif data is not None and data.empty:
            st.warning("No data found for this symbol. Please check the ticker (e.g. TCS.NS).")
    else:
        st.info("Select a company in the sidebar and click 'Run Analysis'.")

else:
    st.sidebar.subheader("Select Companies to Compare")
    selected_names = st.sidebar.multiselect(
        "Companies", list(COMPANIES.keys()),
        default=list(COMPANIES.keys())[:2]
    )
    compare_btn = st.sidebar.button("Compare")

    if compare_btn:
        if len(selected_names) < 2:
            st.warning("Please select at least 2 companies to compare.")
        else:
            st.subheader("Normalized Price Comparison (Base = 100)")
            fig = go.Figure()
            summary_rows = []

            for name in selected_names:
                ticker = COMPANIES[name]
                try:
                    data = fetch_data(ticker, years)
                except Exception as e:
                    st.error(f"Could not fetch data for {name}: {e}")
                    continue

                if data.empty:
                    continue

                normalized = (data["Close"] / data["Close"].iloc[0]) * 100
                fig.add_trace(go.Scatter(x=data.index, y=normalized, name=name))

                data_vol, volume_spikes = detect_volume_anomalies(data, volume_multiplier)
                data_price, price_anomalies = detect_price_anomalies(data)
                risk_score = calculate_risk_score(len(volume_spikes), len(price_anomalies), len(data))
                total_return = ((data["Close"].iloc[-1] - data["Close"].iloc[0]) / data["Close"].iloc[0]) * 100

                summary_rows.append({
                    "Company": name,
                    "Ticker": ticker,
                    "Total Return %": round(total_return, 2),
                    "Risk Score": risk_score,
                    "Volume Anomalies": len(volume_spikes),
                    "Price Anomalies": len(price_anomalies)
                })

            fig.update_layout(xaxis_title="Date", yaxis_title="Normalized Price (Base=100)", height=450)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Risk Dashboard")
            if summary_rows:
                st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)
    else:
        st.info("Select at least 2 companies in the sidebar and click 'Compare'.")
