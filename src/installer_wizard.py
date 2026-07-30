import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
import shutil
import subprocess

class InstallerWizard(ctk.CTk):
    """Asistente GUI de Instalación para Frutand Chronos con selección de ruta y configuración de accesos directos."""

    def __init__(self):
        super().__init__()

        self.title("Instalador de Frutand Chronos")
        self.geometry("620x420")
        self.resizable(False, False)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        # Ruta de instalación predeterminada
        default_dir = os.path.join(os.environ.get("LOCALAPPDATA", "C:\\"), "Programs", "Frutand Chronos")
        self.install_path_var = ctk.StringVar(value=default_dir)
        self.desktop_shortcut_var = ctk.BooleanVar(value=True)
        self.start_menu_shortcut_var = ctk.BooleanVar(value=True)
        self.auto_trust_cert_var = ctk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, height=75, corner_radius=0, fg_color=("gray85", "gray17"))
        self.header_frame.pack(fill="x", side="top")

        self.lbl_title = ctk.CTkLabel(
            self.header_frame, 
            text="🌱 FRUTAND CHRONOS", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#2ECC71"
        )
        self.lbl_title.pack(anchor="w", padx=25, pady=(15, 2))

        self.lbl_subtitle = ctk.CTkLabel(
            self.header_frame, 
            text="Asistente de Instalación del Sistema de Asistencia y Liquidación",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        self.lbl_subtitle.pack(anchor="w", padx=25, pady=(0, 15))

        # Body Frame
        self.body_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.body_frame.pack(fill="both", expand=True, padx=25, pady=20)

        # Selección de Carpeta de Destino
        self.lbl_path_title = ctk.CTkLabel(
            self.body_frame, 
            text="📁 Seleccione la ubicación de instalación:", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lbl_path_title.pack(anchor="w", pady=(5, 5))

        self.path_picker_frame = ctk.CTkFrame(self.body_frame, fg_color="transparent")
        self.path_picker_frame.pack(fill="x", pady=5)

        self.txt_path = ctk.CTkEntry(
            self.path_picker_frame, 
            textvariable=self.install_path_var, 
            font=ctk.CTkFont(size=11),
            height=35
        )
        self.txt_path.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_browse = ctk.CTkButton(
            self.path_picker_frame, 
            text="Examinar...", 
            width=100, 
            height=35,
            command=self._browse_path
        )
        self.btn_browse.pack(side="right")

        # Opciones de Instalación
        self.lbl_options_title = ctk.CTkLabel(
            self.body_frame, 
            text="⚙️ Opciones adicionales:", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lbl_options_title.pack(anchor="w", pady=(15, 5))

        self.chk_desktop = ctk.CTkCheckBox(
            self.body_frame, 
            text="Crear acceso directo en el Escritorio", 
            variable=self.desktop_shortcut_var
        )
        self.chk_desktop.pack(anchor="w", pady=4)

        self.chk_start_menu = ctk.CTkCheckBox(
            self.body_frame, 
            text="Crear acceso directo en el Menú Inicio", 
            variable=self.start_menu_shortcut_var
        )
        self.chk_start_menu.pack(anchor="w", pady=4)

        self.chk_cert = ctk.CTkCheckBox(
            self.body_frame, 
            text="Instalar y confiar automáticamente el certificado digital de Frutand S.A.S.", 
            variable=self.auto_trust_cert_var
        )
        self.chk_cert.pack(anchor="w", pady=4)

        # Footer Frame con Botones
        self.footer_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=("gray85", "gray17"))
        self.footer_frame.pack(fill="x", side="bottom")

        self.btn_cancel = ctk.CTkButton(
            self.footer_frame, 
            text="Cancelar", 
            fg_color="gray40", 
            hover_color="gray30", 
            width=100,
            command=self.destroy
        )
        self.btn_cancel.pack(side="right", padx=(5, 20), pady=12)

        self.btn_install = ctk.CTkButton(
            self.footer_frame, 
            text="🚀 Instalar Ahora", 
            fg_color="#27AE60", 
            hover_color="#1E8449",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=140,
            command=self._start_install
        )
        self.btn_install.pack(side="right", padx=5, pady=12)

    def _browse_path(self):
        chosen = filedialog.askdirectory(
            title="Seleccionar carpeta de instalación",
            initialdir=self.install_path_var.get()
        )
        if chosen:
            self.install_path_var.set(os.path.normpath(chosen))

    def _start_install(self):
        target_dir = self.install_path_var.get().strip()
        if not target_dir:
            messagebox.showerror("Error", "Por favor seleccione una carpeta de instalación válida.")
            return

        try:
            os.makedirs(target_dir, exist_ok=True)

            # Determinar fuente de los archivos
            source_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            app_src = os.path.join(source_dir, "dist", "FrutandChronos") if os.path.exists(os.path.join(source_dir, "dist", "FrutandChronos")) else source_dir

            # Copiar archivos principales
            for item in os.listdir(app_src):
                s = os.path.join(app_src, item)
                d = os.path.join(target_dir, item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)

            exe_installed = os.path.join(target_dir, "FrutandChronos.exe")

            # 1. Instalar Certificado si está activado
            if self.auto_trust_cert_var.get() and os.path.exists(exe_installed):
                try:
                    cmd = (
                        f"$sig = Get-AuthenticodeSignature '{exe_installed}'; "
                        "if ($sig.SignerCertificate) { "
                        "  $store = New-Object System.Security.Cryptography.X509Certificates.X509Store('Root', 'CurrentUser'); "
                        "  $store.Open('ReadWrite'); "
                        "  $store.Add($sig.SignerCertificate); "
                        "  $store.Close(); "
                        "}"
                    )
                    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd], capture_output=True)
                except Exception:
                    pass

            # 2. Crear accesos directos mediante PowerShell WScript.Shell
            if self.desktop_shortcut_var.get() and os.path.exists(exe_installed):
                desktop_folder = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
                shortcut_path = os.path.join(desktop_folder, "Frutand Chronos.lnk")
                ps_shortcut = (
                    f"$wsh = New-Object -ComObject WScript.Shell; "
                    f"$s = $wsh.CreateShortcut('{shortcut_path}'); "
                    f"$s.TargetPath = '{exe_installed}'; "
                    f"$s.WorkingDirectory = '{target_dir}'; "
                    f"$s.Save()"
                )
                subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_shortcut], capture_output=True)

            ans = messagebox.askyesno(
                "Instalación Completada", 
                f"✅ Frutand Chronos se ha instalado correctamente en:\n{target_dir}\n\n¿Desea iniciar la aplicación ahora?"
            )
            if ans and os.path.exists(exe_installed):
                subprocess.Popen([exe_installed], cwd=target_dir)

            self.destroy()

        except Exception as e:
            messagebox.showerror("Error de Instalación", f"No se pudo completar la instalación:\n\n{str(e)}")

if __name__ == "__main__":
    wizard = InstallerWizard()
    wizard.mainloop()
