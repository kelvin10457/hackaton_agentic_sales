-- Las conversaciones usan IDs de leads_v2. Eliminar solo la FK legacy a leads
-- permite ambas tablas históricas sin forzar una referencia incorrecta.
DO $$
DECLARE
    fk_name TEXT;
BEGIN
    SELECT conname INTO fk_name
    FROM pg_constraint
    WHERE conrelid = 'conversations'::regclass
      AND contype = 'f'
      AND pg_get_constraintdef(oid) LIKE '%(lead_id)%';

    IF fk_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE conversations DROP CONSTRAINT %I', fk_name);
    END IF;
END $$;
