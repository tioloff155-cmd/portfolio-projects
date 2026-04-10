import asyncio
import aiohttp
import socket

async def test():
    try:
        # Força o uso do protocolo IPv4 e desabilita o DNS cache se houver problemas
        connector = aiohttp.TCPConnector(family=socket.AF_INET)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get('https://api.binance.com/api/v3/ping') as resp:
                print(f"Status: {resp.status}")
                print(await resp.text())
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
