"""
AI Analyzer - AI feature module
Connect this module to your existing Streamlit app.

This module contains the AI feature definitions and a small interface.
The actual model can be connected later without changing the feature API.
"""

FEATURES = [
    "AI Stock Analysis",
    "AI Technical Analysis",
    "AI Trend Analysis",
    "AI News Analysis",
    "AI News Sentiment",
    "AI Portfolio Analysis",
    "AI Risk Analysis",
    "AI Stock Comparison",
    "AI Market Chat",
    "AI Chart Explanation",
    "AI Fundamental Explanation",
    "AI Watchlist Analysis",
]

SYSTEM_PROMPT = """You are AI Analyzer, an educational stock-market assistant.
Use only the market information supplied to you. Never invent live prices,
news, or financial figures. Explain uncertainty. Never guarantee profit or
future returns. Clearly distinguish facts from analysis.
"""

def build_prompt(feature, question="", stock_data=None, portfolio=None,
                 news=None, comparison=None, watchlist=None):
    parts = [
        SYSTEM_PROMPT,
        f"FEATURE: {feature}",
        f"USER QUESTION: {question}",
        f"STOCK DATA: {stock_data or {}}",
        f"PORTFOLIO: {portfolio or []}",
        f"NEWS: {news or []}",
        f"COMPARISON: {comparison or {}}",
        f"WATCHLIST: {watchlist or []}",
    ]
    return "\n\n".join(parts)

def analyze(feature, question="", stock_data=None, portfolio=None,
            news=None, comparison=None, watchlist=None):
    """Return a prompt package for the AI model."""
    if feature not in FEATURES:
        raise ValueError(f"Unknown feature: {feature}")
    return build_prompt(
        feature, question, stock_data, portfolio, news, comparison, watchlist
    )

def list_features():
    return FEATURES.copy()
