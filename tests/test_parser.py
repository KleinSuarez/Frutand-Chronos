import pytest
import pandas as pd
import os
from core.parser import BiometricParser

def test_parser_valid_excel(tmp_path):
    file_path = tmp_path / "reporte_biometrico_test.xlsx"
    df_test = pd.DataFrame({
        "ID Empleado": ["E001", "E002", "E001"],
        "Nombre Empleado": ["Carlos Mendoza", "Ana Gómez", "Carlos Mendoza"],
        "Área": ["Operativos", "Administrativos", "Operativos"],
        "Fecha": ["2026-07-01", "2026-07-01", "2026-07-02"],
        "Hora Entrada": ["07:00", "08:00", "07:05"],
        "Hora Salida": ["17:00", "16:00", "17:10"]
    })
    df_test.to_excel(file_path, index=False)

    parser = BiometricParser(str(file_path))
    result = parser.parse()

    assert len(result["empleados"]) == 2
    assert len(result["marcaciones"]) == 3
    assert result["periodos"][0]["nombre"] == "1.ª Quincena - Julio 2026"

def test_parser_xlsx_renamed_to_xls(tmp_path):
    file_path = tmp_path / "reporte_guardado_como.xls"
    df_test = pd.DataFrame({
        "ID Empleado": ["E001", "E002"],
        "Nombre Empleado": ["Carlos Mendoza", "Ana Gómez"],
        "Área": ["Operativos", "Administrativos"],
        "Fecha": ["2026-07-01", "2026-07-01"],
        "Hora Entrada": ["07:00", "08:00"],
        "Hora Salida": ["17:00", "16:00"]
    })
    df_test.to_excel(file_path, index=False, engine='openpyxl')

    parser = BiometricParser(str(file_path))
    result = parser.parse()

    assert len(result["empleados"]) == 2
    assert len(result["marcaciones"]) == 2

def test_parser_real_hikvision_quincenas_split():
    real_file = r"c:\Users\yahir\Code\Frutand Chronos\context\report junio.xlsx"
    if not os.path.exists(real_file):
        pytest.skip(f"Archivo de prueba real '{real_file}' no encontrado.")

    parser = BiometricParser(real_file)
    result = parser.parse()

    assert "empleados" in result
    assert "periodos" in result
    assert len(result["periodos"]) == 2
    
    # 1.ª Quincena (del 1 al 15 de junio)
    q1 = result["periodos"][0]
    assert q1["nombre"] == "1.ª Quincena - Junio 2026"
    assert q1["fecha_inicio"] == "2026-06-01"
    assert q1["fecha_fin"] == "2026-06-15"

    # 2.ª Quincena (del 16 al 30 de junio)
    q2 = result["periodos"][1]
    assert q2["nombre"] == "2.ª Quincena - Junio 2026"
    assert q2["fecha_inicio"] == "2026-06-16"
    assert q2["fecha_fin"] == "2026-06-30"

    assert len(result["empleados"]) == 39
    assert len(result["marcaciones"]) == 548

def test_parser_real_hikvision_xls_frameset_quincenas():
    real_file_xls = r"c:\Users\yahir\Code\Frutand Chronos\context\report junio.xls"
    if not os.path.exists(real_file_xls):
        pytest.skip(f"Archivo de prueba real '.xls' '{real_file_xls}' no encontrado.")

    parser = BiometricParser(real_file_xls)
    result = parser.parse()

    assert "periodos" in result
    assert len(result["periodos"]) == 2
    assert result["periodos"][0]["nombre"] == "1.ª Quincena - Junio 2026"
    assert result["periodos"][1]["nombre"] == "2.ª Quincena - Junio 2026"
    assert len(result["marcaciones"]) == 548

def test_parser_valid_csv_comma(tmp_path):
    file_path = tmp_path / "reporte_biometrico.csv"
    content = (
        "id_empleado,nombre,area,fecha,hora_entrada,hora_salida\n"
        "101,Juan Perez,Planta,2026-07-01,06:00,14:00\n"
        "102,Maria Lopez,Calidad,2026-07-01,07:00,15:00\n"
    )
    file_path.write_text(content, encoding="utf-8")

    parser = BiometricParser(str(file_path))
    result = parser.parse()

    assert len(result["empleados"]) == 2
    assert len(result["marcaciones"]) == 2

def test_parser_valid_csv_semicolon(tmp_path):
    file_path = tmp_path / "reporte_biometrico_semicolon.csv"
    content = (
        "Cédula;Nombre Empleado;Departamento;Fecha;Entrada;Salida\n"
        "9901;Roberto Gomez;Operaciones;2026-07-10;08:00;17:00\n"
    )
    file_path.write_text(content, encoding="utf-8")

    parser = BiometricParser(str(file_path))
    result = parser.parse()

    assert len(result["empleados"]) == 1

def test_parser_high_volume_excel(tmp_path):
    file_path = tmp_path / "masivo_test.xlsx"
    records = []
    for i in range(10000):
        records.append({
            "id_empleado": f"EMP_{i % 500:03d}",
            "nombre": f"Empleado Test {i % 500}",
            "area": "Planta" if i % 2 == 0 else "Logística",
            "fecha": f"2026-07-{(i % 15) + 1:02d}",
            "hora_entrada": "07:00",
            "hora_salida": "17:00"
        })
    df_masivo = pd.DataFrame(records)
    df_masivo.to_excel(file_path, index=False)

    parser = BiometricParser(str(file_path))
    result = parser.parse()

    assert len(result["empleados"]) == 500
    assert len(result["marcaciones"]) == 10000

def test_parser_unsupported_file_extension(tmp_path):
    file_path = tmp_path / "reporte.pdf"
    file_path.write_text("PDF Fake Data", encoding="utf-8")

    with pytest.raises(ValueError, match="Formato de archivo no válido"):
        BiometricParser(str(file_path))

def test_parser_missing_required_columns(tmp_path):
    file_path = tmp_path / "invalido.csv"
    file_path.write_text("ColumnaA,ColumnaB\n1,2", encoding="utf-8")

    parser = BiometricParser(str(file_path))
    with pytest.raises(ValueError, match="Columnas requeridas no encontradas"):
        parser.parse()
