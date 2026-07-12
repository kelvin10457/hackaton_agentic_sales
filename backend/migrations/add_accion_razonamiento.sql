-- Alinea acciones_propuestas con la Biblia §4.6 (AccionPropuesta).
--
-- Faltaban tres campos del contrato que la consola de R4 necesita para el
-- criterio 3.2 ("acción propuesta con razonamiento visible"):
--   · asunto              → el borrador tiene asunto + cuerpo, no solo cuerpo
--   · razonamiento        → por qué el agente propone esto (lo lee Carlos)
--   · fuentes_consultadas → las citas del corpus que respaldan la propuesta
--
-- Todas nullable: las filas existentes siguen siendo válidas.
-- Idempotente: se puede correr varias veces sin error.

ALTER TABLE acciones_propuestas ADD COLUMN IF NOT EXISTS asunto VARCHAR(300);
ALTER TABLE acciones_propuestas ADD COLUMN IF NOT EXISTS razonamiento TEXT;
ALTER TABLE acciones_propuestas ADD COLUMN IF NOT EXISTS fuentes_consultadas JSONB;
