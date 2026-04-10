import asyncio
import websockets
import json
import ssl

async def test():
    print("Iniciando Teste de Conexão Binance (HFT Sniper Mode)...")
    url = "wss://stream.binance.com:9443/ws/btcusdt@aggTrade"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        async with websockets.connect(url, ssl=ctx, timeout=10) as ws:
            print("✅ CONEXÃO OK! BINANCE ESTÁ RESPONDENDO.")
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"✅ DADO RECEBIDO COM SUCESSO: Price: {data['p']}")
            return True
    except Exception as e:
        print(f"❌ FALHA DE CONEXÃO: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test())
