"""
core/probar_conversacion_real.py — Escribe como si fueras un prospecto,
y al final el agente (con Gemini de verdad) te clasifica y extrae señales.
"""
from dotenv import load_dotenv

load_dotenv(override=True)

from tools.clasificar_prospecto import clasificar_prospecto
from tools.extraer_senales import extraer_senales
from tools.calcular_score import calcular_score
from tools.calcular_ruta import calcular_ruta

print("=== Simulador de conversación con Gemini real ===")
print("Escribe como si fueras un prospecto hablando con el chat de Futuro Academy.")
print("Ejemplos de cosas que podrías escribir:")
print('  "Hola, quiero empezar a invertir mis ahorros"')
print('  "Tengo unos 5000 dólares y nunca he invertido antes"')
print('  "Me gustaría hablar con un asesor"')
print('Escribe "fin" cuando termines.\n')

mensajes_usuario = []
while True:
    texto = input("Tú: ").strip()
    if texto.lower() == "fin":
        break
    if texto:
        mensajes_usuario.append(texto)

if not mensajes_usuario:
    print("No escribiste ningún mensaje. Corre el script de nuevo.")
    exit(0)

print("\n=== Procesando con Gemini... ===\n")

clasificacion = clasificar_prospecto(mensajes_usuario)
print(f"T1 — Clasificación: {clasificacion.tipo} (confianza: {clasificacion.confianza:.2f})")

senales = extraer_senales(mensajes_usuario, clasificacion.tipo)
print(f"\nT3 — Señales extraídas:")
print(senales.model_dump_json(indent=2, exclude_none=True))

score = calcular_score(senales, clasificacion.tipo)
ruta = calcular_ruta(clasificacion.tipo, score.total, senales.pidio_asesor)

print(f"\nT4 — Score: {score.total} ({score.banda})")
print(f"     Desglose: interés={score.interes} presupuesto={score.presupuesto} "
      f"perfil={score.perfil} urgencia={score.urgencia}")
print(f"     Justificación: {score.justificacion}")
print(f"\nT12 — Ruta sugerida: {ruta}")
