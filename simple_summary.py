import sqlite3
conn = sqlite3.connect('omni_quant.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM trades WHERE action="sell"')
sells = c.fetchone()[0]
c.execute('SELECT SUM(pnl_usd) FROM trades WHERE action="sell"')
pnl = c.fetchone()[0] or 0.0
c.execute('SELECT value FROM state WHERE key="balance"')
bal = c.fetchone()[0]
print(f"TRADES_CLOSED: {sells}")
print(f"TOTAL_PNL: {pnl:.4f}")
print(f"FINAL_BALANCE: {bal:.2f}")
conn.close()
