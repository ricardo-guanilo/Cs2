import streamlit as st
import requests
import pandas as pd

# --- 1. DEFINE YOUR INVENTORY HERE ---
# Write the exact "Market Hash Name" as it appears on Steam
MY_ITEMS = {
    "AK-47 | Slate (Field-Tested)": 1,
    "Desert Eagle | Printstream (Field-Tested)": 1,
    "Recoil Case": 50,
    "Paris 2023 Legends Sticker Capsule": 100,
    # Add your items here...
}

# --- APP SETUP ---
st.set_page_config(page_title="My Skin Portfolio", layout="centered")
st.title("Skins Price Tracker")

with st.sidebar:
    api_key = st.text_input("PriceEmpire API Key", type="password")
    st.info("Since your items are hardcoded, we don't need Steam login at all!")

@st.cache_data(ttl=3600) # Updates prices once per hour
def get_prices(a_key):
    url = "https://api.pricempire.com/v3/items/prices"
    params = {'appId': 730, 'sources': 'steam', 'currency': 'USD', 'api_key': a_key}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('data', {}), None
        else:
            return None, f"PriceEmpire Error: {response.status_code}"
    except Exception as e:
        return None, f"Connection Error: {str(e)}"

# --- MAIN LOGIC ---
if api_key:
    with st.spinner('Updating market prices...'):
        price_db, error = get_prices(api_key)
        
        if error:
            st.error(error)
        else:
            rows = []
            for item_name, qty in MY_ITEMS.items():
                # Get the steam price from the API data
                item_data = price_db.get(item_name, {}).get('steam', {})
                price = item_data.get('price', 0) / 100 # Convert cents to dollars
                
                rows.append({
                    "Item": item_name,
                    "Price": price,
                    "Qty": qty,
                    "Subtotal": price * qty
                })
            
            df = pd.DataFrame(rows)
            total_val = df['Subtotal'].sum()
            
            # Display Metric
            st.metric("Total Portfolio Value", f"${total_val:,.2f}")
            
            # Display Table
            st.dataframe(
                df.style.format({"Price": "${:.2f}", "Subtotal": "${:.2f}"}),
                use_container_width=True,
                hide_index=True
            )
            
            st.success("Prices updated successfully!")
else:
    st.warning("Please enter your PriceEmpire API Key in the sidebar.")
