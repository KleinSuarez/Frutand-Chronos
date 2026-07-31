import customtkinter as ctk
import threading
import calendar
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from tkinter import messagebox

from core.holidays import ColombiaHolidays
from database.repository import DatabaseRepository

class CalendarView(ctk.CTkFrame):
    """Vista de Calendario Visual con sincronización web y gestión manual de festivos."""

    DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    MESES_ES = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    def __init__(self, parent, repo: DatabaseRepository, **kwargs):
        super().__init__(parent, **kwargs)
        self.repo = repo

        today = date.today()
        self.current_year = today.year
        self.current_month = today.month

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # 1. Barra de Navegación de Mes
        self._build_nav_bar()

        # 2. Calendario Visual
        self.cal_frame = ctk.CTkFrame(self, corner_radius=8)
        self.cal_frame.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")

        # 3. Panel Inferior (Acciones + Lista de Festivos)
        self._build_actions_panel()

        # Renderizar el mes actual
        self._render_calendar()

    def _build_nav_bar(self):
        nav = ctk.CTkFrame(self, fg_color=("gray85", "gray17"), corner_radius=8, height=50)
        nav.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")

        self.btn_prev_month = ctk.CTkButton(
            nav, text="◀", width=40, height=32, command=self._prev_month
        )
        self.btn_prev_month.pack(side="left", padx=15, pady=8)

        self.lbl_month_year = ctk.CTkLabel(
            nav, text="", font=ctk.CTkFont(size=18, weight="bold")
        )
        self.lbl_month_year.pack(side="left", expand=True)

        self.btn_next_month = ctk.CTkButton(
            nav, text="▶", width=40, height=32, command=self._next_month
        )
        self.btn_next_month.pack(side="right", padx=15, pady=8)

    def _build_actions_panel(self):
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, padx=15, pady=(5, 15), sticky="ew")

        self.btn_sync = ctk.CTkButton(
            actions, text="🌐 Sincronizar Festivos desde Web",
            fg_color="#3498DB", hover_color="#2980B9", height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_sync_click
        )
        self.btn_sync.pack(side="left", padx=(0, 10))

        self.btn_add_manual = ctk.CTkButton(
            actions, text="📅 Agregar Festivo Institucional",
            fg_color="#8E44AD", hover_color="#6C3483", height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_add_manual_click
        )
        self.btn_add_manual.pack(side="left", padx=(0, 10))

        self.lbl_festivos_count = ctk.CTkLabel(
            actions, text="", font=ctk.CTkFont(size=12), text_color=("gray40", "gray70")
        )
        self.lbl_festivos_count.pack(side="right", padx=10)

    # --- Navegación ---

    def _prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._render_calendar()

    def _next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._render_calendar()

    # --- Renderización del Calendario ---

    def _render_calendar(self):
        self.lbl_month_year.configure(
            text=f"{self.MESES_ES[self.current_month - 1]} {self.current_year}"
        )

        # Limpiar calendario previo
        for w in self.cal_frame.winfo_children():
            w.destroy()

        # Encabezados de días de la semana
        for col, dia in enumerate(self.DIAS_SEMANA):
            fg = "#EF4444" if dia == "Dom" else ("gray70", "gray50")
            lbl = ctk.CTkLabel(
                self.cal_frame, text=dia,
                font=ctk.CTkFont(size=12, weight="bold"), text_color=fg
            )
            lbl.grid(row=0, column=col, padx=2, pady=(10, 5), sticky="ew")
            self.cal_frame.grid_columnconfigure(col, weight=1)

        # Obtener festivos del mes
        db_festivos = {f["fecha"]: f for f in self.repo.get_festivos()}
        calc_holidays = ColombiaHolidays.get_calculated_holidays(self.current_year)

        month_cal = calendar.monthcalendar(self.current_year, self.current_month)
        today = date.today()

        for row_idx, week in enumerate(month_cal, start=1):
            for col_idx, day_num in enumerate(week):
                if day_num == 0:
                    ctk.CTkLabel(self.cal_frame, text="").grid(row=row_idx, column=col_idx, padx=2, pady=2)
                    continue

                d = date(self.current_year, self.current_month, day_num)
                fecha_str = d.strftime("%Y-%m-%d")

                # Determinar tipo de día
                is_sunday = d.weekday() == 6
                is_db_festivo = fecha_str in db_festivos
                is_calc_festivo = d in calc_holidays
                is_today = d == today

                # Colores
                if is_db_festivo or is_calc_festivo:
                    bg = ("#E8DAEF", "#5B2C6F")
                    fg_text = ("#6C3483", "#D7BDE2")
                elif is_sunday:
                    bg = ("#FADBD8", "#641E16")
                    fg_text = ("#C0392B", "#E74C3C")
                elif is_today:
                    bg = ("#D5F5E3", "#1E8449")
                    fg_text = ("#27AE60", "#2ECC71")
                else:
                    bg = ("gray92", "gray22")
                    fg_text = ("gray30", "gray80")

                cell = ctk.CTkFrame(self.cal_frame, fg_color=bg, corner_radius=6, height=55, width=55)
                cell.grid(row=row_idx, column=col_idx, padx=3, pady=3, sticky="nsew")
                self.cal_frame.grid_rowconfigure(row_idx, weight=1)

                day_lbl = ctk.CTkLabel(
                    cell, text=str(day_num),
                    font=ctk.CTkFont(size=14, weight="bold" if is_today else "normal"),
                    text_color=fg_text
                )
                day_lbl.pack(expand=True, pady=(5, 0))

                # Tooltip: descripción del festivo
                if is_db_festivo:
                    desc = db_festivos[fecha_str].get("descripcion", "Festivo")
                    tag = "📌" if db_festivos[fecha_str].get("es_manual") else "🏛️"
                    sub_lbl = ctk.CTkLabel(
                        cell, text=f"{tag}", font=ctk.CTkFont(size=10),
                        text_color=fg_text
                    )
                    sub_lbl.pack(pady=(0, 3))
                elif is_calc_festivo:
                    sub_lbl = ctk.CTkLabel(
                        cell, text="🏛️", font=ctk.CTkFont(size=10),
                        text_color=fg_text
                    )
                    sub_lbl.pack(pady=(0, 3))

        # Actualizar contador
        total_db = len([f for f in db_festivos.values()])
        total_calc = len(calc_holidays)
        self.lbl_festivos_count.configure(text=f"🏛️ {total_calc} Ley Emiliani  |  📌 {total_db} en BD")

    # --- Acciones ---

    def _on_sync_click(self):
        self.btn_sync.configure(state="disabled", text="⏳ Sincronizando...")

        def _sync():
            try:
                fetched = ColombiaHolidays.sync_online_holidays(self.current_year, repo=self.repo)
                next_year = ColombiaHolidays.sync_online_holidays(self.current_year + 1, repo=self.repo)
                total = len(fetched) + len(next_year)
                self.after(0, lambda: self._sync_done(total))
            except Exception as e:
                self.after(0, lambda: self._sync_error(str(e)))

        threading.Thread(target=_sync, daemon=True).start()

    def _sync_done(self, total: int):
        self.btn_sync.configure(state="normal", text="🌐 Sincronizar Festivos desde Web")
        self._render_calendar()
        messagebox.showinfo("Festivos Sincronizados", f"Se sincronizaron {total} festivos colombianos.")

    def _sync_error(self, err: str):
        self.btn_sync.configure(state="normal", text="🌐 Sincronizar Festivos desde Web")
        messagebox.showerror("Error", f"No se pudo sincronizar:\n{err}")

    def _on_add_manual_click(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Agregar Festivo Institucional")
        dialog.geometry("400x240")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="📅 Nuevo Festivo Institucional",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 10))

        ctk.CTkLabel(dialog, text="Fecha (YYYY-MM-DD):", font=ctk.CTkFont(size=12)).pack(padx=25, anchor="w")
        entry_fecha = ctk.CTkEntry(dialog, placeholder_text="Ej: 2026-08-15", width=320)
        entry_fecha.pack(padx=25, pady=(2, 8))

        ctk.CTkLabel(dialog, text="Descripción:", font=ctk.CTkFont(size=12)).pack(padx=25, anchor="w")
        entry_desc = ctk.CTkEntry(dialog, placeholder_text="Ej: Día Cívico Frutand", width=320)
        entry_desc.pack(padx=25, pady=(2, 12))

        def _save():
            fecha = entry_fecha.get().strip()
            desc = entry_desc.get().strip()
            if not fecha or not desc:
                messagebox.showwarning("Campos Vacíos", "Ingrese fecha y descripción.")
                return
            try:
                datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Formato Inválido", "Use el formato YYYY-MM-DD.")
                return
            self.repo.add_festivo(fecha, desc, es_manual=1)
            messagebox.showinfo("Festivo Agregado", f"'{desc}' registrado el {fecha}.")
            dialog.destroy()
            self._render_calendar()

        ctk.CTkButton(
            dialog, text="💾 Guardar Festivo",
            fg_color="#27AE60", hover_color="#1E8449", command=_save
        ).pack(pady=8)
