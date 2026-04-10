import os
import sys
import time
import threading

# Fix encoding para Windows PowerShell
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

def test():
    load_dotenv()
    email = os.getenv("IQ_EMAIL")
    password = os.getenv("IQ_PASSWORD")
    account_type = os.getenv("IQ_ACCOUNT_TYPE", "PRACTICE")
    
    print(f"[1] Conectando com: {email}")
    API = IQ_Option(email, password)
    
    result = [False, "timeout"]
    def _connect():
        try:
            c, r = API.connect()
            result[0] = c
            result[1] = r
        except Exception as ex:
            result[1] = str(ex)
    
    t = threading.Thread(target=_connect, daemon=True)
    t.start()
    t.join(timeout=30)
    
    if t.is_alive():
        print("[ERRO] Conexao travou (timeout 30s).")
        os._exit(1)
    
    if not result[0]:
        print(f"[ERRO] Conexao falhou: {result[1]}")
        return
    
    print("[2] Conectado! Trocando para PRACTICE...")
    API.change_balance(account_type)
    time.sleep(2)
    
    balance = API.get_balance()
    print(f"[3] Saldo Practice: ${balance}")
    
    print("[4] Testando get_candles para EURUSD-OTC...")
    try:
        candles = API.get_candles("EURUSD-OTC", 60, 5, time.time())
        if candles:
            print(f"    Candles recebidos: {len(candles)}")
            for c in candles:
                print(f"    O:{c['open']:.5f} H:{c['max']:.5f} L:{c['min']:.5f} C:{c['close']:.5f}")
        else:
            print("    Nenhum candle retornado (ativo pode estar fechado)")
    except Exception as e:
        print(f"    Erro: {e}")
    
    print("[5] Testando realtime stream...")
    try:
        API.start_candles_stream("EURUSD-OTC", 60, 10)
        time.sleep(3)
        rt = API.get_realtime_candles("EURUSD-OTC", 60)
        if rt:
            print(f"    Realtime candles: {len(rt)} no buffer")
            for ts in sorted(rt.keys())[-3:]:
                c = rt[ts]
                print(f"    [{ts}] C:{c['close']:.5f}")
        else:
            print("    Nenhum candle realtime")
        API.stop_candles_stream("EURUSD-OTC", 60)
    except Exception as e:
        print(f"    Erro stream: {e}")
    
    print("\n[OK] Teste de conexao completo!")

if __name__ == "__main__":
    test()
