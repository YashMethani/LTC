import sys
import io
import zipfile
import streamlit as st

# Automatically launch streamlit if run via 'python yfin_app.py' or VS Code Play button
if __name__ == "__main__" and not st.runtime.exists():
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", sys.argv[0]]
    sys.exit(stcli.main())

import yfinance as yf
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="Stock Data Downloader", page_icon="📈", layout="wide")

st.title("📈 Stock Data Downloader")
st.markdown("Download historical stock data from Yahoo Finance for single or multiple symbols, save to CSV, and export as a ZIP.")

# Helper to format symbols (append .NS if needed)
def format_symbol(sym: str, append_ns: bool = True) -> str:
    sym = str(sym).strip()
    if not sym:
        return ""
    if append_ns:
        # Don't append if index (^NSEI) or already has an exchange suffix like .NS or .BO
        if not sym.startswith("^") and not sym.upper().endswith((".NS", ".BO")):
            sym = f"{sym}.NS"
    return sym

# Clean DataFrame downloaded from yfinance
def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    df_cleaned = df.reset_index()
    if "Date" in df_cleaned.columns:
        df_cleaned["Date"] = pd.to_datetime(df_cleaned["Date"]).dt.strftime("%Y-%m-%d")
    return df_cleaned


# --- Sidebar Inputs ---
with st.sidebar:
    st.header("1. Choose Input Mode")
    input_mode = st.radio(
        "Input Mode",
        ["Single Scrip", "Upload CSV (Batch)"],
        horizontal=True
    )
    
    symbols_to_fetch = []
    
    if input_mode == "Single Scrip":
        single_sym = st.text_input(
            "Scrip Name / Symbol",
            value="RELIANCE",
            help="Enter a stock name or index (e.g. RELIANCE, TCS, ^NSEI, AAPL)"
        ).strip()
        
        append_ns = st.checkbox(
            "Auto-append '.NS' for Indian stocks",
            value=True,
            help="Appends '.NS' (e.g. RELIANCE -> RELIANCE.NS) unless already present or starts with '^'"
        )
        
        if single_sym:
            formatted = format_symbol(single_sym, append_ns)
            symbols_to_fetch = [formatted]

    else:
        uploaded_file = st.file_uploader(
            "Upload CSV file with 'Symbol' column",
            type=["csv"],
            help="CSV must contain a column named 'Symbol' (or Scrip/Ticker)"
        )
        
        append_ns = st.checkbox(
            "Auto-append '.NS' to symbols",
            value=True,
            help="Appends '.NS' to each symbol in the CSV if not already present"
        )
        
        if uploaded_file is not None:
            try:
                input_df = pd.read_csv(uploaded_file)
                st.write("Uploaded CSV preview:")
                st.dataframe(input_df.head(3), use_container_width=True)

                # Find candidate column
                match_cols = [c for c in input_df.columns if c.strip().lower() in ["symbol", "symbols", "scrip", "scrips", "ticker", "tickers"]]
                default_col = match_cols[0] if match_cols else input_df.columns[0]
                
                selected_col = st.selectbox(
                    "Select the Symbol column:",
                    options=list(input_df.columns),
                    index=list(input_df.columns).index(default_col)
                )
                
                raw_symbols = input_df[selected_col].dropna().astype(str).tolist()
                symbols_to_fetch = [format_symbol(s, append_ns) for s in raw_symbols if s.strip()]
                st.info(f"Found **{len(symbols_to_fetch)}** symbol(s) to process.")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")

    st.header("2. Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=365))
    with col2:
        end_date = st.date_input("End Date", value=date.today())
        
    fetch_btn = st.button("🚀 Fetch Data", type="primary", use_container_width=True)


# --- Execution Logic ---
if fetch_btn:
    if not symbols_to_fetch:
        st.warning("Please provide a valid symbol or upload a CSV file.")
    elif start_date >= end_date:
        st.error("Error: Start Date must be earlier than End Date.")
    else:
        st.write(f"### Fetching data for {len(symbols_to_fetch)} symbol(s)...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        zip_buffer = io.BytesIO()
        successful_dfs = {}
        failed_symbols = []
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, symbol in enumerate(symbols_to_fetch):
                status_text.text(f"Fetching ({idx + 1}/{len(symbols_to_fetch)}): {symbol}...")
                progress_bar.progress((idx + 1) / len(symbols_to_fetch))
                
                try:
                    df = yf.download(symbol, start=start_date, end=end_date, progress=False)
                    df_cleaned = clean_dataframe(df)
                    
                    if df_cleaned.empty:
                        failed_symbols.append((symbol, "No data returned"))
                    else:
                        clean_sym_name = symbol.replace("^", "").replace(".", "_")
                        csv_name = f"{clean_sym_name}_{start_date}_{end_date}.csv"
                        csv_content = df_cleaned.to_csv(index=False)
                        
                        # Add individual CSV to the ZIP archive
                        zip_file.writestr(csv_name, csv_content)
                        
                        # Save local copy on disk as well
                        df_cleaned.to_csv(csv_name, index=False)
                        
                        successful_dfs[symbol] = df_cleaned
                except Exception as e:
                    failed_symbols.append((symbol, str(e)))

        status_text.empty()
        progress_bar.empty()
        
        # Summary Section
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.metric("Total Requested", len(symbols_to_fetch))
        with col_s2:
            st.metric("Successfully Fetched", len(successful_dfs))
        with col_s3:
            st.metric("Failed / Empty", len(failed_symbols))

        # Failed warnings
        if failed_symbols:
            with st.expander("⚠️ View Failed Symbols", expanded=False):
                st.table(pd.DataFrame(failed_symbols, columns=["Symbol", "Reason"]))

        # ZIP Download Button
        if successful_dfs:
            zip_bytes = zip_buffer.getvalue()
            st.download_button(
                label="📦 Download All CSVs (ZIP File)",
                data=zip_bytes,
                file_name=f"stock_data_{start_date}_{end_date}.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True
            )
            
            st.success(f"🎉 Generated {len(successful_dfs)} CSV files. You can now download the ZIP package above!")

            # If Single Scrip mode, show detailed view
            if input_mode == "Single Scrip" and len(successful_dfs) == 1:
                sym_name, df_display = list(successful_dfs.items())[0]
                
                # Single CSV Download Button
                single_csv_name = f"{sym_name.replace('^', '').replace('.', '_')}_{start_date}_{end_date}.csv"
                st.download_button(
                    label=f"📄 Download Single CSV ({single_csv_name})",
                    data=df_display.to_csv(index=False).encode("utf-8"),
                    file_name=single_csv_name,
                    mime="text/csv"
                )
                
                st.subheader(f"Historical Data: {sym_name}")
                st.dataframe(df_display, use_container_width=True)
                
                if "Close" in df_display.columns and "Date" in df_display.columns:
                    st.subheader(f"Closing Price Trend ({sym_name})")
                    chart_data = df_display.set_index("Date")[["Close"]]
                    st.line_chart(chart_data)

            # If Batch mode, show quick preview tabs/expanders
            elif input_mode == "Upload CSV (Batch)":
                st.subheader("Data Summary of Fetched Symbols")
                summary_data = []
                for sym, d in successful_dfs.items():
                    latest_close = d["Close"].iloc[-1] if "Close" in d.columns and len(d) > 0 else None
                    summary_data.append({
                        "Symbol": sym,
                        "Rows": len(d),
                        "Start Date": d["Date"].iloc[0] if "Date" in d.columns else "",
                        "End Date": d["Date"].iloc[-1] if "Date" in d.columns else "",
                        "Latest Close": f"{latest_close:.2f}" if latest_close is not None else "N/A"
                    })
                st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
