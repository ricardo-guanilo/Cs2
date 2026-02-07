import streamlit as st
import requests
import pandas as pd
import time

# --- 1. YOUR ITEMS (English Names Required) ---
MY_ITEMS = {
    "AK-47 | The Empress (Field-Tested)": 1,
    "Copenhagen 2024 Contenders Sticker Capsule": 31,
    "Copenhagen 2024 Challengers Sticker Capsule": 26,
    "Fever Case": 10,
    "USP-S | Flashback (Factory New)": 1,
    "Sawed-Off | Black Sand (Factory New)": 1,
}

# Current Exchange Rate as of February 2026
EXCHANGE_RATE = 3.3535  # 1 USD to PEN

st.set_page_config(page_title="CS2 Inventory Tracker", layout="centered")

st.title("Skins Price Tracker")
st.write(f"**Current Exchange Rate:** 1 USD = {EXCHANGE_RATE} PEN")

def get_price_usd(item_name):
    """Fetches price for ONE item in USD."""
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {'appid': 730, 'currency': 1, 'market_hash_name': item_name}
    try:
        time.sleep(1.2) # Rate limit protection
        res = requests.get(url, params=params).json()
        if res.get('success'):
            price_str = res.get('lowest_price', '0').replace('$', '').replace(',', '')
            return float(price_str)
        return 0.0
    except:
        return 0.0

if st.button('Update Prices'):
    rows = []
    bar = st.progress(0)
    for i, (name, qty) in enumerate(MY_ITEMS.items()):
        usd_price = get_price_usd(name)
        pen_price = usd_price * EXCHANGE_RATE
        
        rows.append({
            "Item": name,
            "Qty": qty,
            "Price (USD)": usd_price,
            "Price (PEN)": pen_price,
            "Total (USD)": usd_price * qty,
            "Total (PEN)": pen_price * qty
        })
        bar.progress((i + 1) / len(MY_ITEMS))
    
    st.session_state['inventory_df'] = pd.DataFrame(rows)
    st.success("Prices Updated!")

if 'inventory_df' in st.session_state:
    df = st.session_state['inventory_df']
    
    # Summary Metrics
    col1, col2 = st.columns(2)
    col1.metric("Total Value (USD)", f"${df['Total (USD)'].sum():,.2f}")
    col2.metric("Total Value (PEN)", f"S/ {df['Total (PEN)'].sum():,.2f}")
    
    # Table Formatting
    st.dataframe(
        df.style.format({
            "Price (USD)": "${:.2f}",
            "Price (PEN)": "S/ {:.2f}",
            "Total (USD)": "${:.2f}",
            "Total (PEN)": "S/ {:.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )
