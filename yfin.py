import yfinance as yf

# Use yf.download() because you imported it as 'yf'
x = yf.download("^NSEI", start="2024-01-01", end="2025-01-01", progress=True)
print(x)