import asyncio
import ccxt.async_support as ccxt

async def test():
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    exchange.set_sandbox_mode(True)
    try:
        data = await exchange.fetch_ohlcv('BTC/USDT', timeframe='1m', limit=10)
        print(f"Data length: {len(data)}")
    except Exception as e:
        print("Binance Error Type:", type(e))
        raise e
    finally:
        await exchange.close()

if __name__ == '__main__':
    asyncio.run(test())
