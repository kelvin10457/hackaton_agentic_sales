# Estado del Proyecto: Agentic Sales (Futuro Academy)

Este documento detalla el progreso actual del equipo de desarrollo frente a lo establecido en la **Biblia de Trabajo v2**, así como las partes críticas que deben resolverse inmediatamente antes de seguir avanzando.

## ✅ Progreso Actual (Lo que ya está listo)

1. **Configuraciones (Dueño: R1)**: 
   - Los archivos en `backend/config/` (`pesos_scoring.yaml`, `preguntas_b2b.yaml`, `preguntas_b2c.yaml`, `quiz_perfil_riesgo.yaml`) están creados y alineados.
2. **Herramientas Deterministas y Tests (Dueños: R1, R5)**:
   - Las herramientas `calcular_score.py`, `obtener_quiz.py` y `calcular_ruta.py` están implementadas en `backend/tools/`.
   - Se encuentran respaldadas por sus respectivos tests unitarios en `backend/tests/`.
3. **Corpus de Conocimiento (Dueño: R5)**:
   - Los 14 documentos (FA-001 a FA-014) ya están redactados en la carpeta `knowledge/`.
4. **Backend, Contratos y API (Dueño: R2)**:
   - **Contratos Pydantic**: R2 ha centralizado los contratos en `backend/app/schemas.py` (23 KB de schemas), cubriendo la sección 4.
   - **Despliegue y Segregación**: La API está estructurada en FastAPI dentro de `backend/app/routers/` con segregación clara entre `/chat` y `/consola`, cumpliendo la sección 4.10.
   - **Adaptadores**: Se han construido los conectores para `crm.py`, `identity.py`, `auditoria.py` en `backend/app/`.
   - **Semilla**: Se ha implementado `seed.py` para sembrar la base de datos de prueba.
5. **Frontend UI (Dueños: R3, R4)**:
   - La base de la interfaz (Chat y Consola) está levantada en `web/app/`. Se han usado mocks temporales (`mocks-consola.ts`) para diseñar el layout maestro-detalle.

---

## 🚨 CRÍTICO: Qué debe arreglarse AHORA (Bloqueantes)

El equipo ha avanzado muchísimo en la infraestructura backend (R2) y en la UI estática (R3/R4). Sin embargo, **el núcleo del agente inteligente (R1) sigue sin existir**, lo cual bloquea la integración final:

### 1. Faltan Orquestador y Estado (Dueño: R1)
- **Problema**: `backend/core/orquestador.py` y `backend/core/estado.py` no han sido creados.
- **Impacto**: No existe la "Máquina de Estados de la Conversación" (Sección 7 de la Biblia). El LLM actualmente no controla el flujo de la conversación, no extrae señales, ni sabe cuándo transicionar de etapa (anonimo -> identificado -> calificado). Toda la lógica base de "Agente" está ausente.
- **Acción**: R1 debe implementar el grafo/bucle del agente que una los routers de FastAPI con el LLM.

### 2. Faltan los Guardrails (Dueño: R1)
- **Problema**: La carpeta `backend/core/guardrails/` está vacía. Faltan G1 (no asesoramiento), G1-bis, y G2 (negativa honesta) al G8.
- **Impacto**: Estos guardrails valen el 25% de la nota de evaluación (Sección 10 de la rúbrica). Son el pilar conceptual del proyecto ("El agente tiene frenos"). Sin ellos, el agente puede alucinar, prometer cosas indebidas, y descalificar al equipo.
- **Acción**: R1 debe comenzar a codificar las reglas duras de contención y asociarlas al flujo del orquestador.

### 3. Conexión Frontend - Backend (Dueños: R3, R4)
- **Problema**: El Frontend en `web/` sigue utilizando fuertemente `mocks-consola.ts` (datos falsos).
- **Impacto**: Aunque R2 ya construyó la API segregada en FastAPI, el Frontend no está consumiendo la fuente de la verdad.
- **Acción**: R3 y R4 deben empezar a reemplazar los mocks por llamadas a la API real (`/chat` y `/consola`), conectando los tipos de TypeScript con los endpoints de Pydantic.

## 📌 Próximos pasos inmediatos (Checkpoint H11 - H17)
1. **R1**: Es el foco absoluto. Debe programar el `orquestador.py` (ciclo del agente) y poblar `guardrails/`.
2. **R3/R4**: Borrar los mocks y enchufar el frontend contra FastAPI.
3. **R2**: Dar soporte a R1 y R3/R4 si la API necesita ajustes durante la integración.
