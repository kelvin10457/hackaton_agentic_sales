"""
core/chat_consola.py — El chatbot completo, con Gemini real, manejado
desde tu consola. Así se ve el producto final antes de que R3 construya
la interfaz web de verdad.

Corre con:  python -m core.chat_consola
"""
import uuid

from dotenv import load_dotenv

load_dotenv(override=True)

from langgraph.types import Command

from core.orquestador import app
from core.estado import estado_inicial

print("=== Chat de Futuro Academy (consola) ===")
print("(Ctrl+C para salir en cualquier momento)\n")

thread_id = f"conv_consola_{uuid.uuid4().hex[:8]}"
config = {"configurable": {"thread_id": thread_id}}

estado = estado_inicial(thread_id)
resultado = app.invoke(estado, config=config)

while "__interrupt__" in resultado:
    interrupcion = resultado["__interrupt__"][0]
    pregunta = interrupcion.value["pregunta"]
    print(f"Agente: {pregunta}")
    respuesta_usuario = input("Tú: ")
    resultado = app.invoke(Command(resume=respuesta_usuario), config=config)

print("\n=== Conversación terminada ===")
if resultado.get("score"):
    print(f"Score final: {resultado['score'].total} ({resultado['score'].banda})")
    print(f"  interés={resultado['score'].interes} presupuesto={resultado['score'].presupuesto} "
          f"perfil={resultado['score'].perfil} urgencia={resultado['score'].urgencia}")
    print(f"Ruta sugerida: {resultado.get('ruta_sugerida')}")
if resultado.get("perfil_riesgo"):
    print(f"Perfil de riesgo: {resultado['perfil_riesgo']}")
if resultado["historial"]:
    print(f"\nÚltimo mensaje del agente: {resultado['historial'][-1]['texto']}")
