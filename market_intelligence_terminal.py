import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# ============================================================
# MARKET INTELLIGENCE TERMINAL
# Evidence-based market research / paper trading prototype
# No price prediction. No guaranteed returns.
# ============================================================

st.set_page_config(
    page_title="Market Intelligence Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- THEME -------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: #0b0f14;
}
[data-testid="stHeader"] {
    background: rgba(11,15,20,0.92);
}
[data-testid="stSidebar"] {
    background: #0e141c;
    border-right: 1px solid #202936;
}
.block-container {
    max-width: 1500px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}
h1,h2,h3 { letter-spacing: -0.02em; }
.mini {
    color:#8e9aaa;
    font-size:0.78rem;
    text-transform:uppercase;
    letter-spacing:.08em;
}
.hero {
    padding: 24px 28px;
    border:1px solid #202936;
    border-radius:18px;
    background:linear-gradient(135deg,#111923,#0d1219);
    margin-bottom:18px;
}
.card {
    background:#111821;
    border:1px solid #202936;
    border-radius:16px;
    padding:18px;
}
.metric-title { color:#8e9aaa; font-size:.78rem; text-transform:uppercase; }
.metric-value { font-size:1.65rem; font-weight:700; margin-top:5px; }
.good { color:#35c98b; }
.bad { color:#ff6678; }
.neutral { color:#b7c0cc; }
div.stButton > button {
    border-radius:10px;
    border:1px solid #2a3543;
    min-height:42px;
}
div[data-testid="stMetric"] {
    background:#111821;
    border:1px solid #202936;
    padding:12px;
    border-radius:14px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------- DATA / CONFIG ---------------------
COMPANIES = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "SBI": "SBIN.NS",
    "Hindustan Unilever": "HINDUNILVR.NS",
    "ITC": "ITC.NS",
    "Larsen & Toubro": "LT.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
}

INDEXES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK",
}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_data(ticker, period="1y"):
    try:
        df = yf.download(ticker, period=period, auto_adjust=False, progress=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.rename(columns=str.title)
        needed = ["Open", "High", "Low", "Close", "Volume"]
        for c in needed:
            if c not in df.columns:
                return None
        return df[needed].dropna()
    except Exception:
        return None

def pct_change(series):
    if len(series) < 2:
        return np.nan
    return float((series.iloc[-1] / series.iloc[-2] - 1) * 100)

def market_card(name, ticker):
    d = fetch_data(ticker, "5d")
    if d is None or len(d) < 2:
        st.metric(name, "Unavailable")
        return
    value = float(d["Close"].iloc[-1])
    chg = pct_change(d["Close"])
    st.metric(name, f"{value:,.2f}", f"{chg:+.2f}%")

def add_indicators(df):
    d = df.copy()
    d["SMA20"] = d["Close"].rolling(20).mean()
    d["SMA50"] = d["Close"].rolling(50).mean()
    delta = d["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    d["RSI"] = 100 - (100 / (1 + rs))
    d["VolAvg20"] = d["Volume"].rolling(20).mean()
    d["VolumeRatio"] = d["Volume"] / d["VolAvg20"]
    d["Return"] = d["Close"].pct_change() * 100
    d["Drawdown"] = d["Close"] / d["Close"].cummax() - 1
    return d

def evidence_summary(d):
    x = add_indicators(d).dropna()
    if x.empty:
        return {}
    last = x.iloc[-1]
    return {
        "price": float(last["Close"]),
        "return": float(last["Return"]),
        "volume_ratio": float(last["VolumeRatio"]),
        "rsi": float(last["RSI"]),
        "drawdown": float(last["Drawdown"] * 100),
        "sma20": float(last["SMA20"]),
        "sma50": float(last["SMA50"]),
    }

def classify_activity(e):
    if not e:
        return "Unavailable"
    flags = []
    if e["volume_ratio"] >= 2:
        flags.append("unusual volume")
    if abs(e["return"]) >= 4:
        flags.append("large daily movement")
    if e["rsi"] >= 70:
        flags.append("high RSI")
    elif e["rsi"] <= 30:
        flags.append("low RSI")
    return ", ".join(flags) if flags else "No major statistical flag"

def stock_chart(d, name):
    x = d.copy()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=x.index, open=x["Open"], high=x["High"],
        low=x["Low"], close=x["Close"], name="Price"
    ))
    if "SMA20" in x:
        fig.add_trace(go.Scatter(x=x.index, y=x["SMA20"], name="SMA 20", line=dict(width=1.5)))
    if "SMA50" in x:
        fig.add_trace(go.Scatter(x=x.index, y=x["SMA50"], name="SMA 50", line=dict(width=1.5)))
    fig.update_layout(
        template="plotly_dark",
        height=520,
        margin=dict(l=10,r=10,t=35,b=10),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h"),
        title=f"{name} — historical price & moving averages",
    )
    return fig

def performance_metrics(d):
    x = d.copy()
    x["Return"] = x["Close"].pct_change().fillna(0)
    equity = (1 + x["Return"]).cumprod()
    total_return = (equity.iloc[-1] - 1) * 100
    years = max((x.index[-1] - x.index[0]).days / 365.25, 1/365.25)
    cagr = ((equity.iloc[-1]) ** (1/years) - 1) * 100
    max_dd = ((equity / equity.cummax()) - 1).min() * 100
    vol = x["Return"].std() * np.sqrt(252) * 100
    return total_return, cagr, max_dd, vol

# ---------------------------- SIDEBAR -------------------------
with st.sidebar:
    st.markdown("## 📈 Market Intelligence")
    st.caption("Evidence-based market research terminal")
    st.divider()

    st.markdown("### 🧭 WORKSPACE")
    mode = st.radio(
        "Workspace",
        ["Market Home", "Stock Research", "Historical Analysis", "Paper Trading"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("### ⚙️ DATA")
    period = st.selectbox(
        "Historical window",
        ["3mo", "6mo", "1y", "2y", "5y"],
        index=2,
    )

    st.divider()
    st.caption("DATA POLICY")
    st.caption("Prices are fetched from the configured data source. Data may be delayed. This app reports observations and historical statistics; it does not predict future prices.")

# ----------------------------- HEADER -------------------------
st.markdown("""
<div class="hero">
    <div class="mini">MARKET INTELLIGENCE TERMINAL</div>
    <h1 style="margin:5px 0 3px 0;">Evidence before opinion.</h1>
    <div style="color:#9ba7b6;">
        Historical market analysis • anomaly monitoring • paper trading
    </div>
</div>
""", unsafe_allow_html=True)

# ========================== MARKET HOME ======================
if mode == "Market Home":
    st.subheader("Market Overview")
    cols = st.columns(3)
    for i, (name, ticker) in enumerate(INDEXES.items()):
        with cols[i]:
            market_card(name, ticker)

    st.markdown("### Market Watch")
    rows = []
    for company, ticker in COMPANIES.items():
        d = fetch_data(ticker, "5d")
        if d is not None and len(d) >= 2:
            rows.append({
                "Company": company,
                "Price": float(d["Close"].iloc[-1]),
                "Daily %": pct_change(d["Close"]),
                "Volume": int(d["Volume"].iloc[-1]),
            })

    if rows:
        watch = pd.DataFrame(rows)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🔥 Top Movers")
            st.dataframe(
                watch.sort_values("Daily %", ascending=False).head(5),
                use_container_width=True, hide_index=True
            )
        with c2:
            st.markdown("#### ⚠️ Unusual Volume")
            watch["Volume"] = pd.to_numeric(watch["Volume"])
            st.dataframe(
                watch.sort_values("Volume", ascending=False).head(5),
                use_container_width=True, hide_index=True
            )

        st.markdown("### Daily Research Snapshot")
        st.info("This dashboard reports current/historical observations only. No future price prediction is generated.")

# ========================== STOCK RESEARCH ====================
elif mode == "Stock Research":
    st.subheader("Stock Research")
    company = st.selectbox("Select company", list(COMPANIES.keys()))
    ticker = COMPANIES[company]
    d = fetch_data(ticker, period)

    if d is None or d.empty:
        st.error("Data is currently unavailable for this security.")
        st.stop()

    x = add_indicators(d)
    e = evidence_summary(d)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price", f"₹{e['price']:,.2f}")
    c2.metric("Daily change", f"{e['return']:+.2f}%")
    c3.metric("Volume / avg", f"{e['volume_ratio']:.2f}×")
    c4.metric("RSI(14)", f"{e['rsi']:.1f}")

    st.plotly_chart(stock_chart(x, company), use_container_width=True)

    st.markdown("### Evidence-based activity")
    st.info(classify_activity(e))

    a, b, c, dcol = st.columns(4)
    a.metric("SMA 20", f"₹{e['sma20']:,.2f}")
    b.metric("SMA 50", f"₹{e['sma50']:,.2f}")
    c.metric("Drawdown", f"{e['drawdown']:.2f}%")
    dcol.metric("Historical volatility", f"{x['Return'].std()*np.sqrt(252)*100:.2f}%")

    with st.expander("Raw historical data"):
        st.dataframe(x.tail(100), use_container_width=True)

# ======================== HISTORICAL ANALYSIS =================
elif mode == "Historical Analysis":
    st.subheader("Historical Analysis")
    company = st.selectbox("Security", list(COMPANIES.keys()))
    ticker = COMPANIES[company]
    d = fetch_data(ticker, period)

    if d is None or len(d) < 30:
        st.warning("Not enough historical data for this analysis.")
        st.stop()

    total_return, cagr, max_dd, vol = performance_metrics(d)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total return", f"{total_return:+.2f}%")
    c2.metric("CAGR", f"{cagr:+.2f}%")
    c3.metric("Max drawdown", f"{max_dd:.2f}%")
    c4.metric("Annualized volatility", f"{vol:.2f}%")

    x = d.copy()
    x["Daily Return %"] = x["Close"].pct_change() * 100
    x["Equity"] = (1 + x["Daily Return %"].fillna(0)/100).cumprod()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x.index, y=x["Equity"], name="Growth of ₹1"))
    fig.update_layout(template="plotly_dark", height=400, title="Historical growth of ₹1")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Why did historical P&L change?")
    positive = x[x["Daily Return %"] > 0]
    negative = x[x["Daily Return %"] < 0]

    p1, p2 = st.columns(2)
    with p1:
        st.markdown("#### 📈 Positive periods")
        if not positive.empty:
            best = positive.nlargest(5, "Daily Return %")[["Daily Return %"]]
            st.dataframe(best, use_container_width=True)
        st.caption("Positive P&L is mechanically caused by positive price returns in the selected historical period. This section does not infer future causes without supporting event data.")

    with p2:
        st.markdown("#### 📉 Negative periods")
        if not negative.empty:
            worst = negative.nsmallest(5, "Daily Return %")[["Daily Return %"]]
            st.dataframe(worst, use_container_width=True)
        st.caption("Negative P&L is mechanically caused by negative price returns in the selected historical period. News/event attribution requires separate verified event data.")

    st.markdown("### Historical observations")
    st.dataframe(
        x[["Close", "Daily Return %", "Equity"]].tail(120),
        use_container_width=True,
    )

# =========================== PAPER TRADING ====================
else:
    st.subheader("Paper Trading")
    if "cash" not in st.session_state:
        st.session_state.cash = 100000.0
    if "holdings" not in st.session_state:
        st.session_state.holdings = {}
    if "trades" not in st.session_state:
        st.session_state.trades = []

    company = st.selectbox("Security", list(COMPANIES.keys()))
    ticker = COMPANIES[company]
    d = fetch_data(ticker, "5d")

    if d is None or d.empty:
        st.error("Current data is unavailable.")
        st.stop()

    current = float(d["Close"].iloc[-1])
    holdings = st.session_state.holdings.get(ticker, 0)
    market_value = holdings * current
    invested = sum(
        q * float(fetch_data(t, "5d")["Close"].iloc[-1])
        for t, q in st.session_state.holdings.items()
        if fetch_data(t, "5d") is not None and q > 0
    )

    total_value = st.session_state.cash + invested

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Virtual cash", f"₹{st.session_state.cash:,.2f}")
    c2.metric("Portfolio value", f"₹{total_value:,.2f}")
    c3.metric("Current position", f"{holdings} shares")
    c4.metric("Current price", f"₹{current:,.2f}")

    st.markdown("### Order Ticket")
    left, right = st.columns(2)

    with left:
        qty = st.number_input("Quantity", min_value=1, value=1, step=1)
        st.caption(f"Estimated order value: ₹{qty*current:,.2f}")

        buy, sell = st.columns(2)
        with buy:
            if st.button("🟢 BUY", use_container_width=True):
                cost = qty * current
                if cost <= st.session_state.cash:
                    st.session_state.cash -= cost
                    st.session_state.holdings[ticker] = holdings + qty
                    st.session_state.trades.append({
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Company": company,
                        "Side": "BUY",
                        "Quantity": qty,
                        "Price": current,
                        "Value": cost,
                    })
                    st.success("Paper order recorded.")
                else:
                    st.error("Insufficient virtual cash.")

        with sell:
            if st.button("🔴 SELL", use_container_width=True):
                if qty <= holdings:
                    proceeds = qty * current
                    st.session_state.cash += proceeds
                    new_qty = holdings - qty
                    if new_qty:
                        st.session_state.holdings[ticker] = new_qty
                    else:
                        st.session_state.holdings.pop(ticker, None)
                    st.session_state.trades.append({
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Company": company,
                        "Side": "SELL",
                        "Quantity": qty,
                        "Price": current,
                        "Value": proceeds,
                    })
                    st.success("Paper order recorded.")
                else:
                    st.error("You do not hold enough shares.")

    with right:
        st.markdown("### Position")
        st.metric("Shares held", holdings)
        st.metric("Market value", f"₹{market_value:,.2f}")

    st.markdown("### Trade History")
    if st.session_state.trades:
        st.dataframe(pd.DataFrame(st.session_state.trades), use_container_width=True)
    else:
        st.info("No paper trades yet.")

    st.caption("Paper trading only. No real-money orders are sent.")

# ----------------------------- FOOTER -------------------------
st.divider()
st.caption(
    "Market Intelligence Terminal • Evidence-based historical analysis • "
    "Paper trading only • Data may be delayed • No investment prediction"
)
