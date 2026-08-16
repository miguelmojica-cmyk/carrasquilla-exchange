import sqlite3

conn = sqlite3.connect('instance/carrasquilla.db')
cursor = conn.cursor()

print("Iniciando migración...")

# 1. Agregar columna 'tipo' sin perder datos existentes
try:
    cursor.execute("ALTER TABLE figuritas ADD COLUMN tipo TEXT DEFAULT 'normal'")
    print("Columna 'tipo' agregada.")
except sqlite3.OperationalError as e:
    print("La columna 'tipo' ya existe, se omite este paso.")

# 2. Recrear la tabla figuritas SIN la restricción de número único
cursor.execute("""
    CREATE TABLE figuritas_nueva (
        id INTEGER PRIMARY KEY,
        numero VARCHAR(10) NOT NULL,
        tipo VARCHAR(20) DEFAULT 'normal',
        nombre_jugador VARCHAR(100) NOT NULL,
        pais VARCHAR(100) NOT NULL,
        imagen_url VARCHAR(255) DEFAULT ''
    )
""")

# 3. Copiar todos los datos existentes a la tabla nueva
cursor.execute("""
    INSERT INTO figuritas_nueva (id, numero, tipo, nombre_jugador, pais, imagen_url)
    SELECT id, numero, COALESCE(tipo, 'normal'), nombre_jugador, pais, imagen_url FROM figuritas
""")

# 4. Reemplazar la tabla vieja por la nueva
cursor.execute("DROP TABLE figuritas")
cursor.execute("ALTER TABLE figuritas_nueva RENAME TO figuritas")

conn.commit()
conn.close()
print("Migración completada. Tus usuarios y figuritas anteriores siguen intactos.")