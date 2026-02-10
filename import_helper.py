"""
Helper para importar schemas.py correctamente
Evita conflictos con el package schemas/
"""
import sys
import importlib.util

spec = importlib.util.spec_from_file_location("schemas", "/home/muentes/devs/erp/schemas.py")
schemas_module = importlib.util.module_from_spec(spec)
sys.modules['schemas_module'] = schemas_module
spec.loader.exec_module(schemas_module)

# Hacer disponible como 'schemas' para compatibilidad
sys.modules['schemas_py'] = schemas_module
