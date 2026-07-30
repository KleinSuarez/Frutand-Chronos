import threading
from typing import Callable, Dict, Any, Optional
from core.parser import BiometricParser
from database.repository import DatabaseRepository

class IngestionController:
    """Controlador asíncrono para ingesta de marcaciones biométricas clasificadas por quincenas en SQLite."""

    def __init__(self, repository: DatabaseRepository):
        self.repo = repository

    def process_excel_async(
        self,
        file_path: str,
        on_start: Optional[Callable[[], None]] = None,
        on_success: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_duplicate: Optional[Callable[[Dict[str, Any], Callable[[bool], None]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """
        Inicia la lectura y persistencia quincenal en un hilo secundario (Background Thread).
        Garantiza la detección de periodos existentes para alertar al usuario sobre sobrescrituras.
        """
        if on_start:
            on_start()

        def _worker():
            try:
                # 1. Parsear el archivo con clasificación de quincenas
                parser = BiometricParser(file_path)
                data = parser.parse()

                empleados = data["empleados"]
                periodos_list = data.get("periodos", [])
                if not periodos_list and "periodo" in data:
                    periodos_list = [{
                        "nombre": data["periodo"]["nombre"],
                        "fecha_inicio": data["periodo"]["fecha_inicio"],
                        "fecha_fin": data["periodo"]["fecha_fin"],
                        "marcaciones": data["marcaciones"]
                    }]

                # 2. Verificar cuáles quincenas ya existen en la BD
                existing_quincenas = []
                periodos_plan = []

                for q_data in periodos_list:
                    periodo_id, is_new = self.repo.get_or_create_periodo(
                        nombre=q_data["nombre"],
                        fecha_inicio=q_data["fecha_inicio"],
                        fecha_fin=q_data["fecha_fin"]
                    )
                    periodos_plan.append((periodo_id, is_new, q_data))
                    if not is_new:
                        existing_quincenas.append(q_data["nombre"])

                def _execute_save(overwrite: bool = False):
                    def _save_task():
                        try:
                            # Persistir empleados
                            self.repo.upsert_empleados(empleados)

                            last_periodo_id = None
                            last_periodo_nombre = ""
                            total_marcaciones = 0
                            created_periodos_names = []

                            for p_id, is_new, q_data in periodos_plan:
                                if is_new or overwrite:
                                    self.repo.overwrite_periodo_marcaciones(p_id, q_data["marcaciones"])
                                
                                last_periodo_id = p_id
                                last_periodo_nombre = q_data["nombre"]
                                total_marcaciones += len(q_data["marcaciones"])
                                created_periodos_names.append(q_data["nombre"])

                            summary = {
                                "periodo_id": last_periodo_id,
                                "periodo_nombre": ", ".join(created_periodos_names) if len(created_periodos_names) > 1 else last_periodo_nombre,
                                "num_empleados": len(empleados),
                                "num_marcaciones": total_marcaciones,
                                "num_quincenas": len(periodos_plan),
                                "overwritten": overwrite
                            }

                            if on_success:
                                on_success(summary)
                        except Exception as ex:
                            if on_error:
                                on_error(f"Error al guardar datos en SQLite: {str(ex)}")

                    threading.Thread(target=_save_task, daemon=True).start()

                # Si alguna quincena ya existía, notificar advertencia al usuario
                if existing_quincenas and on_duplicate:
                    dup_summary = {
                        "nombre": ", ".join(existing_quincenas),
                        "quincenas": existing_quincenas
                    }
                    on_duplicate(dup_summary, lambda proceed: _execute_save(overwrite=proceed))
                else:
                    _execute_save(overwrite=False)

            except Exception as e:
                if on_error:
                    on_error(str(e))

        threading.Thread(target=_worker, daemon=True).start()
