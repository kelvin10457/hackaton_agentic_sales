"""
core/probar_api_key.py — Prueba mínima: ¿tu GEMINI_API_KEY funciona?
"""
import os

from dotenv import load_dotenv

load_dotenv()  # lee el archivo .env y carga GEMINI_API_KEY al entorno

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key or api_key == "tu_api_key_aqui":
    print("❌ No encontré una GEMINI_API_KEY válida.")
    print("   1. Copia .env.example a .env")
    print("   2. Abre .env y pega tu key real")
    exit(1)

print(f"✔ Encontré una key que empieza con: {api_key[:8]}...")

from google import genai

client = genai.Client(api_key=api_key)

print("Llamando a Gemini...")
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Responde solo con la palabra: funciona",
)

print("\n=== Respuesta de Gemini ===")
print(response.text)
print("\n✔ Tu API key funciona correctamente.")
