import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ---------------------------------------------------------------
# PAGE CONFIG & STYLING
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Market Intelligence | Early Warning",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-header {
        color: #9CA3AF;
        font-size: 1rem;
        margin-top: 0px;
        margin-bottom: 1rem;
    }
    .risk-badge-low {
        background-color: #14532d;
        color: #bbf7d0;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    .risk-badge-moderate {
        background-color: #78350f;
        color: #fde68a;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    .risk-badge-high {
        background-color: #7f1d1d;
        color: #fecaca;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    .disclaimer-box {
        background-color: #1f2937;
        border-left: 4px solid #f59e0b;
        padding: 12px 16px;
        border-radius: 6px;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<p class="main-header">Market Intelligence & Early Warning</p>',
    unsafe_allow_html=True
)
st.markdown(
    '<p class="sub-header">Market analysis • Risk intelligence • Early-warning signals • Paper trading</p>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="disclaimer-box">
<b>Disclaimer:</b> This tool performs statistical risk detection on public price, volume and news data only.
It does <b>not</b> confirm fraud, insider trading, or manipulation, and it is <b>not</b> investment advice.
All flags are automated pattern signals meant for educational research. Always verify independently.
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# COMPANY LIST (10 companies for study)
# ---------------------------------------------------------------
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

SECTORS = {
    "RELIANCE.NS": "Energy & Conglomerate",
    "TCS.NS": "Information Technology",
    "INFY.NS": "Information Technology",
    "HDFCBANK.NS": "Banking & Finance",
    "ICICIBANK.NS": "Banking & Finance",
    "SBIN.NS": "Banking & Finance",
    "TATAMOTORS.NS": "Automobile",
    "WIPRO.NS": "Information Technology",
    "ITC.NS": "FMCG",
    "BHARTIARTL.NS": "Telecom",
}

NIFTY_INDEX = "^NSEI"

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []
if "analyst_notes" not in st.session_state:
    st.session_state.analyst_notes = {}

# ---------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------
st.sidebar.markdown(
    """
    <div style="padding: 8px 0 18px 0;">
        <h2 style="margin:0;">📈 Market Intelligence</h2>
        <p style="margin:4px 0 0 0; opacity:0.65; font-size:0.85rem;">
            Early Warning & Research
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 Navigation")
mode = st.sidebar.radio("Mode", ["Single Company Analysis", "Compare Companies", "Market Screener"])
research_mode = st.sidebar.checkbox("Research Mode (show raw data & extra stats)", value=False)
years = st.sidebar.slider("Years of history", 1, 10, 5)
price_threshold = st.sidebar.slider(
    "Big monthly price move threshold (%)", 5, 30, 10,
    help="Monthly moves above this percentage are flagged as anomalies"
)
volume_multiplier = st.sidebar.slider(
    "Volume spike sensitivity (x average)", 1.5, 5.0, 2.5, step=0.5,
    help="Days where volume is this many times the 30-day average are flagged"
)
pump_dump_window = st.sidebar.slider(
    "Pump & dump detection window (days)", 5, 30, 10,
    help="Window used to detect a rapid rise followed by a rapid fall"
)

# ---------------------------------------------------------------
# CORE DATA FUNCTIONS
# ---------------------------------------------------------------

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
            rows.append({"Month": date.strftime("%B %Y"), "Type": move_type, "Change %": round(ret, 2)})
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


def detect_pump_and_dump(data, window_days, rise_threshold=25, fall_threshold=-20):
    """
    Rule-based heuristic: flags periods where price rose sharply within the window
    and then fell sharply within the same or following window.
    This is a simple statistical pattern flag, not a confirmed manipulation detector.
    """
    data = data.copy()
    close = data["Close"]
    rolling_max = close.rolling(window=window_days, min_periods=3).max()
    rolling_min_after = close[::-1].rolling(window=window_days, min_periods=3).min()[::-1]

    rise_pct = ((rolling_max - close.shift(window_days)) / close.shift(window_days)) * 100
    fall_pct = ((rolling_min_after - close) / close) * 100

    flagged_dates = []
    for date in data.index:
        try:
            r = rise_pct.loc[date]
            f = fall_pct.loc[date]
            if pd.notna(r) and pd.notna(f) and r >= rise_threshold and f <= fall_threshold:
                flagged_dates.append(date)
        except Exception:
            continue

    pattern_df = data.loc[data.index.isin(flagged_dates)]
    return pattern_df


def detect_volume_price_divergence(data, volume_multiplier, price_move_cap=1.5):
    """
    Flags days with unusually high volume but very little price movement.
    Can indicate wash-trading-like activity, but is only a statistical signal.
    """
    data = data.copy()
    avg_volume = data["Volume"].rolling(window=30, min_periods=10).mean()
    data["Volume_Avg_30d"] = avg_volume
    data["Daily_Return_%"] = data["Close"].pct_change() * 100
    condition = (data["Volume"] > (avg_volume * volume_multiplier)) & (data["Daily_Return_%"].abs() < price_move_cap)
    divergence = data[condition]
    return divergence


def calculate_risk_score(volume_spikes_count, price_anomaly_count, pump_dump_count, divergence_count, total_days):
    if total_days == 0:
        return 0
    volume_ratio = min(volume_spikes_count / total_days * 100, 1) * 30
    price_ratio = min(price_anomaly_count / total_days * 100, 1) * 30
    pump_dump_ratio = min(pump_dump_count / total_days * 100, 1) * 25
    divergence_ratio = min(divergence_count / total_days * 100, 1) * 15
    score = round(volume_ratio + price_ratio + pump_dump_ratio + divergence_ratio, 1)
    return min(score, 100)


def risk_label(score):
    if score < 20:
        return "Low", "risk-badge-low"
    elif score < 50:
        return "Moderate", "risk-badge-moderate"
    else:
        return "High", "risk-badge-high"


def build_audit_trail(volume_spikes, price_anomalies, pump_dump_df, divergence_df, volume_multiplier):
    trail = []
    for date, row in volume_spikes.iterrows():
        trail.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Alert Type": "Volume Anomaly",
            "Reason": f"Volume {int(row['Volume']):,} exceeded {volume_multiplier}x the 30-day average",
            "Generated At": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    for date, row in price_anomalies.iterrows():
        trail.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Alert Type": "Price Anomaly",
            "Reason": f"Daily move of {row['Daily_Return_%']:.2f}% exceeded the set threshold",
            "Generated At": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    for date in pump_dump_df.index:
        trail.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Alert Type": "Pump & Dump Pattern",
            "Reason": "Sharp price rise followed by a sharp fall within the detection window",
            "Generated At": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    for date in divergence_df.index:
        trail.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Alert Type": "Volume-Price Divergence",
            "Reason": "Unusually high volume with very little price movement",
            "Generated At": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    if not trail:
        return pd.DataFrame(columns=["Date", "Alert Type", "Reason", "Generated At"])
    return pd.DataFrame(trail).sort_values("Date", ascending=False)


def fetch_news(ticker):
    try:
        stock = yf.Ticker(ticker)
        news_items = stock.news
        if not news_items:
            return pd.DataFrame(columns=["Date", "Title", "Publisher"])
        rows = []
        for item in news_items[:15]:
            content = item.get("content", item)
            title = content.get("title", "No title")
            provider = content.get("provider", {})
            publisher = provider.get("displayName", "Unknown") if isinstance(provider, dict) else "Unknown"
            pub_date = content.get("pubDate", "")
            rows.append({"Date": pub_date, "Title": title, "Publisher": publisher})
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame(columns=["Date", "Title", "Publisher"])


def match_news_to_anomalies(news_df, volume_spikes, price_anomalies):
    if news_df.empty:
        return pd.DataFrame(columns=["Anomaly Date", "Anomaly Type", "Possible Related News"])

    news_df = news_df.copy()
    news_df["Date_parsed"] = pd.to_datetime(news_df["Date"], errors="coerce", utc=True).dt.tz_localize(None)

    anomaly_dates = [(d, "Volume Anomaly") for d in volume_spikes.index] + \
                     [(d, "Price Anomaly") for d in price_anomalies.index]

    matches = []
    for date, atype in anomaly_dates:
        window_start = date - pd.Timedelta(days=3)
        window_end = date + pd.Timedelta(days=3)
        nearby = news_df[(news_df["Date_parsed"] >= window_start) & (news_df["Date_parsed"] <= window_end)]
        headline = nearby.iloc[0]["Title"] if not nearby.empty else "No matching news found nearby"
        matches.append({"Anomaly Date": date.strftime("%Y-%m-%d"), "Anomaly Type": atype, "Possible Related News": headline})

    if not matches:
        return pd.DataFrame(columns=["Anomaly Date", "Anomaly Type", "Possible Related News"])
    return pd.DataFrame(matches).sort_values("Anomaly Date", ascending=False)


def generate_ai_style_explanation(ticker, risk_score, volume_count, price_count, pump_dump_count,
                                   divergence_count, total_return, news_matched_count):
    label, _ = risk_label(risk_score)
    lines = [f"**Automated Risk Explanation for {ticker}**", ""]

    if risk_score < 20:
        lines.append(
            f"Over the selected period, {ticker} shows a **Low** risk score of {risk_score}/100. "
            f"Price and volume behaved close to normal historical patterns, with only "
            f"{volume_count} volume anomalies and {price_count} price anomalies detected. "
            f"No significant pump-and-dump or volume-price divergence patterns were found."
        )
    elif risk_score < 50:
        lines.append(
            f"{ticker} shows a **Moderate** risk score of {risk_score}/100. "
            f"There were {volume_count} unusual volume days, {price_count} unusual price-move days, "
            f"{pump_dump_count} possible pump-and-dump pattern windows, and {divergence_count} "
            f"volume-price divergence flags. This suggests periods of higher-than-normal activity, "
            f"which can happen around results, sector news, or broader market moves. "
            f"It does not by itself indicate wrongdoing."
        )
    else:
        lines.append(
            f"{ticker} shows a **High** risk score of {risk_score}/100, driven by {volume_count} volume "
            f"anomalies, {price_count} price anomalies, {pump_dump_count} pump-and-dump pattern windows, "
            f"and {divergence_count} volume-price divergence flags. This level of unusual activity is "
            f"worth a closer look, but remains only a statistical flag based on public price and volume "
            f"data - it is not proof of fraud or manipulation."
        )

    if news_matched_count > 0:
        lines.append(
            f"\n{news_matched_count} of the flagged anomaly dates had related news within a 3-day window, "
            f"which may help explain some of the unusual activity."
        )
    else:
        lines.append(
            "\nNo directly matching news was found near the flagged dates in the available news feed. "
            "This does not confirm or rule out any cause."
        )

    lines.append(
        f"\nOverall return over the selected period was {total_return:.2f}%. "
        "This explanation is generated by rules applied to historical data, not by a financial expert, "
        "and should not be treated as investment advice."
    )
    return "\n".join(lines)


def generate_summary(ticker, data, big_moves_df, risk_score):
    total_return = ((data["Close"].iloc[-1] - data["Close"].iloc[0]) / data["Close"].iloc[0]) * 100
    profit_months = len(big_moves_df[big_moves_df["Type"] == "PROFIT"]) if not big_moves_df.empty else 0
    loss_months = len(big_moves_df[big_moves_df["Type"] == "LOSS"]) if not big_moves_df.empty else 0
    high = data["Close"].max()
    low = data["Close"].min()
    return f"""
- Total return over period: **{total_return:.2f}%**
- Highest price: Rs {float(high):.2f}
- Lowest price: Rs {float(low):.2f}
- Months with large profit moves: {profit_months}
- Months with large loss moves: {loss_months}
- Early Warning Risk Score: **{risk_score}/100**

This is a historical summary only. No guarantee is made about future performance.
"""


def data_quality_score(data):
    """Simple % of expected trading days actually present with no gaps/nulls."""
    if data.empty:
        return 0
    null_pct = data[["Close", "Volume"]].isna().mean().mean() * 100
    score = round(100 - null_pct, 1)
    return max(0, min(score, 100))


def model_confidence_score(total_days, dq_score):
    """Heuristic confidence based on sample size and data quality."""
    if total_days < 60:
        size_score = 40
    elif total_days < 250:
        size_score = 70
    else:
        size_score = 95
    confidence = round((size_score * 0.6) + (dq_score * 0.4), 1)
    return min(confidence, 100)


def detect_correlation_break(data, ticker, window=30):
    """Compares rolling correlation between stock and Nifty index; flags breakdowns."""
    try:
        index_data = fetch_data(NIFTY_INDEX, years=max(1, years))
        if index_data.empty:
            return None, pd.DataFrame()
        merged = pd.DataFrame({
            "stock": data["Close"],
            "index": index_data["Close"]
        }).dropna()
        if len(merged) < window + 5:
            return None, pd.DataFrame()
        stock_ret = merged["stock"].pct_change()
        index_ret = merged["index"].pct_change()
        rolling_corr = stock_ret.rolling(window=window).corr(index_ret)
        breaks = rolling_corr[rolling_corr < 0.1]
        return rolling_corr, breaks
    except Exception:
        return None, pd.DataFrame()


def what_changed_analysis(data):
    """Compares first half vs second half of the selected period."""
    if len(data) < 20:
        return {}
    midpoint = len(data) // 2
    first_half = data.iloc[:midpoint]
    second_half = data.iloc[midpoint:]

    first_return = ((first_half["Close"].iloc[-1] - first_half["Close"].iloc[0]) / first_half["Close"].iloc[0]) * 100
    second_return = ((second_half["Close"].iloc[-1] - second_half["Close"].iloc[0]) / second_half["Close"].iloc[0]) * 100
    first_avg_vol = first_half["Volume"].mean()
    second_avg_vol = second_half["Volume"].mean()
    vol_change_pct = ((second_avg_vol - first_avg_vol) / first_avg_vol) * 100 if first_avg_vol else 0

    return {
        "first_half_return": round(first_return, 2),
        "second_half_return": round(second_return, 2),
        "avg_volume_change_pct": round(vol_change_pct, 2),
        "first_half_volatility": round(first_half["Close"].pct_change().std() * 100, 2),
        "second_half_volatility": round(second_half["Close"].pct_change().std() * 100, 2),
    }


def run_market_screener(years, volume_multiplier, price_threshold, pump_dump_window):
    """Runs anomaly detection across all companies for market-wide and cross-company views."""
    rows = []
    all_anomaly_dates = {}
    for name, ticker in COMPANIES.items():
        try:
            data = fetch_data(ticker, years)
        except Exception:
            continue
        if data.empty:
            continue

        _, volume_spikes = detect_volume_anomalies(data, volume_multiplier)
        _, price_anomalies = detect_price_anomalies(data)
        pump_dump_df = detect_pump_and_dump(data, pump_dump_window)
        divergence_df = detect_volume_price_divergence(data, volume_multiplier)

        risk_score = calculate_risk_score(
            len(volume_spikes), len(price_anomalies), len(pump_dump_df), len(divergence_df), len(data)
        )
        total_return = ((data["Close"].iloc[-1] - data["Close"].iloc[0]) / data["Close"].iloc[0]) * 100
        dq = data_quality_score(data)
        confidence = model_confidence_score(len(data), dq)

        rows.append({
            "Company": name, "Ticker": ticker, "Sector": SECTORS.get(ticker, "Other"),
            "Risk Score": risk_score, "Total Return %": round(total_return, 2),
            "Volume Anomalies": len(volume_spikes), "Price Anomalies": len(price_anomalies),
            "Pump & Dump Flags": len(pump_dump_df), "Data Quality": dq, "Model Confidence": confidence
        })

        recent_anomaly_dates = set(volume_spikes.index[-10:]) | set(price_anomalies.index[-10:])
        for d in recent_anomaly_dates:
            all_anomaly_dates.setdefault(d, []).append(name)

    screener_df = pd.DataFrame(rows)

    cross_company_rows = []
    for date, companies in all_anomaly_dates.items():
        if len(companies) >= 2:
            cross_company_rows.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Companies Flagged Together": ", ".join(companies),
                "Count": len(companies)
            })
    cross_df = pd.DataFrame(cross_company_rows).sort_values("Date", ascending=False) if cross_company_rows else pd.DataFrame()

    return screener_df, cross_df


# ---------------------------------------------------------------
# SINGLE COMPANY MODE
# ---------------------------------------------------------------
if mode == "Single Company Analysis":
    st.sidebar.subheader("Select Company")
    company_name = st.sidebar.selectbox("Company", list(COMPANIES.keys()))
    custom_ticker = st.sidebar.text_input("Or enter a custom ticker (optional)", value="")
    ticker_input = custom_ticker.strip() if custom_ticker.strip() else COMPANIES[company_name]
    analyze_btn = st.sidebar.button("Run Analysis", type="primary")

    if analyze_btn:
        with st.spinner("Fetching data and running risk analysis..."):
            try:
                data = fetch_data(ticker_input, years)
            except Exception as e:
                st.error(f"Could not fetch data. Error: {e}")
                data = None

        if data is not None and not data.empty:
            data_vol, volume_spikes = detect_volume_anomalies(data, volume_multiplier)
            data_price, price_anomalies = detect_price_anomalies(data)
            pump_dump_df = detect_pump_and_dump(data, pump_dump_window)
            divergence_df = detect_volume_price_divergence(data, volume_multiplier)

            risk_score = calculate_risk_score(
                len(volume_spikes), len(price_anomalies), len(pump_dump_df), len(divergence_df), len(data)
            )
            label, badge_class = risk_label(risk_score)
            total_return = ((data["Close"].iloc[-1] - data["Close"].iloc[0]) / data["Close"].iloc[0]) * 100

            dq_score = data_quality_score(data)
            confidence_score = model_confidence_score(len(data), dq_score)

            # Top metrics row
            header_col, watch_col = st.columns([4, 1])
            with header_col:
                st.markdown(f"### {ticker_input}")
            with watch_col:
                if ticker_input in st.session_state.watchlist:
                    if st.button("Remove from Watchlist"):
                        st.session_state.watchlist.remove(ticker_input)
                        st.rerun()
                else:
                    if st.button("Add to Watchlist"):
                        st.session_state.watchlist.append(ticker_input)
                        st.rerun()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Return", f"{total_return:.2f}%")
            c2.metric("Risk Score", f"{risk_score}/100")
            c3.metric("Highest Price", f"Rs {data['Close'].max():.2f}")
            c4.metric("Lowest Price", f"Rs {data['Close'].min():.2f}")
            st.markdown(f'<span class="{badge_class}">{label} Risk</span>', unsafe_allow_html=True)
            st.progress(int(risk_score))

            cq1, cq2 = st.columns(2)
            cq1.metric("Data Quality Score", f"{dq_score}/100")
            cq2.metric("Model Confidence Score", f"{confidence_score}/100")
            st.write("")

            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "Overview", "Anomaly Detection", "News & AI Explanation",
                "Backtesting & Timeline", "Audit Trail & Export",
                "Investigation Workspace", "Paper Trading"
            ])

            with tab1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Closing Price"))
                fig.update_layout(xaxis_title="Date", yaxis_title="Price (Rs)", height=420)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("#### Analysis Summary")
                st.markdown(generate_summary(ticker_input, data, find_big_monthly_moves(data, price_threshold), risk_score))

            with tab2:
                st.markdown("#### Volume Anomaly Detection")
                if not volume_spikes.empty:
                    st.dataframe(volume_spikes[["Close", "Volume", "Volume_Avg_30d"]].tail(20), use_container_width=True)
                else:
                    st.info("No significant volume anomalies detected at this sensitivity.")

                st.markdown("#### Price Anomaly Detection (Daily)")
                if not price_anomalies.empty:
                    st.dataframe(price_anomalies[["Close", "Daily_Return_%"]].tail(20), use_container_width=True)
                else:
                    st.info("No significant single-day price anomalies detected.")

                st.markdown("#### Pump & Dump Pattern Detection")
                st.caption("Flags a sharp rise followed by a sharp fall within the selected window. Statistical pattern only.")
                if not pump_dump_df.empty:
                    st.dataframe(pump_dump_df[["Close", "Volume"]].tail(20), use_container_width=True)
                else:
                    st.info("No pump-and-dump style patterns detected.")

                st.markdown("#### Volume-Price Divergence")
                st.caption("Flags high volume with very little price movement - a possible wash-trading style signal.")
                if not divergence_df.empty:
                    st.dataframe(divergence_df[["Close", "Volume", "Daily_Return_%"]].tail(20), use_container_width=True)
                else:
                    st.info("No volume-price divergence detected.")

            with tab3:
                st.markdown("#### Recent News")
                with st.spinner("Fetching recent news..."):
                    news_df = fetch_news(ticker_input)
                if not news_df.empty:
                    st.dataframe(news_df[["Date", "Title", "Publisher"]], use_container_width=True)
                else:
                    st.info("No recent news available for this ticker from the data source.")

                news_match_df = match_news_to_anomalies(news_df, volume_spikes, price_anomalies)
                st.markdown("#### Anomaly Dates Matched with Nearby News (+/- 3 days)")
                if not news_match_df.empty:
                    st.dataframe(news_match_df, use_container_width=True)
                else:
                    st.info("No anomalies to match against news.")

                news_matched_count = 0
                if not news_match_df.empty:
                    news_matched_count = len(news_match_df[news_match_df["Possible Related News"] != "No matching news found nearby"])

                st.markdown("#### AI Risk Analysis & Explanation")
                st.caption("Rule-based automated explanation - not a live AI model call.")
                explanation_text = generate_ai_style_explanation(
                    ticker_input, risk_score, len(volume_spikes), len(price_anomalies),
                    len(pump_dump_df), len(divergence_df), total_return, news_matched_count
                )
                st.markdown(explanation_text)

            with tab4:
                st.markdown("#### Company Risk Timeline")
                timeline_fig = go.Figure()
                timeline_fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Price", line=dict(color="lightblue")))
                if not volume_spikes.empty:
                    timeline_fig.add_trace(go.Scatter(
                        x=volume_spikes.index, y=volume_spikes["Close"], mode="markers",
                        name="Volume Anomaly", marker=dict(color="orange", size=9, symbol="triangle-up")
                    ))
                if not price_anomalies.empty:
                    timeline_fig.add_trace(go.Scatter(
                        x=price_anomalies.index, y=price_anomalies["Close"], mode="markers",
                        name="Price Anomaly", marker=dict(color="red", size=9, symbol="x")
                    ))
                if not pump_dump_df.empty:
                    timeline_fig.add_trace(go.Scatter(
                        x=pump_dump_df.index, y=pump_dump_df["Close"], mode="markers",
                        name="Pump & Dump Pattern", marker=dict(color="magenta", size=10, symbol="star")
                    ))
                timeline_fig.update_layout(xaxis_title="Date", yaxis_title="Price (Rs)", height=450)
                st.plotly_chart(timeline_fig, use_container_width=True)

                st.markdown("#### Historical Event Backtesting (Monthly Big Moves)")
                big_moves_df = find_big_monthly_moves(data, price_threshold)
                if not big_moves_df.empty:
                    st.dataframe(big_moves_df, use_container_width=True)
                else:
                    st.info("No monthly moves exceeded the selected threshold.")

            with tab5:
                st.markdown("#### Audit Trail - Every Alert and Why It Was Generated")
                audit_df = build_audit_trail(volume_spikes, price_anomalies, pump_dump_df, divergence_df, volume_multiplier)
                if not audit_df.empty:
                    st.dataframe(audit_df, use_container_width=True)
                else:
                    st.info("No alerts generated for this period.")

                st.markdown("#### Export Report")
                csv_data = data.to_csv().encode("utf-8")
                st.download_button("Download Price Data (CSV)", data=csv_data,
                                    file_name=f"{ticker_input}_data.csv", mime="text/csv")
                if not audit_df.empty:
                    audit_csv = audit_df.to_csv(index=False).encode("utf-8")
                    st.download_button("Download Audit Trail (CSV)", data=audit_csv,
                                        file_name=f"{ticker_input}_audit_trail.csv", mime="text/csv")

            with tab6:
                st.markdown("#### What-Changed Analysis")
                st.caption("Compares the first half vs second half of the selected period.")
                changes = what_changed_analysis(data)
                if changes:
                    wc1, wc2 = st.columns(2)
                    wc1.metric("First Half Return", f"{changes['first_half_return']}%")
                    wc2.metric("Second Half Return", f"{changes['second_half_return']}%")
                    wc3, wc4 = st.columns(2)
                    wc3.metric("Volume Change", f"{changes['avg_volume_change_pct']}%")
                    wc4.metric("Volatility Change",
                               f"{changes['first_half_volatility']}% -> {changes['second_half_volatility']}%")
                else:
                    st.info("Not enough data for a what-changed comparison.")

                st.markdown("#### Correlation Break Detection (vs Nifty 50)")
                st.caption("Flags when the stock's 30-day rolling correlation with the market index drops sharply.")
                rolling_corr, corr_breaks = detect_correlation_break(data, ticker_input)
                if rolling_corr is not None and not rolling_corr.empty:
                    corr_fig = go.Figure()
                    corr_fig.add_trace(go.Scatter(x=rolling_corr.index, y=rolling_corr, name="Rolling Correlation"))
                    corr_fig.update_layout(xaxis_title="Date", yaxis_title="Correlation with Nifty 50", height=350)
                    st.plotly_chart(corr_fig, use_container_width=True)
                    if not corr_breaks.empty:
                        st.warning(f"{len(corr_breaks)} days found where correlation with the index broke down (below 0.1).")
                    else:
                        st.info("No significant correlation breakdown detected.")
                else:
                    st.info("Could not compute correlation with the index for this period.")

                st.markdown("#### Analyst Investigation Notes")
                st.caption("Write your own observations here. Notes are kept only for this session.")
                existing_note = st.session_state.analyst_notes.get(ticker_input, "")
                note_text = st.text_area("Notes", value=existing_note, height=150, key=f"note_{ticker_input}")
                if st.button("Save Notes"):
                    st.session_state.analyst_notes[ticker_input] = note_text
                    st.success("Notes saved for this session.")

                if research_mode:
                    st.markdown("#### Research Mode - Raw Data")
                    st.dataframe(data.tail(100), use_container_width=True)
                    st.markdown("Descriptive statistics:")
                    st.dataframe(data[["Close", "Volume"]].describe(), use_container_width=True)

            with tab7:
                st.markdown("#### Paper Trading (Virtual Simulation)")
                st.caption(
                    "Practice buying and selling with virtual money at the latest available closing price. "
                    "No real money is involved. Your portfolio resets if you refresh or close the app."
                )

                if "paper_cash" not in st.session_state:
                    st.session_state.paper_cash = 100000.0
                if "paper_holdings" not in st.session_state:
                    st.session_state.paper_holdings = {}
                if "paper_log" not in st.session_state:
                    st.session_state.paper_log = []

                latest_price = float(data["Close"].iloc[-1])
                current_shares = st.session_state.paper_holdings.get(ticker_input, 0)

                pc1, pc2, pc3 = st.columns(3)
                pc1.metric("Virtual Cash", f"Rs {st.session_state.paper_cash:,.2f}")
                pc2.metric("Latest Price", f"Rs {latest_price:.2f}")
                pc3.metric(f"Shares Held ({ticker_input})", f"{current_shares}")

                trade_col1, trade_col2, trade_col3 = st.columns(3)
                with trade_col1:
                    qty = st.number_input("Quantity", min_value=1, value=1, step=1, key="paper_qty")
                with trade_col2:
                    if st.button("Buy"):
                        cost = qty * latest_price
                        if cost > st.session_state.paper_cash:
                            st.error("Not enough virtual cash for this purchase.")
                        else:
                            st.session_state.paper_cash -= cost
                            st.session_state.paper_holdings[ticker_input] = current_shares + qty
                            st.session_state.paper_log.append({
                                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "Ticker": ticker_input, "Action": "BUY", "Qty": qty,
                                "Price": round(latest_price, 2), "Total": round(cost, 2)
                            })
                            st.rerun()
                with trade_col3:
                    if st.button("Sell"):
                        if qty > current_shares:
                            st.error("You do not own enough shares to sell this quantity.")
                        else:
                            proceeds = qty * latest_price
                            st.session_state.paper_cash += proceeds
                            st.session_state.paper_holdings[ticker_input] = current_shares - qty
                            st.session_state.paper_log.append({
                                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "Ticker": ticker_input, "Action": "SELL", "Qty": qty,
                                "Price": round(latest_price, 2), "Total": round(proceeds, 2)
                            })
                            st.rerun()

                st.markdown("#### Portfolio Holdings")
                holdings_rows = []
                total_holdings_value = 0
                for held_ticker, shares in st.session_state.paper_holdings.items():
                    if shares <= 0:
                        continue
                    if held_ticker == ticker_input:
                        price_used = latest_price
                    else:
                        price_used = None
                    value = shares * price_used if price_used else None
                    holdings_rows.append({
                        "Ticker": held_ticker, "Shares": shares,
                        "Price Used": f"Rs {price_used:.2f}" if price_used else "Open this stock to price it",
                        "Value": f"Rs {value:,.2f}" if value else "-"
                    })
                    if value:
                        total_holdings_value += value
                if holdings_rows:
                    st.dataframe(pd.DataFrame(holdings_rows), use_container_width=True)
                    st.metric("Total Portfolio Value (cash + priced holdings)",
                               f"Rs {st.session_state.paper_cash + total_holdings_value:,.2f}")
                else:
                    st.info("No holdings yet. Use Buy above to start your simulation.")

                st.markdown("#### Trade Log")
                if st.session_state.paper_log:
                    st.dataframe(pd.DataFrame(st.session_state.paper_log), use_container_width=True)
                    log_csv = pd.DataFrame(st.session_state.paper_log).to_csv(index=False).encode("utf-8")
                    st.download_button("Download Trade Log (CSV)", data=log_csv,
                                        file_name="paper_trade_log.csv", mime="text/csv")
                else:
                    st.info("No trades yet.")

        elif data is not None and data.empty:
            st.warning("No data found for this symbol. Please check the ticker (e.g. TCS.NS).")
    else:
        st.info("Select a company in the sidebar and click 'Run Analysis' to begin.")

# ---------------------------------------------------------------
# COMPARE COMPANIES MODE
# ---------------------------------------------------------------
elif mode == "Compare Companies":
    st.sidebar.subheader("Select Companies to Compare")
    selected_names = st.sidebar.multiselect("Companies", list(COMPANIES.keys()), default=list(COMPANIES.keys())[:2])
    compare_btn = st.sidebar.button("Compare", type="primary")

    if compare_btn:
        if len(selected_names) < 2:
            st.warning("Please select at least 2 companies to compare.")
        else:
            st.markdown("### Normalized Price Comparison (Base = 100)")
            fig = go.Figure()
            summary_rows = []

            with st.spinner("Analyzing selected companies..."):
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

                    _, volume_spikes = detect_volume_anomalies(data, volume_multiplier)
                    _, price_anomalies = detect_price_anomalies(data)
                    pump_dump_df = detect_pump_and_dump(data, pump_dump_window)
                    divergence_df = detect_volume_price_divergence(data, volume_multiplier)

                    risk_score = calculate_risk_score(
                        len(volume_spikes), len(price_anomalies), len(pump_dump_df), len(divergence_df), len(data)
                    )
                    total_return = ((data["Close"].iloc[-1] - data["Close"].iloc[0]) / data["Close"].iloc[0]) * 100

                    summary_rows.append({
                        "Company": name, "Ticker": ticker, "Total Return %": round(total_return, 2),
                        "Risk Score": risk_score, "Volume Anomalies": len(volume_spikes),
                        "Price Anomalies": len(price_anomalies), "Pump & Dump Flags": len(pump_dump_df),
                        "Volume-Price Divergence": len(divergence_df)
                    })

            fig.update_layout(xaxis_title="Date", yaxis_title="Normalized Price (Base=100)", height=450)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Risk Dashboard")
            if summary_rows:
                st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)
    else:
        st.info("Select at least 2 companies in the sidebar and click 'Compare'.")

# ---------------------------------------------------------------
# MARKET SCREENER MODE
# ---------------------------------------------------------------
else:
    st.markdown("### Market-Wide Screener - All Tracked Companies")
    st.caption(
        "Runs anomaly detection across all 10 tracked companies at once. "
        "Useful for spotting sector-wide risk or multiple companies flagged on the same date."
    )
    screener_btn = st.sidebar.button("Run Market Screener", type="primary")

    if screener_btn:
        with st.spinner("Scanning all tracked companies..."):
            screener_df, cross_df = run_market_screener(years, volume_multiplier, price_threshold, pump_dump_window)

        if not screener_df.empty:
            st.markdown("#### Risk Heatmap")
            heatmap_fig = go.Figure(data=go.Heatmap(
                z=[screener_df["Risk Score"].tolist()],
                x=screener_df["Company"].tolist(),
                y=["Risk Score"],
                colorscale=[[0, "#14532d"], [0.5, "#78350f"], [1, "#7f1d1d"]],
                zmin=0, zmax=100,
                text=[screener_df["Risk Score"].tolist()],
                texttemplate="%{text}",
            ))
            heatmap_fig.update_layout(height=250)
            st.plotly_chart(heatmap_fig, use_container_width=True)

            st.markdown("#### Sector-Wise Risk Analysis")
            sector_avg = screener_df.groupby("Sector")["Risk Score"].mean().reset_index().sort_values("Risk Score", ascending=False)
            sector_fig = go.Figure(go.Bar(x=sector_avg["Sector"], y=sector_avg["Risk Score"]))
            sector_fig.update_layout(xaxis_title="Sector", yaxis_title="Average Risk Score", height=350)
            st.plotly_chart(sector_fig, use_container_width=True)

            st.markdown("#### Full Screener Table")
            st.dataframe(screener_df.sort_values("Risk Score", ascending=False), use_container_width=True)

            st.markdown("#### Market-Wide Anomaly Summary")
            high_risk = screener_df[screener_df["Risk Score"] >= 50]
            if not high_risk.empty:
                st.warning(f"{len(high_risk)} companies currently show High risk scores: "
                           f"{', '.join(high_risk['Company'].tolist())}")
            else:
                st.info("No companies currently show High risk scores.")

            st.markdown("#### Cross-Company Pattern Detection")
            st.caption("Dates where 2 or more companies were flagged with anomalies at the same time - "
                       "may indicate a market-wide event rather than a company-specific issue.")
            if not cross_df.empty:
                st.dataframe(cross_df, use_container_width=True)
            else:
                st.info("No overlapping multi-company anomaly dates found in the recent window.")

            screener_csv = screener_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Screener Report (CSV)", data=screener_csv,
                                file_name="market_screener_report.csv", mime="text/csv")
        else:
            st.error("Could not fetch data for the screener. Please try again.")
    else:
        st.info("Click 'Run Market Screener' in the sidebar to scan all tracked companies.")

    if st.session_state.watchlist:
        st.markdown("### Your Watchlist")
        st.write(", ".join(st.session_state.watchlist))
