import sys
import os

# Asegurar que project/src esté en el PATH de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import FrutandChronosApp

def main():
    print("Iniciando Frutand Chronos...")
    app = FrutandChronosApp()
    app.mainloop()

if __name__ == "__main__":
    main()
