"""
core/orquestador.py — El grafo del agente. Biblia §7, Manual R1 §7.

Grafo con dos modos:
  PROSPECTO: clasificacion → identificacion_1 → calificacion → scoring → educacion → identificacion_2 → consentimiento → cierre
  TUTOR:     tutor (RAG + quiz diagnóstico) → tutor_registro → consentimiento → cierre
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from core.estado import EstadoConversacion
from core.guardrails.g1_no_asesoramiento import se_dispara_g1, respuesta_g1
from tools.calcular_score import calcular_score
from tools.calcular_ruta import calcular_ruta
from tools.obtener_quiz import calcular_perfil_riesgo, obtener_preguntas_quiz
from tools.clasificar_prospecto import clasificar_prospecto
from tools.extraer_senales import extraer_senales
from tools.generar_pregunta_calificacion import generar_pregunta_calificacion
from tools.responder_tutor import responder_tutor


# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────

def _agregar_mensaje(historial: list, rol: str, texto: str) -> list:
    return historial + [{"rol": rol, "texto": texto}]


def _extraer_nombre(texto: str) -> str:
    """Extrae el primer nombre propio de una respuesta como 'Soy David y mi empresa...'."""
    palabras_ignorar = {"soy", "me", "llamo", "mi", "nombre", "es", "yo", "el", "la", "un", "una"}
    for palabra in texto.split():
        limpia = palabra.strip(".,!?;:\"'")
        if limpia.lower() not in palabras_ignorar and limpia and limpia[0].isupper():
            return limpia
    return texto.split()[0] if texto.split() else texto


def _detectar_modo_llm(mensaje: str) -> str:
    """
    Detecta si el usuario quiere modo TUTOR o PROSPECTO usando keywords.
    No requiere llamada al LLM — instantáneo y sin costo de API.
    """
    texto = mensaje.lower()
    keywords_tutor = {
        "aprender", "educación", "educacion", "entender",
        "explicar", "explícame", "explicame", "qué es", "que es",
        "cómo funciona", "como funciona", "enseñar", "enseñame",
        "qué son", "que son", "información sobre", "informacion sobre",
        "saber más", "saber mas", "conocer", "curiosidad", "duda",
        "diferencia entre", "concepto", "definición", "definicion",
        "invertir en", "aprendizaje",
    }
    if any(kw in texto for kw in keywords_tutor):
        return "TUTOR"
    return "PROSPECTO"


# ─────────────────────────────────────────────────────────
# NODOS COMUNES
# ─────────────────────────────────────────────────────────

def nodo_saludo(estado: EstadoConversacion) -> dict:
    mensaje = (
        "¡Hola! 👋 Soy el asistente de Futuro Academy. Puedo ayudarte de dos formas:\n\n"
        "📚 **Aprender** — te explico temas de finanzas e inversiones con contenido aprobado\n"
        "💼 **Resolver** — analizo tu situación y te conecto con el asesor o recurso adecuado\n\n"
        "¿En qué te puedo ayudar hoy?"
    )
    respuesta_usuario = interrupt({"pregunta": mensaje})
    historial = _agregar_mensaje(estado["historial"], "agente", mensaje)
    historial = _agregar_mensaje(historial, "usuario", respuesta_usuario)
    return {"historial": historial, "estado_flujo": "deteccion_modo"}


def nodo_deteccion_modo(estado: EstadoConversacion) -> dict:
    """Clasifica la intención del usuario: TUTOR o PROSPECTO."""
    ultimo_mensaje = estado["historial"][-1]["texto"]
    modo = _detectar_modo_llm(ultimo_mensaje)
    
    historial = estado["historial"]
    
    # Si es prospecto pero dio muy poco contexto (ej: solo dijo "resolver")
    # le pedimos más detalles antes de clasificarlo como b2b/b2c
    if modo == "PROSPECTO" and len(ultimo_mensaje.split()) <= 4:
        pregunta = "Perfecto. Para guiarte mejor, ¿podrías contarme brevemente qué buscas o qué problema quieres resolver?"
        historial = _agregar_mensaje(historial, "agente", pregunta)
        respuesta = interrupt({"pregunta": pregunta})
        historial = _agregar_mensaje(historial, "usuario", respuesta)
        
    return {"modo": modo, "historial": historial}


def _enrutar_desde_deteccion(estado: EstadoConversacion) -> str:
    return "tutor" if estado.get("modo") == "TUTOR" else "clasificacion"


# ─────────────────────────────────────────────────────────
# NODOS DEL MODO TUTOR
# ─────────────────────────────────────────────────────────

def _correr_quiz_diagnostico(tema: str, historial: list) -> tuple[list, int]:
    """
    Genera y corre un quiz diagnóstico de 3 preguntas sobre el tema.
    Devuelve (historial actualizado, número de respuestas correctas).
    """
    from tools.generar_quiz_tutor import generar_quiz_tutor

    intro = f"📝 **Quiz diagnóstico: {tema}**\nTe haré 3 preguntas de opción múltiple. Responde con el número (0, 1 o 2). ¡Vamos!"
    historial = _agregar_mensaje(historial, "agente", intro)
    resp_intro = interrupt({"pregunta": intro})
    historial = _agregar_mensaje(historial, "usuario", resp_intro)

    quiz = generar_quiz_tutor(tema)
    correctas = 0

    for i, p in enumerate(quiz.preguntas, 1):
        opciones_texto = "\n".join(f"  {j}: {op}" for j, op in enumerate(p.opciones))
        pregunta_completa = f"**Pregunta {i}/3:** {p.pregunta}\n\n{opciones_texto}\n\n(responde con 0, 1 o 2)"

        respuesta_idx = None
        while respuesta_idx is None:
            resp = interrupt({"pregunta": pregunta_completa})
            historial = _agregar_mensaje(historial, "usuario", resp)
            try:
                candidato = int(resp.strip())
                if 0 <= candidato <= 2:
                    respuesta_idx = candidato
                else:
                    pregunta_completa = f"Por favor responde con 0, 1 o 2.\n\n{pregunta_completa}"
            except ValueError:
                pregunta_completa = f"Necesito un número (0, 1 o 2).\n\n{pregunta_completa}"

        es_correcta = respuesta_idx == p.correcta
        if es_correcta:
            correctas += 1
            feedback = f"✅ **¡Correcto!** {p.explicacion}"
        else:
            feedback = (
                f"❌ **No exactamente.** La respuesta correcta es la **{p.correcta}: {p.opciones[p.correcta]}**\n"
                f"💡 {p.explicacion}"
            )
        historial = _agregar_mensaje(historial, "agente", feedback)
        resp_feedback = interrupt({"pregunta": feedback})
        historial = _agregar_mensaje(historial, "usuario", resp_feedback)

    return historial, correctas


def nodo_tutor(estado: EstadoConversacion) -> dict:
    """
    Bucle del Tutor IA: RAG + quiz diagnóstico opcional.
    - Si el primer mensaje es genérico → muestra menú de 14 temas.
    - Responde con contenido aprobado citando la fuente.
    - Ofrece quiz diagnóstico de 3 preguntas generadas por LLM.
    """
    from tools.buscar_conocimiento import buscar_conocimiento, _cargar_documentos

    historial = estado["historial"]
    tema_acumulado = estado.get("tema_interes") or ""

    # Si el mensaje inicial es genérico, ofrecer menú de temas
    texto_inicial = historial[-1]["texto"]
    palabras_genericas = {"aprender", "educación", "educacion", "saber", "información", "informacion", "aprendizaje"}
    es_generico = (
        not buscar_conocimiento(texto_inicial, top_k=1) or
        (any(p in texto_inicial.lower() for p in palabras_genericas) and len(texto_inicial.split()) < 6)
    )

    if es_generico:
        docs_disponibles = _cargar_documentos()
        temas_lista = "\n".join(f"  • {d['titulo']}" for d in docs_disponibles)
        mensaje_menu = (
            "¡Con gusto! 📚 Estos son los temas que puedo explicarte hoy:\n\n"
            f"{temas_lista}\n\n"
            "¿Sobre cuál de estos temas te gustaría aprender? También puedes escribir tu propia pregunta."
        )
        historial = _agregar_mensaje(historial, "agente", mensaje_menu)
        respuesta = interrupt({"pregunta": mensaje_menu})
        historial = _agregar_mensaje(historial, "usuario", respuesta)

    MAX_TURNOS = 6
    for _ in range(MAX_TURNOS):
        ultima_pregunta = historial[-1]["texto"]

        # ¿El usuario quiere salir?
        palabras_salida = ["asesor", "hablar con", "quiero contactar", "ya fue", "gracias", "adiós", "adios", "bye"]
        if any(p in ultima_pregunta.lower() for p in palabras_salida):
            mensaje_cierre = (
                "¡Con gusto! Si quieres que un asesor de Futuro Academy te contacte, "
                "puedo registrar tu interés. ¿Te gustaría que alguien se ponga en contacto contigo?"
            )
            historial = _agregar_mensaje(historial, "agente", mensaje_cierre)
            resp = interrupt({"pregunta": mensaje_cierre})
            historial = _agregar_mensaje(historial, "usuario", resp)
            break

        # Respuesta educativa con RAG
        resultado = responder_tutor(ultima_pregunta, historial[:-1])
        
        if resultado.get("documentos_usados", 0) == 0:
            docs_disponibles = _cargar_documentos()
            temas_lista = "\n".join(f"  • {d['titulo']}" for d in docs_disponibles)
            mensaje_fallback = (
                "No tengo información aprobada por Futuro Academy sobre ese tema. 😅\n\n"
                "Sin embargo, estos son los temas que sí te puedo explicar:\n\n"
                f"{temas_lista}\n\n"
                "¿Sobre cuál de estos temas te gustaría aprender?"
            )
            historial = _agregar_mensaje(historial, "agente", mensaje_fallback)
            resp = interrupt({"pregunta": mensaje_fallback})
            historial = _agregar_mensaje(historial, "usuario", resp)
            continue

        respuesta_agente = resultado["respuesta"]
        tema = resultado.get("tema", "")
        if tema:
            tema_acumulado = tema

        # Ofrecer quiz diagnóstico después de la explicación
        respuesta_con_oferta_quiz = (
            f"{respuesta_agente}\n\n"
            "---\n"
            "🎯 ¿Quieres hacer un **quiz diagnóstico** de 3 preguntas para ver cuánto entendiste? (sí/no)"
        )
        historial = _agregar_mensaje(historial, "agente", respuesta_con_oferta_quiz)
        quiere_quiz = interrupt({"pregunta": respuesta_con_oferta_quiz})
        historial = _agregar_mensaje(historial, "usuario", quiere_quiz)

        # Correr quiz si acepta
        if quiere_quiz.strip().lower() in ("si", "sí", "s", "yes", "y", "dale", "ok", "claro", "va", "quiero"):
            historial, correctas = _correr_quiz_diagnostico(tema or ultima_pregunta, historial)

            # Retroalimentación final
            if correctas == 3:
                resumen = "🏆 **¡Perfecto! 3/3 correctas.** Dominas el tema. ¿Quieres explorar otro tema?"
            elif correctas == 2:
                resumen = f"👍 **Muy bien! {correctas}/3 correctas.** Tienes buenas bases. ¿Quieres repasar algo o aprender otro tema?"
            elif correctas == 1:
                resumen = f"📚 **{correctas}/3 correctas.** Estás empezando. Te recomiendo releer el material. ¿Quieres que te explique algo con más detalle?"
            else:
                resumen = "💡 **0/3 correctas.** ¡No te preocupes! Todos empezamos desde cero. ¿Quieres que te explique el tema paso a paso?"

            historial = _agregar_mensaje(historial, "agente", resumen)
            continuar = interrupt({"pregunta": resumen})
            historial = _agregar_mensaje(historial, "usuario", continuar)
        else:
            siguiente = "¡Entendido! ¿Tienes alguna otra pregunta sobre este u otro tema de finanzas?"
            historial = _agregar_mensaje(historial, "agente", siguiente)
            continuar = interrupt({"pregunta": siguiente})
            historial = _agregar_mensaje(historial, "usuario", continuar)

        # ¿Terminó?
        resp_final = historial[-1]["texto"].lower()
        if any(p in resp_final for p in ["no", "listo", "ya fue", "bye", "adiós", "gracias", "nada más"]):
            break

    return {
        "historial": historial,
        "tema_interes": tema_acumulado,
        "estado_flujo": "tutor_registro",
    }


def nodo_tutor_registro(estado: EstadoConversacion) -> dict:
    """Registra el tema de interés como señal comercial."""
    tema = estado.get("tema_interes", "finanzas")
    pregunta = (
        f"Me alegra que hayas aprendido sobre **{tema}** hoy. 📖 "
        "¿Te gustaría que te enviáramos más material educativo y te conectáramos con un asesor "
        "si en algún momento lo necesitas? Dame tu correo y lo hacemos."
    )
    respuesta = interrupt({"pregunta": pregunta})
    historial = _agregar_mensaje(estado["historial"], "agente", pregunta)
    historial = _agregar_mensaje(historial, "usuario", respuesta)
    email = respuesta.strip() if "@" in respuesta else None
    return {"historial": historial, "email": email, "estado_flujo": "consentimiento"}


# ─────────────────────────────────────────────────────────
# NODOS DEL MODO PROSPECTO (Conversación Libre)
# ─────────────────────────────────────────────────────────

def nodo_conversacion_prospecto(estado: EstadoConversacion) -> dict:
    """
    Bucle de conversación libre con el usuario. El LLM actúa como consultor,
    determina si es B2B o B2C de forma natural, averigua el problema,
    presupuesto, urgencia e interés.
    """
    from tools.conversar_prospecto import conversar_prospecto

    historial = estado["historial"]
    
    # Bucle conversacional
    MAX_TURNOS = 8
    for _ in range(MAX_TURNOS):
        # Llamar al LLM con todo el historial
        respuesta_llm = conversar_prospecto(historial)
        
        historial = _agregar_mensaje(historial, "agente", respuesta_llm.mensaje_agente)
        
        # Si ya entendió el problema y recomendó un asesor
        if respuesta_llm.listo_para_asesor:
            # Mostrar el último mensaje (que ya incluye la recomendación) y pasar al siguiente nodo
            resp_usuario = interrupt({"pregunta": respuesta_llm.mensaje_agente})
            historial = _agregar_mensaje(historial, "usuario", resp_usuario)
            
            prioridad = None
            if respuesta_llm.evaluacion_lead:
                ev = respuesta_llm.evaluacion_lead
                score = 0
                
                if ev.urgencia == "Alta": score += 3
                elif ev.urgencia == "Media": score += 1
                
                if ev.presupuesto == "Alto": score += 3
                elif ev.presupuesto == "Medio": score += 2
                elif ev.presupuesto == "Bajo": score += 1
                
                if ev.nivel_interes >= 8: score += 2
                elif ev.nivel_interes >= 5: score += 1
                
                if score >= 6: prioridad = "Alta"
                elif score >= 3: prioridad = "Media"
                else: prioridad = "Baja"
                
            return {
                "historial": historial,
                "tipo": respuesta_llm.tipo_prospecto_detectado if respuesta_llm.tipo_prospecto_detectado != "DESCONOCIDO" else None,
                "asesor_sugerido": respuesta_llm.asesor_sugerido,
                "prioridad_lead": prioridad,
                "estado_flujo": "identificacion_2"
            }
            
        # Si aún no está listo, pedir input del usuario y continuar
        resp_usuario = interrupt({"pregunta": respuesta_llm.mensaje_agente})
        historial = _agregar_mensaje(historial, "usuario", resp_usuario)
        
    # Si llega aquí, se acabaron los turnos sin resolverse
    return {"historial": historial, "estado_flujo": "identificacion_2"}


# ─────────────────────────────────────────────────────────
# NODOS COMPARTIDOS
# ─────────────────────────────────────────────────────────

def nodo_identificacion_2(estado: EstadoConversacion) -> dict:
    """★ El momento de oro: pide el email."""
    ultimo_mensaje = estado["historial"][-1]["texto"].lower()
    
    # Si el usuario ya rechazó en el último mensaje
    rechazos = ["no", "no quiero", "no te lo voy a dar", "no gracias", "nunca", "jamas"]
    if any(ultimo_mensaje.strip() == r for r in rechazos) or "no te doy" in ultimo_mensaje:
        return {
            "email": None,
            "estado_identificacion": "descartado",
            "consentimiento_tratamiento_datos": False,
            "estado_flujo": "cierre"
        }

    # Como la conversación fue libre, puede que el usuario ya haya dado su email en el último mensaje
    if "@" in ultimo_mensaje:
        email = ultimo_mensaje.strip()
        historial = estado["historial"]
    else:
        # Si no dio el correo, se lo pedimos explícitamente
        asesor = estado.get("asesor_sugerido", "nuestro equipo especializado")
        pregunta = f"Para conectarte directamente con el {asesor} y enviarte más información, ¿me podrías proporcionar tu correo electrónico?"
        email_raw = interrupt({"pregunta": pregunta})
        email_lower = email_raw.lower()
        historial = _agregar_mensaje(estado["historial"], "agente", pregunta)
        historial = _agregar_mensaje(historial, "usuario", email_raw)
        
        # Si el usuario responde "no" a la pregunta directa del correo
        if any(email_lower.strip() == r for r in rechazos) or "no te doy" in email_lower:
             return {
                "historial": historial,
                "email": None,
                "estado_identificacion": "descartado",
                "consentimiento_tratamiento_datos": False,
                "estado_flujo": "cierre"
            }
        email = email_raw
        
    return {
        "historial": historial,
        "email": email.strip() if email else None,
        "estado_identificacion": "identificado",
        "estado_flujo": "consentimiento",
    }


def nodo_consentimiento(estado: EstadoConversacion) -> dict:
    """Dos casillas separadas, nunca premarcadas (GDPR)."""
    p1 = "Autorizo a Futuro Academy a tratar mis datos para enviarme mi resultado y material educativo. (sí/no)"
    r1 = interrupt({"pregunta": p1})
    historial = _agregar_mensaje(estado["historial"], "agente", p1)
    historial = _agregar_mensaje(historial, "usuario", r1)

    p2 = "Acepto recibir comunicaciones comerciales. (sí/no)"
    r2 = interrupt({"pregunta": p2})
    historial = _agregar_mensaje(historial, "agente", p2)
    historial = _agregar_mensaje(historial, "usuario", r2)

    afirmativas = {"sí", "si", "s", "yes", "y", "acepto", "claro", "ok"}
    return {
        "historial": historial,
        "consentimiento_tratamiento_datos": r1.strip().lower() in afirmativas,
        "consentimiento_comunicaciones": r2.strip().lower() in afirmativas,
        "estado_flujo": "cierre",
    }


def nodo_cierre(estado: EstadoConversacion) -> dict:
    nombre = estado.get("nombre", "")
    nombre_str = f", {_extraer_nombre(nombre)}" if nombre else ""
    if estado.get("consentimiento_tratamiento_datos"):
        mensaje = (
            f"¡Listo{nombre_str}! 🎉 Un asesor de Futuro Academy se pondrá en contacto contigo "
            "en las próximas 24 horas. ¡Que tengas un excelente día!"
        )
    else:
        mensaje = (
            f"Entendido{nombre_str}, no hay problema. Puedes volver cuando quieras y "
            "seguir aprendiendo con nosotros. ¡Fue un placer charlar contigo!"
        )
    historial = _agregar_mensaje(estado["historial"], "agente", mensaje)
    return {"historial": historial}


def _enrutar_desde_email(estado: EstadoConversacion) -> str:
    return "cierre" if estado.get("estado_flujo") == "cierre" else "consentimiento"


# ─────────────────────────────────────────────────────────
# CONSTRUCCIÓN DEL GRAFO
# ─────────────────────────────────────────────────────────

def construir_grafo():
    grafo = StateGraph(EstadoConversacion)

    grafo.add_node("saludo", nodo_saludo)
    grafo.add_node("deteccion_modo", nodo_deteccion_modo)
    grafo.add_node("conversacion_prospecto", nodo_conversacion_prospecto)
    grafo.add_node("identificacion_2", nodo_identificacion_2)
    grafo.add_node("consentimiento", nodo_consentimiento)
    grafo.add_node("cierre", nodo_cierre)
    grafo.add_node("tutor", nodo_tutor)
    grafo.add_node("tutor_registro", nodo_tutor_registro)

    grafo.set_entry_point("saludo")
    grafo.add_edge("saludo", "deteccion_modo")

    grafo.add_conditional_edges(
        "deteccion_modo",
        _enrutar_desde_deteccion,
        {"tutor": "tutor", "clasificacion": "conversacion_prospecto"},
    )

    grafo.add_edge("conversacion_prospecto", "identificacion_2")
    grafo.add_edge("identificacion_2", "consentimiento")

    grafo.add_edge("tutor", "tutor_registro")
    grafo.add_edge("tutor_registro", "consentimiento")

    grafo.add_edge("consentimiento", "cierre")
    grafo.add_edge("cierre", END)

    checkpointer = MemorySaver()
    return grafo.compile(checkpointer=checkpointer)


app = construir_grafo()
