import customtkinter as ctk
from typing import List, Dict, Any, Callable, Optional
import math
from datetime import datetime
from core.calculator import LaborCalculator
from core.holidays import ColombiaHolidays

class DataGridView(ctk.CTkFrame):
    """Grilla con Vista Resumen por Empleado (con totales) y Vista Detalle Semanal."""

    PAGE_SIZE = 50

    def __init__(self, parent, on_filter_change: Optional[Callable[[], None]] = None,
                 on_employee_click: Optional[Callable[[str, Optional[int]], None]] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_filter_change = on_filter_change
        self.on_employee_click = on_employee_click

        self._data: List[Dict[str, Any]] = []
        self.current_page = 1
        self.total_pages = 1
        self._showing_detail = False

        self.grid_rowconfigure(0, weight=0)  # Filtros
        self.grid_rowconfigure(1, weight=0)  # Breadcrumb
        self.grid_rowconfigure(2, weight=0)  # Header
        self.grid_rowconfigure(3, weight=1)  # Rows
        self.grid_rowconfigure(4, weight=0)  # Paginación
        self.grid_columnconfigure(0, weight=1)

        # 1. Filtros
        self._build_filter_bar()

        # 2. Breadcrumb
        self.context_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
        self.context_frame.grid(row=1, column=0, padx=10, pady=(2, 0), sticky="ew")

        self.btn_back = ctk.CTkButton(
            self.context_frame, text="◀ Volver al Resumen", width=150, height=28,
            fg_color="#6C3483", hover_color="#5B2C6F", command=self._back_to_summary
        )
        # Oculto inicialmente
        self.lbl_context = ctk.CTkLabel(
            self.context_frame, text="📊 Resumen de Empleados por Periodo",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=("gray40", "gray70")
        )
        self.lbl_context.pack(side="left")

        # 3. Header fijo
        self.header_frame = ctk.CTkFrame(self, fg_color=("gray75", "gray25"), height=38, corner_radius=4)
        self.header_frame.grid(row=2, column=0, sticky="ew", padx=(15, 30), pady=(5, 0))

        # 4. Rows con scroll
        self.rows_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.rows_frame.grid(row=3, column=0, padx=10, pady=(2, 5), sticky="nsew")

        # 5. Paginación
        self._build_pagination()

        # Definir columnas por defecto
        self._set_summary_headers()

    def _build_filter_bar(self):
        self.filter_frame = ctk.CTkFrame(self, corner_radius=8, fg_color=("gray85", "gray17"))
        self.filter_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

        self.lbl_search = ctk.CTkLabel(self.filter_frame, text="🔍 Buscar:", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_search.pack(side="left", padx=(15, 5), pady=10)

        self.txt_search = ctk.CTkEntry(self.filter_frame, placeholder_text="Nombre o ID...", width=200)
        self.txt_search.pack(side="left", padx=5, pady=10)
        self.txt_search.bind("<KeyRelease>", self._on_input_changed)

        self.lbl_area = ctk.CTkLabel(self.filter_frame, text="🏢 Área:", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_area.pack(side="left", padx=(15, 5), pady=10)

        self.cmb_area = ctk.CTkOptionMenu(self.filter_frame, values=["Todas las áreas"], command=self._on_combo_changed, width=160)
        self.cmb_area.pack(side="left", padx=5, pady=10)

        self.lbl_periodo = ctk.CTkLabel(self.filter_frame, text="📅 Periodo:", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_periodo.pack(side="left", padx=(15, 5), pady=10)

        self.cmb_periodo = ctk.CTkOptionMenu(self.filter_frame, values=["Todos los periodos"], command=self._on_combo_changed, width=220)
        self.cmb_periodo.pack(side="left", padx=5, pady=10)

        self.lbl_counter = ctk.CTkLabel(
            self.filter_frame, text="Total 0 empleados",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=("gray40", "gray70")
        )
        self.lbl_counter.pack(side="right", padx=15, pady=10)

    def _build_pagination(self):
        self.pagination_frame = ctk.CTkFrame(self, corner_radius=6, fg_color=("gray85", "gray17"))
        self.pagination_frame.grid(row=4, column=0, padx=10, pady=(2, 10), sticky="ew")

        self.btn_prev = ctk.CTkButton(self.pagination_frame, text="◀ Anterior", width=90, height=28, command=self._prev_page)
        self.btn_prev.pack(side="left", padx=15, pady=6)

        self.lbl_page_info = ctk.CTkLabel(self.pagination_frame, text="Página 1 de 1", font=ctk.CTkFont(size=11, weight="bold"))
        self.lbl_page_info.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(self.pagination_frame, text="Siguiente ▶", width=90, height=28, command=self._next_page)
        self.btn_next.pack(side="right", padx=15, pady=6)

    # --- Filter Accessors ---

    def _on_input_changed(self, event=None):
        self.current_page = 1
        if not self._showing_detail and self.on_filter_change:
            self.on_filter_change()

    def _on_combo_changed(self, choice=None):
        self.current_page = 1
        if self._showing_detail:
            self._back_to_summary()
        elif self.on_filter_change:
            self.on_filter_change()

    def get_search_text(self) -> str:
        return self.txt_search.get()

    def get_selected_area(self) -> Optional[str]:
        val = self.cmb_area.get()
        return None if val == "Todas las áreas" else val

    def get_selected_periodo_id(self) -> Optional[int]:
        val = self.cmb_periodo.get()
        if val == "Todos los periodos" or not hasattr(self, "_periodo_map"):
            return None
        return self._periodo_map.get(val)

    def update_filters_options(self, areas: List[str], periodos: List[Dict[str, Any]]):
        area_options = ["Todas las áreas"] + sorted(areas)
        current_area = self.cmb_area.get()
        self.cmb_area.configure(values=area_options)
        self.cmb_area.set(current_area if current_area in area_options else "Todas las áreas")

        self._periodo_map = {f"[{p['id']}] {p['nombre']}": p['id'] for p in periodos}
        periodo_options = ["Todos los periodos"] + list(self._periodo_map.keys())
        current_periodo = self.cmb_periodo.get()
        self.cmb_periodo.configure(values=periodo_options)
        self.cmb_periodo.set(current_periodo if current_periodo in periodo_options else "Todos los periodos")

    # --- Paginación ---

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_current_page()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._render_current_page()

    # --- Headers ---

    def _set_summary_headers(self):
        """Configura encabezados de la vista resumen."""
        self._current_headers = ["Nombre Empleado", "Área", "Periodo", "Días", "H.Ord", "Ext.D", "R.Noc", "Deuda", ""]
        self._current_weights = [20, 12, 18, 6, 8, 8, 8, 8, 4]
        self._rebuild_header()

    def _set_detail_headers(self):
        """Configura encabezados de la vista detalle."""
        self._current_headers = ["Sem", "Fecha", "Día", "Entrada", "Salida", "H.Ord", "Ext.D", "R.Noc", "R.Dom", "Deuda", "Estado"]
        self._current_weights = [6, 10, 6, 8, 8, 8, 8, 8, 8, 8, 10]
        self._rebuild_header()

    def _rebuild_header(self):
        for w in self.header_frame.winfo_children():
            w.destroy()

        for col_idx, (text, weight) in enumerate(zip(self._current_headers, self._current_weights)):
            self.header_frame.grid_columnconfigure(col_idx, weight=weight)
            lbl = ctk.CTkLabel(
                self.header_frame, text=text,
                font=ctk.CTkFont(size=12, weight="bold"), anchor="center"
            )
            lbl.grid(row=0, column=col_idx, padx=4, pady=6, sticky="ew")

        # Sincronizar pesos en rows_frame
        for col_idx, weight in enumerate(self._current_weights):
            self.rows_frame.grid_columnconfigure(col_idx, weight=weight)

    # === VISTA RESUMEN ===

    def display_summary(self, resumen: List[Dict[str, Any]]):
        self._showing_detail = False
        self._data = resumen
        self.current_page = 1
        self.total_pages = max(1, math.ceil(len(resumen) / self.PAGE_SIZE))

        self.btn_back.pack_forget()
        self.lbl_context.configure(text="📊 Resumen de Empleados por Periodo")
        self.lbl_counter.configure(text=f"Total {len(resumen)} empleados")

        self._set_summary_headers()
        self._render_current_page()

    def _render_current_page(self):
        for w in self.rows_frame.winfo_children():
            w.destroy()

        num = len(self._data)
        if num == 0:
            self.lbl_page_info.configure(text="Página 0 de 0")
            self.btn_prev.configure(state="disabled")
            self.btn_next.configure(state="disabled")
            ctk.CTkLabel(
                self.rows_frame, text="No se encontraron registros.",
                font=ctk.CTkFont(size=13), text_color="gray60"
            ).grid(row=0, column=0, columnspan=len(self._current_headers), pady=50)
            return

        self.lbl_page_info.configure(text=f"Página {self.current_page} de {self.total_pages}")
        self.btn_prev.configure(state="normal" if self.current_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.current_page < self.total_pages else "disabled")

        start = (self.current_page - 1) * self.PAGE_SIZE
        end = min(start + self.PAGE_SIZE, num)
        page = self._data[start:end]

        num_cols = len(self._current_headers)

        for row_idx, record in enumerate(page):
            bg = ("gray90", "gray20") if row_idx % 2 == 0 else ("gray95", "gray23")
            emp_id = record.get("empleado_id", "")
            pid = record.get("periodo_id")

            values = [
                str(record.get("empleado_nombre", "")),
                str(record.get("empleado_area", "")),
                str(record.get("periodo_nombre", "")),
                str(record.get("total_dias", 0)),
                f"{record.get('horas_ordinarias', 0):.1f}",
                f"{record.get('extras_diurnas', 0):.1f}",
                f"{record.get('recargo_nocturno', 0):.1f}",
                f"{record.get('horas_deuda', 0):.1f}",
                "👁"  # Icono de ver detalle
            ]

            row_frame = ctk.CTkFrame(self.rows_frame, fg_color=bg, corner_radius=2, height=36, cursor="hand2")
            row_frame.grid(row=row_idx, column=0, columnspan=num_cols, sticky="ew", pady=1)

            for c, w in enumerate(self._current_weights):
                row_frame.grid_columnconfigure(c, weight=w)

            for col_idx, val in enumerate(values):
                is_eye = col_idx == num_cols - 1
                lbl = ctk.CTkLabel(
                    row_frame, text=val,
                    font=ctk.CTkFont(size=14 if is_eye else 11, weight="bold" if is_eye else "normal"),
                    anchor="center",
                    text_color=("#3498DB", "#5DADE2") if is_eye else None
                )
                lbl.grid(row=0, column=col_idx, padx=4, pady=5, sticky="ew")
                lbl.bind("<Button-1>", lambda e, eid=emp_id, p=pid: self._on_row_click(eid, p))

            row_frame.bind("<Button-1>", lambda e, eid=emp_id, p=pid: self._on_row_click(eid, p))

    def _on_row_click(self, empleado_id: str, periodo_id):
        if self.on_employee_click:
            self.on_employee_click(empleado_id, periodo_id)

    # === VISTA DETALLE SEMANAL ===

    def display_detail(self, empleado_nombre: str, marcaciones: List[Dict[str, Any]]):
        self._showing_detail = True
        self._data = marcaciones
        self.current_page = 1
        self.total_pages = 1

        self.btn_back.pack(side="left", padx=(0, 10), before=self.lbl_context)
        self.lbl_context.configure(text=f"📋 Detalle Semanal — {empleado_nombre}")
        self.lbl_counter.configure(text=f"Total {len(marcaciones)} días")

        self._set_detail_headers()
        self._render_detail()

    def _back_to_summary(self):
        self._showing_detail = False
        self.btn_back.pack_forget()
        if self.on_filter_change:
            self.on_filter_change()

    def _render_detail(self):
        for w in self.rows_frame.winfo_children():
            w.destroy()

        if not self._data:
            self.lbl_page_info.configure(text="Sin datos")
            self.btn_prev.configure(state="disabled")
            self.btn_next.configure(state="disabled")
            ctk.CTkLabel(
                self.rows_frame, text="No hay marcaciones para este empleado.",
                font=ctk.CTkFont(size=13), text_color="gray60"
            ).grid(row=0, column=0, columnspan=len(self._current_headers), pady=50)
            return

        self.lbl_page_info.configure(text="Vista completa")
        self.btn_prev.configure(state="disabled")
        self.btn_next.configure(state="disabled")

        DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        num_cols = len(self._current_headers)
        row_idx = 0
        current_week = None

        # Pre-cargar festivos del año
        try:
            first_date = datetime.strptime(self._data[0].get("fecha", "2026-01-01"), "%Y-%m-%d").date()
            calc_holidays = ColombiaHolidays.get_calculated_holidays(first_date.year)
        except Exception:
            calc_holidays = set()

        for record in self._data:
            calc = LaborCalculator.calculate_daily_record(record)
            fecha_str = record.get("fecha", "")

            try:
                dt = datetime.strptime(fecha_str, "%Y-%m-%d")
                iso_week = dt.isocalendar()[1]
                dia_nombre = DIAS_ES[dt.weekday()]
                dt_date = dt.date()
                is_festivo = dt_date in calc_holidays or dt_date.weekday() == 6
            except Exception:
                iso_week = 0
                dia_nombre = "?"
                is_festivo = False

            # Separador visual de semana con fondo de color y label
            if current_week is not None and iso_week != current_week:
                sep_frame = ctk.CTkFrame(self.rows_frame, fg_color=("#D6EAF8", "#1B4F72"), corner_radius=4, height=24)
                sep_frame.grid(row=row_idx, column=0, columnspan=num_cols, sticky="ew", pady=(6, 4))
                ctk.CTkLabel(
                    sep_frame, text=f"━━━  Semana {iso_week}  ━━━",
                    font=ctk.CTkFont(size=10, weight="bold"), text_color=("#2471A3", "#AED6F1")
                ).pack(expand=True, pady=2)
                row_idx += 1

            current_week = iso_week

            alerta_color = calc.get("alerta_color", "#10B981")
            alerta_estado = calc.get("alerta_estado", "🟢 Ok")

            # Colores de fondo: festivo resaltado vs normal zebra
            if is_festivo:
                bg = ("#FADBD8", "#641E16")
            else:
                bg = ("gray90", "gray20") if row_idx % 2 == 0 else ("gray95", "gray23")

            row_frame = ctk.CTkFrame(self.rows_frame, fg_color=bg, corner_radius=2, height=32)
            row_frame.grid(row=row_idx, column=0, columnspan=num_cols, sticky="ew", pady=1)
            for c, w in enumerate(self._current_weights):
                row_frame.grid_columnconfigure(c, weight=w)

            # Prefijo festivo en el día
            dia_display = f"🏛️ {dia_nombre}" if is_festivo else dia_nombre

            values = [
                f"S{iso_week}",
                fecha_str,
                dia_display,
                str(record.get("hora_entrada", "--:--")),
                str(record.get("hora_salida", "--:--")),
                f"{calc.get('horas_ordinarias', 0):.1f}",
                f"{calc.get('extras_diurnas', 0):.1f}",
                f"{calc.get('recargo_nocturno', 0):.1f}",
                f"{calc.get('recargo_dominical_festivo', 0):.1f}",
                f"{calc.get('horas_deuda', 0):.1f}",
                alerta_estado
            ]

            for col_idx, val in enumerate(values):
                txt_color = alerta_color if col_idx == 10 else (("#C0392B", "#E74C3C") if is_festivo else None)
                lbl = ctk.CTkLabel(
                    row_frame, text=val,
                    font=ctk.CTkFont(size=11, weight="bold" if (col_idx == 10 or is_festivo) else "normal"),
                    anchor="center", text_color=txt_color
                )
                lbl.grid(row=0, column=col_idx, padx=3, pady=4, sticky="ew")

            row_idx += 1

    # --- Retrocompatibilidad ---

    def display_data(self, marcaciones: List[Dict[str, Any]]):
        self.display_summary(marcaciones)
