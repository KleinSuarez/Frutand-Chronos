import sys
import os

# Configurar sys.path para compatibilidad con entorno de desarrollo y bundle ejecutable PyInstaller
base_dir = os.path.dirname(os.path.abspath(__file__))
if hasattr(sys, '_MEIPASS'):
    bundle_dir = getattr(sys, '_MEIPASS')
    sys.path.insert(0, bundle_dir)
    sys.path.insert(0, os.path.join(bundle_dir, 'src'))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from ui.app import FrutandChronosApp

def main():
    app = FrutandChronosApp()
    app.mainloop()

if __name__ == "__main__":
    main()
