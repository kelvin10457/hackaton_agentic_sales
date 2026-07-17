# Decisiones de demo — qué parece una falla pero es a propósito

> Guía para el equipo antes del vídeo y el Q&A del jurado. Cada punto es una
> decisión **deliberada**, no un bug pendiente. Aquí está el porqué y **cómo
> defenderlo en una frase** si un juez lo señala.

El principio que las une: **un demo honesto muestra los frenos, no los esconde.**
Varias de estas "limitaciones" son en realidad el argumento del producto.

> ⚠️ Este documento describe el comportamiento **actual** (v2). Si algo aquí no
> coincide con lo que ves, es que estás sobre una build vieja.

---

## 1. El quiz es SIEMPRE el mismo (no cambia según la pregunta)

**Qué se ve:** preguntas por "¿qué es un ETF?" y, si pides el quiz, sale el
cuestionario de **perfil de riesgo** — el mismo, no uno sobre ETFs.

**Por qué es a propósito:** el quiz es un **instrumento diagnóstico**, no un
trivia por tema. Es uno de nuestros 5 principios: *"un instrumento diagnóstico no
lo improvisa una IA"*. Vive fijo en `config/quiz_perfil_riesgo.yaml`, con rúbrica
determinista. Que sea reproducible es la gracia: mismas respuestas → mismo perfil.

> **Defensa:** *"En finanzas, un test de idoneidad lo aprueba cumplimiento, no lo
> inventa un modelo en cada conversación."* Hay un guardrail (**G-QUIZ**) que
> **impide** que el LLM se ponga a improvisar preguntas de riesgo.

## 2. Respuestas incoherentes ("eyruieo") → el lead sale frío

**Qué se ve:** si contestas basura a "¿con qué monto empezarías?", el agente
avanza pero esa señal no suma puntos.

**Por qué es a propósito:** *"El LLM extrae, el código calcula"* (G7). El extractor
determinista **no adivina**: si la respuesta no es un dato válido, la señal queda
en `None` y la rúbrica no suma. Eso protege al equipo de ventas de leads basura.

> **Ojo — esto NO es lo mismo que el bug ya corregido:** antes, respuestas
> **válidas** como `10 000`, `3 meses` o `no` tampoco se entendían y TODOS
> salíamos fríos. Eso **ya está arreglado** (ver la lista final). Hoy solo sale
> frío quien de verdad no aporta señales.

## 3. En "comunicaciones" solo pedimos correo (no correo/celular/ambos)

**Por qué es a propósito:** un solo canal = **consistencia de datos** garantizada.
Teléfono + "ambos" multiplica estados y errores justo en la parte regulada
(consentimiento). Preferimos un flujo impecable a uno vistoso con inconsistencias.

> **Defensa:** *"El consentimiento es la pieza legal; ahí priorizamos corrección
> sobre features. Añadir canales es cambiar un enum, no la arquitectura."*

## 4. Los botones alternativos del lead bloqueado muestran un aviso, no ejecutan

**Qué se ve:** en Sofía (sin consentimiento comercial), teléfono / material /
pedir-consentimiento lanzan un toast.

**Por qué es a propósito:** lo que gana el criterio es **el bloqueo**, no las
alternativas. Son la prueba de que el consentimiento es *por finalidad*: un lead
sin consentimiento comercial no es basura, es un prospecto con restricción de
canal.

> **Defensa:** *"El botón Aprobar bloqueado —y el 403 del backend detrás— es el
> plano estrella. Las alternativas señalan que el lead sigue siendo válido."*

## 5. El agente NO envía correos de verdad ("envío simulado")

**Por qué es a propósito:** **es toda la tesis.** *"El agente no tiene manos para
cruzar la línea roja."* No existe la función `enviar_correo`: la línea roja no es
un prompt, es la **ausencia de la herramienta**.

> **Defensa:** *"El agente nunca tuvo la capacidad de enviarlo. Lo envió Carlos, y
> queda registrado que fue él."* Es una **fortaleza**, no una carencia.

## 6. El login de la consola acepta cualquier email/contraseña (stub)

**Por qué es a propósito:** **AuthN ≠ AuthZ.** La identidad (login real) es de
Futuro Academy; la consumimos detrás de un `IdentityPort`. En la demo es un stub
para no montar un SSO.

> **Defensa:** *"Futuro ya tiene identidad. Nuestro agente se enchufa detrás de
> tres puertos —Identidad, CRM, Conocimiento— sin cambiar el núcleo."*

## 7. El CRM es simulado (no HubSpot/Salesforce real)

**Por qué es a propósito:** `CRMSimulado` implementa el mismo `CRMPort` que
implementaría el CRM corporativo. La consola de la demo ES ese CRM llenándose.

> **Defensa:** *"Cambiar el CRM simulado por el corporativo es implementar una
> interfaz. El núcleo agéntico no cambia ni una línea."*

## 8. La búsqueda del corpus es por palabras clave, no embeddings

**Por qué es a propósito:** son **15 documentos** (14 temas + un índice). Una base
vectorial para 15 archivos es sobre-ingeniería que no aporta. La búsqueda **tolera
variantes** (sin tildes, plural/singular, prefijos y sinónimos del dominio: "riesgos"
encuentra "perfil de riesgo"), así que ya no exige la palabra literal. La cita al
corpus y la negativa honesta (G2) siguen funcionando igual.

> **Defensa:** *"No sobre-ingenierizamos: para 15 documentos, una recuperación léxica
> tolerante + citas es más simple, más rápida e igual de verificable que embeddings."*

## 9. La continuidad usa el historial guardado en la BD

**Qué se ve:** cierras el navegador, reabres, y la conversación sigue.

**Por qué es a propósito:** el token vive en `localStorage` y el historial se
persiste tras cada turno. El checkpointer nativo de LangGraph (`PostgresSaver`)
es la versión "canónica" y queda como mejora, pero la continuidad ya se graba.

## 10. Nombres tipo "Correito" o "Jdpooveda" en el pipeline

**Por qué:** son leads creados por **los propios testers ANTES del fix** de
identificación progresiva — el agente no pedía el nombre y usaba el prefijo del
correo. **Ya está corregido:** ahora pide *"¿cómo te llamas?"* y guarda el nombre
real. Los leads nuevos salen bien; los viejos son datos de prueba.

> **Defensa:** *"Eran leads de testing previos al fix."* Se limpian corriendo
> `python -m app.seed` sobre una BD fresca.

## 11. El nombre y el correo NO son obligatorios

**Por qué es a propósito:** **el consentimiento debe ser libre** (LOPDP). Si
castigamos al usuario quitándole el servicio, deja de ser libre. El tutor sigue
funcionando aunque no consienta nada.

> **Defensa:** *"Si negarse costara el servicio, el consentimiento no sería libre.
> Ese es nuestro diferenciador legal."*

---

## Lo que NO es decisión de demo — ya se corrigió (mostrarlo funcionando)

Estos eran fallos reales del testing y **están arreglados**:

- El agente **pide el nombre** y el CRM guarda el nombre real, no el prefijo del correo.
- `10 000`, `3 meses`, `no` ahora **se entienden** → el lead sale caliente, no frío.
- El agente **acusa recibo** de cada dato ("Anotado, Kenny: USD 10.000") y usa el nombre.
- Ante respuestas incoherentes, **aclara una vez y avanza** (nunca en bucle).
- El tutor **responde las dudas educativas** aunque estés a mitad del embudo.
- La tarjeta de correo tiene **"Ahora no"**, se cierra al escribir y no reaparece.
- **Aprobar / editar y aprobar / rechazar** funcionan; los errores se leen (no `[object Object]`).
- Tras aprobar, los botones **se bloquean** y se muestra la resolución.
- Un solo botón adaptativo: **"Aprobar envío"** ↔ **"Editar y aprobar"**.
- Guardrails nuevos: **inyección de instrucciones (G5)** y **actividades ilícitas (G6)**.
- Sidebar con enlaces reales, chip "Conectado exitosamente", sin franjas blancas al hacer scroll.
