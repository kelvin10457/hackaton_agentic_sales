-- Sincroniza columnas existentes con los modelos SQLAlchemy actuales.
-- Es aditiva e idempotente: no crea tablas ni modifica datos existentes.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS rol VARCHAR(50) NOT NULL DEFAULT 'ejecutivo';

ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS token_sesion VARCHAR(512);

ALTER TABLE acciones_propuestas
    ADD COLUMN IF NOT EXISTS motivo_rechazo TEXT;

ALTER TABLE senales_lead
    ADD COLUMN IF NOT EXISTS objetivo VARCHAR(50),
    ADD COLUMN IF NOT EXISTS horizonte VARCHAR(20),
    ADD COLUMN IF NOT EXISTS pidio_asesor BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS mensajes_intercambiados INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS completo_quiz BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS monto_declarado_usd DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS experiencia_inversion VARCHAR(30),
    ADD COLUMN IF NOT EXISTS perfil_riesgo VARCHAR(50),
    ADD COLUMN IF NOT EXISTS num_colaboradores INTEGER,
    ADD COLUMN IF NOT EXISTS presupuesto_capacitacion_usd DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS es_decisor BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS solicito_propuesta BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS documento_valido BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS ruc_valido BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email_valido BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email_corporativo BOOLEAN NOT NULL DEFAULT FALSE;
