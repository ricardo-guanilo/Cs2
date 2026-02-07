import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="CS2 Tracker", layout="centered")

st.title("💰 CS2 Inventory Tracker")

with st.sidebar:
    st.header("Settings")
    steam_id = st.text_input("SteamID64 (17 digits)", placeholder="76561198...")
    api_key = st.text_input("PriceEmpire API Key", type="password")
    st.info("If it fails, wait 15 mins. Steam rate-limits are strict.")

@st.cache_data(ttl=600)
def get_data(s_id, a_key):
    # Mimic a real browser VERY closely
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    
    inv_url = f"https://steamcommunity.com/inventory/{s_id}/730/2?l=english&count=5000"
    
    try:
        response = requests.get(inv_url, headers=headers, timeout=15)
        
        # 1. Check HTTP Status
        if response.status_code == 429:
            return None, "Steam blocked this request (Rate Limit). Please wait 15-30 minutes."
        if response.status_code == 403:
            return None, "Access Denied (403). Ensure your Steam Inventory is 'Public' in privacy settings."
        
        # 2. Try to parse JSON safely
        try:
            inv_data = response.json()
        except Exception:
            return None, "Steam sent a non-JSON response. They are likely blocking the server temporarily."

        # 3. Check Steam's internal 'success' flag
        if not inv_data or inv_data.get('success') != 1:
            return None, "Steam returned Success: False. Your profile might be private or Steam is down."

        # Process Items
        descriptions = {d['classid']: d for d in inv_data.get('descriptions', [])}
        item_names = [descriptions[item['classid']]['market_hash_name'] for item in inv_data.get('assets', [])]

        # 4. Get Prices
        price_url = "https://api.pricempire.com/v3/items/prices"
        params = {'appId': 730, 'sources': 'steam', 'currency': 'USD', 'api_key': a_key}
        price_res = requests.get(price_url, params=params).json()
        price_db = price_res.get('data', {})

        rows = []
        for name in item_names:
            price_cents = price_db.get(name, {}).get('steam', {}).get('price', 0)
            rows.append({"Item": name, "Price": price_cents / 100})

        df = pd.DataFrame(rows)
        if df.empty: return None, "No items found."

        summary = df.groupby('Item').agg({'Price': 'first', 'Item': 'count'}).rename(columns={'Item': 'Qty'}).reset_index()
        summary['Subtotal'] = summary['Price'] * summary['Qty']
        return summary.sort_values('Subtotal', ascending=False), None

    except Exception as e:
        return None, f"App Error: {str(e)}"

# UI Execution
if steam_id and api_key:
    if st.button('Refresh Inventory'):
        st.cache_data.clear()

    with st.spinner('Accessing Steam...'):
        data, error = get_data(steam_id, api_key)
        
        if error:
            st.error(error)
        else:
            st.metric("Total Value", f"${data['Subtotal'].sum():,.2f}")
            st.dataframe(data, use_container_width=True, hide_index=True)
else:
    st.warning("Please enter your SteamID64 and PriceEmpire Key in the sidebar.")
