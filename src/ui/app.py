import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from typing import Dict, Any

from database.repository import DatabaseRepository
from ui.controllers.ingestion_controller import IngestionController
from ui.views.grid_view import DataGridView

class FrutandChronosApp(ctk.CTk):
    """Ventana Principal de Frutand Chronos — Release 1."""

    def __init__(self, db_path: str = "frutand_chronos.db"):
        super().__init__()

        self.title("Frutand Chronos — Sistema de Asistencia y Liquidación")
        self.geometry("1240x740")
        self.minsize(1024, 640)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Repositorio y Controlador
        self.repo = DatabaseRepository(db_path)
        self.ingestion_controller = IngestionController(self.repo)

        # Configurar Grid principal con anchos mínimos garantizados
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=1)

        # 1. Sidebar Panel Izquierdo
        self._build_sidebar()

        # 2. Main Panel Derecho (Grilla de Datos)
        self.grid_view = DataGridView(self, on_filter_change=self.on_filter_changed)
        self.grid_view.grid(row=0, column=1, padx=(10, 15), pady=15, sticky="nsew")

        # Cargar datos iniciales
        self.refresh_data()

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        # Logo y Título
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="🌱 FRUTAND\nCHRONOS", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("green", "#2ECC71")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(25, 20))

        # Botón Cargar Excel / Hoja de Cálculo
        self.btn_cargar = ctk.CTkButton(
            self.sidebar_frame, 
            text="📂 Cargar Hoja de Cálculo", 
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#27AE60",
            hover_color="#1E8449",
            height=40,
            command=self.on_click_cargar_excel
        )
        self.btn_cargar.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Botón Refrescar
        self.btn_refrescar = ctk.CTkButton(
            self.sidebar_frame,
            text="🔄 Refrescar Tabla",
            command=self.refresh_data
        )
        self.btn_refrescar.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        # Card de Estadísticas Rápidas
        self.stats_card = ctk.CTkFrame(self.sidebar_frame, corner_radius=8, fg_color=("gray85", "gray18"))
        self.stats_card.grid(row=3, column=0, padx=20, pady=20, sticky="ew")

        self.lbl_stats_title = ctk.CTkLabel(
            self.stats_card, text="📊 Resumen General", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_stats_title.pack(padx=10, pady=(10, 5))

        self.lbl_stat_emp = ctk.CTkLabel(self.stats_card, text="Empleados: 0", font=ctk.CTkFont(size=11))
        self.lbl_stat_emp.pack(padx=10, pady=2)

        self.lbl_stat_per = ctk.CTkLabel(self.stats_card, text="Periodos: 0", font=ctk.CTkFont(size=11))
        self.lbl_stat_per.pack(padx=10, pady=(2, 10))

        # Footer
        self.lbl_footer = ctk.CTkLabel(
            self.sidebar_frame, text="Release 1 — MVP Base", font=ctk.CTkFont(size=10), text_color="gray50"
        )
        self.lbl_footer.grid(row=6, column=0, padx=20, pady=15)

    def refresh_data(self):
        """Actualiza las opciones de filtros, estadísticas y el contenido de la grilla."""
        areas = self.repo.get_areas()
        periodos = self.repo.get_periodos()
        self.grid_view.update_filters_options(areas, periodos)

        # Actualizar Stats
        with self.repo._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM empleados")
            total_emp = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM periodos")
            total_per = cursor.fetchone()[0]

        self.lbl_stat_emp.configure(text=f"Empleados: {total_emp:,}")
        self.lbl_stat_per.configure(text=f"Periodos: {total_per:,}")

        # Recargar Marcaciones
        self.on_filter_changed()

    def on_filter_changed(self):
        """Callback invocado al escribir en el buscador o cambiar filtros desplegables."""
        search_text = self.grid_view.get_search_text()
        selected_area = self.grid_view.get_selected_area()
        selected_periodo_id = self.grid_view.get_selected_periodo_id()

        marcaciones = self.repo.get_marcaciones(
            periodo_id=selected_periodo_id,
            busqueda=search_text,
            area=selected_area
        )
        self.grid_view.display_data(marcaciones)

    def on_click_cargar_excel(self):
        """Abre el diálogo de selección de archivo e inicia la ingesta asíncrona."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar Reporte Biométrico (Excel, CSV, ODS)",
            filetypes=[
                ("Todos los formatos de Hoja de Cálculo", "*.xlsx *.xls *.csv *.ods *.tsv *.txt"),
                ("Archivos Excel (.xlsx, .xls)", "*.xlsx *.xls"),
                ("Excel antiguo (.xls)", "*.xls"),
                ("Excel moderno (.xlsx)", "*.xlsx"),
                ("Archivos CSV / TSV (.csv, .tsv)", "*.csv *.tsv *.txt"),
                ("OpenDocument (.ods)", "*.ods"),
                ("Todos los archivos", "*.*")
            ]
        )
        if not file_path:
            return

        # Modal / Overlay de Carga Asíncrona (Spinner)
        overlay = ctk.CTkToplevel(self)
        overlay.title("Procesando...")
        overlay.geometry("400x160")
        overlay.resizable(False, False)
        overlay.transient(self)
        overlay.grab_set()

        lbl_loading = ctk.CTkLabel(
            overlay, 
            text="⚙️ Procesando reporte biométrico...\nPor favor espere un momento.",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        lbl_loading.pack(pady=(30, 15))

        progressbar = ctk.CTkProgressBar(overlay, mode="indeterminate", width=300)
        progressbar.pack(pady=10)
        progressbar.start()

        def close_overlay():
            try:
                progressbar.stop()
                overlay.destroy()
            except Exception:
                pass

        def on_start():
            pass

        def on_success(summary: Dict[str, Any]):
            self.after(0, close_overlay)
            self.after(100, lambda: self._show_success(summary))

        def on_duplicate(dup_summary: Dict[str, Any], proceed_cb):
            def _handle_duplicate():
                close_overlay()
                ans = messagebox.askyesno(
                    "Periodo Quincenal Existente",
                    f"Las siguientes quincenas de este archivo ya existen en la base de datos:\n\n"
                    f"• {dup_summary['nombre']}\n\n"
                    f"¿Desea sobrescribir o actualizar las marcaciones anteriores con los datos del nuevo archivo?"
                )
                if ans:
                    # Reabrir el spinner overlay para indicar la actualización
                    new_overlay = ctk.CTkToplevel(self)
                    new_overlay.title("Actualizando...")
                    new_overlay.geometry("400x160")
                    new_overlay.resizable(False, False)
                    new_overlay.transient(self)
                    new_overlay.grab_set()

                    lbl_upd = ctk.CTkLabel(
                        new_overlay, 
                        text="🔄 Actualizando quincenas biométricas...",
                        font=ctk.CTkFont(size=14, weight="bold")
                    )
                    lbl_upd.pack(pady=(30, 15))

                    p_bar = ctk.CTkProgressBar(new_overlay, mode="indeterminate", width=300)
                    p_bar.pack(pady=10)
                    p_bar.start()

                    def _close_new():
                        try:
                            p_bar.stop()
                            new_overlay.destroy()
                        except Exception:
                            pass

                    def _override_success(summary):
                        self.after(0, _close_new)
                        self.after(100, lambda: self._show_success(summary))

                    # Sustituir callback
                    proceed_cb(True)
                else:
                    proceed_cb(False)

            self.after(0, _handle_duplicate)

        def on_error(err_msg: str):
            self.after(0, close_overlay)
            self.after(100, lambda: messagebox.showerror("Error de Ingesta", f"No se pudo procesar el archivo Excel:\n\n{err_msg}"))

        self.ingestion_controller.process_excel_async(
            file_path=file_path,
            on_start=on_start,
            on_success=on_success,
            on_duplicate=on_duplicate,
            on_error=on_error
        )

    def _show_success(self, summary: Dict[str, Any]):
        self.refresh_data()
        
        # Seleccionar automáticamente el último periodo recién cargado en la grilla
        periodo_key = f"[{summary['periodo_id']}] {summary['periodo_nombre'].split(', ')[-1]}"
        if hasattr(self.grid_view, "_periodo_map"):
            for key in self.grid_view._periodo_map.keys():
                if str(summary['periodo_id']) in key or summary['periodo_nombre'].split(', ')[-1] in key:
                    self.grid_view.cmb_periodo.set(key)
                    self.on_filter_changed()
                    break

        action_text = "sobrescrito / actualizado" if summary.get("overwritten") else "registrado"
        msg = (
            f"✅ Archivo procesado exitosamente ({action_text}).\n\n"
            f"• Periodo(s): {summary['periodo_nombre']}\n"
            f"• Empleados registrados/actualizados: {summary['num_empleados']}\n"
            f"• Marcaciones procesadas: {summary['num_marcaciones']:,}"
        )
        messagebox.showinfo("Ingesta Exitosa", msg)
