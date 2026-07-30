import pytest
import os
from database.repository import DatabaseRepository

def test_sqlite_repository_crud(tmp_path):
    db_file = tmp_path / "test_repo.db"
    repo = DatabaseRepository(str(db_file))

    # 1. Upsert Empleados
    empleados = [
        {"id": "E100", "nombre": "Juan Pérez", "area": "Ventas"},
        {"id": "E200", "nombre": "Maria Lopez", "area": "Sistemas"}
    ]
    repo.upsert_empleados(empleados)

    areas = repo.get_areas()
    assert "Sistemas" in areas
    assert "Ventas" in areas

    # 2. Periodo
    p_id, is_new = repo.get_or_create_periodo("Quincena 1 Julio", "2026-07-01", "2026-07-15")
    assert is_new is True
    assert p_id > 0

    p_id2, is_new2 = repo.get_or_create_periodo("Quincena 1 Julio", "2026-07-01", "2026-07-15")
    assert is_new2 is False
    assert p_id2 == p_id

    # 3. Insert Bulk Marcaciones
    marcaciones = [
        {"empleado_id": "E100", "fecha": "2026-07-02", "hora_entrada": "08:00", "hora_salida": "17:00"},
        {"empleado_id": "E200", "fecha": "2026-07-02", "hora_entrada": "09:00", "hora_salida": "18:00"}
    ]
    repo.insert_marcaciones_bulk(p_id, marcaciones)

    # 4. Consultas con Filtro
    all_marks = repo.get_marcaciones(periodo_id=p_id)
    assert len(all_marks) == 2

    ventas_marks = repo.get_marcaciones(periodo_id=p_id, area="Ventas")
    assert len(ventas_marks) == 1
    assert ventas_marks[0]["empleado_nombre"] == "Juan Pérez"

    search_marks = repo.get_marcaciones(periodo_id=p_id, busqueda="Maria")
    assert len(search_marks) == 1
    assert search_marks[0]["empleado_id"] == "E200"

def test_overwrite_periodo(tmp_path):
    db_file = tmp_path / "test_overwrite.db"
    repo = DatabaseRepository(str(db_file))

    repo.upsert_empleados([{"id": "E1", "nombre": "Pedro", "area": "Lab"}])
    p_id, _ = repo.get_or_create_periodo("Periodo 1", "2026-07-01", "2026-07-15")

    # Primera ingesta
    repo.insert_marcaciones_bulk(p_id, [{"empleado_id": "E1", "fecha": "2026-07-01", "hora_entrada": "08:00", "hora_salida": "17:00"}])
    assert len(repo.get_marcaciones(periodo_id=p_id)) == 1

    # Sobreescritura
    repo.overwrite_periodo_marcaciones(p_id, [
        {"empleado_id": "E1", "fecha": "2026-07-01", "hora_entrada": "08:30", "hora_salida": "17:30"},
        {"empleado_id": "E1", "fecha": "2026-07-02", "hora_entrada": "08:00", "hora_salida": "17:00"}
    ])
    updated_marks = repo.get_marcaciones(periodo_id=p_id)
    assert len(updated_marks) == 2
    assert updated_marks[0]["hora_entrada"] in ["08:30", "08:00"]
