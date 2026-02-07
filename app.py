import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="CS2 Price Tracker", layout="centered")

st.title("PT's CS2 Inventory Tracker")
st.caption("Live Steam prices via PriceEmpire API")

# Setup sidebar for configuration
with st.sidebar:
    st.header("Settings")
    steam_id = st.text_input("SteamID64", placeholder="76561198...")
    api_key = st.text_input("PriceEmpire API Key", type="password")
    
if not steam_id or not api_key:
    st.info("Please enter your SteamID and API Key in the sidebar to begin.")
    st.stop()

@st.cache_data(ttl=3600) # Caches data for 1 hour so it's fast
def get_data(s_id, a_key):
    # 1. Get Inventory
    inv_url = f"https://steamcommunity.com/inventory/{s_id}/730/2?l=english&count=5000"
    inv_res = requests.get(inv_url).json()
    
    if 'assets' not in inv_res:
        return None, "Inventory private or not found."

    descriptions = {d['classid']: d for d in inv_res['descriptions']}
    my_items = [descriptions[item['classid']]['market_hash_name'] for item in inv_res['assets']]

    # 2. Get Prices
    price_url = "https://api.pricempire.com/v3/items/prices"
    params = {'appId': 730, 'sources': 'steam', 'currency': 'USD', 'api_key': a_key}
    price_res = requests.get(price_url, params=params).json().get('data', {})
    
    # 3. Process
    rows = []
    for name in my_items:
        price_cents = price_res.get(name, {}).get('steam', {}).get('price', 0)
        rows.append({"Item": name, "Price": price_cents / 100})
    
    df = pd.DataFrame(rows)
    summary = df.groupby('Item').agg({'Price': 'first', 'Item': 'count'}).rename(columns={'Item': 'Qty'}).reset_index()
    summary['Subtotal'] = summary['Price'] * summary['Qty']
    return summary, None

if st.button('Refresh Inventory'):
    with st.spinner('Fetching live data...'):
        df, error = get_data(steam_id, api_key)
        
        if error:
            st.error(error)
        else:
            total_val = df['Subtotal'].sum()
            st.metric("Total Inventory Value (Steam)", f"${total_val:,.2f}")
            st.dataframe(df.sort_values('Subtotal', ascending=False), use_container_width=True)