-- PostgreSQL migration: timestamps are stored and returned as UTC offsets.
ALTER TABLE conversations
    ALTER COLUMN started_at TYPE TIMESTAMP WITH TIME ZONE
        USING started_at AT TIME ZONE 'UTC',
    ALTER COLUMN ended_at TYPE TIMESTAMP WITH TIME ZONE
        USING ended_at AT TIME ZONE 'UTC';

-- Acciones nuevas usan el contrato estructurado {email, nombre}.
ALTER TABLE acciones_propuestas
    ALTER COLUMN destinatario TYPE JSONB
        USING jsonb_build_object('email', destinatario, 'nombre', '');
