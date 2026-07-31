import sqlite3
import os
from typing import List, Dict, Any, Optional, Tuple

class DatabaseRepository:
    """Gestor de persistencia SQLite local para Frutand Chronos."""
    
    def __init__(self, db_path: str = "frutand_chronos.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Crea la estructura de tablas relacionales si no existe."""
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
                    fecha_inicio DATE NOT NULL,
                    fecha_fin DATE NOT NULL
                )
            """)
            # Tabla Marcaciones Raw
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marcaciones_raw (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empleado_id TEXT NOT NULL,
                    fecha DATE NOT NULL,
                    hora_entrada TEXT,
                    hora_salida TEXT,
                    periodo_id INTEGER NOT NULL,
                    FOREIGN KEY (empleado_id) REFERENCES empleados(id),
                    FOREIGN KEY (periodo_id) REFERENCES periodos(id)
                )
            """)
            conn.commit()

    def upsert_empleados(self, empleados: List[Dict[str, str]]):
        """Inserta o actualiza el catálogo de empleados."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO empleados (id, nombre, area)
                VALUES (:id, :nombre, :area)
                ON CONFLICT(id) DO UPDATE SET
                    nombre=excluded.nombre,
                    area=excluded.area
            """, empleados)
            conn.commit()

    def get_or_create_periodo(self, nombre: str, fecha_inicio: str, fecha_fin: str) -> Tuple[int, bool]:
        """
        Retorna (periodo_id, es_nuevo).
        Si existe un periodo para exactamente ese rango de fechas, retorna (id, False).
        De lo contrario crea uno nuevo y retorna (id, True).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM periodos 
                WHERE fecha_inicio = ? AND fecha_fin = ?
            """, (fecha_inicio, fecha_fin))
            row = cursor.fetchone()
            
            if row:
                return row["id"], False
            
            # Verificar si la tabla periodos tiene la columna 'anio'
            cols = [r[1] for r in cursor.execute("PRAGMA table_info(periodos)").fetchall()]
            if 'anio' in cols:
                try:
                    dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                    anio_val, mes_val, q_val = dt.year, dt.month, (1 if dt.day <= 15 else 2)
                except Exception:
                    anio_val, mes_val, q_val = 2026, 6, 1
                cursor.execute("""
                    INSERT INTO periodos (nombre, anio, mes, quincena, fecha_inicio, fecha_fin)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (nombre, anio_val, mes_val, q_val, fecha_inicio, fecha_fin))
            else:
                cursor.execute("""
                    INSERT INTO periodos (nombre, fecha_inicio, fecha_fin)
                    VALUES (?, ?, ?)
                """, (nombre, fecha_inicio, fecha_fin))

            conn.commit()
            return cursor.lastrowid, True

    def insert_marcaciones_bulk(self, periodo_id: int, marcaciones: List[Dict[str, Any]]):
        """Inserta marcaciones en lote en una única transacción."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            data = [
                (m["empleado_id"], m["fecha"], m["hora_entrada"], m["hora_salida"], periodo_id)
                for m in marcaciones
            ]
            cursor.executemany("""
                INSERT INTO marcaciones_raw (empleado_id, fecha, hora_entrada, hora_salida, periodo_id)
                VALUES (?, ?, ?, ?, ?)
            """, data)
            conn.commit()

    def overwrite_periodo_marcaciones(self, periodo_id: int, marcaciones: List[Dict[str, Any]]):
        """Limpia las marcaciones anteriores de un periodo y las reemplaza en lote."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM marcaciones_raw WHERE periodo_id = ?", (periodo_id,))
            data = [
                (m["empleado_id"], m["fecha"], m["hora_entrada"], m["hora_salida"], periodo_id)
                for m in marcaciones
            ]
            cursor.executemany("""
                INSERT INTO marcaciones_raw (empleado_id, fecha, hora_entrada, hora_salida, periodo_id)
                VALUES (?, ?, ?, ?, ?)
            """, data)
            conn.commit()

    def get_periodos(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de todos los periodos registrados."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, fecha_inicio, fecha_fin FROM periodos ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_areas(self) -> List[str]:
        """Obtiene la lista de áreas/departamentos únicos de empleados."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT area FROM empleados WHERE area IS NOT NULL AND area != '' ORDER BY area")
            return [row["area"] for row in cursor.fetchall()]

    def get_marcaciones(
        self, 
        periodo_id: Optional[int] = None, 
        busqueda: str = "", 
        area: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Consulta las marcaciones uniéndolas con la tabla empleados.
        Permite filtrado dinámico por periodo, texto de búsqueda (nombre/ID) y área.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    m.id,
                    m.empleado_id,
                    e.nombre AS empleado_nombre,
                    e.area AS empleado_area,
                    m.fecha,
                    m.hora_entrada,
                    m.hora_salida,
                    p.nombre AS periodo_nombre
                FROM marcaciones_raw m
                JOIN empleados e ON m.empleado_id = e.id
                JOIN periodos p ON m.periodo_id = p.id
                WHERE 1=1
            """
            params = []

            if periodo_id:
                query += " AND m.periodo_id = ?"
                params.append(periodo_id)

            if area and area != "Todas las áreas":
                query += " AND e.area = ?"
                params.append(area)

            if busqueda and busqueda.strip():
                term = f"%{busqueda.strip()}%"
                query += " AND (e.nombre LIKE ? OR e.id LIKE ?)"
                params.extend([term, term])

            query += " ORDER BY m.fecha DESC, e.nombre ASC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
