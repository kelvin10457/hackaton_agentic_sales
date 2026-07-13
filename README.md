# Futuro Academy — Agente con frenos

> *No es un chatbot con un CRM detrás. Es un agente con frenos.*

Agente de IA que capta, califica y educa prospectos 24/7 — y **nunca envía una
comunicación ni cruza una línea regulada sin la aprobación de un humano**, con
traza auditable de cada decisión.

```

| Bloque | Estado | % |
|---|---|---|
| **R1 · Núcleo agéntico** — grafo, tools, guardrails G1–G8, preguntas configurables | Completo | 97% |
| **R2 · Backend / Datos / CRM** — contratos, API, bitácora, semillas | Completo | 95% |
| **R3 · Chat del prospecto** — tutor con citas, quiz, consentimiento, continuidad | Completo | 97% |
| **R4 · Consola del ejecutivo** — pipeline, score, brief, **aprobar / editar / rechazar** | Completo | 95% |
| **R5 · Entregables** — vídeo, documento, despliegue, ZIP | Sin empezar | 15% |

> **Lectura honesta:** las 3 historias de usuario están **cerradas de punta a punta** y
> verificadas con 133 tests. Lo que falta ya no es código de producto: es
> **desplegarlo y grabarlo**. El jurado no nos ve en vivo — *lo que no sale en el
> vídeo, para el jurado no existe.*

---

## ✅ Lo que funciona hoy (verificado, no asumido)

### El ciclo de vida del lead está cerrado de punta a punta

```
ANÓNIMO ──▶ IDENTIFICADO ──▶ CALIFICADO ──▶ EDUCADO ──▶ CONSENTIDO
(chat)      (email)          (score+ruta)   (quiz)      (por finalidad)
                                                             │
                                                             ▼
                                            OPORTUNIDAD + ACCIÓN PROPUESTA (pendiente)
                                                             │
══════════════════ ● LÍNEA ROJA ═════════════════════════════╪══════════
                                                             ▼
                                                  CARLOS (humano) aprueba
```

- **Chat** (`/api/chat/*`): cada mensaje despierta al núcleo agéntico. El tutor
  responde **solo con el corpus aprobado y cita la fuente**; si no hay respaldo,
  dice que no sabe (G2). Quiz determinista de 3 preguntas. Dos casillas de
  consentimiento, sin premarcar. La conversación sobrevive a cerrar el navegador.
- **Al consentir**, el lead entra al CRM (upsert idempotente por email) y el sistema
  genera **automáticamente**: señales → score → ruta → oportunidad → **AccionPropuesta
  pendiente**. La consola ya no muestra campos nulos.
- **Consola** (`/api/consola/*`): pipeline priorizado, score en 4 barras con su
  justificación, **brief con la necesidad y las objeciones** del prospecto,
  razonamiento del agente, y **aprobar · editar y aprobar · rechazar**.

### El foso: el human-in-the-loop está completo (criterio 3.3)

Carlos abre el borrador que redactó el agente y puede:

| Acción | Qué queda registrado |
|---|---|
| **Aprobar** | `estado = aprobada` · el lead pasa a `derivado` |
| **Editar y aprobar** | `estado = editada_y_aprobada` · se guarda `borrador_final` (**lo que realmente salió**) · se conserva el borrador original del agente para poder compararlos · **`editado_por_humano = true`** |
| **Rechazar** | `estado = rechazada` + motivo · el lead vuelve a `nutricion` (**no se descarta**) |

> *"El agente nunca tuvo la capacidad de enviarlo. Lo envió Carlos, y queda
> registrado que fue él."*

El sistema **no censura** al asesor habilitado: lo hace **responsable**. Y editar el
borrador **no permite sortear el bloqueo**: sin consentimiento comercial sigue
devolviendo **403** (hay un test que lo intenta).

### Los 5 principios, verificables en el código

| # | Principio | Dónde se verifica |
|---|---|---|
| 1 | El LLM extrae. **El código calcula.** | `app/scoring.py` no importa ningún SDK de LLM. **María = 88, Andrés = 65** (los números exactos de la Biblia §5.6) |
| 2 | **Sin fuente, no hay afirmación.** | `buscar_conocimiento` vacío → G2 negativa honesta |
| 3 | El agente **no tiene manos**. | No existe `enviar_correo`. La acción nace `pendiente` y solo Carlos la mueve |
| 4 | Consentimiento **por finalidad**. | Dos filas independientes; sin la comercial, aprobar → **HTTP 403** |
| 5 | Un instrumento diagnóstico **no lo improvisa una IA**. | `config/quiz_perfil_riesgo.yaml` + rúbrica fija |

### Guardrails (25 % de la nota) — los 8, implementados

`G1` no-asesoramiento (entrada) · `G1-bis` no-asesoramiento (**salida de T11**) ·
`G2` negativa honesta · `G3` consentimiento · `G4` minimización de datos ·
`G5` segregación de superficies · `G6` alcance temático · `G7` cifras deterministas ·
`G8` **cada disparo genera un `EventoAuditoria`**.

### Las preguntas son CONFIGURABLES (criterio 1.1)

El agente **no improvisa** las preguntas de calificación: las lee de
`config/preguntas_b2c.yaml` y `config/preguntas_b2b.yaml` (T2 · código puro).
Cambiar una pregunta es **editar un YAML** — no tocar código.

Y nunca repite una pregunta: ni las ya contestadas, ni las ya formuladas. Si el
prospecto responde algo que el extractor no logra mapear ("mmm, no sé"), el agente
**avanza** en vez de quedarse en bucle.

```
B2C: objetivo → monto → horizonte → experiencia → [quiz] → email → consentimiento
B2B: objetivo → colaboradores → presupuesto → horizonte → email → consentimiento
     (B2B no lleva quiz: el perfil de riesgo es personal — Biblia §2.5)
```

---

## 🔧 Cambios de esta sesión

### 1. Brief + AccionPropuesta automáticos al consentir
(`prompt_brief_accion_propuesta.md`)

Al entrar al CRM, `app/routers/chat.py` ejecuta un enriquecimiento **100 % determinista**
(cero LLM): infiere señales del historial (monto, horizonte, experiencia, pidió-asesor,
quiz, **necesidad y objeciones**), calcula score y ruta, avanza la etapa del embudo,
actualiza la oportunidad y genera la **AccionPropuesta pendiente** con su
**razonamiento** y sus **fuentes**.

> Sin evidencia en el historial → `None`. **Prohibido adivinar** (Biblia §4.2).

### 2. Cerrados los pendientes 2, 4, 5 y 9

| # | Qué faltaba | Qué se hizo |
|---|---|---|
| **2** | *"Editar y aprobar"* **no persistía**: `/aprobar` no aceptaba cuerpo, la edición se perdía y la bitácora no podía registrar quién la cambió | El endpoint acepta `{asunto, cuerpo}`. Nuevas columnas `borrador_final`, `editado_por_humano`, `revisado_en`. **El foso está completo** |
| **9** | `EstadoAccion` no tenía `editada_y_aprobada` (la Biblia §4.6 sí lo define) | Añadido al enum. Era la base del punto 2 |
| **4** | `config/preguntas_*.yaml` existía pero **el agente no lo leía**: las preguntas las improvisaba el LLM → el criterio 1.1 no se cumplía | Nueva tool `obtener_preguntas.py` (T2). El agente sirve las preguntas del YAML, sin repetirlas, y enruta B2C→quiz / B2B→email |
| **5** | El brief no tenía **objeciones** ni **necesidad** → la ficha salía a medias | Nueva tool `inferir_senales.py` (código puro) que las extrae del historial. Columnas `necesidad` y `objeciones` en `leads_v2` |

### 3. 🚨 Cuatro fallos que habrían roto la demo (encontrados y corregidos)

| # | Fallo | Consecuencia si no se corrige |
|---|---|---|
| 1 | `TipoAccion` no incluía los tipos de la Biblia §4.6 (`agendar_reunion`…). `consola.py` hace `TipoAccion(a.tipo)` → `ValueError` | **HTTP 500** en `GET /api/consola/leads/{id}/acciones`. La consola entera caía |
| 2 | El endpoint de consentimiento **nunca creaba la fila `Consentimiento`** (solo eventos de auditoría) | La consola leía "no consintió" y **bloqueaba el botón Aprobar incluso a quien SÍ consintió** |
| 3 | `seed.py` creaba 12 leads **sin ninguna `AccionPropuesta`** | La consola caía a un borrador de respaldo con id `"acc_1"` → `Number("acc_1")` = `NaN` → **aprobar a María fallaba**. El clímax del vídeo (2:30–2:45) |
| 4 | El build del frontend **estaba roto** (`Banda` incluía `critico`, los componentes solo mapeaban 3) | **Vercel no habría desplegado.** `npm run build` fallaba |

### 4. Huecos de contrato cerrados

- `AccionPropuesta` ganó `asunto`, `razonamiento`, `fuentes_consultadas`,
  `borrador_final`, `editado_por_humano` y `revisado_en` (Biblia §4.6).
  Migraciones: `add_accion_razonamiento.sql` y `add_brief_y_edicion_humana.sql`.
- `LeadV2` ganó `necesidad` y `objeciones` (Biblia §4.1) — el brief de Carlos.
- `ruta_sugerida` ahora llega a la ficha (el *"para que"* de la HU1).
- CV7: el agente dice **cuándo** contactarán ("en las próximas 24 horas hábiles").
- Un solo sitio genera propuestas (`app/propuestas.py`), usado por el chat **y** el
  seed: así los datos de demo y los reales no divergen.

### 5. Cambios de R1 aplicados
- `buscar_conocimiento`: keywords de **≥ 3 letras** — `"etf"` tiene exactamente 3 y
  se estaba descartando; el RAG no encontraba FA-006, *la pregunta de la demo*.
- `servicio_agente`: un saludo ambiguo ya no dispara un G2 innecesario.

---

## 🔎 Verificación ejecutada

| Prueba | Resultado |
|---|---|
| `pytest app/tests tests/` | **133 pasan** |
| **Editar y aprobar** (criterio 3.3) | `editada_y_aprobada` · `editado_por_humano = true` · se guarda lo que **realmente salió** y se conserva el borrador del agente · bitácora con nombre y hora |
| **Editar ≠ sortear el bloqueo** | Editar el borrador de Sofía y aprobar → sigue **403** |
| Rechazar | El lead vuelve a `nutricion` — **no se descarta** |
| **Preguntas configurables** (criterio 1.1) | B2C sirve **4/4** preguntas desde `config/`, B2B **3/4**, **cero repeticiones**, y no entra en bucle si no entiende la respuesta |
| **B2B no se rompe** (un juez lo va a probar) | *"Represento a una empresa de 100 empleados"* → badge **B2B**, sin quiz, → `derivar_a_ventas_corporativas` |
| **Brief** (criterio 3.1) | necesidad + **objeciones** reales ("Le preocupa perder dinero") |
| E2E chat → consentimiento → consola | María: score **89**, ruta `asesoria_inversion`, acción con razonamiento real → **aprobar 200** |
| Caso Sofía (sin consentimiento comercial) | Acción **existe** (para mostrar el bloqueo) → **aprobar 403** |
| Segregación de superficies | El chat **no filtra** score/brief/bitácora |
| `seed.py` | 12 leads, **idempotente**. **María 88 · Andrés 65** — los números exactos de la Biblia §5.6 |
| `npm run build` (frontend) | **Compila** (antes fallaba) |
| API key real de OpenRouter | **Funciona**: el tutor responde con el LLM y **cita FA-006** |

---

## 🚨 Puntos pendientes (por prioridad)

> Los antiguos puntos **2, 4, 5, 6 y 9 están CERRADOS** (ver "Cambios de esta sesión").
> El alcance mínimo del Track 1 está completo. Lo que queda es sacarlo a producción
> y grabarlo.

### 🔴 Bloqueantes

1. **DESPLIEGUE VIVO — el riesgo nº 1 del equipo. Dueño: R2.**
   No existe todavía. El Contrato de Stack §9 lo pedía en H4 *sin excepción*, y la
   Biblia lo marca como riesgo X1. **Sin esto no hay entregable.**
   - Backend → Railway · Frontend → Vercel (Root Directory = `web`) · BD → Neon.
   - Definir `NEXT_PUBLIC_API_URL` en Vercel o el frontend no habla con nadie.
   - ⚠ En una BD **ya existente**, `create_all` **no añade columnas**: hay que correr
     los `.sql` de `backend/migrations/` (los dos nuevos incluidos).
   - Tras desplegar: `python -m app.seed` una vez, o la consola sale vacía.

2. **Entregables (R5)** — vídeo 3:00, documento explicativo PDF, ZIP sin claves,
   repo público, los 5 enlaces. **Sin esto hay descalificación**, aunque el código
   sea perfecto.

### 🟡 Deuda técnica / trampas conocidas

3. **`psycopg2` vs `psycopg` v3** — `requirements.txt` trae `psycopg2-binary`, que el
   Contrato de Stack §3 marca como **incompatible con `langgraph-checkpoint-postgres`**.
   Hoy no rompe nada porque el grafo usa `MemorySaver`; **romperá** el día que se
   migre a `PostgresSaver`. Para el despliegue actual, `DATABASE_URL` debe usar
   `postgresql://` (psycopg2), **no** `postgresql+psycopg://`.

4. **Continuidad**: hoy la da el historial persistido en la BD (funciona y se puede
   grabar). La versión canónica de LangGraph (`PostgresSaver` + `thread_id`) sigue
   pendiente — ver punto 3 antes de intentarlo.

5. **`test_reintentos.py`** requiere `google-genai` instalado; falla solo en entornos
   mínimos. No es una regresión.

6. **`TipoAccion` conserva valores legacy** (`llamada`, `email`, `reunion`…) junto a
   los 4 de la Biblia, para no invalidar filas ya persistidas. El agente solo genera
   los de la Biblia.

### 🔒 Secretos

La `OPENROUTER_API_KEY` **fue rotada**: la clave que se compartió en texto plano por
WhatsApp está revocada y sustituida. Vive solo en `backend/.env`, que está
gitignoreado (verificado) y **no está trackeado por git**.

> Al preparar el ZIP de la entrega: comprobar que **no** va ningún `.env` dentro.
> *"Ningún secreto en el repo. Nunca. Ni en el ZIP."* (Biblia §21.5)

---

## ▶️ Cómo correr el proyecto

### Backend

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # rellena las claves (DATABASE_URL puede ser sqlite:///./dev.db)
python -m app.seed            # 12 leads de demo, con score y acción propuesta
uvicorn app.main:app --reload
# Contrato interactivo: http://localhost:8000/docs
```

Sin `OPENROUTER_API_KEY` el chat **sigue funcionando**: responde con el corpus
aprobado (RAG determinista) y aplica los guardrails. Nunca lanza 500.

### Frontend

```bash
cd web
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
# Chat del prospecto: http://localhost:3000/chat
# Consola del ejecutivo: http://localhost:3000/consola
```

### Tests

```bash
cd backend && pytest app/tests tests/ -q     # 133 tests
```

Los que sostienen la tesis ante el jurado:

| Test | Qué demuestra |
|---|---|
| `tests/test_score.py` | Mismo input → mismo score. **María = 88 · Andrés = 65** |
| `tests/test_quiz.py` | El quiz es determinista. Cero LLM |
| `tests/test_guardrails*.py` | G1 · G1-bis · G2 · G5 · G6 · G7 |
| `tests/test_preguntas_configurables.py` | Las preguntas salen de `config/`, no se repiten, y **B2B no se rompe** |
| `tests/test_servicio_agente.py` | El agente corre **sin la API del LLM** (mockeado) |
| `app/tests/test_aprobacion_humana.py` | **Aprobar · editar y aprobar · rechazar**, y que editar **no sortea** el bloqueo |
| `app/tests/test_superficies.py` | El endpoint público **no devuelve** score, brief ni otros leads |
| `app/tests/test_consentimiento.py` | Sin consentimiento no hay CRM ni aprobación |
| `app/tests/test_upsert_idempotente.py` | Dos veces el mismo email → **un** contacto |

---

## 🗺️ Arquitectura

```
NAVEGADOR (TypeScript)          web/app/chat  ·  web/app/consola
        │ HTTP + JSON
SERVIDOR (Python — UN SOLO PROCESO)
   app/      (R2 · FastAPI)  ──importa──▶  core/ + tools/  (R1 · el agente)
   app/crm   (CRMPort)                     core/guardrails/ (G1–G8)
        │
   PostgreSQL / SQLite
```

**Regla sagrada:** `core/` no importa nada de `app/` ni de `web/`.
Dirección de dependencia: `app/ → core/ → tools/ → schemas/`. Nunca al revés.

---

*Agentic Scale 2026 · Ecuador Tech Week · ESPOL · Track 1 — Futuro Academy*
