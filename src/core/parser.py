import pandas as pd
import os
import csv
import io
import calendar
from html.parser import HTMLParser
from typing import Dict, Any, List, Optional
from datetime import datetime

class _SimpleHTMLTableParser(HTMLParser):
    """Parser liviano basado en la librería estándar de Python para extraer tablas HTML."""
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = []
        self.current_cell = []
        self.in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag in ('td', 'th'):
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            self.in_cell = False
            self.current_row.append(''.join(self.current_cell).strip())
        elif tag == 'tr':
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = []

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell.append(data)


class BiometricParser:
    """
    Parser multiformato universal para extracción, autodetección y normalización de marcaciones biométricas 
    con clasificación estricta de quincenas de nómina (1.ª Quincena: días 1-15, 2.ª Quincena: días 16-fin de mes).
    Compatible con exportaciones nativas de Hikvision, ZKTeco, Anviz (ej. 'report junio.xls' y 'report junio.xlsx').
    """
    
    SUPPORTED_EXTENSIONS = ('.xlsx', '.xls', '.csv', '.ods', '.tsv', '.txt', '.htm', '.html')

    COLUMN_MAPPINGS = {
        "id": ["id de persona", "id_persona", "id", "id_empleado", "id empleado", "cedula", "cédula", "codigo", "código", "employee_id", "badgenumber", "nro doc", "documento"],
        "nombre": ["nombre", "nombre_empleado", "nombre empleado", "empleado", "name", "employee_name", "nombres"],
        "area": ["departamento", "department", "area", "área", "seccion", "sección", "cargo"],
        "fecha": ["fecha", "date", "dia", "día"],
        "hora_combinada": ["hora", "time", "timestamp", "fecha_hora", "fecha y hora"],
        "hora_entrada": ["hora_entrada", "hora entrada", "entrada", "check_in", "checkin", "in_time", "ingreso"],
        "hora_salida": ["hora_salida", "hora salida", "salida", "check_out", "checkout", "out_time", "egreso"]
    }

    MESES_ES = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo '{file_path}' no existe.")
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext and ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Formato de archivo no válido ('{ext}'). "
                f"Debe seleccionar una hoja de cálculo o archivo delimitado: {', '.join(self.SUPPORTED_EXTENSIONS)}."
            )
        
        self.file_path = file_path
        self.ext = ext or ".xlsx"

    def _get_quincena_info(self, fecha_str: str) -> Dict[str, str]:
        """Clasifica una fecha en 1.ª Quincena (días 1-15) o 2.ª Quincena (días 16 a fin de mes)."""
        dt = datetime.strptime(fecha_str, '%Y-%m-%d')
        month_name = self.MESES_ES[dt.month - 1]
        
        if dt.day <= 15:
            return {
                "key": f"{dt.year}-{dt.month:02d}-Q1",
                "nombre": f"1.ª Quincena - {month_name} {dt.year}",
                "fecha_inicio": f"{dt.year}-{dt.month:02d}-01",
                "fecha_fin": f"{dt.year}-{dt.month:02d}-15"
            }
        else:
            last_day = calendar.monthrange(dt.year, dt.month)[1]
            return {
                "key": f"{dt.year}-{dt.month:02d}-Q2",
                "nombre": f"2.ª Quincena - {month_name} {dt.year}",
                "fecha_inicio": f"{dt.year}-{dt.month:02d}-16",
                "fecha_fin": f"{dt.year}-{dt.month:02d}-{last_day:02d}"
            }

    def _find_column(self, df: pd.DataFrame, key: str) -> Optional[str]:
        """Busca la columna correspondiente en el DataFrame comparando variaciones de nombres."""
        df_cols_lower = {str(col).strip().lower(): col for col in df.columns}
        for candidate in self.COLUMN_MAPPINGS.get(key, []):
            if candidate in df_cols_lower:
                return df_cols_lower[candidate]
        return None

    def _find_header_row(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Escanea las primeras 15 filas para ubicar la fila que contiene los encabezados."""
        for i in range(min(15, len(df_raw))):
            row_values = [str(val).strip().lower() for val in df_raw.iloc[i].values if pd.notna(val)]
            matches_id = any(candidate in row_values for candidate in self.COLUMN_MAPPINGS["id"])
            matches_nombre = any(candidate in row_values for candidate in self.COLUMN_MAPPINGS["nombre"])
            
            if matches_id and matches_nombre:
                df = df_raw.iloc[i+1:].copy()
                df.columns = df_raw.iloc[i].values
                return df.reset_index(drop=True)
        
        return df_raw

    def _load_dataframe(self) -> pd.DataFrame:
        """Carga el DataFrame por flujo de memoria (io.BytesIO) resolviendo HTML Framesets."""
        with open(self.file_path, 'rb') as f:
            content = f.read()

        if not content:
            raise ValueError("El archivo seleccionado está completamente vacío.")

        # 0. Detección de Excel HTML Frameset (.xls que apunta a su carpeta .files/sheet001.htm)
        if b'Excel Workbook Frameset' in content or b'<frame src=' in content:
            base_dir = os.path.dirname(self.file_path)
            file_name_no_ext = os.path.splitext(os.path.basename(self.file_path))[0]
            files_dir = os.path.join(base_dir, f"{file_name_no_ext}.files")
            
            if os.path.exists(files_dir):
                for candidate in sorted(os.listdir(files_dir)):
                    if candidate.lower().endswith(('.htm', '.html')) and ('sheet' in candidate.lower() or 'file' in candidate.lower()):
                        cand_path = os.path.join(files_dir, candidate)
                        try:
                            with open(cand_path, 'rb') as sf:
                                content = sf.read()
                            break
                        except Exception:
                            pass

        df_raw = None

        # 1. Probar lectura de Tablas HTML (Común en exportaciones biométricas .xls)
        if b'<table' in content.lower() or b'<tr' in content.lower():
            try:
                p = _SimpleHTMLTableParser()
                p.feed(content.decode('utf-8', errors='ignore'))
                if p.rows:
                    df_raw = pd.DataFrame(p.rows)
            except Exception:
                pass

        # 2. Probar motores Excel / OpenDocument mediante flujo de bytes (openpyxl, xlrd, odf)
        if df_raw is None:
            for eng in ['openpyxl', 'xlrd', 'odf']:
                try:
                    df_raw = pd.read_excel(io.BytesIO(content), header=None, dtype=str, engine=eng)
                    if df_raw is not None and not df_raw.empty:
                        break
                except Exception:
                    continue

        # 3. Fallback pd.read_excel sin engine explícito
        if df_raw is None:
            try:
                df_raw = pd.read_excel(io.BytesIO(content), header=None, dtype=str)
            except Exception:
                pass

        # 4. Fallback CSV/TSV
        if df_raw is None:
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    dialect_sep = None
                    try:
                        sample_text = content[:4096].decode(encoding, errors='ignore')
                        dialect = csv.Sniffer().sniff(sample_text, delimiters=[',', ';', '\t', '|'])
                        dialect_sep = dialect.delimiter
                    except Exception:
                        dialect_sep = None

                    if dialect_sep:
                        df_raw = pd.read_csv(io.BytesIO(content), sep=dialect_sep, encoding=encoding, header=None, dtype=str)
                    else:
                        df_raw = pd.read_csv(io.BytesIO(content), sep=None, engine='python', encoding=encoding, header=None, dtype=str)

                    if df_raw is not None and not df_raw.empty:
                        break
                except Exception:
                    continue

        if df_raw is None or df_raw.empty:
            raise ValueError(f"No se pudo interpretar el contenido del archivo ('{self.ext}'). Verifique que el formato sea una hoja de cálculo o tabla válida.")

        return self._find_header_row(df_raw)

    def parse(self) -> Dict[str, Any]:
        """
        Lee el archivo y extrae la información normalizada de empleados, agrupando marcaciones 
        en periodos quincenales independientes (1.ª Quincena: 1-15, 2.ª Quincena: 16-fin).
        """
        df = self._load_dataframe()

        col_id = self._find_column(df, "id")
        col_nombre = self._find_column(df, "nombre")
        col_area = self._find_column(df, "area")
        col_fecha = self._find_column(df, "fecha")
        col_hora_comb = self._find_column(df, "hora_combinada")
        col_entrada = self._find_column(df, "hora_entrada")
        col_salida = self._find_column(df, "hora_salida")

        # Verificar columnas mínimas requeridas
        missing = []
        if not col_id: missing.append("ID/Cédula")
        if not col_nombre: missing.append("Nombre")
        if not col_fecha and not col_hora_comb: missing.append("Fecha o Hora")

        if missing:
            raise ValueError(f"Columnas requeridas no encontradas en el archivo: {', '.join(missing)}")

        empleados_dict = {}
        raw_records = []

        # CASO A: Reportes en bruto con columna 'Hora' combinada
        if col_hora_comb and (not col_entrada or not col_salida or col_hora_comb == col_entrada):
            df['Hora_dt'] = pd.to_datetime(df[col_hora_comb], errors='coerce')
            df_valid = df.dropna(subset=['Hora_dt']).copy()

            if df_valid.empty:
                raise ValueError("No se pudieron parsear fechas/horas válidas en la columna 'Hora'.")

            df_valid['emp_id_clean'] = df_valid[col_id].astype(str).str.strip().str.replace("'", "")
            df_valid['emp_nombre_clean'] = df_valid[col_nombre].astype(str).str.strip()
            
            if col_area and col_area in df_valid.columns:
                df_valid['emp_area_clean'] = df_valid[col_area].astype(str).str.strip().apply(
                    lambda x: x.split('/')[-1] if '/' in x else (x if x.lower() not in ('nan', 'none', '') else "General")
                )
            else:
                df_valid['emp_area_clean'] = "General"

            df_valid['fecha_str'] = df_valid['Hora_dt'].dt.strftime('%Y-%m-%d')
            df_valid['hora_str'] = df_valid['Hora_dt'].dt.strftime('%H:%M')

            for _, row in df_valid[['emp_id_clean', 'emp_nombre_clean', 'emp_area_clean']].drop_duplicates().iterrows():
                emp_id = row['emp_id_clean']
                if emp_id and emp_id.lower() not in ('nan', 'none', ''):
                    empleados_dict[emp_id] = {
                        "id": emp_id,
                        "nombre": row['emp_nombre_clean'],
                        "area": row['emp_area_clean']
                    }

            grouped = df_valid.groupby(['emp_id_clean', 'fecha_str'])
            for (emp_id, fecha_str), group in grouped:
                if emp_id not in empleados_dict:
                    continue
                
                horas_sorted = group['hora_str'].sort_values().tolist()
                entrada_str = horas_sorted[0]
                salida_str = horas_sorted[-1] if len(horas_sorted) > 1 and horas_sorted[-1] != entrada_str else "--:--"

                raw_records.append({
                    "empleado_id": emp_id,
                    "fecha": fecha_str,
                    "hora_entrada": entrada_str,
                    "hora_salida": salida_str
                })

        # CASO B: Reportes procesados con columnas explícitas 'Hora Entrada' y 'Hora Salida'
        else:
            for _, row in df.iterrows():
                emp_id = str(row[col_id]).strip().replace("'", "")
                if not emp_id or emp_id.lower() in ('nan', 'none', ''):
                    continue

                emp_nombre = str(row[col_nombre]).strip() if col_nombre and pd.notna(row[col_nombre]) else f"Empleado {emp_id}"
                
                if col_area and pd.notna(row[col_area]):
                    area_raw = str(row[col_area]).strip()
                    emp_area = area_raw.split('/')[-1] if '/' in area_raw else area_raw
                else:
                    emp_area = "General"

                if emp_id not in empleados_dict:
                    empleados_dict[emp_id] = {
                        "id": emp_id,
                        "nombre": emp_nombre,
                        "area": emp_area
                    }

                raw_fecha = str(row[col_fecha]).strip() if col_fecha and pd.notna(row[col_fecha]) else ""
                if not raw_fecha or raw_fecha.lower() in ('nan', 'none'):
                    continue

                fecha_str = raw_fecha.split()[0]
                entrada_str = str(row[col_entrada]).strip() if col_entrada and pd.notna(row[col_entrada]) and str(row[col_entrada]).strip().lower() not in ('nan', 'none') else "--:--"
                salida_str = str(row[col_salida]).strip() if col_salida and pd.notna(row[col_salida]) and str(row[col_salida]).strip().lower() not in ('nan', 'none') else "--:--"

                raw_records.append({
                    "empleado_id": emp_id,
                    "fecha": fecha_str,
                    "hora_entrada": entrada_str,
                    "hora_salida": salida_str
                })

        if not raw_records:
            raise ValueError("No se encontraron registros de marcaciones válidos en el archivo.")

        # Agrupar marcaciones por quincenas estrictas
        quincenas_dict = {}
        for rec in raw_records:
            q_info = self._get_quincena_info(rec["fecha"])
            key = q_info["key"]
            if key not in quincenas_dict:
                quincenas_dict[key] = {
                    "nombre": q_info["nombre"],
                    "fecha_inicio": q_info["fecha_inicio"],
                    "fecha_fin": q_info["fecha_fin"],
                    "marcaciones": []
                }
            quincenas_dict[key]["marcaciones"].append(rec)

        periodos_list = [
            {
                "nombre": q_data["nombre"],
                "fecha_inicio": q_data["fecha_inicio"],
                "fecha_fin": q_data["fecha_fin"],
                "marcaciones": q_data["marcaciones"]
            }
            for q_data in sorted(quincenas_dict.values(), key=lambda x: x["fecha_inicio"])
        ]

        # Mantener retrocompatibilidad agregando 'periodo' y 'marcaciones' generales
        first_q = periodos_list[0]
        all_marcaciones = [m for q in periodos_list for m in q["marcaciones"]]

        return {
            "empleados": list(empleados_dict.values()),
            "periodos": periodos_list,
            "periodo": {
                "nombre": first_q["nombre"],
                "fecha_inicio": first_q["fecha_inicio"],
                "fecha_fin": first_q["fecha_fin"]
            },
            "marcaciones": all_marcaciones,
            "total_rows": len(all_marcaciones)
        }
