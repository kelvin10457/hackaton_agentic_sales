# Estado de la Rama R1 (Agent Core) — Integración R1 ↔ R2

Rama paralela donde R1 construye el núcleo de IA (LangGraph + tools + guardrails)
y se integra con la API de R2 sin romper `main`. Este documento refleja el estado
**después de conectar el chat web con el núcleo agéntico y completar los guardrails**.

---

## ✅ Progreso Actual (verificado)

1. **Configuraciones (R1)** — `backend/config/` alineado a la Biblia (preguntas B2C/B2B,
   quiz de perfil de riesgo con rúbrica fija, pesos de scoring).
2. **Herramientas deterministas (R1/R5)** — `calcular_score.py`, `obtener_quiz.py`,
   `calcular_ruta.py` (código puro, con tests: María = 88).
3. **Cerebro del agente (R1)** — máquina de estados (`core/estado.py`) y grafo
   (`core/orquestador.py`) con modos TUTOR y PROSPECTO; tools que llaman al LLM
   vía OpenRouter (`tools/conversar_prospecto.py`, `tools/responder_tutor.py`,
   RAG por keywords en `tools/buscar_conocimiento.py`).
4. **UI / CORS** — `web/` y `app/main.py` sincronizados con `main`; mocks apagados
   (`web/lib/mocks.ts` → `USE_MOCKS = false`); CORS abierto para el frontend.

### 🆕 Resuelto en esta sesión de integración

5. **El chat web ya habla con el núcleo agéntico** *(problema #2 del backlog — RESUELTO)*.
   `app/routers/chat.py` dejó de ser un cascarón: ahora expone el contrato completo
   que consume `web/lib/api-client.ts` y **cada mensaje despierta al agente**.
   - `POST /api/chat/iniciar` — crea la conversación anónima y firma su token de sesión.
   - `POST /api/chat/mensaje` — llama a `core/servicio_agente.procesar_turno(...)`, que
     reutiliza **las tools de R1** (RAG + LLM) y aplica los guardrails; devuelve
     `{mensaje, fuentes, estado_flujo, badge_tipo, guardrail, accion}`.
   - `GET /api/chat/conversacion` — recupera el historial (continuidad al reabrir el
     navegador). Superset: incluye `historial`/`badge_tipo` (frontend) y `id`/`messages`
     (segregación, `test_superficies`).
   - `POST /api/chat/quiz` y `POST /api/chat/quiz/respuestas` — quiz determinista
     (el perfil lo calcula CÓDIGO, nunca el LLM). Las opciones se envían **sin puntajes**.
   - `POST /api/chat/consentimiento` — consentimiento **por finalidad**; con datos + email
     el lead entra al CRM (`crm_upsert` idempotente) y se registra en la bitácora.
   - El token de sesión se acepta en `Authorization: Bearer` (frontend) **o**
     `X-Session-Token` (contrato interno). La segregación de superficies se mantiene.

6. **Bloque de guardrails completo** *(problema #1 del backlog — RESUELTO)*.
   Paquete `core/guardrails/` con fachada unificada (`evaluar_entrada_usuario`,
   `evaluar_salida_agente`) e integrado en el turno del chat:
   | Malla | Qué hace | Archivo |
   |---|---|---|
   | **G1** | No-asesoramiento sobre la ENTRADA del usuario | `g1_no_asesoramiento.py` |
   | **G1-bis** | No-asesoramiento sobre la SALIDA del agente (no receta productos) | `g1bis_salida_asesoramiento.py` |
   | **G2** | Negativa honesta cuando el RAG viene vacío | `g2_negativa_honesta.py` |
   | **G3** | Consentimiento por finalidad (checkers reutilizables) | `adicionales.py` |
   | **G4** | Minimización de datos (no pedir cédula antes de tiempo) | `adicionales.py` |
   | **G5** | Segregación de superficies (no filtrar score/brief al prospecto) | `adicionales.py` |
   | **G6** | Alcance temático (se mantiene en educación financiera) | `adicionales.py` |
   | **G7** | Cifras deterministas / no prometer rendimientos | `g7_cifras_deterministas.py` |
   | **G8** | Cada guardrail disparado se audita como `EventoAuditoria` | `registro.py` + `routers/chat.py` |

7. **Degradación sin API key** — si falta `OPENROUTER_API_KEY`, el chat **sigue
   funcionando**: responde con el corpus aprobado (RAG determinista) y aplica los
   guardrails. Nunca lanza 500. Con la clave, el tutor y el consultor usan el LLM real.

8. **Tests** — `openai` añadido a `requirements.txt`; `.env.example` documenta las
   variables. Cobertura nueva: `tests/test_guardrails_completos.py` y
   `tests/test_servicio_agente.py`.

### 🔎 Verificación ejecutada

- `pytest app/tests` → **74/74 OK** (incluye `test_superficies` y `test_consentimiento`,
  los más sensibles a los cambios del router).
- `pytest tests/test_guardrails*.py tests/test_servicio_agente.py tests/test_quiz.py
  tests/test_score.py tests/test_ruta.py` → **OK**.
- Flujo end-to-end del chat (modo degradado, SQLite) verificado de punta a punta:
  `iniciar → mensaje (tutor con cita) → G1 → G2 → quiz → perfil → consentimiento →
  conversacion`, con el lead entrando al CRM y 4 eventos en la bitácora.
- **Total: 118 tests en verde.** (Ver nota de entorno abajo sobre `test_reintentos`.)

---

## 🚨 Puntos por abordar antes del merge a `main`

1. **Claves de entorno en el despliegue**
   - Backend: definir `OPENROUTER_API_KEY` (LLM real), `DATABASE_URL`, `SECRET_KEY`,
     `CHAT_TOKEN_SECRET` (usar `backend/.env.example` como plantilla; nunca commitear `.env`).
   - Frontend: `NEXT_PUBLIC_API_URL` apuntando al backend desplegado.

2. **Continuidad "de verdad" con `PostgresSaver`** *(mejora, no bloqueante)*
   - El grafo de `orquestador.py` usa `MemorySaver` (memoria de proceso). La continuidad
     que hoy ve el usuario proviene del historial persistido en la BD por el router
     (`GET /api/chat/conversacion`), lo cual es suficiente para la demo. Para el criterio
     de continuidad "canónico" con LangGraph, cambiar a `PostgresSaver` cuando la BD esté
     lista (Manual R1 §7). No afecta al contrato del chat.

3. **`test_reintentos.py` requiere `google-genai`**
   - Es un test de la utilidad Gemini de R1 (`tools/_gemini_utils.py`). Pasa cuando se
     instala `requirements.txt` completo; falló solo en el entorno mínimo de verificación
     (sin `google-genai`) por `ModuleNotFoundError`. No es una regresión.

4. **`orquestador.py` (grafo interrupt) vs. servicio de turno**
   - La superficie HTTP usa `core/servicio_agente.py` (un turno por request), que reutiliza
     las **mismas tools y guardrails** que el grafo. El grafo con `interrupt()` sigue vivo
     para la demo por CLI (`core/prueba_local.py`). Si se quiere unificar, migrar el grafo a
     un checkpointer persistente y exponerlo por `Command(resume=...)`; hoy no es necesario.

5. **Guardrails G3–G6**
   - G1, G1-bis, G2, G7 y G8 están implementados con la lógica exacta del Manual R1 §9.
     G3–G6 sostienen los 5 principios de diseño con reglas deterministas razonables; si la
     Biblia define una rúbrica más específica para alguno, ajustar el archivo correspondiente
     en `core/guardrails/adicionales.py`.

## 📌 Próximos pasos inmediatos
1. Cargar variables de entorno y probar el chat web contra el backend con `OPENROUTER_API_KEY`.
2. (Opcional) Migrar a `PostgresSaver` para la continuidad canónica de LangGraph.
3. Correr `pip install -r requirements.txt` completo y `pytest` de todo el backend.
4. **MERGE** a `main` una vez validado el chat web con LLM real.

---

## Cómo correr el backend en local

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # y rellena las claves (DATABASE_URL puede ser sqlite:///./dev.db)
uvicorn app.main:app --reload
# Docs interactivas del contrato: http://localhost:8000/docs
```

El frontend (`web/`) ya apunta a la API real (`USE_MOCKS = false`); define
`NEXT_PUBLIC_API_URL` y levántalo con `npm run dev`.
