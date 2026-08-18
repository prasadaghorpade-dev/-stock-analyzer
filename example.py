from ai_features import analyze, list_features

print("Available AI features:")
for feature in list_features():
    print("-", feature)

prompt = analyze(
    "AI Stock Analysis",
    question="Explain the current situation",
    stock_data={
        "symbol": "RELIANCE",
        "price": 1450,
        "change_percent": 1.2,
        "rsi": 58,
        "macd": 12,
    },
)

print("\nGenerated AI prompt:\n")
print(prompt)
