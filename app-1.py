import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ---------------------------------------------------------------
# PAGE CONFIG & STYLING
# ---------------------------------------------------------------
st.set_page_config(page_title="Market Intelligence | Early Warning", layout="wide", page_icon="📈", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp {
        background-color: #000000;
    }
    [data-testid="stSidebar"] {
        background-color: #050505;
        border-right: 1px solid #1a1a1a;
    }
    .main-header {
        font-family: 'Courier New', monospace;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0px;
        color: #00ff88;
        letter-spacing: 1px;
    }
    .sub-header {
        font-family: 'Courier New', monospace;
        color: #6b7280;
        font-size: 0.95rem;
        margin-top: 0px;
        margin-bottom: 1rem;
    }
    .risk-badge-low {
        background-color: #001a0d;
        color: #00ff88;
        border: 1px solid #00ff88;
        padding: 6px 16px;
        border-radius: 4px;
        font-weight: 700;
        font-family: 'Courier New', monospace;
        display: inline-block;
    }
    .risk-badge-moderate {
        background-color: #1a1400;
        color: #ffcc00;
        border: 1px solid #ffcc00;
        padding: 6px 16px;
        border-radius: 4px;
        font-weight: 700;
        font-family: 'Courier New', monospace;
        display: inline-block;
    }
    .risk-badge-high {
        background-color: #1a0008;
        color: #ff3366;
        border: 1px solid #ff3366;
        padding: 6px 16px;
        border-radius: 4px;
        font-weight: 700;
        font-family: 'Courier New', monospace;
        display: inline-block;
    }
    .disclaimer-box {
        background-color: #0a0a0a;
        border-left: 4px solid #ffcc00;
        padding: 12px 16px;
        border-radius: 4px;
        font-size: 0.85rem;
        margin-bottom: 1.5rem;
        color: #cccccc;
    }
    .section-historical {
        background-color: #050505;
        border: 1px solid #1a1a1a;
        border-left: 4px solid #3b82f6;
        padding: 14px 18px;
        border-radius: 6px;
        margin: 12px 0px;
    }
    .section-live-trading {
        background-color: #050505;
        border: 1px solid #1a1a1a;
        border-left: 4px solid #00ff88;
        padding: 14px 18px;
        border-radius: 6px;
        margin: 12px 0px;
    }
    .ticker-tag {
        font-family: 'Courier New', monospace;
        font-size: 0.75rem;
        color: #6b7280;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    div[data-testid="stMetric"] {
        background-color: #0a0a0a;
        border: 1px solid #1a1a1a;
        border-radius: 6px;
        padding: 10px;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Courier New', monospace;
    }
    .stButton > button {
        font-family: 'Courier New', monospace;
        font-weight: 700;
    }
    .buy-button button {
        background-color: #001a0d !important;
        color: #00ff88 !important;
        border: 1px solid #00ff88 !important;
    }
    .sell-button button {
        background-color: #1a0008 !important;
        color: #ff3366 !important;
        border: 1px solid #ff3366 !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📈 MARKET INTELLIGENCE | EARLY WARNING</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">&gt; market analysis // risk intelligence // early-warning signals // paper trading</p>',
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

INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK",
}

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

if "jump_mode" in st.session_state:
    st.session_state["mode_radio"] = st.session_state.pop("jump_mode")

mode = st.sidebar.radio(
    "Mode",
    ["Daily Market Update", "Single Company Analysis", "Portfolio", "Compare Companies", "Market Screener", "Methodology & Disclaimer"],
    key="mode_radio"
)

st.sidebar.markdown("---")
st.sidebar.markdown('<p class="ticker-tag">⚡ QUICK JUMP - COMPANIES</p>', unsafe_allow_html=True)
st.sidebar.caption("Tap a company to instantly open its live chart, historical analysis and paper trading.")
for c_name, c_ticker in COMPANIES.items():
    if st.sidebar.button(c_name, key=f"quickjump_{c_ticker}", use_container_width=True):
        st.session_state["jump_mode"] = "Single Company Analysis"
        st.session_state["jump_company"] = c_name
        st.session_state["auto_run"] = True
        st.rerun()

st.sidebar.markdown("---")
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


def answer_stock_question(question, context):
    """
    Keyword-based Q&A over already-computed data for one company.
    context is a dict with: ticker, data, risk_score, volume_spikes, price_anomalies,
    pump_dump_df, divergence_df, news_df, total_return, dq_score, confidence_score, fundamentals
    """
    q = question.lower()
    ticker = context["ticker"]
    answers = []

    if any(w in q for w in ["risk", "score", "safe", "dangerous", "danger"]):
        label, _ = risk_label(context["risk_score"])
        answers.append(
            f"**Risk:** {ticker} currently has a risk score of {context['risk_score']}/100 ({label}). "
            f"This is based on {len(context['volume_spikes'])} volume anomalies, "
            f"{len(context['price_anomalies'])} price anomalies, {len(context['pump_dump_df'])} pump-and-dump "
            f"style flags, and {len(context['divergence_df'])} volume-price divergence flags over the selected period."
        )

    if any(w in q for w in ["volume", "trading activity", "turnover"]):
        vol_count = len(context["volume_spikes"])
        if vol_count > 0:
            last_spike = context["volume_spikes"].index[-1].strftime("%Y-%m-%d")
            answers.append(
                f"**Volume:** {vol_count} unusual volume days were detected in the selected period. "
                f"The most recent one was on {last_spike}, where volume was significantly above the 30-day average."
            )
        else:
            answers.append("**Volume:** No unusual volume spikes were detected in the selected period.")

    if any(w in q for w in ["price", "move", "crash", "spike", "anomaly", "fall", "drop", "jump"]):
        price_count = len(context["price_anomalies"])
        if price_count > 0:
            last_move = context["price_anomalies"].index[-1].strftime("%Y-%m-%d")
            last_ret = context["price_anomalies"]["Daily_Return_%"].iloc[-1]
            answers.append(
                f"**Price moves:** {price_count} single-day price anomalies were detected. "
                f"The most recent was on {last_move}, a move of {last_ret:.2f}% in a single day."
            )
        else:
            answers.append("**Price moves:** No unusual single-day price moves were detected in the selected period.")

    if any(w in q for w in ["news", "headline", "announcement", "event"]):
        news_df = context.get("news_df")
        if news_df is not None and not news_df.empty:
            top_news = news_df.iloc[0]
            answers.append(f"**Recent news:** The most recent headline found is: \"{top_news['Title']}\" ({top_news.get('Publisher', 'Unknown source')}).")
        else:
            answers.append("**Recent news:** No recent news was found for this ticker from the available data source.")

    if any(w in q for w in ["return", "trend", "performance", "gain", "loss", "growth"]):
        answers.append(f"**Overall performance:** {ticker} has moved {context['total_return']:.2f}% over the selected period.")

    if any(w in q for w in ["manipulat", "pump", "dump", "fraud", "fake", "scam"]):
        pd_count = len(context["pump_dump_df"])
        div_count = len(context["divergence_df"])
        answers.append(
            f"**Manipulation-style patterns:** {pd_count} pump-and-dump style pattern windows and {div_count} "
            f"volume-price divergence flags were detected. These are statistical flags only - they do not confirm "
            f"actual manipulation or fraud."
        )

    if any(w in q for w in ["fundamental", "pe", "p/e", "eps", "revenue", "profit", "debt", "roe"]):
        fundamentals = context.get("fundamentals", {})
        if fundamentals:
            f_lines = [f"- {k}: {format_fundamental_value(k, v)}" for k, v in fundamentals.items()]
            answers.append("**Fundamentals:**\n" + "\n".join(f_lines))
        else:
            answers.append("**Fundamentals:** Data unavailable for this ticker from the free data source.")

    if any(w in q for w in ["confidence", "quality", "reliable", "trust"]):
        answers.append(
            f"**Data reliability:** Data quality score is {context['dq_score']}/100 and model confidence is "
            f"{context['confidence_score']}/100, based on sample size and completeness of the data."
        )

    if any(w in q for w in ["buy", "sell", "should i", "invest", "worth it", "good stock", "recommend"]):
        answers.append(
            "**On buying or selling:** This tool cannot tell you whether to buy or sell - that would be investment "
            "advice, which this project does not provide. What it can tell you is the historical risk score, "
            "price/volume patterns, and fundamentals shown above, so you can research and decide for yourself. "
            "You can practice your own decision using the Paper Trading section with virtual money."
        )

    if not answers:
        answers.append(
            f"I could not match your question to a specific topic for {ticker}. "
            "Try asking about: risk score, volume, price moves, news, returns/trend, fundamentals, "
            "manipulation patterns, or data confidence."
        )

    return "\n\n".join(answers)


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


def get_daily_snapshot():
    """Fetches last 2 trading days for indices and all tracked companies to build a daily update."""
    index_rows = []
    for name, ticker in INDICES.items():
        try:
            data = yf.download(ticker, period="5d", progress=False)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            if len(data) >= 2:
                last_close = data["Close"].iloc[-1]
                prev_close = data["Close"].iloc[-2]
                change_pct = ((last_close - prev_close) / prev_close) * 100
                index_rows.append({
                    "Index": name, "Last Close": round(float(last_close), 2),
                    "Change %": round(float(change_pct), 2), "Date": data.index[-1].strftime("%Y-%m-%d")
                })
        except Exception:
            continue

    company_rows = []
    for name, ticker in COMPANIES.items():
        try:
            data = yf.download(ticker, period="5d", progress=False)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            if len(data) >= 2:
                last_close = data["Close"].iloc[-1]
                prev_close = data["Close"].iloc[-2]
                change_pct = ((last_close - prev_close) / prev_close) * 100
                last_volume = data["Volume"].iloc[-1]
                avg_volume = data["Volume"].mean()
                volume_ratio = last_volume / avg_volume if avg_volume else 0
                company_rows.append({
                    "Company": name, "Ticker": ticker, "Sector": SECTORS.get(ticker, "Other"),
                    "Last Close": round(float(last_close), 2), "Change %": round(float(change_pct), 2),
                    "Volume": int(last_volume), "Volume vs Avg": round(float(volume_ratio), 2)
                })
        except Exception:
            continue

    return pd.DataFrame(index_rows), pd.DataFrame(company_rows)


def calculate_technical_indicators(data):
    df = data.copy()
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA50"] = df["Close"].rolling(window=50).mean()
    df["MA200"] = df["Close"].rolling(window=200).mean()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    df["Resistance"] = df["Close"].rolling(window=20).max()
    df["Support"] = df["Close"].rolling(window=20).min()

    return df


def get_company_profile(ticker):
    try:
        info = yf.Ticker(ticker).info
        return {
            "Name": info.get("longName", ticker),
            "Sector": info.get("sector", SECTORS.get(ticker, "Unknown")),
            "Industry": info.get("industry", "Unknown"),
            "Market Cap": info.get("marketCap"),
            "52 Week High": info.get("fiftyTwoWeekHigh"),
            "52 Week Low": info.get("fiftyTwoWeekLow"),
            "Website": info.get("website", "N/A"),
        }
    except Exception:
        return {}


def get_fundamentals(ticker):
    try:
        info = yf.Ticker(ticker).info
        return {
            "Revenue (TTM)": info.get("totalRevenue"),
            "Profit Margin": info.get("profitMargins"),
            "EPS (TTM)": info.get("trailingEps"),
            "P/E Ratio": info.get("trailingPE"),
            "P/B Ratio": info.get("priceToBook"),
            "Debt to Equity": info.get("debtToEquity"),
            "Return on Equity": info.get("returnOnEquity"),
            "Dividend Yield": info.get("dividendYield"),
        }
    except Exception:
        return {}


def format_fundamental_value(key, value):
    if value is None:
        return "Data unavailable"
    if key in ["Profit Margin", "Return on Equity", "Dividend Yield"]:
        return f"{value * 100:.2f}%" if isinstance(value, (int, float)) else "Data unavailable"
    if key == "Revenue (TTM)":
        return f"Rs {value:,.0f}" if isinstance(value, (int, float)) else "Data unavailable"
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return "Data unavailable"


def get_corporate_calendar(ticker):
    try:
        stock = yf.Ticker(ticker)
        cal = stock.calendar
        rows = []
        if isinstance(cal, dict) and cal:
            for key, val in cal.items():
                rows.append({"Event": key, "Details": str(val)})
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def filter_by_timeframe(data, timeframe):
    if timeframe == "1D":
        return data.tail(2)
    elif timeframe == "1W":
        return data.tail(5)
    elif timeframe == "1M":
        return data.tail(22)
    elif timeframe == "1Y":
        return data.tail(252)
    else:
        return data


def find_breakouts_breakdowns(data):
    df = data.copy()
    df["Resistance"] = df["Close"].rolling(window=20).max().shift(1)
    df["Support"] = df["Close"].rolling(window=20).min().shift(1)
    breakout = df[df["Close"] > df["Resistance"]]
    breakdown = df[df["Close"] < df["Support"]]
    return breakout, breakdown


# ---------------------------------------------------------------
# DAILY MARKET UPDATE MODE
# ---------------------------------------------------------------
if mode == "Daily Market Update":
    st.markdown("### Daily Market Update")
    st.caption(
        "Snapshot based on the most recent available trading data (may be delayed, not real-time). "
        "Covers Nifty 50, Sensex, Bank Nifty, and the 10 tracked companies."
    )
    st.markdown(
        f'<div style="background-color:#1f2937;padding:6px 12px;border-radius:6px;font-size:0.85rem;'
        f'display:inline-block;">Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M")} '
        f'(local device time) | Data status: delayed, not real-time</div>',
        unsafe_allow_html=True
    )
    st.write("")
    refresh_btn = st.sidebar.button("Refresh Daily Update", type="primary")

    if refresh_btn or "daily_snapshot_loaded" not in st.session_state:
        with st.spinner("Fetching latest market snapshot..."):
            index_df, company_df = get_daily_snapshot()
        st.session_state.daily_snapshot_loaded = True
        st.session_state.index_df = index_df
        st.session_state.company_df = company_df
    else:
        index_df = st.session_state.get("index_df", pd.DataFrame())
        company_df = st.session_state.get("company_df", pd.DataFrame())

    if not index_df.empty:
        avg_index_change = index_df["Change %"].mean()
        if avg_index_change > 0.3:
            trend_label, trend_class = "Bullish", "risk-badge-low"
        elif avg_index_change < -0.3:
            trend_label, trend_class = "Bearish", "risk-badge-high"
        else:
            trend_label, trend_class = "Neutral", "risk-badge-moderate"
        st.markdown(f'**Market Trend:** <span class="{trend_class}">{trend_label}</span>', unsafe_allow_html=True)
        st.write("")

        st.markdown("#### Market Indices")
        idx_cols = st.columns(len(index_df))
        for i, row in index_df.iterrows():
            with idx_cols[i]:
                st.metric(row["Index"], f"{row['Last Close']:,}", f"{row['Change %']}%")
        st.caption(f"As of {index_df['Date'].iloc[0]}")
    else:
        st.info("Could not fetch index data right now.")

    if not company_df.empty:
        st.markdown("#### Top Gainers (Tracked Companies)")
        gainers = company_df.sort_values("Change %", ascending=False).head(5)
        st.dataframe(gainers[["Company", "Last Close", "Change %", "Sector"]], use_container_width=True)

        st.markdown("#### Top Losers (Tracked Companies)")
        losers = company_df.sort_values("Change %", ascending=True).head(5)
        st.dataframe(losers[["Company", "Last Close", "Change %", "Sector"]], use_container_width=True)

        st.markdown("#### Most Active by Volume")
        most_active = company_df.sort_values("Volume", ascending=False).head(5)
        st.dataframe(most_active[["Company", "Volume", "Last Close", "Change %"]], use_container_width=True)

        st.markdown("#### Unusual Volume Today (vs Average)")
        unusual = company_df[company_df["Volume vs Avg"] >= 1.5].sort_values("Volume vs Avg", ascending=False)
        if not unusual.empty:
            st.dataframe(unusual[["Company", "Volume vs Avg", "Change %"]], use_container_width=True)
        else:
            st.info("No unusual volume activity detected today among tracked companies.")

        st.markdown("#### Sector Performance Today")
        sector_perf = company_df.groupby("Sector")["Change %"].mean().reset_index().sort_values("Change %", ascending=False)
        sector_fig = go.Figure(go.Bar(x=sector_perf["Sector"], y=sector_perf["Change %"]))
        sector_fig.update_layout(xaxis_title="Sector", yaxis_title="Average Change %", height=350)
        st.plotly_chart(sector_fig, use_container_width=True)

        st.markdown("#### Full Snapshot Table")
        st.dataframe(company_df.sort_values("Change %", ascending=False), use_container_width=True)

        st.markdown("#### Open a Company - View P&L and Paper Trade")
        st.caption("Pick a company below to jump straight to its price, risk analysis and paper trading screen.")
        jump_col1, jump_col2 = st.columns([3, 1])
        with jump_col1:
            company_pick = st.selectbox("Company", company_df["Company"].tolist(), key="dashboard_company_pick")
        with jump_col2:
            st.write("")
            st.write("")
            if st.button("Open & Trade", type="primary"):
                st.session_state["jump_mode"] = "Single Company Analysis"
                st.session_state["jump_company"] = company_pick
                st.session_state["auto_run"] = True
                st.rerun()

        st.markdown("#### Alert Center")
        st.caption("Simple price and volume alerts for tracked companies, based on today's snapshot.")
        alert_rows = []
        for _, row in company_df.iterrows():
            if abs(row["Change %"]) >= 5:
                alert_rows.append({"Company": row["Company"], "Alert": f"Price moved {row['Change %']}% today", "Type": "Price Alert"})
            if row["Volume vs Avg"] >= 2:
                alert_rows.append({"Company": row["Company"], "Alert": f"Volume is {row['Volume vs Avg']}x the average", "Type": "Volume Alert"})
            if row["Company"] in [c for c in st.session_state.watchlist if c in COMPANIES.values()] or \
               COMPANIES.get(row["Company"]) in st.session_state.watchlist:
                alert_rows.append({"Company": row["Company"], "Alert": "On your watchlist", "Type": "Watchlist Alert"})
        if alert_rows:
            st.dataframe(pd.DataFrame(alert_rows), use_container_width=True)
        else:
            st.info("No alerts triggered today for tracked companies.")
    else:
        st.info("Click 'Refresh Daily Update' in the sidebar to load today's snapshot.")



# ---------------------------------------------------------------
# SINGLE COMPANY MODE
# ---------------------------------------------------------------
elif mode == "Single Company Analysis":
    st.sidebar.subheader("Select Company")

    if "jump_company" in st.session_state:
        st.session_state["company_select"] = st.session_state.pop("jump_company")

    company_name = st.sidebar.selectbox("Company", list(COMPANIES.keys()), key="company_select")
    custom_ticker = st.sidebar.text_input("Or enter a custom ticker (optional)", value="")
    ticker_input = custom_ticker.strip() if custom_ticker.strip() else COMPANIES[company_name]

    auto_run = st.session_state.pop("auto_run", False)
    analyze_btn = st.sidebar.button("Run Analysis", type="primary") or auto_run

    if auto_run:
        st.info(f"Opened {company_name} from the dashboard. Analysis is running automatically below.")

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

            # Quick P&L + Quick Trade panel (visible without opening a tab)
            if "paper_cash" not in st.session_state:
                st.session_state.paper_cash = 100000.0
            if "paper_holdings" not in st.session_state:
                st.session_state.paper_holdings = {}
            if "paper_log" not in st.session_state:
                st.session_state.paper_log = []

            latest_price_quick = float(data["Close"].iloc[-1])
            shares_held_quick = st.session_state.paper_holdings.get(ticker_input, 0)
            log_df_quick = pd.DataFrame(st.session_state.paper_log)
            ticker_log_quick = log_df_quick[log_df_quick["Ticker"] == ticker_input] if not log_df_quick.empty else pd.DataFrame()
            avg_buy_quick = 0
            if not ticker_log_quick.empty and not ticker_log_quick[ticker_log_quick["Action"] == "BUY"].empty:
                buy_rows = ticker_log_quick[ticker_log_quick["Action"] == "BUY"]
                avg_buy_quick = buy_rows["Total"].sum() / buy_rows["Qty"].sum()
            unrealized_pnl_quick = (latest_price_quick - avg_buy_quick) * shares_held_quick if avg_buy_quick else 0

            st.markdown('<div class="section-live-trading">', unsafe_allow_html=True)
            st.markdown('<p class="ticker-tag">🟢 LIVE PAPER TRADING (virtual money)</p>', unsafe_allow_html=True)
            latest_data_date = data.index[-1].strftime("%Y-%m-%d")
            st.caption(f"Price as of last available trading data: {latest_data_date}. Not real-time - free data source updates with a delay.")
            qp1, qp2, qp3, qp4 = st.columns(4)
            qp1.metric("Latest Price", f"Rs {latest_price_quick:.2f}")
            qp2.metric("Shares Held", f"{shares_held_quick}")
            qp3.metric("Avg Buy Price", f"Rs {avg_buy_quick:.2f}" if avg_buy_quick else "N/A")
            qp4.metric("Unrealized P&L", f"Rs {unrealized_pnl_quick:,.2f}")

            qt1, qt2, qt3, qt4 = st.columns(4)
            with qt1:
                quick_qty = st.number_input("Qty", min_value=1, value=1, step=1, key="quick_qty")
            with qt2:
                quick_term = st.selectbox("Term", ["Short-Term", "Long-Term"], key="quick_term")
            with qt3:
                st.write("")
                st.write("")
                st.markdown('<div class="buy-button">', unsafe_allow_html=True)
                if st.button("BUY", key="quick_buy_btn"):
                    cost = quick_qty * latest_price_quick
                    if cost > st.session_state.paper_cash:
                        st.error("Not enough virtual cash.")
                    else:
                        st.session_state.paper_cash -= cost
                        st.session_state.paper_holdings[ticker_input] = shares_held_quick + quick_qty
                        st.session_state.paper_log.append({
                            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Ticker": ticker_input, "Action": "BUY", "Qty": quick_qty,
                            "Price": round(latest_price_quick, 2), "Total": round(cost, 2),
                            "Term": quick_term
                        })
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with qt4:
                st.write("")
                st.write("")
                st.markdown('<div class="sell-button">', unsafe_allow_html=True)
                if st.button("SELL", key="quick_sell_btn"):
                    if quick_qty > shares_held_quick:
                        st.error("You do not own enough shares.")
                    else:
                        proceeds = quick_qty * latest_price_quick
                        st.session_state.paper_cash += proceeds
                        st.session_state.paper_holdings[ticker_input] = shares_held_quick - quick_qty
                        st.session_state.paper_log.append({
                            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Ticker": ticker_input, "Action": "SELL", "Qty": quick_qty,
                            "Price": round(latest_price_quick, 2), "Total": round(proceeds, 2),
                            "Term": quick_term
                        })
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            st.caption(f"Virtual cash available: Rs {st.session_state.paper_cash:,.2f}. This is simulated trading only - no real money is used.")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<p class="ticker-tag">🔵 HISTORICAL ANALYSIS (past data - not live, no trades here)</p>', unsafe_allow_html=True)

            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
                "Overview", "Chart & Indicators", "Anomaly Detection", "News & AI Explanation",
                "Backtesting & Timeline", "Audit Trail & Export",
                "Investigation Workspace", "Paper Trading"
            ])

            with tab1:
                st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} (local device time) | Data status: delayed, not real-time")
                profile = get_company_profile(ticker_input)
                if profile:
                    st.markdown("#### Company Profile")
                    p1, p2, p3 = st.columns(3)
                    p1.write(f"**Name:** {profile.get('Name', '-')}")
                    p1.write(f"**Sector:** {profile.get('Sector', '-')}")
                    p2.write(f"**Industry:** {profile.get('Industry', '-')}")
                    mcap = profile.get("Market Cap")
                    p2.write(f"**Market Cap:** Rs {mcap:,.0f}" if mcap else "**Market Cap:** N/A")
                    p3.write(f"**52W High:** Rs {profile.get('52 Week High', 0):.2f}" if profile.get('52 Week High') else "**52W High:** N/A")
                    p3.write(f"**52W Low:** Rs {profile.get('52 Week Low', 0):.2f}" if profile.get('52 Week Low') else "**52W Low:** N/A")
                    st.write("")

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Closing Price"))
                fig.update_layout(xaxis_title="Date", yaxis_title="Price (Rs)", height=420)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("#### Analysis Summary")
                st.markdown(generate_summary(ticker_input, data, find_big_monthly_moves(data, price_threshold), risk_score))

                st.markdown("#### Fundamentals")
                st.caption("Where data is not available from the free data source, it is shown as 'Data unavailable' rather than an estimate.")
                fundamentals = get_fundamentals(ticker_input)
                if fundamentals:
                    f1, f2, f3, f4 = st.columns(4)
                    cols = [f1, f2, f3, f4]
                    for i, (key, val) in enumerate(fundamentals.items()):
                        cols[i % 4].metric(key, format_fundamental_value(key, val))
                else:
                    st.info("Fundamental data unavailable for this ticker.")

                st.markdown("#### Corporate Calendar")
                cal_df = get_corporate_calendar(ticker_input)
                if not cal_df.empty:
                    st.dataframe(cal_df, use_container_width=True)
                else:
                    st.info("No upcoming corporate events found for this ticker from the free data source.")

            with tab2:
                st.markdown("#### Professional Chart")
                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    chart_type = st.radio("Chart Type", ["Candlestick", "Line"], horizontal=True, key="chart_type")
                with chart_col2:
                    timeframe = st.radio("Timeframe", ["1D", "1W", "1M", "1Y", "5Y"], horizontal=True, index=4, key="timeframe")

                tf_data = filter_by_timeframe(data, timeframe)
                ind_data = calculate_technical_indicators(data)
                tf_ind_data = filter_by_timeframe(ind_data, timeframe)

                show_ma = st.checkbox("Show Moving Averages (20/50/200)", value=True)
                show_support_resistance = st.checkbox("Show Support / Resistance (20-day)", value=False)

                price_fig = go.Figure()
                if chart_type == "Candlestick" and len(tf_data) > 1:
                    price_fig.add_trace(go.Candlestick(
                        x=tf_data.index, open=tf_data["Open"], high=tf_data["High"],
                        low=tf_data["Low"], close=tf_data["Close"], name="Price"
                    ))
                else:
                    price_fig.add_trace(go.Scatter(x=tf_data.index, y=tf_data["Close"], name="Close", line=dict(color="lightblue")))

                if show_ma:
                    price_fig.add_trace(go.Scatter(x=tf_ind_data.index, y=tf_ind_data["MA20"], name="MA 20", line=dict(width=1)))
                    price_fig.add_trace(go.Scatter(x=tf_ind_data.index, y=tf_ind_data["MA50"], name="MA 50", line=dict(width=1)))
                    price_fig.add_trace(go.Scatter(x=tf_ind_data.index, y=tf_ind_data["MA200"], name="MA 200", line=dict(width=1)))
                if show_support_resistance:
                    price_fig.add_trace(go.Scatter(x=tf_ind_data.index, y=tf_ind_data["Resistance"], name="Resistance", line=dict(color="red", dash="dot")))
                    price_fig.add_trace(go.Scatter(x=tf_ind_data.index, y=tf_ind_data["Support"], name="Support", line=dict(color="green", dash="dot")))

                price_fig.update_layout(height=450, xaxis_title="Date", yaxis_title="Price (Rs)", xaxis_rangeslider_visible=False)
                st.plotly_chart(price_fig, use_container_width=True)

                st.markdown("#### Volume")
                vol_fig = go.Figure(go.Bar(x=tf_data.index, y=tf_data["Volume"]))
                vol_fig.update_layout(height=200, xaxis_title="Date", yaxis_title="Volume")
                st.plotly_chart(vol_fig, use_container_width=True)

                st.markdown("#### RSI (14)")
                rsi_fig = go.Figure()
                rsi_fig.add_trace(go.Scatter(x=tf_ind_data.index, y=tf_ind_data["RSI"], name="RSI"))
                rsi_fig.add_hline(y=70, line_dash="dot", line_color="red")
                rsi_fig.add_hline(y=30, line_dash="dot", line_color="green")
                rsi_fig.update_layout(height=250, yaxis_title="RSI")
                st.plotly_chart(rsi_fig, use_container_width=True)

                st.markdown("#### MACD")
                macd_fig = go.Figure()
                macd_fig.add_trace(go.Scatter(x=tf_ind_data.index, y=tf_ind_data["MACD"], name="MACD"))
                macd_fig.add_trace(go.Scatter(x=tf_ind_data.index, y=tf_ind_data["MACD_Signal"], name="Signal"))
                macd_fig.update_layout(height=250, yaxis_title="MACD")
                st.plotly_chart(macd_fig, use_container_width=True)

            with tab3:
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

            with tab4:
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

                st.markdown("---")
                st.markdown("#### 💬 Ask About This Stock")
                st.caption(
                    "Ask a question in your own words about this stock's risk, volume, price moves, news, "
                    "fundamentals, or returns. Answers are pulled from the analysis already computed above - "
                    "not a prediction, not investment advice."
                )
                user_question = st.text_input("Your question", placeholder="e.g. Why is the risk score high? What's the recent volume like?", key="stock_qa_input")
                if st.button("Get Answer", key="stock_qa_btn"):
                    if user_question.strip():
                        qa_context = {
                            "ticker": ticker_input,
                            "data": data,
                            "risk_score": risk_score,
                            "volume_spikes": volume_spikes,
                            "price_anomalies": price_anomalies,
                            "pump_dump_df": pump_dump_df,
                            "divergence_df": divergence_df,
                            "news_df": news_df,
                            "total_return": total_return,
                            "dq_score": dq_score,
                            "confidence_score": confidence_score,
                            "fundamentals": get_fundamentals(ticker_input),
                        }
                        answer = answer_stock_question(user_question, qa_context)
                        st.markdown(answer)
                    else:
                        st.warning("Type a question first.")

            with tab5:
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

            with tab6:
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

            with tab7:
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

            with tab8:
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

                trade_col1, trade_col2, trade_col3, trade_col4 = st.columns(4)
                with trade_col1:
                    qty = st.number_input("Quantity", min_value=1, value=1, step=1, key="paper_qty")
                with trade_col2:
                    trade_term = st.selectbox("Term", ["Short-Term", "Long-Term"], key="paper_term")
                with trade_col3:
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
                                "Price": round(latest_price, 2), "Total": round(cost, 2),
                                "Term": trade_term
                            })
                            st.rerun()
                with trade_col4:
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
                                "Price": round(latest_price, 2), "Total": round(proceeds, 2),
                                "Term": trade_term
                            })
                            st.rerun()

                st.markdown("#### Stop-Loss / Target Simulation")
                st.caption(
                    "Set a stop-loss and target for your current holding in this stock. "
                    "This checks against the latest available price each time you run analysis - "
                    "it does not auto-execute trades in real time."
                )
                if "paper_sl_target" not in st.session_state:
                    st.session_state.paper_sl_target = {}

                sl_col, tgt_col = st.columns(2)
                existing_sl_tgt = st.session_state.paper_sl_target.get(ticker_input, {})
                with sl_col:
                    stop_loss = st.number_input(
                        "Stop-Loss Price (Rs)", min_value=0.0,
                        value=float(existing_sl_tgt.get("stop_loss", 0.0)), key="sl_input"
                    )
                with tgt_col:
                    target_price = st.number_input(
                        "Target Price (Rs)", min_value=0.0,
                        value=float(existing_sl_tgt.get("target", 0.0)), key="tgt_input"
                    )
                if st.button("Save Stop-Loss / Target"):
                    st.session_state.paper_sl_target[ticker_input] = {
                        "stop_loss": stop_loss, "target": target_price
                    }
                    st.success("Stop-loss and target saved for this session.")

                if current_shares > 0:
                    if stop_loss > 0 and latest_price <= stop_loss:
                        st.error(f"Stop-loss triggered: latest price Rs {latest_price:.2f} is at or below stop-loss Rs {stop_loss:.2f}")
                    if target_price > 0 and latest_price >= target_price:
                        st.success(f"Target reached: latest price Rs {latest_price:.2f} is at or above target Rs {target_price:.2f}")

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

                st.markdown("#### P&L Analytics")
                if st.session_state.paper_log:
                    log_df = pd.DataFrame(st.session_state.paper_log)
                    ticker_log = log_df[log_df["Ticker"] == ticker_input]
                    total_bought = ticker_log[ticker_log["Action"] == "BUY"]["Total"].sum()
                    total_sold = ticker_log[ticker_log["Action"] == "SELL"]["Total"].sum()
                    realized_pnl = total_sold - ticker_log[ticker_log["Action"] == "SELL"]["Qty"].sum() * \
                        (ticker_log[ticker_log["Action"] == "BUY"]["Total"].sum() /
                         ticker_log[ticker_log["Action"] == "BUY"]["Qty"].sum()) if not ticker_log[ticker_log["Action"] == "BUY"].empty and not ticker_log[ticker_log["Action"] == "SELL"].empty else 0
                    unrealized_value = current_shares * latest_price
                    avg_buy_price = (ticker_log[ticker_log["Action"] == "BUY"]["Total"].sum() /
                                      ticker_log[ticker_log["Action"] == "BUY"]["Qty"].sum()) if not ticker_log[ticker_log["Action"] == "BUY"].empty else 0
                    unrealized_pnl = (latest_price - avg_buy_price) * current_shares if avg_buy_price else 0

                    pnl1, pnl2, pnl3 = st.columns(3)
                    pnl1.metric("Average Buy Price", f"Rs {avg_buy_price:.2f}" if avg_buy_price else "N/A")
                    pnl2.metric("Unrealized P&L (current holding)", f"Rs {unrealized_pnl:,.2f}")
                    pnl3.metric("Current Position Value", f"Rs {unrealized_value:,.2f}")

                    if "Term" in log_df.columns:
                        st.markdown("**Holdings by Term (all companies, current session):**")
                        term_summary = log_df.groupby("Term").agg(
                            Trades=("Action", "count"),
                            Total_Bought=("Total", lambda x: x[log_df.loc[x.index, "Action"] == "BUY"].sum()),
                            Total_Sold=("Total", lambda x: x[log_df.loc[x.index, "Action"] == "SELL"].sum())
                        ).reset_index()
                        st.dataframe(term_summary, use_container_width=True)
                else:
                    st.info("No trades yet for P&L analytics.")

                st.markdown("#### Trade Log")
                if st.session_state.paper_log:
                    full_log_df = pd.DataFrame(st.session_state.paper_log)
                    if "Term" not in full_log_df.columns:
                        full_log_df["Term"] = "Not specified"
                    st.dataframe(full_log_df, use_container_width=True)
                    log_csv = full_log_df.to_csv(index=False).encode("utf-8")
                    st.download_button("Download Trade Log (CSV)", data=log_csv,
                                        file_name="paper_trade_log.csv", mime="text/csv")
                else:
                    st.info("No trades yet.")

        elif data is not None and data.empty:
            st.warning("No data found for this symbol. Please check the ticker (e.g. TCS.NS).")
    else:
        st.info("Select a company in the sidebar and click 'Run Analysis' to begin.")

# ---------------------------------------------------------------
# PORTFOLIO MODE
# ---------------------------------------------------------------
elif mode == "Portfolio":
    st.markdown('<p class="ticker-tag">🟢 YOUR PAPER TRADING PORTFOLIO</p>', unsafe_allow_html=True)
    st.caption(
        "Consolidated view of all your simulated holdings across tracked companies. "
        "Virtual money only - resets if you refresh or close the app."
    )

    if "paper_cash" not in st.session_state:
        st.session_state.paper_cash = 100000.0
    if "paper_holdings" not in st.session_state:
        st.session_state.paper_holdings = {}
    if "paper_log" not in st.session_state:
        st.session_state.paper_log = []

    ticker_to_name = {v: k for k, v in COMPANIES.items()}
    held_tickers = {t: s for t, s in st.session_state.paper_holdings.items() if s > 0}

    if not held_tickers:
        st.info("You have no open holdings yet. Use the Quick Jump list in the sidebar to open a company and start paper trading.")
        st.metric("Virtual Cash Available", f"Rs {st.session_state.paper_cash:,.2f}")
    else:
        with st.spinner("Fetching latest prices for your holdings..."):
            log_df_all = pd.DataFrame(st.session_state.paper_log)
            portfolio_rows = []
            total_current_value = 0
            total_invested = 0

            for ticker, shares in held_tickers.items():
                try:
                    stock_data = fetch_data(ticker, 1)
                except Exception:
                    continue
                if stock_data.empty:
                    continue
                current_price = float(stock_data["Close"].iloc[-1])

                ticker_log = log_df_all[log_df_all["Ticker"] == ticker] if not log_df_all.empty else pd.DataFrame()
                avg_buy = 0
                if not ticker_log.empty and not ticker_log[ticker_log["Action"] == "BUY"].empty:
                    buy_rows = ticker_log[ticker_log["Action"] == "BUY"]
                    avg_buy = buy_rows["Total"].sum() / buy_rows["Qty"].sum()

                current_value = shares * current_price
                invested_value = shares * avg_buy if avg_buy else 0
                pnl = current_value - invested_value
                pnl_pct = (pnl / invested_value * 100) if invested_value else 0

                total_current_value += current_value
                total_invested += invested_value

                company_name = ticker_to_name.get(ticker, ticker)
                portfolio_rows.append({
                    "Company": company_name, "Ticker": ticker, "Sector": SECTORS.get(ticker, "Other"),
                    "Shares": shares, "Avg Buy Price": round(avg_buy, 2), "Current Price": round(current_price, 2),
                    "Current Value": round(current_value, 2), "P&L": round(pnl, 2), "P&L %": round(pnl_pct, 2)
                })

        if portfolio_rows:
            portfolio_df = pd.DataFrame(portfolio_rows)
            total_pnl = total_current_value - total_invested
            total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0
            total_portfolio_value = total_current_value + st.session_state.paper_cash

            pc1, pc2, pc3, pc4 = st.columns(4)
            pc1.metric("Total Portfolio Value", f"Rs {total_portfolio_value:,.2f}")
            pc2.metric("Virtual Cash", f"Rs {st.session_state.paper_cash:,.2f}")
            pc3.metric("Holdings Value", f"Rs {total_current_value:,.2f}")
            pc4.metric("Total P&L", f"Rs {total_pnl:,.2f}", f"{total_pnl_pct:.2f}%")

            st.markdown("#### Holdings")
            st.dataframe(portfolio_df, use_container_width=True)

            st.markdown("#### Sector Allocation")
            sector_alloc = portfolio_df.groupby("Sector")["Current Value"].sum().reset_index()
            alloc_fig = go.Figure(data=[go.Pie(labels=sector_alloc["Sector"], values=sector_alloc["Current Value"], hole=0.4)])
            alloc_fig.update_layout(height=400)
            st.plotly_chart(alloc_fig, use_container_width=True)

            st.markdown("#### Company Allocation")
            company_fig = go.Figure(data=[go.Pie(labels=portfolio_df["Company"], values=portfolio_df["Current Value"], hole=0.4)])
            company_fig.update_layout(height=400)
            st.plotly_chart(company_fig, use_container_width=True)

            st.markdown("#### Portfolio Risk Snapshot")
            st.caption("Average risk score across your currently held companies, based on the same anomaly detection engine used elsewhere in this app.")
            risk_rows = []
            for _, row in portfolio_df.iterrows():
                try:
                    stock_data = fetch_data(row["Ticker"], years)
                except Exception:
                    continue
                if stock_data.empty:
                    continue
                _, vs = detect_volume_anomalies(stock_data, volume_multiplier)
                _, pa = detect_price_anomalies(stock_data)
                pdd = detect_pump_and_dump(stock_data, pump_dump_window)
                dv = detect_volume_price_divergence(stock_data, volume_multiplier)
                rs = calculate_risk_score(len(vs), len(pa), len(pdd), len(dv), len(stock_data))
                risk_rows.append({"Company": row["Company"], "Risk Score": rs})
            if risk_rows:
                risk_df = pd.DataFrame(risk_rows)
                st.dataframe(risk_df, use_container_width=True)
                st.metric("Average Portfolio Risk Score", f"{risk_df['Risk Score'].mean():.1f}/100")

            portfolio_csv = portfolio_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Portfolio Report (CSV)", data=portfolio_csv,
                                file_name="portfolio_report.csv", mime="text/csv")
        else:
            st.warning("Could not fetch current prices for your holdings. Please try again.")

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
elif mode == "Market Screener":
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

            st.markdown("#### Breakouts, Breakdowns & Volatility Scanner")
            breakout_rows, volatility_rows = [], []
            for _, row in screener_df.iterrows():
                ticker = row["Ticker"]
                try:
                    stock_data = fetch_data(ticker, years)
                except Exception:
                    continue
                if stock_data.empty:
                    continue
                breakout_df, breakdown_df = find_breakouts_breakdowns(stock_data)
                daily_vol = stock_data["Close"].pct_change().std() * 100
                if not breakout_df.empty and stock_data.index[-1] in breakout_df.index:
                    breakout_rows.append({"Company": row["Company"], "Status": "Breakout (above 20-day resistance)"})
                if not breakdown_df.empty and stock_data.index[-1] in breakdown_df.index:
                    breakout_rows.append({"Company": row["Company"], "Status": "Breakdown (below 20-day support)"})
                volatility_rows.append({"Company": row["Company"], "Daily Volatility %": round(daily_vol, 2)})

            if breakout_rows:
                st.dataframe(pd.DataFrame(breakout_rows), use_container_width=True)
            else:
                st.info("No current breakouts or breakdowns detected.")

            if volatility_rows:
                vol_df = pd.DataFrame(volatility_rows).sort_values("Daily Volatility %", ascending=False)
                st.markdown("**Volatility Ranking (highest to lowest):**")
                st.dataframe(vol_df, use_container_width=True)

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

# ---------------------------------------------------------------
# METHODOLOGY & DISCLAIMER PAGE
# ---------------------------------------------------------------
else:
    st.markdown("### Methodology & Disclaimer")

    st.markdown("""
#### What this tool does
This is a student-built research tool for studying historical price, volume and news patterns
of 10 major Indian listed companies. It uses free, publicly available data (Yahoo Finance)
and applies rule-based statistical methods to flag unusual activity.

#### What this tool does NOT do
- It does **not** confirm fraud, insider trading, or market manipulation.
- It does **not** use live or real-time prices - all data is delayed (typically by minutes to a day).
- It does **not** provide investment advice or stock recommendations.
- It does **not** access paid regulatory data such as promoter pledge filings, related-party
  transaction disclosures, or corporate governance filings - these require paid institutional
  data feeds that are not available for free.

#### How the Risk Score is calculated
The Early Warning Risk Score (0-100) is a weighted combination of four rule-based signals:
- Volume anomalies (days with volume far above the 30-day average)
- Price anomalies (single-day moves beyond a set threshold)
- Pump-and-dump style patterns (sharp rise followed by a sharp fall in a short window)
- Volume-price divergence (high volume with very little price movement)

This is a statistical heuristic, not a machine-learning model trained on confirmed fraud cases,
because no such labeled dataset is freely available. Precision/recall metrics are therefore not
reported, since there is no verified ground truth to measure against.

#### Data sources
- Price, volume and news data: Yahoo Finance (via the yfinance library)
- Company sector classification: manually assigned for the 10 tracked companies

#### Paper Trading
The paper trading feature uses virtual money only. No real trades are placed. Portfolio data
is stored only for your current browser session and is lost on refresh, since this app does not
use a persistent database.

#### Intended use
This project is intended for educational purposes - to practice data analysis, pattern detection,
and software development. It is not a substitute for professional financial research or advice.
""")

    st.info(
        "If you are using this for a school project or competition, you are welcome to reference "
        "this methodology page to explain how the tool works and its limitations."
    )
