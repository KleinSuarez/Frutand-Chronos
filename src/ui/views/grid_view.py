import customtkinter as ctk
from typing import List, Dict, Any, Callable, Optional
import math

class DataGridView(ctk.CTkFrame):
    """Componente de grilla interactiva para visualización, paginación y filtrado de marcaciones de asistencia."""

    PAGE_SIZE = 50  # 50 registros por página para renderizado ultrasrápido y estable

    def __init__(self, parent, on_filter_change: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_filter_change = on_filter_change
        
        self._marcaciones_data: List[Dict[str, Any]] = []
        self.current_page = 1
        self.total_pages = 1

        # Configurar Grid principal del DataGridView
        self.grid_rowconfigure(0, weight=0)  # Barra de Filtros (fija)
        self.grid_rowconfigure(1, weight=1)  # Tabla de Datos (expandible)
        self.grid_rowconfigure(2, weight=0)  # Barra de Paginación (fija)
        self.grid_columnconfigure(0, weight=1)

        # 1. Barra de Filtros Superior
        self.filter_frame = ctk.CTkFrame(self, corner_radius=8, fg_color=("gray85", "gray17"))
        self.filter_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

        # Buscador por texto
        self.lbl_search = ctk.CTkLabel(self.filter_frame, text="🔍 Buscar:", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_search.pack(side="left", padx=(15, 5), pady=10)

        self.txt_search = ctk.CTkEntry(self.filter_frame, placeholder_text="Nombre o ID...", width=200)
        self.txt_search.pack(side="left", padx=5, pady=10)
        self.txt_search.bind("<KeyRelease>", self._on_input_changed)

        # Filtro de Área
        self.lbl_area = ctk.CTkLabel(self.filter_frame, text="🏢 Área:", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_area.pack(side="left", padx=(15, 5), pady=10)

        self.cmb_area = ctk.CTkOptionMenu(
            self.filter_frame, 
            values=["Todas las áreas"], 
            command=self._on_combo_changed,
            width=160
        )
        self.cmb_area.pack(side="left", padx=5, pady=10)

        # Filtro de Periodo
        self.lbl_periodo = ctk.CTkLabel(self.filter_frame, text="📅 Periodo:", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_periodo.pack(side="left", padx=(15, 5), pady=10)

        self.cmb_periodo = ctk.CTkOptionMenu(
            self.filter_frame, 
            values=["Todos los periodos"], 
            command=self._on_combo_changed,
            width=220
        )
        self.cmb_periodo.pack(side="left", padx=5, pady=10)

        # Contador de registros
        self.lbl_counter = ctk.CTkLabel(
            self.filter_frame, 
            text="Total: 0 marcaciones", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray40", "gray70")
        )
        self.lbl_counter.pack(side="right", padx=15, pady=10)

        # 2. Contenedor de la Tabla con Scroll
        self.table_container = ctk.CTkFrame(self, corner_radius=8)
        self.table_container.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.table_container.grid_rowconfigure(0, weight=0)
        self.table_container.grid_rowconfigure(1, weight=1)
        self.table_container.grid_columnconfigure(0, weight=1)

        # Encabezados de la Tabla
        self.headers = ["ID Empleado", "Nombre Empleado", "Área", "Fecha", "Hora Entrada", "Hora Salida", "Periodo"]
        self.col_weights = [12, 22, 14, 12, 12, 12, 24]
        self.col_alignments = ["center", "center", "center", "center", "center", "center", "center"]

        # Compensación del ancho de la barra de desplazamiento (padx derecho 22px)
        self.header_frame = ctk.CTkFrame(self.table_container, fg_color=("gray75", "gray25"), height=38, corner_radius=4)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=(5, 22), pady=(5, 2))
        
        for col_idx, (header_text, weight, align) in enumerate(zip(self.headers, self.col_weights, self.col_alignments)):
            self.header_frame.grid_columnconfigure(col_idx, weight=weight)
            lbl = ctk.CTkLabel(
                self.header_frame, 
                text=header_text, 
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor=align
            )
            lbl.grid(row=0, column=col_idx, padx=4, pady=6, sticky="ew")

        # Scrollable Frame para las filas
        self.rows_frame = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.rows_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        for col_idx, weight in enumerate(self.col_weights):
            self.rows_frame.grid_columnconfigure(col_idx, weight=weight)

        # 3. Barra de Paginación Inferior
        self.pagination_frame = ctk.CTkFrame(self, corner_radius=6, fg_color=("gray85", "gray17"))
        self.pagination_frame.grid(row=2, column=0, padx=10, pady=(2, 10), sticky="ew")

        self.btn_prev = ctk.CTkButton(
            self.pagination_frame, 
            text="◀ Anterior", 
            width=90, 
            height=28,
            command=self._prev_page
        )
        self.btn_prev.pack(side="left", padx=15, pady=6)

        self.lbl_page_info = ctk.CTkLabel(
            self.pagination_frame, 
            text="Página 1 de 1", 
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.lbl_page_info.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(
            self.pagination_frame, 
            text="Siguiente ▶", 
            width=90, 
            height=28,
            command=self._next_page
        )
        self.btn_next.pack(side="right", padx=15, pady=6)

    def _on_input_changed(self, event=None):
        self.current_page = 1
        if self.on_filter_change:
            self.on_filter_change()

    def _on_combo_changed(self, choice=None):
        self.current_page = 1
        if self.on_filter_change:
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
        """Actualiza las opciones desplegables de áreas y periodos."""
        # Áreas
        area_options = ["Todas las áreas"] + sorted(areas)
        current_area = self.cmb_area.get()
        self.cmb_area.configure(values=area_options)
        if current_area in area_options:
            self.cmb_area.set(current_area)
        else:
            self.cmb_area.set("Todas las áreas")

        # Periodos
        self._periodo_map = {f"[{p['id']}] {p['nombre']}": p['id'] for p in periodos}
        periodo_options = ["Todos los periodos"] + list(self._periodo_map.keys())
        current_periodo = self.cmb_periodo.get()
        self.cmb_periodo.configure(values=periodo_options)
        if current_periodo in periodo_options:
            self.cmb_periodo.set(current_periodo)
        else:
            self.cmb_periodo.set("Todos los periodos")

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_current_page()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._render_current_page()

    def display_data(self, marcaciones: List[Dict[str, Any]]):
        """Almacena la lista de marcaciones filtradas y renderiza la primera página."""
        self._marcaciones_data = marcaciones
        num_records = len(marcaciones)
        self.total_pages = max(1, math.ceil(num_records / self.PAGE_SIZE))
        if self.current_page > self.total_pages:
            self.current_page = 1
        
        self.lbl_counter.configure(text=f"Total: {num_records:,} marcaciones")
        self._render_current_page()

    def _render_current_page(self):
        """Renderiza únicamente las filas de la página actual."""
        # Limpiar filas anteriores
        for widget in self.rows_frame.winfo_children():
            widget.destroy()

        num_records = len(self._marcaciones_data)
        if num_records == 0:
            self.lbl_page_info.configure(text="Página 0 de 0")
            self.btn_prev.configure(state="disabled")
            self.btn_next.configure(state="disabled")

            empty_label = ctk.CTkLabel(
                self.rows_frame, 
                text="No se encontraron marcaciones que coincidan con los filtros.",
                font=ctk.CTkFont(size=13),
                text_color="gray60"
            )
            empty_label.grid(row=0, column=0, columnspan=7, pady=50)
            return

        # Actualizar estado de botones de paginación
        self.lbl_page_info.configure(text=f"Página {self.current_page} de {self.total_pages}")
        self.btn_prev.configure(state="normal" if self.current_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.current_page < self.total_pages else "disabled")

        start_idx = (self.current_page - 1) * self.PAGE_SIZE
        end_idx = min(start_idx + self.PAGE_SIZE, num_records)
        page_records = self._marcaciones_data[start_idx:end_idx]

        # Renderizar filas de la página activa
        for row_idx, record in enumerate(page_records):
            bg_color = ("gray90", "gray20") if row_idx % 2 == 0 else ("gray95", "gray23")
            
            row_frame = ctk.CTkFrame(self.rows_frame, fg_color=bg_color, corner_radius=2, height=32)
            row_frame.grid(row=row_idx, column=0, columnspan=7, sticky="ew", pady=1)
            for col_idx, weight in enumerate(self.col_weights):
                row_frame.grid_columnconfigure(col_idx, weight=weight)

            values = [
                str(record.get("empleado_id", "")),
                str(record.get("empleado_nombre", "")),
                str(record.get("empleado_area", "")),
                str(record.get("fecha", "")),
                str(record.get("hora_entrada", "--:--")),
                str(record.get("hora_salida", "--:--")),
                str(record.get("periodo_nombre", ""))
            ]

            for col_idx, (val, align) in enumerate(zip(values, self.col_alignments)):
                lbl = ctk.CTkLabel(
                    row_frame, 
                    text=val, 
                    font=ctk.CTkFont(size=11),
                    anchor=align
                )
                lbl.grid(row=0, column=col_idx, padx=4, pady=4, sticky="ew")
