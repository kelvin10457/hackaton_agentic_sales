"""
core/prueba_local.py — corre el grafo completo con datos simulados de María.

No necesita Gemini todavía (los nodos de clasificación/calificación están
en modo heurístico). Esto solo prueba que el GRAFO en sí está bien armado.

Corre con:  python core/prueba_local.py
"""
from core.orquestador import app
from core.estado import estado_inicial
from schemas.senales import Senales

estado = estado_inicial("conv_prueba_maria")

# Simulamos que ya se conversó y ya se extrajeron las señales de María
# (en la vida real, esto lo llenaría T3 con Gemini)
estado["historial"] = [
    {"rol": "usuario", "texto": "Hola, quiero empezar a invertir mis ahorros"},
]
estado["senales"] = Senales(
    objetivo="invertir",
    horizonte="1-3m",
    pidio_asesor=True,
    mensajes_intercambiados=11,
    completo_quiz=True,
    monto_declarado_usd=10000,
    experiencia_inversion="ninguna",
    cedula_valida=True,
    email_valido=True,
)

config = {"configurable": {"thread_id": "conv_prueba_maria"}}
resultado = app.invoke(estado, config=config)

print("=== Resultado del grafo para María ===")
print("Tipo:", resultado["tipo"])
print("Score total:", resultado["score"].total)
print("Banda:", resultado["score"].banda)
print("Ruta sugerida:", resultado["ruta_sugerida"])
print("\nÚltimo mensaje del agente:", resultado["historial"][-1]["texto"])

assert resultado["score"].total == 88, "El score debería dar 88, como en la Biblia"
print("\n✔ El grafo corrió de punta a punta y el score coincide con la Biblia.")
