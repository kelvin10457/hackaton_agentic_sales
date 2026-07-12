-- Cierra dos huecos de contrato contra la Biblia.
--
-- 1) acciones_propuestas — rendición de cuentas (Biblia §4.6, criterio 3.3)
--    El ejecutivo puede APROBAR, EDITAR o RECHAZAR. Hasta ahora la edición se
--    perdía: no había dónde guardar lo que Carlos realmente envió, ni la marca
--    de que fue él quien lo cambió.
--      · borrador_final     → {asunto, cuerpo} tal como salió, si lo editó
--      · editado_por_humano → la marca de responsabilidad
--      · revisado_en        → cuándo lo revisó
--
-- 2) leads_v2 — el brief (Biblia §4.1, criterio 3.1)
--      · necesidad  → lo que el prospecto dijo que quiere, con sus palabras
--      · objeciones → sus frenos declarados ("me da miedo perder dinero")
--
-- Todas nullable / con default: las filas existentes siguen siendo válidas.
-- Idempotente: se puede correr varias veces sin error.

ALTER TABLE acciones_propuestas ADD COLUMN IF NOT EXISTS borrador_final JSONB;
ALTER TABLE acciones_propuestas ADD COLUMN IF NOT EXISTS editado_por_humano BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE acciones_propuestas ADD COLUMN IF NOT EXISTS revisado_en TIMESTAMP;

ALTER TABLE leads_v2 ADD COLUMN IF NOT EXISTS necesidad TEXT;
ALTER TABLE leads_v2 ADD COLUMN IF NOT EXISTS objeciones JSONB;
