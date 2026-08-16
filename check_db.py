import sqlite3
conn = sqlite3.connect('instance/carrasquilla.db')
tablas = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(tablas)
conn.close()