import streamlit as st
import requests
import pandas as pd
import time

# --- 1. LIST YOUR ITEMS HERE ---
MY_ITEMS = {
    "AK-47 | The Empress (Field-Tested)": 1,
    "Copenhagen 2024 Contenders Sticker Capsule": 31,
    "Copenhagen 2024 Challengers Sticker Capsule": 26,
    "Fever Case": 10,
    "USP-S | Flashback (Factory New)": 1,
    "Sawed-Off | Black Sand (Factory New)": 1
}

st.set_page_config(page_title="Mi Inventario CS2", layout="centered")
st.title("🇵🇪 Tracker de Precios (PEN)")

def get_single_price_pen(item_name):
    """Fetches price for ONE item in Peruvian Sol (PEN)."""
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {
        'appid': 730,
        'currency': 26, # 26 is the code for Peruvian Sol (PEN)
        'market_hash_name': item_name
    }
    try:
        # Respect Steam's rate limits
        time.sleep(1.2) 
        res = requests.get(url, params=params).json()
        
        if res.get('success'):
            # Steam returns "S/ 1.50" or "S/. 1,50"
            price_str = res.get('lowest_price', '0')
            # Clean string: remove S/, spaces, and commas
            clean_price = price_str.replace('S/', '').replace('S/.', '').replace(',', '').strip()
            return float(clean_price)
        return 0.0
    except:
        return 0.0

if st.button('Actualizar Precios en Soles'):
    rows = []
    progress_bar = st.progress(0)
    total_items = len(MY_ITEMS)
    
    for i, (item_name, qty) in enumerate(MY_ITEMS.items()):
        price = get_single_price_pen(item_name)
        rows.append({
            "Item": item_name,
            "Precio (S/)": price,
            "Cant": qty,
            "Subtotal": price * qty
        })
        progress_bar.progress((i + 1) / total_items)
    
    df = pd.DataFrame(rows)
    st.session_state['df_pen'] = df
    st.success("¡Precios actualizados!")

if 'df_pen' in st.session_state:
    df = st.session_state['df_pen']
    total_soles = df['Subtotal'].sum()
    
    st.metric("Valor Total", f"S/ {total_soles:,.2f}")
    
    # Display Table
    st.dataframe(
        df.style.format({"Precio (S/)": "S/ {:.2f}", "Subtotal": "S/ {:.2f}"}),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Haz clic en el botón para ver los precios actuales en Soles.")
