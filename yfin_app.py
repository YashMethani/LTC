import sys
import os
import io
import glob
import zipfile
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta, datetime

# Automatically launch streamlit if run via 'python yfin_app.py' or VS Code Play button
if __name__ == "__main__" and not st.runtime.exists():
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", sys.argv[0]]
    sys.exit(stcli.main())

import yfinance as yf

# --- Page Configuration ---
st.set_page_config(
    page_title="NSE Pro Screener | 3-Indicator Strategy (EMA, RSI, MACD)",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATABASE_DIR = "database"
os.makedirs(DATABASE_DIR, exist_ok=True)

# --- Professional Dark Trading Theme CSS ---
st.markdown("""
<style>
    /* Metric Card Styling */
    div[data-testid="metric-container"] {
        background-color: rgba(28, 33, 40, 0.85);
        border: 1px solid rgba(80, 90, 105, 0.4);
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    div[data-testid="metric-container"] label {
        color: #90caf9 !important;
        font-size: 0.85rem !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }
    .badge-strong-buy {
        background-color: #00C853; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;
    }
    .badge-buy {
        background-color: #2E7D32; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;
    }
    .badge-watchlist {
        background-color: #FFB300; color: #111; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;
    }
    .badge-sell {
        background-color: #C62828; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;
    }
    .badge-strong-sell {
        background-color: #D50000; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 18px;
        font-weight: 600;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)


# --- Company Name Registry ---
COMPANY_NAMES = {
    "ADANIENT.NS": "Adani Enterprises Ltd.",
    "ADANIPORTS.NS": "Adani Ports and SEZ Ltd.",
    "APOLLOHOSP.NS": "Apollo Hospitals Enterprise Ltd.",
    "ASIANPAINT.NS": "Asian Paints Ltd.",
    "AXISBANK.NS": "Axis Bank Ltd.",
    "BAJAJ-AUTO.NS": "Bajaj Auto Ltd.",
    "BAJAJFINSV.NS": "Bajaj Finserv Ltd.",
    "BAJFINANCE.NS": "Bajaj Finance Ltd.",
    "BEL.NS": "Bharat Electronics Ltd.",
    "BHARTIARTL.NS": "Bharti Airtel Ltd.",
    "BPCL.NS": "Bharat Petroleum Corp Ltd.",
    "BRITANNIA.NS": "Britannia Industries Ltd.",
    "CIPLA.NS": "Cipla Ltd.",
    "COALINDIA.NS": "Coal India Ltd.",
    "DRREDDY.NS": "Dr. Reddy's Laboratories Ltd.",
    "EICHERMOT.NS": "Eicher Motors Ltd.",
    "GRASIM.NS": "Grasim Industries Ltd.",
    "HCLTECH.NS": "HCL Technologies Ltd.",
    "HDFCBANK.NS": "HDFC Bank Ltd.",
    "HDFCLIFE.NS": "HDFC Life Insurance Co Ltd.",
    "HINDALCO.NS": "Hindalco Industries Ltd.",
    "HINDUNILVR.NS": "Hindustan Unilever Ltd.",
    "ICICIBANK.NS": "ICICI Bank Ltd.",
    "INDUSINDBK.NS": "IndusInd Bank Ltd.",
    "INFY.NS": "Infosys Ltd.",
    "ITC.NS": "ITC Ltd.",
    "JIOFIN.NS": "Jio Financial Services Ltd.",
    "JSWSTEEL.NS": "JSW Steel Ltd.",
    "KOTAKBANK.NS": "Kotak Mahindra Bank Ltd.",
    "LT.NS": "Larsen & Toubro Ltd.",
    "LTIM.NS": "LTIMindtree Ltd.",
    "M&M.NS": "Mahindra & Mahindra Ltd.",
    "MARUTI.NS": "Maruti Suzuki India Ltd.",
    "MAXHEALTH.NS": "Max Healthcare Institute Ltd.",
    "NESTLEIND.NS": "Nestle India Ltd.",
    "NTPC.NS": "NTPC Ltd.",
    "ONGC.NS": "Oil & Natural Gas Corp Ltd.",
    "POWERGRID.NS": "Power Grid Corp of India Ltd.",
    "RELIANCE.NS": "Reliance Industries Ltd.",
    "SBILIFE.NS": "SBI Life Insurance Co Ltd.",
    "SBIN.NS": "State Bank of India",
    "SHRIRAMFIN.NS": "Shriram Finance Ltd.",
    "SUNPHARMA.NS": "Sun Pharmaceutical Ind Ltd.",
    "TATACONSUM.NS": "Tata Consumer Products Ltd.",
    "TATAMOTORS.NS": "Tata Motors Ltd.",
    "TATASTEEL.NS": "Tata Steel Ltd.",
    "TCS.NS": "Tata Consultancy Services Ltd.",
    "TECHM.NS": "Tech Mahindra Ltd.",
    "TITAN.NS": "Titan Company Ltd.",
    "TRENT.NS": "Trent Ltd.",
    "ULTRACEMCO.NS": "UltraTech Cement Ltd.",
    "WIPRO.NS": "Wipro Ltd.",
    "BSE.NS": "BSE Ltd.",
    "INDIGO.NS": "InterGlobe Aviation Ltd.",
    "ASTRAL.NS": "Astral Ltd.",
    "AUROPHARMA.NS": "Aurobindo Pharma Ltd.",
    "BHARATFORG.NS": "Bharat Forge Ltd.",
    "BHEL.NS": "Bharat Heavy Electricals Ltd.",
    "COFORGE.NS": "Coforge Ltd.",
    "CONCOR.NS": "Container Corp of India Ltd.",
    "CUMMINSIND.NS": "Cummins India Ltd.",
    "DIXON.NS": "Dixon Technologies India Ltd.",
    "FEDERALBNK.NS": "The Federal Bank Ltd.",
    "GODREJPROP.NS": "Godrej Properties Ltd.",
    "IDFCFIRSTB.NS": "IDFC First Bank Ltd.",
    "INDHOTEL.NS": "The Indian Hotels Co Ltd.",
    "JINDALSTEL.NS": "Jindal Steel & Power Ltd.",
    "JUBLFOOD.NS": "Jubilant FoodWorks Ltd.",
    "LUPIN.NS": "Lupin Ltd.",
    "MPHASIS.NS": "Mphasis Ltd.",
    "MRF.NS": "MRF Ltd.",
    "PERSISTENT.NS": "Persistent Systems Ltd.",
    "POLYCAB.NS": "Polycab India Ltd.",
    "TATAPOWER.NS": "Tata Power Company Ltd.",
    "VOLTAS.NS": "Voltas Ltd."
}

def get_company_name(symbol: str) -> str:
    clean = symbol.strip().upper()
    if clean in COMPANY_NAMES:
        return COMPANY_NAMES[clean]
    clean_ns = f"{clean}.NS" if not clean.endswith(".NS") else clean
    return COMPANY_NAMES.get(clean_ns, clean.replace(".NS", "").replace("^", ""))


# --- Preset Index Lists ---
PRESET_INDICES = {
    "Nifty 50 (50 Stocks)": [
        "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
        "BAJAJ-AUTO", "BAJAJFINSV", "BAJFINANCE", "BEL", "BHARTIARTL",
        "BPCL", "BRITANNIA", "CIPLA", "COALINDIA", "DRREDDY",
        "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE",
        "HINDALCO", "HINDUNILVR", "ICICIBANK", "INDUSINDBK", "INFY",
        "ITC", "JSWSTEEL", "KOTAKBANK", "LT", "LTIM",
        "M&M", "MARUTI", "NESTLEIND", "NTPC", "ONGC",
        "POWERGRID", "RELIANCE", "SBILIFE", "SBIN", "SHRIRAMFIN",
        "SUNPHARMA", "TATACONSUM", "TATAMOTORS", "TATASTEEL", "TCS",
        "TECHM", "TITAN", "TRENT", "ULTRACEMCO", "WIPRO"
    ],
    "Nifty Midcap 50 (50 Stocks)": [
        "ASTRAL", "AUROPHARMA", "BHARATFORG", "BHEL", "COFORGE",
        "CONCOR", "CUMMINSIND", "DIXON", "ESCORTS", "FEDERALBNK",
        "GMRINFRA", "GODREJPROP", "HINDPETRO", "IDFCFIRSTB", "INDHOTEL",
        "INDUSTOWER", "JINDALSTEL", "JUBLFOOD", "LUPIN", "MAXHEALTH",
        "MGL", "MPHASIS", "MRF", "NMDC", "OBEROIRLTY",
        "OFSS", "PERSISTENT", "PETRONET", "POLYCAB", "PVRINOX",
        "SAIL", "SUNDARMFIN", "SUPREMEIND", "TATACOMM", "TATAPOWER",
        "TORNTPOWER", "TUBEINVEST", "UBL", "VOLTAS", "YESBANK",
        "ASHOKLEY", "BALKRISIND", "BANDHANBNK", "BIOCON", "CHOLAFIN",
        "DALBHARAT", "DEEPAKNTR", "GLENMARK", "LAURUSLABS", "PIIND"
    ],
    "Nifty Bank (12 Stocks)": [
        "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK",
        "INDUSINDBK", "BANKBARODA", "PNB", "IDFCFIRSTB", "FEDERALBNK",
        "AUBANK", "BANDHANBNK"
    ],
    "Nifty IT (10 Stocks)": [
        "TCS", "INFY", "HCLTECH", "WIPRO", "TECHM",
        "LTIM", "PERSISTENT", "COFORGE", "MPHASIS", "LTTS"
    ]
}

# --- Timeframe Definitions ---
TIMEFRAMES = {
    "Daily": {"interval": "1d", "period": "1y", "label": "1D"},
    "1 Hour": {"interval": "60m", "period": "730d", "label": "1H"},
    "30 Minutes": {"interval": "30m", "period": "60d", "label": "30m"},
    "15 Minutes": {"interval": "15m", "period": "60d", "label": "15m"},
    "5 Minutes": {"interval": "5m", "period": "5d", "label": "5m"},
    "Weekly": {"interval": "1wk", "period": "3y", "label": "1W"}
}


# --- Indicator Calculations ---
def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or len(df) < 30:
        return pd.DataFrame()
        
    df = df.copy()
    
    # 1. 20 EMA and 50 EMA
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    
    # 2. RSI (14 Period)
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))
    
    # 3. MACD (12, 26, 9)
    ema_fast = df["Close"].ewm(span=12, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
    
    # 4. Volume Average (20 Period)
    if "Volume" in df.columns:
        df["Avg_Volume"] = df["Volume"].rolling(window=20).mean()
    else:
        df["Avg_Volume"] = 0
        
    return df


# --- Crossover & Signal Analyzer ---
def analyze_stock(symbol: str, df: pd.DataFrame) -> dict:
    if df is None or len(df) < 50:
        return None
        
    df_calc = compute_indicators(df)
    if df_calc.empty:
        return None
        
    df_valid = df_calc.dropna(subset=["EMA_20", "EMA_50", "RSI", "MACD", "MACD_Signal"])
    if len(df_valid) < 2:
        return None
        
    latest = df_valid.iloc[-1]
    prev = df_valid.iloc[-2]
    
    cmp_price = float(latest["Close"])
    prev_close = float(prev["Close"])
    pct_change = ((cmp_price - prev_close) / prev_close) * 100 if prev_close else 0.0
    
    ema20 = float(latest["EMA_20"])
    ema50 = float(latest["EMA_50"])
    rsi = float(latest["RSI"])
    macd = float(latest["MACD"])
    macd_signal = float(latest["MACD_Signal"])
    macd_hist = float(latest["MACD_Hist"])
    volume = int(latest["Volume"]) if "Volume" in latest and not pd.isna(latest["Volume"]) else 0
    avg_volume = int(latest["Avg_Volume"]) if "Avg_Volume" in latest and not pd.isna(latest["Avg_Volume"]) else 0
    
    # Indicator Logic
    ema_bullish = (ema20 > ema50)
    rsi_bullish = (rsi > 50.0)
    macd_bullish = (macd > macd_signal)
    
    # Crossover Tracking
    ema20_series = df_valid["EMA_20"]
    ema50_series = df_valid["EMA_50"]
    above_series = (ema20_series > ema50_series)
    above_prev = above_series.shift(1).fillna(above_series)
    
    bull_cross = (above_series == True) & (above_prev == False)
    bear_cross = (above_series == False) & (above_prev == True)
    
    last_cross_type = "None"
    last_cross_time = "N/A"
    candles_since_cross = 999
    
    time_col = "Datetime" if "Datetime" in df_valid.columns else ("Date" if "Date" in df_valid.columns else df_valid.index.name)
    
    for i in range(len(df_valid) - 1, max(-1, len(df_valid) - 40), -1):
        if bull_cross.iloc[i]:
            last_cross_type = "Bullish (20 > 50)"
            candles_since_cross = len(df_valid) - 1 - i
            t_val = df_valid[time_col].iloc[i] if time_col in df_valid else df_valid.index[i]
            last_cross_time = str(t_val).split(".")[0]
            break
        elif bear_cross.iloc[i]:
            last_cross_type = "Bearish (20 < 50)"
            candles_since_cross = len(df_valid) - 1 - i
            t_val = df_valid[time_col].iloc[i] if time_col in df_valid else df_valid.index[i]
            last_cross_time = str(t_val).split(".")[0]
            break
            
    # Gap percentage between 20 & 50 EMA
    ema_gap_pct = abs(ema20 - ema50) / ema50 * 100
    
    # Signal Scoring
    bull_confirmations = sum([ema_bullish, rsi_bullish, macd_bullish])
    bear_confirmations = sum([not ema_bullish, not rsi_bullish, not macd_bullish])
    
    # Category Classification:
    # 1. STRONG BUY: 20 EMA > 50 EMA, RSI > 50, MACD bullish (3/3 confirmation)
    # 2. BUY: Bullish EMA crossover with >=1 confirmation OR 2/3 bullish with EMA20 > EMA50
    # 3. STRONG SELL: 20 EMA < 50 EMA, RSI < 50, MACD bearish (3/3 confirmation)
    # 4. SELL: Bearish EMA crossover with >=1 confirmation OR 2/3 bearish with EMA20 < EMA50
    # 5. WATCHLIST: Approaching crossover (|EMA20 - EMA50| / EMA50 < 0.75%) or oversold/overbought recovery
    
    if ema_bullish and rsi_bullish and macd_bullish:
        category = "STRONG BUY"
        strength = "3/3 High"
    elif not ema_bullish and not rsi_bullish and not macd_bullish:
        category = "STRONG SELL"
        strength = "3/3 High"
    elif ema_gap_pct <= 0.75:
        category = "WATCHLIST"
        strength = "Approaching Crossover"
    elif (last_cross_type.startswith("Bullish") and candles_since_cross <= 5 and (rsi_bullish or macd_bullish)) or (ema_bullish and bull_confirmations >= 2):
        category = "BUY"
        strength = f"{bull_confirmations}/3 Moderate"
    elif (last_cross_type.startswith("Bearish") and candles_since_cross <= 5 and (not rsi_bullish or not macd_bullish)) or (not ema_bullish and bear_confirmations >= 2):
        category = "SELL"
        strength = f"{bear_confirmations}/3 Moderate"
    else:
        category = "NEUTRAL"
        strength = "1/3 Mixed"

    # RSI condition tag
    if rsi >= 70:
        rsi_tag = "Overbought (>70)"
    elif rsi <= 30:
        rsi_tag = "Oversold (<30)"
    elif rsi > 50:
        rsi_tag = "Bullish (>50)"
    else:
        rsi_tag = "Bearish (<50)"

    return {
        "Symbol": symbol,
        "Company Name": get_company_name(symbol),
        "Price (₹)": round(cmp_price, 2),
        "Change (%)": round(pct_change, 2),
        "20 EMA (₹)": round(ema20, 2),
        "50 EMA (₹)": round(ema50, 2),
        "EMA Trend": "Bullish (20>50)" if ema_bullish else "Bearish (20<50)",
        "RSI": round(rsi, 2),
        "RSI Status": rsi_tag,
        "MACD": round(macd, 2),
        "MACD Signal": round(macd_signal, 2),
        "MACD Status": "Bullish (>Signal)" if macd_bullish else "Bearish (<Signal)",
        "Volume": volume,
        "Avg Volume": avg_volume,
        "Signal": category,
        "Signal Strength": strength,
        "Last Crossover": last_cross_type,
        "Candles Since Cross": candles_since_cross if candles_since_cross < 999 else "None",
        "Crossover Time": last_cross_time,
        "df_processed": df_calc
    }


# --- Cache Helper ---
def load_or_fetch_stock_data(symbol: str, timeframe: str, use_cache: bool = True) -> pd.DataFrame:
    clean_sym = symbol.replace("^", "").replace(".", "_")
    interval = TIMEFRAMES[timeframe]["interval"]
    period = TIMEFRAMES[timeframe]["period"]
    
    cache_file = os.path.join(DATABASE_DIR, f"{clean_sym}_{interval}.csv")
    
    # Check interval specific cache in database folder
    if use_cache and os.path.exists(cache_file):
        try:
            df = pd.read_csv(cache_file)
            if not df.empty and "Close" in df.columns:
                return df
        except Exception:
            pass
            
    # For Daily timeframe, check existing pre-downloaded files in database folder
    if use_cache and interval == "1d":
        patterns = [
            os.path.join(DATABASE_DIR, f"{clean_sym}_*.csv"),
            os.path.join(DATABASE_DIR, f"{clean_sym}.csv"),
        ]
        for pat in patterns:
            matches = glob.glob(pat)
            if matches:
                matches.sort(key=os.path.getmtime, reverse=True)
                try:
                    df = pd.read_csv(matches[0])
                    if not df.empty and "Close" in df.columns and len(df) >= 30:
                        return df
                except Exception:
                    pass

    # Download from yfinance
    try:
        raw_df = yf.download(symbol, period=period, interval=interval, progress=False)
        if raw_df is not None and not raw_df.empty:
            if isinstance(raw_df.columns, pd.MultiIndex):
                raw_df.columns = [c[0] for c in raw_df.columns]
            df = raw_df.reset_index()
            # Standardize date column
            date_col = "Datetime" if "Datetime" in df.columns else ("Date" if "Date" in df.columns else df.columns[0])
            df.rename(columns={date_col: "Date"}, inplace=True)
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d %H:%M")
            # Save to interval cache
            df.to_csv(cache_file, index=False)
            return df
    except Exception:
        pass
        
    return pd.DataFrame()


# --- Streamlit Sidebar Controls ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bullish.png", width=64)
    st.title("NSE Pro Screener")
    st.caption("3-Indicator Strategy: 20/50 EMA + RSI (14) + MACD (12,26,9)")
    
    st.markdown("---")
    st.subheader("1. Timeframe Selection")
    selected_timeframe = st.selectbox(
        "Candle Timeframe:",
        list(TIMEFRAMES.keys()),
        index=0,
        help="All 3 indicators automatically recalculate for the chosen timeframe."
    )
    
    st.markdown("---")
    st.subheader("2. Stock Basket / Universe")
    basket_mode = st.radio(
        "Source:",
        ["Select Preset Index", "Upload Custom CSV"],
        index=0
    )
    
    symbols_to_scan = []
    
    if basket_mode == "Select Preset Index":
        preset_choice = st.selectbox("Index Basket:", list(PRESET_INDICES.keys()), index=0)
        raw_symbols = PRESET_INDICES[preset_choice]
        symbols_to_scan = [f"{s}.NS" if not s.endswith(".NS") else s for s in raw_symbols]
        st.caption(f"Loaded **{len(symbols_to_scan)}** stocks from {preset_choice}.")
    else:
        uploaded_file = st.file_uploader("Upload CSV (with 'Symbol' column):", type=["csv"])
        if uploaded_file is not None:
            try:
                up_df = pd.read_csv(uploaded_file)
                match_cols = [c for c in up_df.columns if c.strip().lower() in ["symbol", "symbols", "scrip", "ticker"]]
                col_name = match_cols[0] if match_cols else up_df.columns[0]
                raw_list = up_df[col_name].dropna().astype(str).tolist()
                symbols_to_scan = [f"{s}.NS" if not s.endswith((".NS", ".BO")) and not s.startswith("^") else s for s in raw_list if s.strip()]
                st.caption(f"Loaded **{len(symbols_to_scan)}** symbols from CSV.")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")

    st.markdown("---")
    st.subheader("3. Advanced Filters")
    
    filter_signal = st.multiselect(
        "Signal Category Filter:",
        ["STRONG BUY", "BUY", "WATCHLIST", "SELL", "STRONG SELL"],
        default=["STRONG BUY", "BUY", "WATCHLIST", "SELL", "STRONG SELL"]
    )
    
    rsi_range = st.slider("RSI Range Filter:", 0, 100, (0, 100))
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        min_price = st.number_input("Min Price (₹):", min_value=0.0, value=0.0, step=50.0)
    with col_p2:
        max_price = st.number_input("Max Price (₹):", min_value=0.0, value=100000.0, step=500.0)
        
    crossover_filter = st.selectbox(
        "EMA Crossover Recency:",
        ["All Stocks", "Crossover in Last 1 Candle", "Crossover in Last 3 Candles", "Crossover in Last 5 Candles"]
    )
    
    min_volume = st.number_input("Min Volume:", min_value=0, value=0, step=50000)
    
    st.markdown("---")
    use_cache = st.checkbox("⚡ Use Database Cache (Fast)", value=True, help="Reuses downloaded historical data stored in the local 'database' folder for instant screening.")
    
    scan_button = st.button("🚀 Run Live Screener", type="primary", use_container_width=True)


# --- Initialize Session State for Results ---
if "screener_results" not in st.session_state:
    st.session_state.screener_results = []
if "processed_stock_dfs" not in st.session_state:
    st.session_state.processed_stock_dfs = {}
if "last_scan_time" not in st.session_state:
    st.session_state.last_scan_time = None


# --- Run Screener Logic ---
if scan_button:
    if not symbols_to_scan:
        st.warning("Please select an index basket or upload a valid CSV file.")
    else:
        st.markdown(f"### ⚡ Scanning {len(symbols_to_scan)} NSE Stocks ({selected_timeframe} timeframe)...")
        progress = st.progress(0)
        status_box = st.empty()
        
        results = []
        stock_dfs = {}
        
        for idx, sym in enumerate(symbols_to_scan):
            progress.progress((idx + 1) / len(symbols_to_scan))
            status_box.text(f"Analyzing ({idx + 1}/{len(symbols_to_scan)}): {sym}...")
            
            df = load_or_fetch_stock_data(sym, selected_timeframe, use_cache=use_cache)
            if not df.empty:
                res = analyze_stock(sym, df)
                if res is not None:
                    stock_dfs[sym] = res.pop("df_processed")
                    results.append(res)
                    
        progress.empty()
        status_box.empty()
        
        st.session_state.screener_results = results
        st.session_state.processed_stock_dfs = stock_dfs
        st.session_state.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --- Main Dashboard Area ---
st.title("📈 NSE Real-Time Multi-Indicator Screener")
st.markdown("**Strategy:** 20/50 EMA Trend & Crossovers • 14 RSI Momentum • 12/26/9 MACD Signal Confirmation")

if st.session_state.last_scan_time:
    st.caption(f"🕒 **Last Scan Completed:** `{st.session_state.last_scan_time}` | **Timeframe:** `{selected_timeframe}` | **Market:** `NSE India (delayed data)`")
else:
    st.info("👈 Click **'🚀 Run Live Screener'** in the sidebar to scan stocks now!")


# Filter Results
raw_results = st.session_state.screener_results
filtered_results = []

if raw_results:
    for r in raw_results:
        # Category Filter
        if r["Signal"] not in filter_signal:
            continue
        # RSI Filter
        if not (rsi_range[0] <= r["RSI"] <= r["RSI_range" if "RSI_range" in r else "RSI"] <= rsi_range[1]):
            continue
        # Price Filter
        if not (min_price <= r["Price (₹)"] <= max_price):
            continue
        # Volume Filter
        if r["Volume"] < min_volume:
            continue
        # Crossover Filter
        if crossover_filter == "Crossover in Last 1 Candle" and (r["Candles Since Cross"] == "None" or int(r["Candles Since Cross"]) > 1):
            continue
        elif crossover_filter == "Crossover in Last 3 Candles" and (r["Candles Since Cross"] == "None" or int(r["Candles Since Cross"]) > 3):
            continue
        elif crossover_filter == "Crossover in Last 5 Candles" and (r["Candles Since Cross"] == "None" or int(r["Candles Since Cross"]) > 5):
            continue
            
        filtered_results.append(r)


# --- Tabs Navigation ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Screener Dashboard",
    "📈 Interactive Stock Chart & Analysis",
    "🚨 Live Alert Center",
    "ℹ️ Strategy & Risk Management"
])


# ==========================================
# TAB 1: SCREENER DASHBOARD
# ==========================================
with tab1:
    if raw_results:
        # Top KPI Summary Cards
        counts = {
            "Total": len(raw_results),
            "STRONG BUY": sum(1 for r in raw_results if r["Signal"] == "STRONG BUY"),
            "BUY": sum(1 for r in raw_results if r["Signal"] == "BUY"),
            "WATCHLIST": sum(1 for r in raw_results if r["Signal"] == "WATCHLIST"),
            "SELL": sum(1 for r in raw_results if r["Signal"] == "SELL"),
            "STRONG SELL": sum(1 for r in raw_results if r["Signal"] == "STRONG SELL"),
        }
        
        col_k1, col_k2, col_k3, col_k4, col_k5, col_k6 = st.columns(6)
        with col_k1:
            st.metric("Total Scanned", counts["Total"])
        with col_k2:
            st.metric("🟢 Strong Buy", counts["STRONG BUY"], help="20 EMA > 50 EMA, RSI > 50, and MACD > Signal")
        with col_k3:
            st.metric("🟢 Buy", counts["BUY"], help="Bullish crossover with momentum confirmation")
        with col_k4:
            st.metric("🟡 Watchlist", counts["WATCHLIST"], help="Approaching crossover gap < 0.75%")
        with col_k5:
            st.metric("🔴 Sell", counts["SELL"], help="Bearish crossover with momentum confirmation")
        with col_k6:
            st.metric("🔴 Strong Sell", counts["STRONG SELL"], help="20 EMA < 50 EMA, RSI < 50, and MACD < Signal")

        st.markdown("---")
        
        # Search & Display Filtered Table
        col_tb1, col_tb2 = st.columns([3, 1])
        with col_tb1:
            search_query = st.text_input("🔍 Quick Search by Symbol or Company Name:", placeholder="e.g. RELIANCE, Tata, HDFC").strip().lower()
        with col_tb2:
            st.write("")
            st.write(f"**Showing {len(filtered_results)} of {len(raw_results)} stocks**")
            
        display_list = filtered_results
        if search_query:
            display_list = [r for r in display_list if search_query in r["Symbol"].lower() or search_query in r["Company Name"].lower()]

        if display_list:
            df_table = pd.DataFrame(display_list)
            
            # Format display dataframe
            show_cols = [
                "Symbol", "Company Name", "Price (₹)", "Change (%)",
                "20 EMA (₹)", "50 EMA (₹)", "RSI", "MACD", "Signal",
                "Signal Strength", "Volume", "Last Crossover", "Candles Since Cross"
            ]
            
            st.dataframe(
                df_table[show_cols],
                use_container_width=True,
                height=480,
                column_config={
                    "Price (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Change (%)": st.column_config.NumberColumn(format="%.2f%%"),
                    "20 EMA (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "50 EMA (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "RSI": st.column_config.NumberColumn(format="%.1f"),
                    "MACD": st.column_config.NumberColumn(format="%.2f"),
                    "Volume": st.column_config.NumberColumn(format="%d"),
                }
            )
            
            # Quick Copy Stock Symbols
            st.subheader("📋 Quick Copy Filtered Stock Symbols:")
            cat_tabs = st.tabs(["All Filtered", "Strong Buy", "Buy", "Watchlist", "Strong Sell / Sell"])
            with cat_tabs[0]:
                st.code(", ".join([r["Symbol"] for r in display_list]), language="text")
            with cat_tabs[1]:
                sb_list = [r["Symbol"] for r in display_list if r["Signal"] == "STRONG BUY"]
                st.code(", ".join(sb_list) if sb_list else "No Strong Buy stocks in filtered view", language="text")
            with cat_tabs[2]:
                b_list = [r["Symbol"] for r in display_list if r["Signal"] == "BUY"]
                st.code(", ".join(b_list) if b_list else "No Buy stocks in filtered view", language="text")
            with cat_tabs[3]:
                w_list = [r["Symbol"] for r in display_list if r["Signal"] == "WATCHLIST"]
                st.code(", ".join(w_list) if w_list else "No Watchlist stocks in filtered view", language="text")
            with cat_tabs[4]:
                s_list = [r["Symbol"] for r in display_list if "SELL" in r["Signal"]]
                st.code(", ".join(s_list) if s_list else "No Sell stocks in filtered view", language="text")

            # Automatically save copy of generated results into database folder
            try:
                db_results_path = os.path.join(DATABASE_DIR, f"screener_results_{selected_timeframe}_{date.today()}.csv")
                df_table.to_csv(db_results_path, index=False)
            except Exception:
                pass

            # Download Options
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                csv_bytes = df_table.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Screener Results (CSV)",
                    data=csv_bytes,
                    file_name=f"screener_results_{selected_timeframe}_{date.today()}.csv",
                    mime="text/csv",
                    type="primary",
                    use_container_width=True
                )
            with col_d2:
                # Zip of all stock data
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for s_item in display_list:
                        sym = s_item["Symbol"]
                        if sym in st.session_state.processed_stock_dfs:
                            csv_data = st.session_state.processed_stock_dfs[sym].to_csv(index=False)
                            zf.writestr(f"{sym.replace('.NS', '')}_{selected_timeframe}.csv", csv_data)
                st.download_button(
                    label="📦 Download Historical CSVs (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"nse_stock_data_{selected_timeframe}_{date.today()}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
        else:
            st.warning("No stocks matched your active filter criteria. Try adjusting the filters in the sidebar.")
    else:
        st.info("👈 Click **'🚀 Run Live Screener'** on the left to start screening.")


# ==========================================
# TAB 2: DETAILED STOCK CHART & ANALYSIS
# ==========================================
with tab2:
    st.subheader("📈 Multi-Pane Technical Analysis Chart")
    
    available_symbols = [r["Symbol"] for r in (filtered_results if filtered_results else raw_results)]
    
    if available_symbols:
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            selected_sym = st.selectbox("Select Stock for Deep Technical Analysis:", available_symbols, index=0)
        with col_c2:
            st.write("")
            sym_meta = next((r for r in raw_results if r["Symbol"] == selected_sym), None)
            if sym_meta:
                sig_color = "#00C853" if "BUY" in sym_meta["Signal"] else ("#D50000" if "SELL" in sym_meta["Signal"] else "#FFB300")
                st.markdown(f"**Signal:** <span style='background:{sig_color};color:white;padding:4px 8px;border-radius:4px;'>{sym_meta['Signal']} ({sym_meta['Signal Strength']})</span>", unsafe_allow_html=True)
                
        if selected_sym in st.session_state.processed_stock_dfs:
            chart_df = st.session_state.processed_stock_dfs[selected_sym].copy()
            
            # Subplots: Row 1 = Candlestick + 20/50 EMA, Row 2 = Volume, Row 3 = RSI, Row 4 = MACD
            fig = make_subplots(
                rows=4, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.50, 0.15, 0.17, 0.18],
                subplot_titles=(
                    f"{selected_sym} - {get_company_name(selected_sym)} ({selected_timeframe})",
                    "Volume",
                    "RSI (14 Period)",
                    "MACD (12, 26, 9)"
                )
            )
            
            # 1. Candlestick
            x_axis = chart_df["Date"] if "Date" in chart_df.columns else chart_df.index
            fig.add_trace(go.Candlestick(
                x=x_axis,
                open=chart_df["Open"],
                high=chart_df["High"],
                low=chart_df["Low"],
                close=chart_df["Close"],
                name="Price",
                increasing_line_color="#00C853",
                decreasing_line_color="#D50000"
            ), row=1, col=1)
            
            # EMA 20 & EMA 50
            fig.add_trace(go.Scatter(
                x=x_axis, y=chart_df["EMA_20"],
                name="20 EMA", line=dict(color="#00E5FF", width=2)
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=x_axis, y=chart_df["EMA_50"],
                name="50 EMA", line=dict(color="#FF9100", width=2)
            ), row=1, col=1)
            
            # 2. Volume
            vol_colors = ["#00C853" if c >= o else "#D50000" for c, o in zip(chart_df["Close"], chart_df["Open"])]
            fig.add_trace(go.Bar(
                x=x_axis, y=chart_df["Volume"],
                name="Volume", marker_color=vol_colors, opacity=0.7
            ), row=2, col=1)
            
            if "Avg_Volume" in chart_df.columns:
                fig.add_trace(go.Scatter(
                    x=x_axis, y=chart_df["Avg_Volume"],
                    name="20 Avg Vol", line=dict(color="#B0BEC5", width=1.5, dash="dot")
                ), row=2, col=1)
                
            # 3. RSI
            fig.add_trace(go.Scatter(
                x=x_axis, y=chart_df["RSI"],
                name="RSI (14)", line=dict(color="#BA68C8", width=2)
            ), row=3, col=1)
            # RSI reference bands
            fig.add_hline(y=70, line=dict(color="#E53935", width=1, dash="dash"), row=3, col=1)
            fig.add_hline(y=50, line=dict(color="#90A4AE", width=1, dash="dot"), row=3, col=1)
            fig.add_hline(y=30, line=dict(color="#43A047", width=1, dash="dash"), row=3, col=1)
            
            # 4. MACD
            fig.add_trace(go.Scatter(
                x=x_axis, y=chart_df["MACD"],
                name="MACD Line", line=dict(color="#29B6F6", width=2)
            ), row=4, col=1)
            fig.add_trace(go.Scatter(
                x=x_axis, y=chart_df["MACD_Signal"],
                name="Signal Line", line=dict(color="#FFA726", width=2)
            ), row=4, col=1)
            
            hist_colors = ["#00C853" if h >= 0 else "#D50000" for h in chart_df["MACD_Hist"]]
            fig.add_trace(go.Bar(
                x=x_axis, y=chart_df["MACD_Hist"],
                name="Histogram", marker_color=hist_colors
            ), row=4, col=1)
            
            fig.update_layout(
                height=850,
                template="plotly_dark",
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=30, r=30, t=50, b=30)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # --- Technical Breakdown Cards & Trade Setup ---
            if sym_meta:
                st.subheader(f"📋 Technical Audit: {selected_sym}")
                col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                with col_a1:
                    st.markdown("**1. Moving Average Trend**")
                    st.write(f"• 20 EMA: **₹{sym_meta['20 EMA (₹)']:.2f}**")
                    st.write(f"• 50 EMA: **₹{sym_meta['50 EMA (₹)']:.2f}**")
                    st.write(f"• Status: `{sym_meta['EMA Trend']}`")
                    st.write(f"• Last Cross: `{sym_meta['Last Crossover']}`")
                with col_a2:
                    st.markdown("**2. RSI (14) Momentum**")
                    st.write(f"• RSI Value: **{sym_meta['RSI']:.2f}**")
                    st.write(f"• Reading: `{sym_meta['RSI Status']}`")
                    st.write("• Zone: " + ("🚨 Overbought" if sym_meta['RSI'] >= 70 else ("🟢 Oversold" if sym_meta['RSI'] <= 30 else "⚪ Neutral")))
                with col_a3:
                    st.markdown("**3. MACD Momentum**")
                    st.write(f"• MACD: **{sym_meta['MACD']:.2f}**")
                    st.write(f"• Signal: **{sym_meta['MACD Signal']:.2f}**")
                    st.write(f"• Cross: `{sym_meta['MACD Status']}`")
                with col_a4:
                    st.markdown("**4. Suggested Trade Plan (Risk/Reward)**")
                    price = sym_meta["Price (₹)"]
                    stop_loss = sym_meta["50 EMA (₹)"]
                    risk = abs(price - stop_loss)
                    target1 = price + (risk * 1.5) if "BUY" in sym_meta["Signal"] else max(1.0, price - (risk * 1.5))
                    target2 = price + (risk * 2.0) if "BUY" in sym_meta["Signal"] else max(1.0, price - (risk * 2.0))
                    
                    st.write(f"• Entry: **₹{price:.2f}**")
                    st.write(f"• Stop Loss: **₹{stop_loss:.2f}**")
                    st.write(f"• Target 1 (1:1.5): **₹{target1:.2f}**")
                    st.write(f"• Target 2 (1:2.0): **₹{target2:.2f}**")
    else:
        st.info("No scanned stock data available. Run the screener from the sidebar first.")


# ==========================================
# TAB 3: LIVE ALERT CENTER
# ==========================================
with tab3:
    st.subheader("🚨 Real-Time Trading Setup Alerts")
    st.caption("Active alerts based on fresh crossovers (last 1-3 candles) and triple indicator confirmations.")
    
    if raw_results:
        fresh_bull_cross = [r for r in raw_results if r["Last Crossover"].startswith("Bullish") and r["Candles Since Cross"] != "None" and int(r["Candles Since Cross"]) <= 3]
        fresh_bear_cross = [r for r in raw_results if r["Last Crossover"].startswith("Bearish") and r["Candles Since Cross"] != "None" and int(r["Candles Since Cross"]) <= 3]
        strong_buys = [r for r in raw_results if r["Signal"] == "STRONG BUY"]
        strong_sells = [r for r in raw_results if r["Signal"] == "STRONG SELL"]
        approaching = [r for r in raw_results if r["Signal"] == "WATCHLIST"]
        
        col_al1, col_al2 = st.columns(2)
        
        with col_al1:
            st.markdown("#### 🟢 Bullish Trigger Alerts")
            if fresh_bull_cross:
                st.success(f"**⚡ {len(fresh_bull_cross)} Fresh Bullish EMA Crossovers (Last 3 Candles):**")
                for s in fresh_bull_cross:
                    st.write(f"• **{s['Symbol']}** ({s['Company Name']}) - CMP: ₹{s['Price (₹)']} | Crossed on candle {s['Candles Since Cross']} ago ({s['Crossover Time']})")
            else:
                st.info("No fresh bullish crossovers in the last 3 candles.")
                
            if strong_buys:
                st.markdown(f"**💎 {len(strong_buys)} Triple Indicator Bullish Setups (Strong Buy):**")
                sb_df = pd.DataFrame(strong_buys)[["Symbol", "Price (₹)", "RSI", "MACD", "Volume"]]
                st.dataframe(sb_df, use_container_width=True)
                
        with col_al2:
            st.markdown("#### 🔴 Bearish Trigger Alerts")
            if fresh_bear_cross:
                st.error(f"**⚡ {len(fresh_bear_cross)} Fresh Bearish EMA Crossovers (Last 3 Candles):**")
                for s in fresh_bear_cross:
                    st.write(f"• **{s['Symbol']}** ({s['Company Name']}) - CMP: ₹{s['Price (₹)']} | Crossed on candle {s['Candles Since Cross']} ago ({s['Crossover Time']})")
            else:
                st.info("No fresh bearish crossovers in the last 3 candles.")
                
            if strong_sells:
                st.markdown(f"**⚠️ {len(strong_sells)} Triple Indicator Bearish Setups (Strong Sell):**")
                ss_df = pd.DataFrame(strong_sells)[["Symbol", "Price (₹)", "RSI", "MACD", "Volume"]]
                st.dataframe(ss_df, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🟡 Watchlist (Approaching Crossover within < 0.75% Gap):")
        if approaching:
            app_df = pd.DataFrame(approaching)[["Symbol", "Price (₹)", "20 EMA (₹)", "50 EMA (₹)", "RSI", "MACD"]]
            st.dataframe(app_df, use_container_width=True)
        else:
            st.info("No stocks currently approaching an imminent crossover.")
    else:
        st.info("Run the screener from the sidebar to populate live alerts.")


# ==========================================
# TAB 4: STRATEGY & RISK MANAGEMENT
# ==========================================
with tab4:
    st.subheader("📘 3-Indicator Strategy Architecture & Risk Management Rules")
    
    col_str1, col_str2 = st.columns(2)
    with col_str1:
        st.markdown("""
        ### 🎯 Strategy Rules:
        
        1. **Indicator 1: Moving Average Trend & Crossover**
           * **20 EMA:** Short-term trend momentum.
           * **50 EMA:** Medium-term trend anchor.
           * **Bullish Crossover:** 20 EMA crosses above 50 EMA.
           * **Bearish Crossover:** 20 EMA crosses below 50 EMA.
           * Ongoing trend: 20 EMA above 50 EMA confirms upward trend.
           
        2. **Indicator 2: RSI (Relative Strength Index - 14)**
           * **Above 50:** Confirms bullish price momentum.
           * **Below 50:** Confirms bearish price momentum.
           * **Above 70 (Overbought):** Look for exhaustion or tightening stop losses.
           * **Below 30 (Oversold):** Potential reversal / exhaustion zone.
           
        3. **Indicator 3: MACD (12, 26, 9)**
           * **Bullish:** MACD line > Signal line (Histogram > 0).
           * **Bearish:** MACD line < Signal line (Histogram < 0).
        """)
        
    with col_str2:
        st.markdown("""
        ### 🛡️ Risk Management & Execution Principles:
        
        * **Not Automated Execution:** This screener identifies high-probability trading candidates; all executions are manual and subject to user confirmation.
        * **1:2 Risk-to-Reward Ratio:** Always aim for at least 1:2 risk-to-reward. If risk is ₹10 per share, target at least ₹20.
        * **Position Sizing:** Never risk more than 1% to 2% of total trading capital on any single setup.
        * **Stop-Loss Discipline:** Use the 50 EMA or previous swing low/high as a trailing stop-loss.
        * **Market Context:** Check overall market direction (Nifty 50 Index trend) before taking individual stock positions.
        """)

    st.warning("""
    ⚠️ **Important Disclaimer:** Stock market trading and investing involve substantial risk of capital loss. 
    This application is designed strictly for technical screening and educational purposes. 
    It does not provide financial or investment advice. Always perform your own due diligence or consult a SEBI registered investment advisor before executing trades.
    """)
