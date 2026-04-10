import requests
try:
    resp = requests.get('https://api.binance.com/api/v3/ping')
    print(f"Status: {resp.status_code}")
    print(resp.text)
except Exception as e:
    print(f"Error: {e}")
