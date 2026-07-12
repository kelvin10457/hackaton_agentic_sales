"""
core/probar_modelos.py — Prueba varios modelos de Gemini y dice cuál
funciona con TU cuenta específica. Google ha estado cambiando la
disponibilidad de modelos muy seguido en 2026; esto evita ir adivinando
uno por uno.

Corre con:  python core/probar_modelos.py
"""
import os

from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key or api_key == "tu_api_key_aqui":
    print("❌ No encontré una GEMINI_API_KEY válida en tu .env.")
    exit(1)

from google import genai
from google.genai import errors

client = genai.Client(api_key=api_key)

# Candidatos, del más nuevo/recomendado al más viejo, todos con free tier
# según la documentación oficial de Google al día de hoy.
CANDIDATOS = [
    "gemini-flash-latest",       # alias que Google mantiene apuntando al Flash GA más reciente
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
]

print(f"Probando {len(CANDIDATOS)} modelos con tu cuenta...\n")

funciono = None

for modelo in CANDIDATOS:
    print(f"→ Probando '{modelo}'...", end=" ")
    try:
        response = client.models.generate_content(
            model=modelo,
            contents="Responde solo con la palabra: funciona",
        )
        print(f"✔ FUNCIONA — respuesta: {response.text.strip()!r}")
        funciono = modelo
        break
    except errors.ClientError as e:
        codigo = e.details.get("error", {}).get("code") if hasattr(e, "details") else None
        print(f"❌ falló ({e})")
    except Exception as e:
        print(f"❌ falló ({e})")

print()
if funciono:
    print(f"✅ Usa este modelo en tu código: \"{funciono}\"")
else:
    print("❌ Ninguno funcionó. Puede ser un problema de cuenta/región, no de nombre de modelo.")
    print("   Revisa https://aistudio.google.com/apikey y confirma el proyecto activo.")
