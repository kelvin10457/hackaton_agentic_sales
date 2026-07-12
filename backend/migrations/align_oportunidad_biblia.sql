-- Etapas canónicas de la Biblia para leads y oportunidades existentes.
UPDATE leads_v2
SET etapa_embudo = CASE etapa_embudo
    WHEN 'prospecto' THEN 'nuevo'
    WHEN 'propuesta' THEN 'educando'
    WHEN 'negociacion' THEN 'listo_para_asesor'
    WHEN 'cerrado_ganado' THEN 'derivado'
    WHEN 'cerrado_perdido' THEN 'descartado'
    ELSE etapa_embudo
END;

ALTER TABLE oportunidades
    ADD COLUMN IF NOT EXISTS nombre VARCHAR(300),
    ADD COLUMN IF NOT EXISTS tipo VARCHAR(50),
    ADD COLUMN IF NOT EXISTS score_actual FLOAT,
    ADD COLUMN IF NOT EXISTS propietario VARCHAR(200);

UPDATE oportunidades o
SET etapa = l.etapa_embudo,
    nombre = COALESCE(o.nombre, l.nombre || ' — Programa Inicial'),
    tipo = COALESCE(o.tipo, CASE WHEN l.segmento = 'b2b' THEN 'B2B_corporativo' ELSE 'B2C_programa' END),
    score_actual = COALESCE(o.score_actual, s.total, 0),
    propietario = COALESCE(o.propietario, 'carlos@futuroacademy.ec')
FROM leads_v2 l
LEFT JOIN scores_lead s ON s.lead_id = l.id
WHERE o.lead_id = l.id;

ALTER TABLE oportunidades
    ALTER COLUMN nombre SET NOT NULL,
    ALTER COLUMN tipo SET NOT NULL,
    ALTER COLUMN score_actual SET NOT NULL,
    ALTER COLUMN propietario SET NOT NULL;
