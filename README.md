# Futuro Academy — Agente con frenos

> *No es un chatbot con un CRM detrás. Es un agente con frenos.*

Agente de IA que capta, califica y educa prospectos 24/7 — y **nunca envía una
comunicación ni cruza una línea regulada sin la aprobación de un humano**, con
traza auditable de cada decisión.

---

## 📊 PROGRESO GLOBAL: **72 / 100**

```
Código y producto   ██████████████████░░  90%   ← el agente funciona de punta a punta
Despliegue vivo     ░░░░░░░░░░░░░░░░░░░░   0%   ← 🚨 RIESGO CRÍTICO (Contrato de Stack §9)
Entregables (R5)    ███░░░░░░░░░░░░░░░░░  15%   ← vídeo, doc explicativo, ZIP, 5 enlaces
────────────────────────────────────────────────
GLOBAL PONDERADO    ██████████████░░░░░░  72%
```

| Bloque | Estado | % |
|---|---|---|
| **R1 · Núcleo agéntico** — grafo, tools, guardrails G1–G8 | Completo | 92% |
| **R2 · Backend / Datos / CRM** — contratos, API, bitácora, semillas | Completo | 92% |
| **R3 · Chat del prospecto** — tutor con citas, quiz, consentimiento, continuidad | Completo | 95% |
| **R4 · Consola del ejecutivo** — pipeline, score, brief, aprobar/rechazar | Falta *editar* | 85% |
| **R5 · Entregables** — vídeo, documento, despliegue, ZIP | Sin empezar | 15% |

> **Lectura honesta:** el producto está construido y verificado. Lo que falta ya no
> es código de producto: es **desplegarlo y grabarlo**. El jurado no nos ve en vivo —
> *lo que no sale en el vídeo, para el jurado no existe.*

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
  justificación, brief, razonamiento del agente, y **aprobar / rechazar**.

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

---

## 🔧 Cambios de esta sesión

### 1. Implementado: brief + AccionPropuesta automáticos al consentir
(`prompt_brief_accion_propuesta.md`)

Al entrar al CRM, `app/routers/chat.py` ahora ejecuta un enriquecimiento
**100 % determinista** (cero LLM): infiere señales del historial (monto, horizonte,
experiencia, pidió-asesor, quiz), calcula score y ruta, avanza la etapa del embudo,
actualiza la oportunidad y genera la **AccionPropuesta pendiente** con su
**razonamiento** y sus **fuentes**.

> Sin evidencia en el historial → `None`. **Prohibido adivinar** (Biblia §4.2).

### 2. 🚨 Cuatro fallos que habrían roto la demo (encontrados y corregidos)

| # | Fallo | Consecuencia si no se corrige |
|---|---|---|
| 1 | `TipoAccion` no incluía los tipos de la Biblia §4.6 (`agendar_reunion`…). `consola.py` hace `TipoAccion(a.tipo)` → `ValueError` | **HTTP 500** en `GET /api/consola/leads/{id}/acciones`. La consola entera caía |
| 2 | El endpoint de consentimiento **nunca creaba la fila `Consentimiento`** (solo eventos de auditoría) | La consola leía "no consintió" y **bloqueaba el botón Aprobar incluso a quien SÍ consintió** |
| 3 | `seed.py` creaba 12 leads **sin ninguna `AccionPropuesta`** | La consola caía a un borrador de respaldo con id `"acc_1"` → `Number("acc_1")` = `NaN` → **aprobar a María fallaba**. El clímax del vídeo (2:30–2:45) |
| 4 | El build del frontend **estaba roto** (`Banda` incluía `critico`, los componentes solo mapeaban 3) | **Vercel no habría desplegado.** `npm run build` fallaba |

### 3. Huecos de contrato cerrados

- `AccionPropuesta` ganó `asunto`, `razonamiento` y `fuentes_consultadas`
  (Biblia §4.6). Antes la consola mostraba `"agente:cv5"` como razonamiento —
  el criterio 3.2 pide *"acción propuesta con razonamiento visible"*.
  Migración: `migrations/add_accion_razonamiento.sql`.
- `ruta_sugerida` ahora llega a la ficha (el *"para que"* de la HU1).
- CV7: el agente dice **cuándo** contactarán ("en las próximas 24 horas hábiles").
- Un solo sitio genera propuestas (`app/propuestas.py`), usado por el chat **y** el
  seed: así los datos de demo y los reales no divergen.

### 4. Cambios de R1 aplicados
- `buscar_conocimiento`: keywords de **≥ 3 letras** — `"etf"` tiene exactamente 3 y
  se estaba descartando; el RAG no encontraba FA-006, *la pregunta de la demo*.
- `servicio_agente`: un saludo ambiguo ya no dispara un G2 innecesario.

---

## 🔎 Verificación ejecutada

| Prueba | Resultado |
|---|---|
| `pytest app/tests tests/` | **118 pasan** |
| E2E chat → consentimiento → consola | María: score **89**, ruta `asesoria_inversion`, acción `agendar_reunion` con razonamiento real → **aprobar 200** |
| Caso Sofía (sin consentimiento comercial) | Acción **existe** (para mostrar el bloqueo) → **aprobar 403** |
| Segregación de superficies | El chat **no filtra** score/brief/bitácora |
| `seed.py` | 12 leads, **idempotente** (2ª corrida: 0 duplicados). **María 88 · Andrés 65** — los números exactos de la Biblia |
| `npm run build` (frontend) | **Compila** (antes fallaba) |
| API key real de OpenRouter | **Funciona**: el tutor responde con el LLM y **cita FA-006** |

---

## 🚨 Puntos pendientes (por prioridad)

### 🔴 Bloqueantes

1. **DESPLIEGUE VIVO — el riesgo nº 1 del equipo.**
   No existe todavía. El Contrato de Stack §9 lo pedía en H4 *sin excepción*, y la
   Biblia lo marca como riesgo X1. Sin esto no hay entregable.
   - Backend → Railway · Frontend → Vercel (Root Directory = `web`) · BD → Neon.
   - Definir `NEXT_PUBLIC_API_URL` en Vercel o el frontend no habla con nadie.

2. **"Editar y aprobar" no persiste la edición** — *el foso está a medias.*
   El criterio **3.3** dice: *"el ejecutivo puede aprobar, **editar** o rechazar"*.
   Hoy `ApprovalBlock` deja editar el borrador en pantalla, pero
   `POST /api/consola/acciones/{id}/aprobar` **no acepta cuerpo**: la edición se
   pierde y la bitácora no puede registrar `editado_por_humano = true`.
   - Falta: aceptar `{asunto, cuerpo}` en el endpoint, columnas `borrador_final` +
     `editado_por_humano`, y el estado `editada_y_aprobada` (que **no existe** en el
     enum `EstadoAccion`, aunque la Biblia §4.6 lo define).
   - Es el plano final del vídeo: *"El agente nunca tuvo la capacidad de enviarlo.
     Lo envió Carlos, y queda registrado que fue él."*

3. **Entregables (R5)** — vídeo 3:00, documento explicativo PDF, ZIP sin claves,
   repo público, los 5 enlaces. **Sin esto hay descalificación**, aunque el código
   sea perfecto.

### 🟠 Importantes

4. **Criterio 1.1 — "preguntas configurables"**: existen
   `config/preguntas_b2c.yaml` / `preguntas_b2b.yaml`, pero **el agente no las lee**:
   las preguntas las improvisa el LLM desde `prompts/`. La rúbrica pide que sean
   configurables. Conectar `config/` al turno de calificación.

5. **Brief incompleto (criterio 3.1)**: no se extraen **objeciones** del historial,
   así que la ficha las muestra vacías. `necesidad` es hoy solo el `objetivo`.

6. **Rotar `OPENROUTER_API_KEY`**: se compartió en texto plano por WhatsApp. Está en
   `backend/.env` (gitignoreado, verificado), pero conviene regenerarla.

### 🟡 Deuda técnica / trampas conocidas

7. **`psycopg2` vs `psycopg` v3** — `requirements.txt` trae `psycopg2-binary`, que el
   Contrato de Stack §3 marca como **incompatible con `langgraph-checkpoint-postgres`**.
   Hoy no rompe nada porque el grafo usa `MemorySaver`; **romperá** el día que se
   migre a `PostgresSaver`.

8. **Continuidad**: hoy la da el historial persistido en la BD (funciona y se puede
   grabar). La versión canónica de LangGraph (`PostgresSaver` + `thread_id`) sigue
   pendiente — ver punto 7 antes de intentarlo.

9. **`EstadoAccion`/`TipoAccion` divergen de la Biblia**: `TipoAccion` ya se alineó
   (los valores viejos se conservan por compatibilidad). `EstadoAccion` aún no tiene
   `editada_y_aprobada` (ver punto 2).

10. **`test_reintentos.py`** requiere `google-genai` instalado; falla solo en entornos
    mínimos. No es una regresión.

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
cd backend && pytest app/tests tests/ -q     # 118 tests
```

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
