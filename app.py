import streamlit as st
import requests
import pandas as pd

# Page Configuration
st.set_page_config(page_title="CS2 Price App", layout="centered")

st.title("💰 CS2 Inventory Tracker")
st.caption("Live Steam Prices | Anti-Block Version")

# Sidebar for credentials
with st.sidebar:
    st.header("Settings")
    steam_id = st.text_input("SteamID64", placeholder="76561198...")
    api_key = st.text_input("PriceEmpire API Key", type="password")
    st.markdown("---")
    st.info("💡 Pro Tip: If it says 'Private', wait 15 minutes. Steam rate-limits Cloud IPs often.")

@st.cache_data(ttl=600)
def get_inventory_and_prices(s_id, a_key):
    # Setup a session to look like a real browser
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    # 1. Fetch Inventory
    inv_url = f"https://steamcommunity.com/inventory/{s_id}/730/2?l=english&count=5000"
    try:
        response = session.get(inv_url, headers=headers, timeout=15)
        
        if response.status_code == 429:
            return None, "Error 429: Steam is rate-limiting this server. Please try again in 15 minutes."
        
        inv_data = response.json()
        
        if not inv_data or inv_data.get('success') != 1:
            # Check specifically for Steam's internal error message
            steam_error = inv_data.get('Error', 'Inventory is private or Steam is busy.')
            return None, f"Steam says: {steam_error}"

    except Exception as e:
        return None, f"Connection Failed: {str(e)}"

    # Process descriptions and assets
    descriptions = {d['classid']: d for d in inv_data['descriptions']}
    item_names = [descriptions[item['classid']]['market_hash_name'] for item in inv_data['assets']]

    # 2. Fetch Prices from PriceEmpire
    price_url = "https://api.pricempire.com/v3/items/prices"
    params = {'appId': 730, 'sources': 'steam', 'currency': 'USD', 'api_key': a_key}
    
    try:
        price_res = requests.get(price_url, params=params).json()
        price_db = price_res.get('data', {})
    except:
        return None, "Steam inventory found, but PriceEmpire API is unreachable."

    # 3. Build DataFrame
    rows = []
    for name in item_names:
        item_price_data = price_db.get(name, {}).get('steam', {})
        price_cents = item_price_data.get('price', 0)
        rows.append({"Item": name, "Price": price_cents / 100})

    df = pd.DataFrame(rows)
    if df.empty:
        return None, "Inventory found but it seems empty."

    # Grouping
    summary = df.groupby('Item').agg({'Price': 'first', 'Item': 'count'}).rename(columns={'Item': 'Qty'}).reset_index()
    summary['Subtotal'] = summary['Price'] * summary['Qty']
    return summary.sort_values('Subtotal', ascending=False), None

# App UI Logic
if steam_id and api_key:
    if st.button('Refresh Now'):
        st.cache_data.clear()
        
    with st.spinner('Fetching inventory...'):
        data, error = get_inventory_and_prices(steam_id, api_key)
        
        if error:
            st.error(error)
            st.write("Troubleshooting: Make sure your Steam Profile AND Inventory are Public.")
        else:
            total = data['Subtotal'].sum()
            st.metric("Total Steam Value", f"${total:,.2f}")
            
            # Interactive Table
            st.dataframe(
                data.style.format({"Price": "${:.2f}", "Subtotal": "${:.2f}"}),
                use_container_width=True,
                hide_index=True
            )
else:
    st.info("Enter your 17-digit SteamID64 and API Key in the sidebar to start.")
