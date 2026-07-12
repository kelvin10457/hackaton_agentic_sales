# Estado del Proyecto: Agentic Sales (Futuro Academy)

Este documento detalla el progreso actual del equipo de desarrollo frente a lo establecido en la **Biblia de Trabajo v2**, así como las partes críticas que deben resolverse inmediatamente antes de seguir avanzando.

## ✅ Progreso Actual (Lo que ya está listo)

1. **Configuraciones (Dueño: R1)**: 
   - Los archivos en `backend/config/` (`pesos_scoring.yaml`, `preguntas_b2b.yaml`, `preguntas_b2c.yaml`, `quiz_perfil_riesgo.yaml`) están creados y alineados con el criterio 1.1 y la sección 8.
2. **Herramientas Deterministas y Tests (Dueños: R1, R5)**:
   - Las herramientas `calcular_score.py`, `obtener_quiz.py` y `calcular_ruta.py` están implementadas en `backend/tools/`.
   - Se encuentran respaldadas por sus respectivos tests unitarios en `backend/tests/` (`test_score.py`, `test_quiz.py`, `test_ruta.py`). Esto asegura que no dependen del LLM, cumpliendo la sección 5 y 6.
3. **Corpus de Conocimiento (Dueño: R5)**:
   - Los 14 documentos (FA-001 a FA-014) ya están redactados en la carpeta `knowledge/`, cumpliendo con el Deadline Duro (H10).
4. **Interfaces Base (Dueños: R3, R4)**:
   - Las carpetas `web/app/chat` y `web/app/consola` están estructuradas. Se está utilizando un mock (`mocks-consola.ts`) para renderizar el pipeline y los componentes básicos de la consola.

---

## 🚨 CRÍTICO: Qué debe arreglarse AHORA (Bloqueantes)

Según el cronograma (H1-H4) y la sección 13 de la Biblia, las siguientes piezas están incompletas o faltantes y **bloquean al resto del equipo**. Deben priorizarse antes de tocar más código del orquestador o la interfaz:

### 1. Contratos de Datos incompletos (Dueño: R2)
- **Problema**: En `backend/schemas/` solo existen `score.py` y `senales.py`. Faltan los demás contratos definidos en la sección 4 (Lead, Consentimiento, Oportunidad, etc.).
- **Impacto**: La Biblia establece explícitamente: *"Los tipos de TypeScript se GENERAN desde OpenAPI. Nadie escribe un tipo a mano."* Si estos esquemas en Pydantic no se terminan, el Frontend (R3, R4) está trabajando a ciegas y costará el triple cambiarlo después.
- **Acción**: R2 debe completar los 13 contratos de la sección 4.

### 2. Despliegue de API y Segregación de Rutas (Dueño: R2)
- **Problema**: La carpeta `web/app/api/` no existe. No se ha implementado la segregación obligatoria de la API Pública (`/api/chat/*`) y la API Interna (`/api/consola/*`).
- **Impacto**: Esta separación es un requisito de seguridad (Sección 4.10) y previene que el score y la bitácora queden expuestos al usuario final.
- **Acción**: R2 debe levantar los endpoints base (aunque sea devolviendo mocks) y crear la estructura segregada de la API.

### 3. Faltan los Guardrails (Dueño: R1)
- **Problema**: La carpeta `backend/core/guardrails/` está vacía (solo tiene `__init__.py`). Faltan G1, G1-bis, y G2 al G8.
- **Impacto**: Estos guardrails valen el 25% de la nota (Sección 10). G1 y G2 son críticos para la tesis del producto ("El agente tiene frenos").
- **Acción**: R1 debe comenzar a codificar las reglas duras de contención.

### 4. Arquitectura de Integraciones (Dueño: R2)
- **Problema**: La carpeta `backend/adapters/` (Puertos e Integraciones) no existe. No hay rastro de `crm_simulado.py` ni `identidad_stub.py`.
- **Impacto**: El sistema no tiene donde persistir el `crm_upsert` ni manejar el ciclo de vida del lead.
- **Acción**: R2 debe inicializar la arquitectura hexagonal base (puertos) para que R1 pueda inyectarlos en el agente.

### 5. Faltan Orquestador y Estado (Dueño: R1)
- **Problema**: `backend/core/orquestador.py` y `backend/core/estado.py` aún no han sido creados.
- **Impacto**: No existe la "Máquina de Estados de la Conversación" (Sección 7). El LLM aún no controla el flujo.
- **Acción**: Una vez que R2 termine los esquemas, R1 debe implementar el grafo/bucle del agente.

## 📌 Próximos pasos inmediatos
1. **R2**: Detener todo y terminar los 13 schemas (Pydantic) y los stubs de la API segregada.
2. **R1**: Una vez que R2 haga push de los schemas, empezar a construir `guardrails/` y el `orquestador.py`.
3. **R3/R4**: Continuar puliendo la UI pero estar listos para reemplazar `mocks-consola.ts` por los tipos autogenerados en cuanto R2 termine el contrato de la API.
