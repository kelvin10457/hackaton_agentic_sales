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
5. **Frontend UI Integrado (Dueños: R3, R4)**:
   - La interfaz estática (Chat y Consola) construida en `web/app/` ha sido **conectada exitosamente con la API del Backend (FastAPI)**.
   - Los **datos falsos (mocks) se han eliminado** y los tipos de TypeScript están 100% sincronizados con los schemas de Pydantic.
   - La seguridad CORS está habilitada en el backend permitiendo conectar `localhost:3000` con el servidor en la nube sin errores.

---

## 🚨 CRÍTICO: Qué debe arreglarse AHORA (Bloqueantes)

La infraestructura backend (R2) y el Frontend (R3/R4) están completos e integrados. Sin embargo, **el núcleo del agente inteligente (R1) sigue sin existir**, lo cual es el bloqueo crítico principal para que la solución tome vida:

### 1. Faltan Orquestador y Estado (Dueño: R1)
- **Problema**: Los archivos `backend/core/orquestador.py` y `backend/core/estado.py` no han sido creados o programados.
- **Impacto**: No existe la "Máquina de Estados de la Conversación" (Sección 7 de la Biblia). El LLM actualmente no controla el flujo de la conversación, no extrae señales, ni sabe cuándo transicionar de etapa (anonimo -> identificado -> calificado). Toda la lógica base de "Agente" está ausente.
- **Acción**: R1 debe implementar el grafo/bucle del agente (usando LangGraph o equivalente) que conecte los routers de FastAPI con el LLM.

### 2. Faltan los Guardrails (Dueño: R1)
- **Problema**: La carpeta `backend/core/guardrails/` está vacía (solo existe la carpeta, no hay código). Faltan G1 (no asesoramiento), G1-bis, y G2 (negativa honesta) al G8.
- **Impacto**: Estos guardrails valen el 25% de la nota de evaluación (Sección 10 de la rúbrica). Son el pilar conceptual del proyecto ("El agente tiene frenos"). Sin ellos, el agente puede alucinar, prometer cosas indebidas, y descalificar al equipo.
- **Acción**: R1 debe comenzar a codificar las reglas duras de contención e insertarlas explícitamente en el flujo del orquestador.

## 📌 Próximos pasos inmediatos (Checkpoint Final)
1. **R1 (Foco Absoluto)**: Toda la atención debe estar en programar el `orquestador.py` (cerebro del agente y estado) y programar en `/guardrails`.
2. **R2, R3, R4**: Entrar en modo de soporte y ajustes finos. Todo el andamiaje está listo, ahora deben ayudar a R1 a empaquetar el motor del LLM en los endpoints ya definidos.
