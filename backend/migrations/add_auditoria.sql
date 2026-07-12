-- Migración Tarea #6: tabla de bitácora append-only
-- Ejecutar UNA SOLA VEZ. Sin UPDATE ni DELETE sobre esta tabla nunca.

CREATE TABLE IF NOT EXISTS eventos_auditoria (
    id          SERIAL PRIMARY KEY,
    actor       VARCHAR(20)  NOT NULL,   -- agente | humano | sistema
    actor_id    VARCHAR(200) NOT NULL,   -- email o "agente:cv5"
    tipo_evento VARCHAR(60)  NOT NULL,
    lead_id     INTEGER,                 -- nullable, SIN FK (la bitácora sobrevive borrado de leads)
    payload     JSONB,
    timestamp   TIMESTAMP NOT NULL DEFAULT NOW()
    -- NO hay updated_at. NO hay columna mutable. APPEND-ONLY.
);

CREATE INDEX IF NOT EXISTS ix_eventos_auditoria_lead_id    ON eventos_auditoria(lead_id);
CREATE INDEX IF NOT EXISTS ix_eventos_auditoria_tipo_evento ON eventos_auditoria(tipo_evento);
CREATE INDEX IF NOT EXISTS ix_eventos_auditoria_timestamp  ON eventos_auditoria(timestamp DESC);

-- Bloqueo a nivel de BD (refuerzo adicional al bloqueo en código):
-- Crear una regla que rechaza UPDATE y DELETE sobre esta tabla.
-- (Opcional pero recomendado para producción)
-- CREATE RULE no_update_auditoria AS ON UPDATE TO eventos_auditoria DO INSTEAD NOTHING;
-- CREATE RULE no_delete_auditoria AS ON DELETE TO eventos_auditoria DO INSTEAD NOTHING;

-- Verificar:
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_name = 'eventos_auditoria' ORDER BY ordinal_position;
