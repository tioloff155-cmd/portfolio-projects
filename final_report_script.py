import sqlite3
import pandas as pd

def final_report():
    conn = sqlite3.connect('omni_quant.db')
    try:
        # Pega as últimas transações (últimas 24h ou da última sessão)
        # Assumindo que o usuário quer o resumo geral do que está no DB
        trades = pd.read_sql_query("SELECT * FROM trades", conn)
        state = pd.read_sql_query("SELECT value FROM state WHERE key='balance'", conn)
        balance = state.iloc[0,0] if not state.empty else 0.0
        
        if trades.empty:
            print("Nenhuma operação encontrada no banco de dados.")
            print(f"Saldo Atual: ${balance:.2f}")
            return
            
        sell_trades = trades[trades['action'] == 'sell']
        total_pnl = sell_trades['pnl_usd'].sum()
        total_executed = len(sell_trades)
        wins = len(sell_trades[sell_trades['pnl_usd'] > 0])
        accuracy = (wins / total_executed * 100) if total_executed > 0 else 0
        
        print(f"=== OMNIQUANT FINAL REPORT ===")
        print(f"Saldo Final: ${balance:.2f}")
        print(f"PnL Total: ${total_pnl:+.4f}")
        print(f"Trades Fechados: {total_executed}")
        print(f"Taxa de Acerto: {accuracy:.1f}%")
        print("\nÚltimos 5 Sells:")
        print(sell_trades.tail(5)[['asset', 'price', 'pnl_usd', 'pnl_pct', 'reason']].to_string(index=False))
        
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    final_report()
