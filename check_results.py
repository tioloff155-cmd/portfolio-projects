import sqlite3
import pandas as pd

def get_summary():
    conn = sqlite3.connect('omni_quant.db')
    try:
        # Load trades
        trades = pd.read_sql_query("SELECT * FROM trades", conn)
        # Load balance
        balance = pd.read_sql_query("SELECT value FROM state WHERE key='balance'", conn).iloc[0,0]
        
        if trades.empty:
            print("Nenhuma operação registrada nesta sessão ou no histórico recente.")
            print(f"Saldo Final: ${balance:.2f}")
            return

        total_trades = len(trades[trades['action'] == 'sell'])
        buys = len(trades[trades['action'] == 'buy'])
        sells = len(trades[trades['action'] == 'sell'])
        
        total_pnl = trades['pnl_usd'].sum()
        avg_pnl_pct = trades['pnl_pct'].mean()
        
        wins = len(trades[trades['pnl_usd'] > 0])
        losses = len(trades[trades['pnl_usd'] < 0])
        accuracy = (wins / total_trades * 100) if total_trades > 0 else 0
        
        print(f"--- RESUMO DE OPERAÇÕES ---")
        print(f"Total de Trades (Completos): {total_trades}")
        print(f"Compras: {buys} | Vendas: {sells}")
        print(f"Taxa de Acerto: {accuracy:.1f}%")
        print(f"P&L Total Acumulado: ${total_pnl:+.4f}")
        print(f"Saldo em Conta: ${balance:.2f}")
        print("\nÚltimos 10 Trades:")
        print(trades.tail(10)[['asset', 'action', 'price', 'pnl_usd', 'reason']].to_string(index=False))
        
    except Exception as e:
        print(f"Erro ao ler banco de dados: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    get_summary()
