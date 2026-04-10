import sqlite3
import os

def reset_db():
    db_name = 'omni_quant.db'
    if os.path.exists(db_name):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE state SET value=1000.0 WHERE key='balance'")
        # Também podemos reiniciar o ledger se desejar
        cursor.execute("DELETE FROM trades")
        cursor.execute("DELETE FROM positions")
        conn.commit()
        conn.close()
        print("Database reset to 1000.0 and trades wiped.")
    else:
        print("DB not found.")

reset_db()
