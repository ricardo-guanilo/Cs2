import streamlit as st
import requests
import pandas as pd

# Basic page setup for mobile
st.set_page_config(page_title="CS2 Inventory", layout="centered")

st.title("💰 CS2 Inventory Tracker")
st.caption("Live Steam Prices via PriceEmpire")

# Sidebar for inputs (so they don't take up screen space)
with st.sidebar:
    st.header("Credentials")
    # You can hardcode these if you don't want to type them every time
    steam_id = st.text_input("SteamID64", placeholder="76561198...")
    api_key = st.text_input("PriceEmpire API Key", type="password")
    st.info("Ensure your Steam Inventory is set to 'Public'.")

@st.cache_data(ttl=600)  # Caches data for 10 mins to avoid Steam rate limits

def get_inventory_and_prices(s_id, a_key):
    # 1. Fetch Inventory from Steam
    inv_url = f"https://steamcommunity.com/inventory/{s_id}/730/2?l=english&count=5000"
    try:
        response = requests.get(inv_url)
        
        # DEBUG: Let's see what Steam is actually saying
        if response.status_code != 200:
            return None, f"Steam API Error: Code {response.status_code}. (429 means too many requests, 403 means private profile)"
        
        inv_data = response.json()
        
        # If Steam returns success: False
        if not inv_data or inv_data.get('success') != 1:
            # Check if there's a specific message from Steam
            msg = inv_data.get('Error') if inv_data else "Null Response"
            return None, f"Steam refused: {msg}. Check if your SteamID64 is correct and public."

    except Exception as e:
        return None, f"App Error: {str(e)}"

def get_inventory_and_prices(s_id, a_key):
    # 1. Fetch Inventory from Steam
    inv_url = f"https://steamcommunity.com/inventory/{s_id}/730/2?l=english&count=5000"
    try:
        response = requests.get(inv_url)
        if response.status_code == 429:
            return None, "Steam is busy (Rate Limited). Try again in 5-10 mins."
        
        inv_data = response.json()
        if not inv_data or inv_data.get('success') != 1:
            return None, "Inventory private or Steam servers are down."
    except Exception as e:
        return None, f"Connection Error: {str(e)}"

    # Map classid to names
    descriptions = {d['classid']: d for d in inv_data['descriptions']}
    item_names = [descriptions[item['classid']]['market_hash_name'] for item in inv_data['assets']]

    # 2. Fetch Prices from PriceEmpire
    price_url = "https://api.pricempire.com/v3/items/prices"
    params = {'appId': 730, 'sources': 'steam', 'currency': 'USD', 'api_key': a_key}
    
    try:
        price_response = requests.get(price_url, params=params).json()
        price_db = price_response.get('data', {})
    except:
        return None, "Failed to reach PriceEmpire API."

    # 3. Combine Data
    rows = []
    for name in item_names:
        # PriceEmpire returns prices in cents
        raw_price = price_db.get(name, {}).get('steam', {}).get('price', 0)
        rows.append({"Item": name, "Price": raw_price / 100})

    df = pd.DataFrame(rows)
    if df.empty:
        return None, "No items found."

    # Create Summary Table
    summary = df.groupby('Item').agg({'Price': 'first', 'Item': 'count'}).rename(columns={'Item': 'Qty'}).reset_index()
    summary['Subtotal'] = summary['Price'] * summary['Qty']
    return summary.sort_values(by='Subtotal', ascending=False), None

# Main App Logic
if steam_id and api_key:
    if st.button('Refresh Inventory'):
        st.cache_data.clear() # Forces a fresh download

    with st.spinner('Loading your skins...'):
        data, error = get_inventory_and_prices(steam_id, api_key)
        
        if error:
            st.error(error)
        else:
            total_value = data['Subtotal'].sum()
            st.metric("Total Steam Value", f"${total_value:,.2f}")
            
            # Formats the price columns for the table
            st.dataframe(
                data.style.format({"Price": "${:.2f}", "Subtotal": "${:.2f}"}),
                use_container_width=True,
                hide_index=True
            )
else:
    st.warning("Please enter your SteamID and API Key in the sidebar.")

