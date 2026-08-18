# AI Analyzer - AI Module

This ZIP contains only the AI feature layer. It is designed to be added to
an existing Streamlit stock-market application without replacing the app.

## Included AI features

1. AI Stock Analysis
2. AI Technical Analysis
3. AI Trend Analysis
4. AI News Analysis
5. AI News Sentiment
6. AI Portfolio Analysis
7. AI Risk Analysis
8. AI Stock Comparison
9. AI Market Chat
10. AI Chart Explanation
11. AI Fundamental Explanation
12. AI Watchlist Analysis

## Important

This module does not invent or fetch live market data. Your existing app or a
market-data module should supply current prices, historical data, indicators,
news, and portfolio information.

The module also does not guarantee investment returns.

## Add to your existing app

Copy `ai_features.py` into the same folder as your Streamlit app.

Then use:

    from ai_features import analyze

Example:

    prompt = analyze(
        "AI Stock Analysis",
        question="Analyze this stock",
        stock_data={"symbol": "RELIANCE", "price": 1450}
    )

The returned prompt can be sent to the open-source/local AI model you choose.
