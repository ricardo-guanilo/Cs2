@st.cache_data(ttl=600) # Caches for 10 mins to prevent spamming Steam
def get_data(s_id, a_key):
    # 1. Get Inventory
    inv_url = f"https://steamcommunity.com/inventory/{s_id}/730/2?l=english&count=5000"
    try:
        response = requests.get(inv_url)
        
        # Check if Steam blocked you
        if response.status_code == 429:
            return None, "Steam blocked the request (Too Many Requests). Wait 5 minutes and try again."
        
        inv_res = response.json()
    except Exception as e:
        return None, f"Failed to connect to Steam: {str(e)}"
    
    # Check if the response actually contains the inventory
    if not inv_res or inv_res.get('success') != 1:
        error_msg = inv_res.get('Error', "Unknown Error (Inventory might be private)")
        return None, f"Steam Error: {error_msg}"

    descriptions = {d['classid']: d for d in inv_res['descriptions']}
    my_items = [descriptions[item['classid']]['market_hash_name'] for item in inv_res['assets']]

    # 2. Get Prices from PriceEmpire
    price_url = "https://api.pricempire.com/v3/items/prices"
    params = {'appId': 730, 'sources': 'steam', 'currency': 'USD', 'api_key': a_key}
    
    try:
        price_data = requests.get(price_url, params=params).json().get('data', {})
    except:
        return None, "Connected to Steam, but failed to get prices from PriceEmpire."
    
    # 3. Process
    rows = []
    for name in my_items:
        # Digging into the nested JSON for the steam price
        item_info = price_data.get(name, {})
        steam_info = item_info.get('steam', {})
        price_cents = steam_info.get('price', 0)
        
        rows.append({"Item": name, "Price": price_cents / 100})
    
    df = pd.DataFrame(rows)
    if df.empty:
        return None, "Inventory found, but no marketable items were detected."
        
    summary = df.groupby('Item').agg({'Price': 'first', 'Item': 'count'}).rename(columns={'Item': 'Qty'}).reset_index()
    summary['Subtotal'] = summary['Price'] * summary['Qty']
    return summary, None
