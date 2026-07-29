import pytest
import os
from project.src.database.repository import DatabaseRepository

def test_sqlite_repository_initialization(tmp_path):
    db_file = tmp_path / "test_frutand.db"
    repo = DatabaseRepository(str(db_file))
    
    assert os.path.exists(str(db_file))
    
    with repo._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        assert "empleados" in tables
        assert "periodos" in tables
        assert "marcaciones_raw" in tables
