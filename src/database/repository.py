import sqlite3
import os

class DatabaseRepository:
    """Gestor de persistencia SQLite local para Frutand Chronos."""
    
    def __init__(self, db_path: str = "frutand_chronos.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Tabla Empleados
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS empleados (
                    id TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    area TEXT NOT NULL
                )
            """)
            # Tabla Periodos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS periodos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    fecha_inicio DATE,
                    fecha_fin DATE
                )
            """)
            # Tabla Marcaciones Raw
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marcaciones_raw (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empleado_id TEXT,
                    fecha DATE,
                    hora_entrada TIME,
                    hora_salida TIME,
                    periodo_id INTEGER,
                    FOREIGN KEY (empleado_id) REFERENCES empleados(id),
                    FOREIGN KEY (periodo_id) REFERENCES periodos(id)
                )
            """)
            conn.commit()
