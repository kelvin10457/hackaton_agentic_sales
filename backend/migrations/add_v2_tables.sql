-- Migración Tarea #5: tablas V2 del Manual del R2
-- Ejecutar UNA SOLA VEZ. Las tablas se crean con IF NOT EXISTS para seguridad.

CREATE TABLE IF NOT EXISTS leads_v2 (
    id                   SERIAL PRIMARY KEY,
    nombre               VARCHAR(200) NOT NULL,
    email                VARCHAR(200),
    email_normalizado    VARCHAR(200) UNIQUE,  -- clave de dedup del CRM
    telefono             VARCHAR(50),
    cedula               VARCHAR(20),
    empresa              VARCHAR(200),
    cargo                VARCHAR(200),
    estado_identificacion VARCHAR(50) NOT NULL DEFAULT 'anonimo',
    etapa_embudo         VARCHAR(50) NOT NULL DEFAULT 'prospecto',
    segmento             VARCHAR(10) NOT NULL DEFAULT 'b2c',
    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_leads_v2_email_normalizado ON leads_v2(email_normalizado);

CREATE TABLE IF NOT EXISTS oportunidades (
    id                   SERIAL PRIMARY KEY,
    lead_id              INTEGER NOT NULL UNIQUE REFERENCES leads_v2(id) ON DELETE CASCADE,
    resumen              TEXT NOT NULL,
    valor_estimado       FLOAT,
    moneda               VARCHAR(10) NOT NULL DEFAULT 'USD',
    probabilidad_cierre  FLOAT,
    ruta_sugerida        VARCHAR(50),
    etapa                VARCHAR(50) NOT NULL DEFAULT 'prospecto',
    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP
);

CREATE TABLE IF NOT EXISTS consentimientos (
    id                              SERIAL PRIMARY KEY,
    lead_id                         INTEGER NOT NULL UNIQUE REFERENCES leads_v2(id) ON DELETE CASCADE,

    -- Finalidad 1: habilita escritura en CRM
    tratamiento_datos_otorgado      BOOLEAN NOT NULL DEFAULT FALSE,
    tratamiento_datos_fecha         TIMESTAMP,
    tratamiento_datos_canal         VARCHAR(50),

    -- Finalidad 2: habilita aprobar AccionPropuesta
    comunicaciones_otorgado         BOOLEAN NOT NULL DEFAULT FALSE,
    comunicaciones_fecha            TIMESTAMP,
    comunicaciones_canal            VARCHAR(50),

    version_politica                VARCHAR(50),
    updated_at                      TIMESTAMP
);

-- Verificar:
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public' AND table_name IN ('leads_v2','oportunidades','consentimientos');
