import sqlite3

conn = sqlite3.connect('instance/carrasquilla.db')
cursor = conn.cursor()

print("Iniciando migración...")

# --- Publicaciones: columna imagen_url ---
try:
    cursor.execute("ALTER TABLE publicaciones ADD COLUMN imagen_url TEXT DEFAULT ''")
    print("[OK] Columna 'imagen_url' agregada a publicaciones.")
except sqlite3.OperationalError:
    print("[SKIP] Columna 'imagen_url' en publicaciones ya existía.")

# --- Nueva tabla: mensajes ---
cursor.execute("""
    CREATE TABLE IF NOT EXISTS mensajes (
        id INTEGER PRIMARY KEY,
        id_remitente INTEGER NOT NULL,
        id_destinatario INTEGER NOT NULL,
        id_publicacion INTEGER,
        contenido TEXT NOT NULL,
        leido BOOLEAN DEFAULT 0,
        fecha DATETIME,
        FOREIGN KEY (id_remitente) REFERENCES usuarios(id),
        FOREIGN KEY (id_destinatario) REFERENCES usuarios(id),
        FOREIGN KEY (id_publicacion) REFERENCES publicaciones(id)
    )
""")
print("[OK] Tabla 'mensajes' verificada/creada.")

conn.commit()
conn.close()
print("Migración completada.")