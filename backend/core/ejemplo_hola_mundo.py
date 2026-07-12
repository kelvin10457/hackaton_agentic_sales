"""
core/ejemplo_hola_mundo.py

Un grafo de juguete, 3 nodos, CERO inteligencia artificial.
El objetivo es entender la mecánica de LangGraph antes de tocar el grafo real.

Corre esto con:  python core/ejemplo_hola_mundo.py
"""
from typing import TypedDict

from langgraph.graph import StateGraph, END


# 1. El "estado" es solo un diccionario tipado que viaja de nodo a nodo.
class EstadoJuguete(TypedDict):
    contador: int
    mensajes: list[str]


# 2. Cada nodo es una función normal de Python: recibe el estado, devuelve
#    un pedazo del estado para actualizar.
def nodo_saludar(estado: EstadoJuguete) -> dict:
    print("→ Estoy en el nodo SALUDAR")
    return {"mensajes": estado["mensajes"] + ["Hola, soy el agente"]}


def nodo_contar(estado: EstadoJuguete) -> dict:
    print("→ Estoy en el nodo CONTAR")
    nuevo_contador = estado["contador"] + 1
    return {
        "contador": nuevo_contador,
        "mensajes": estado["mensajes"] + [f"El contador va en {nuevo_contador}"],
    }


def nodo_despedir(estado: EstadoJuguete) -> dict:
    print("→ Estoy en el nodo DESPEDIR")
    return {"mensajes": estado["mensajes"] + ["Adiós"]}


# 3. Construyes el grafo: nodos + aristas (edges) que dicen "de aquí, vas a allá"
grafo = StateGraph(EstadoJuguete)

grafo.add_node("saludar", nodo_saludar)
grafo.add_node("contar", nodo_contar)
grafo.add_node("despedir", nodo_despedir)

grafo.set_entry_point("saludar")       # por dónde empieza
grafo.add_edge("saludar", "contar")    # saludar -> contar
grafo.add_edge("contar", "despedir")   # contar -> despedir
grafo.add_edge("despedir", END)        # despedir -> fin

# 4. Compilas el grafo. Esto lo convierte en algo ejecutable.
app = grafo.compile()

if __name__ == "__main__":
    estado_inicial = {"contador": 0, "mensajes": []}

    print("=== Corriendo el grafo ===")
    resultado_final = app.invoke(estado_inicial)

    print("\n=== Estado final ===")
    print(resultado_final)
