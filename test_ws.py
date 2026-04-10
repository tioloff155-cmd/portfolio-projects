import asyncio
import websockets

async def test():
    assets = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "DOGE/USDT", "TRX/USDT"]
    streams = "/".join([f"{a.replace('/', '').lower()}@aggTrade" for a in assets])
    url = f"wss://stream.binance.com:9443/ws/{streams}"
    print(f"Connecting to {url}")
    try:
        async with websockets.connect(url) as ws:
            print("Connected.")
            msg = await ws.recv()
            print("Received:", msg)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
