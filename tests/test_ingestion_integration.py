import pytest
import pandas as pd
from core.parser import BiometricParser
from database.repository import DatabaseRepository

def test_full_ingestion_pipeline(tmp_path):
    # 1. Generar Excel de prueba
    excel_file = tmp_path / "biometrico_integration.xlsx"
    df = pd.DataFrame({
        "ID": ["101", "102"],
        "Nombre": ["Laura Torres", "Diego Silva"],
        "Área": ["Calidad", "Mantenimiento"],
        "Fecha": ["2026-07-15", "2026-07-15"],
        "Hora Entrada": ["06:00", "07:00"],
        "Hora Salida": ["14:00", "15:00"]
    })
    df.to_excel(excel_file, index=False)

    # 2. Base de Datos SQLite temporal
    db_file = tmp_path / "integration.db"
    repo = DatabaseRepository(str(db_file))

    # 3. Parsing
    parser = BiometricParser(str(excel_file))
    parsed_data = parser.parse()

    # 4. Guardar en BD
    repo.upsert_empleados(parsed_data["empleados"])
    p_id, _ = repo.get_or_create_periodo(
        parsed_data["periodo"]["nombre"],
        parsed_data["periodo"]["fecha_inicio"],
        parsed_data["periodo"]["fecha_fin"]
    )
    repo.insert_marcaciones_bulk(p_id, parsed_data["marcaciones"])

    # 5. Verificación de Integridad Relacional
    results = repo.get_marcaciones(periodo_id=p_id)
    assert len(results) == 2
    assert {r["empleado_nombre"] for r in results} == {"Laura Torres", "Diego Silva"}
    assert {r["empleado_area"] for r in results} == {"Calidad", "Mantenimiento"}
