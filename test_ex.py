import ccxt
def test():
    ex = ccxt.binance()
    try:
        print("Test Binance")
        print(ex.fetch_ohlcv('BTC/USDT', limit=5))
    except Exception as e:
        print(e)
    
    ex2 = ccxt.kucoin()
    try:
        print("Test Kucoin")
        print(ex2.fetch_ohlcv('BTC/USDT', limit=5))
    except Exception as e:
        print(e)

if __name__ == "__main__":
    test()
