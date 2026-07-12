"""
core/listar_modelos.py — Lista TODOS los modelos disponibles para TU cuenta.
Úsalo cuando el nombre de un modelo deja de funcionar para saber cuál usar.

Corre con:  python core/listar_modelos.py
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ No encontré una GEMINI_API_KEY en tu .env.")
    exit(1)

from google import genai

client = genai.Client(api_key=api_key)

print("Modelos disponibles para tu cuenta:\n")
modelos_flash = []
todos = []

for modelo in client.models.list():
    nombre = modelo.name
    todos.append(nombre)
    if "flash" in nombre.lower() or "gemini" in nombre.lower():
        modelos_flash.append(nombre)
        print(f"  {nombre}")

print(f"\nTotal: {len(todos)} modelos")
print("\n--- Copia uno de los nombres de arriba y úsalo en _MODELO ---")
