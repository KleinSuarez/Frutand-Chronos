import customtkinter as ctk

class FrutandChronosApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Frutand Chronos — Sistema de Asistencia y Liquidación")
        self.geometry("1100 x 680")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Configurar Grid principal
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, text="FRUTAND CHRONOS", font=ctk.CTkFont(size=18, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_cargar = ctk.CTkButton(
            self.sidebar_frame, text="📂 Cargar Excel", command=self.on_cargar_excel
        )
        self.btn_cargar.grid(row=1, column=0, padx=20, pady=10)

        # Panel Principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.label_bienvenida = ctk.CTkLabel(
            self.main_frame,
            text="Bienvenido a Frutand Chronos\nSeleccione 'Cargar Excel' para iniciar el procesamiento biométrico.",
            font=ctk.CTkFont(size=15)
        )
        self.label_bienvenida.pack(expand=True, padx=20, pady=20)

    def on_cargar_excel(self):
        file_path = ctk.filedialog.askopenfilename(
            title="Seleccionar Reporte Biométrico Excel",
            filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.label_bienvenida.configure(
                text=f"Archivo seleccionado:\n{file_path}\n(Procesando en Release 1...)"
            )
