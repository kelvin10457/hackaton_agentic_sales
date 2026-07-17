# Futuro Academy — Agente Comercial con Frenos

> *No es un chatbot con un CRM detrás. Es un agente con frenos.*

**Futuro Academy** es un agente conversacional de IA (desarrollado para el Agentic Scale · Ecuador Tech Week 2026, Track 1) que **capta, califica y educa prospectos 24/7** — y **nunca envía una comunicación ni cruza una línea regulada sin la aprobación de un humano**, manteniendo una traza auditable de cada decisión.

---

## 🚀 El Problema y Nuestra Tesis

Futuro Academy (el brazo educativo de una institución financiera) pierde prospectos porque nadie los atiende fuera del horario laboral. Y no puede simplemente poner un chatbot genérico a hablar solo con ellos: en el sector financiero, **una respuesta inventada sobre un producto de inversión no es un bug, es un problema legal**.

**Nuestra solución:** Separar rigurosamente lo que un modelo de lenguaje hace bien (entender lenguaje natural, extraer señales estructuradas, redactar borradores) de lo que *jamás* debe hacer por sí solo (calcular una prioridad comercial, afirmar un hecho financiero, decidir si enviar una comunicación a un titular de datos).

### Los 5 principios de diseño (verificables en código)
1. **El LLM extrae señales. El código calcula.** El score de prioridad se calcula mediante una función pura determinista y testeable.
2. **Sin fuente, no hay afirmación.** Ninguna respuesta factual se emite sin citar directamente los fragmentos extraídos del corpus de conocimiento.
3. **El agente no tiene manos para cruzar la línea roja.** No existe una función `enviar_correo` en el catálogo de herramientas del agente. La contención es estructural (ausencia de código), no dependiente de un *prompt*.
4. **El consentimiento es por finalidad, no un checkbox.** Existen consentimientos distintos y separados (tratamiento de datos y comunicaciones). Si falta el de comunicaciones, el botón de "Aprobar" en la consola queda bloqueado por código.
5. **Un instrumento diagnóstico no lo improvisa una IA.** El quiz para definir el perfil de riesgo es determinista, con preguntas y una rúbrica fija predefinida.

---

## 🧠 Arquitectura y Stack Tecnológico

El proyecto se diseñó bajo una premisa arquitectónica estricta ("lógica separada de la interfaz"), donde el núcleo agéntico nunca se mezcla con la capa de presentación. 

### Stack Principal
- **Núcleo Agéntico:** Python 3.11 y **LangGraph 0.2** (grafo de estados y persistencia `langgraph-checkpoint-postgres`). *Nota: No usamos LangChain para garantizar determinismo absoluto; el modelo solo extrae señales y redacta, mientras el grafo elige el flujo.*
- **LLM:** **DeepSeek** vía **OpenRouter** (`deepseek-chat-v3`) para clasificación rápida, extracción de señales, síntesis y redacción de borradores.
- **Backend & Contratos:** **FastAPI + Uvicorn** segregado en dos superficies (Pública/Chat e Interna/Consola). **Pydantic v2** actúa como fuente de la verdad para contratos tipados generados automáticamente a TypeScript (OpenAPI).
- **Persistencia y Datos:** **SQLite** (entorno de desarrollo local) y **PostgreSQL** usando **SQLAlchemy 2.0 + psycopg2-binary**.
- **Frontend (Chat & Consola):** Un solo proyecto web en **Next.js 14**, **React 18**, **Tailwind CSS 3.4**, y **shadcn/ui**.
- **Despliegue:** Backend en Railway, Frontend en Vercel, Base de datos en Neon.

### Flujo de Human-In-The-Loop (HITL)
El agente maneja el ciclo de vida del prospecto integrando un proceso de contención y aprobación humana inquebrantable:

```text
ANÓNIMO ──▶ IDENTIFICADO ──▶ CALIFICADO ──▶ EDUCADO ──▶ CONSENTIDO
(chat)      (email)          (score+ruta)   (quiz)      (por finalidad)
                                                             │
                                                             ▼
                                            OPORTUNIDAD + ACCIÓN PROPUESTA (pendiente)
                                                             │
══════════════════ ● LÍNEA ROJA (Human-In-The-Loop) ═════════╪══════════
                                                             ▼
                                                  CARLOS (asesor) aprueba / edita / rechaza
```

### Calificación conversacional (no un formulario disfrazado)

La calificación **no** es un banco de preguntas lineal. El agente:
- **Se presenta y pide el nombre** de forma orgánica (identificación progresiva, no un formulario de registro), y lo usa durante la charla. El nombre entra al CRM — no el prefijo del correo.
- **Atribuye cada respuesta a su pregunta**: `10 000` a "¿con qué monto?" es un monto; `no` a "¿has invertido antes?" es *sin experiencia*. Acepta `10k`, `diez mil`, `$10.000`, `3 meses`, etc.
- **Acusa recibo** de cada dato con plantillas deterministas ("Anotado, Kenny: USD 10.000") — cero LLM tocando cifras (G7).
- Ante una respuesta incoherente, **aclara una vez y avanza**; nunca entra en bucle.
- **Responde las dudas educativas en cualquier momento** (con cita del corpus), y luego retoma el embudo. Si pides el quiz por texto, se abre el quiz real (nunca uno improvisado por el LLM — guardrail **G-QUIZ**).
- Nombre y correo son **opcionales**: negarse no degrada el servicio.

Las preguntas viven en `config/preguntas_b2c.yaml` / `preguntas_b2b.yaml` (criterio 1.1 "configurables"): cambiar una es editar el YAML, sin tocar código.

---

## 🛡️ Defensa en Profundidad: Guardrails

La alucinación en educación financiera se traduce en una recomendación de inversión no autorizada. Nuestra defensa consta de 8 capas (*Guardrails*):

- **G1 (No-asesoramiento):** Si el prospecto solicita en qué invertir, el agente se niega mediante reglas estrictas y un clasificador, redirigiendo la consulta.
- **G1-bis (Censura en salida):** El borrador de correo redactado (T11) se valida antes de presentarse en la consola; nunca puede nombrar un producto financiero explícito.
- **G2 (Negativa honesta):** Sin resultados relevantes en la base vectorial sobre el corpus, el agente devuelve una negativa en lugar de aproximar o inventar ("No lo sé").
- **G3 (Consentimiento - LOPDP):** Bloqueos a nivel de Backend. Sin tratamiento de datos, no hay entrada al CRM. Sin consentimiento de comunicación, el humano no puede aprobar envíos.
- **G4 (Negarse no degrada el servicio):** Si el usuario niega datos, el agente sigue educándolo (mantiene la conversión por aportar valor).
- **G5 (Inyección de instrucciones):** Protecciones de sanitización de roles y contexto.
- **G6 (Salida sin fuente):** Cualquier afirmación del tutor que no incluya sus `fuentes[]` tipadas no es emitida.
- **G7 (Cifras no deterministas):** El score o validaciones numéricas operan mediante lógica dura en Python, no generadas textualmente por el LLM.
- **G8 (La Línea Roja Estructural):** La mejor defensa: ausencia total del código capaz de efectuar acciones en el mundo real hasta ser aprobado en consola.

---

## 👥 Dos Embudos de Negocio

El sistema se bifurca dinámicamente según quién interactúe:
- **Flujo B2C (Ej: María):** Solicitud de cédula. Incluye quiz de perfil de riesgo personal, cálculo de experiencia y monto. Acción propuesta: *Agendar Reunión / Enviar Material*.
- **Flujo B2B (Ej: Andrés):** Solicitud de RUC y datos de empresa. Se valora según colaboradores y presupuesto. No aplica test de perfil de riesgo personal. Acción propuesta: *Derivar a Ventas Corporativas*.

---

## ⚙️ Cómo Ejecutar el Proyecto (Setup Local)

### 1. Variables de Entorno
Configura los archivos `.env` respectivos.

Para el backend, crea un archivo `.env` dentro de la carpeta `backend/`:
```env
DATABASE_URL=sqlite:///./dev.db

# ── JWT de usuarios ejecutivos (/api/consola/*) ──────────────────────────────
SECRET_KEY=b35522f20ab21a6f85a2c6345e24e8ecacbe76abdeb2e3e6881ec86a07022af4
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ── Token de sesión del chat público (/api/chat/*) ───────────────────────────
CHAT_TOKEN_SECRET=e0d3f39683c56f2ce8d085f3ee94fac9f4d98d656ae590634cf2331b55365284
CHAT_TOKEN_EXPIRE_HOURS=24

# ── LLM del núcleo agéntico (R1) ─────────────────────────────────────────────
OPENROUTER_API_KEY=sk-or-v1-tu_clave
```

Para el frontend, crea un archivo `.env.local` dentro de la carpeta `web/`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Levantar el Backend (FastAPI + LangGraph)
En la raíz del proyecto:
```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

### 3. Levantar el Frontend (Next.js)
El frontend contiene tanto la vista pública del chat (`/chat`) como la consola interna para el ejecutivo (`/consola`).
```bash
cd web
npm install

# Generar tipados estrictos TypeScript desde el OpenAPI del backend (FastAPI)
npm run types 

# Correr entorno de desarrollo
npm run dev
```

### 4. Tests Automatizados
Corremos un set robusto de pruebas locales con el LLM mockeado para poder iterar validando lógica crítica (**143 pruebas**: scoring determinista, quiz, ruta, los 8+ guardrails, segregación de superficies, aprobar/editar/rechazar, y el flujo conversacional end-to-end con el guión real de testing).
```bash
# Desde backend/ con el entorno virtual activado
cd backend
pytest app/tests tests/ -q
```
> Las decisiones de alcance que pueden parecer bugs pero son intencionales están documentadas en [`docs/DECISIONES_DEMO.md`](docs/DECISIONES_DEMO.md).

---

> **Agentic Scale · Ecuador Tech Week 2026 · Club TAWS · ESPOL**
