import streamlit as st
import requests
import pandas as pd
import time

# --- 1. LIST YOUR ITEMS HERE ---
MY_ITEMS = {
    "Recoil Case": 50,
    "Paris 2023 Legends Sticker Capsule": 100,
    "AK-47 | Slate (Field-Tested)": 1,
}

st.set_page_config(page_title="My Skins", layout="centered")
st.title("Skins Price Tracker (Direct)")

def get_single_price(item_name):
    """Fetches price for ONE item directly from Steam."""
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {
        'appid': 730,
        'currency': 1, # 1 is USD
        'market_hash_name': item_name
    }
    try:
        # We add a small delay so Steam doesn't get mad
        time.sleep(1.1) 
        res = requests.get(url, params=params).json()
        if res.get('success'):
            # Steam returns strings like "$1.50", we need to clean it to a float
            price_str = res.get('lowest_price', '0').replace('$', '').replace(',', '')
            return float(price_str)
        return 0.0
    except:
        return 0.0

if st.button('Update Prices Now'):
    rows = []
    progress_bar = st.progress(0)
    total_items = len(MY_ITEMS)
    
    for i, (item_name, qty) in enumerate(MY_ITEMS.items()):
        price = get_single_price(item_name)
        rows.append({
            "Item": item_name,
            "Price": price,
            "Qty": qty,
            "Subtotal": price * qty
        })
        progress_bar.progress((i + 1) / total_items)
    
    df = pd.DataFrame(rows)
    st.session_state['df'] = df
    st.success("Prices Updated!")

if 'df' in st.session_state:
    df = st.session_state['df']
    st.metric("Total Value", f"${df['Subtotal'].sum():,.2f}")
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Click the button above to fetch live Steam prices.")
