-- Corpus documental aprobado. La tabla se crea vacía deliberadamente.

DO $$
BEGIN
    CREATE TYPE publico_corpus AS ENUM ('B2C', 'B2B', 'ambos');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS documento_corpus (
    id            VARCHAR PRIMARY KEY,
    titulo        VARCHAR NOT NULL,
    seccion       VARCHAR NOT NULL,
    contenido     TEXT NOT NULL,
    publico       publico_corpus NOT NULL,
    version       VARCHAR NOT NULL,
    aprobado_por  VARCHAR NOT NULL,
    cita_visible  TEXT NOT NULL
);
