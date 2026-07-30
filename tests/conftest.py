import sys
import os

# Garantizar que project/src esté siempre disponible para las pruebas
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
