-- Migración: añade campos necesarios para Tarea #3 (auth de superficies)
-- Ejecutar UNA SOLA VEZ contra la BD de desarrollo/producción.
-- Las columnas ya existen en los modelos SQLAlchemy; este script las agrega
-- a tablas existentes sin borrar datos.

-- 1. Rol de usuario (default 'ejecutivo' para usuarios existentes)
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS rol VARCHAR(50) NOT NULL DEFAULT 'ejecutivo';

-- 2. Token de sesión de chat en conversaciones
ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS token_sesion VARCHAR(512);

-- Verificar resultado:
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_name IN ('users', 'conversations')
-- AND column_name IN ('rol', 'token_sesion');
