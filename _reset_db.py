import sqlite3
conn = sqlite3.connect('omni_quant.db')
conn.execute("DELETE FROM positions")
conn.execute("UPDATE state SET value = 1000.0 WHERE key = 'balance'")
conn.execute("INSERT OR IGNORE INTO state (key, value) VALUES ('balance', 1000.0)")
conn.commit()
conn.close()
print("DB resetado: banca = R$ 1.000,00, posicoes limpas.")
