-- Migración para agregar columnas faltantes en leads_v2 según app/models.py
-- Estas columnas existen en el modelo LeadV2 pero no están definidas en la tabla base.

ALTER TABLE leads_v2
    ADD COLUMN IF NOT EXISTS necesidad TEXT;

ALTER TABLE leads_v2
    ADD COLUMN IF NOT EXISTS objeciones JSONB;
