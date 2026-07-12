# Variables de entorno — Agentic Sales API

Todas las variables viven en `backend/.env` (no commiteado). Usa `backend/.env.example` como plantilla.

## Variables requeridas

| Variable | Ejemplo | Descripción |
|---|---|---|
| `DATABASE_URL` | `postgresql://user:pass@localhost:5432/hackaton_db` | Cadena de conexión a PostgreSQL (psycopg2) |
| `SECRET_KEY` | `<hex 32 bytes>` | Clave para firmar JWT de usuarios ejecutivos. Generar con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Vida del JWT ejecutivo en minutos |

## Variables de la superficie de chat (Tarea #3)

| Variable | Ejemplo | Descripción |
|---|---|---|
| `CHAT_TOKEN_SECRET` | `<hex 32 bytes, diferente de SECRET_KEY>` | Clave para firmar tokens opacos de sesión de conversación (`/api/chat/*`) |
| `CHAT_TOKEN_EXPIRE_HOURS` | `24` | Vida del token de chat en horas |

## Variables opcionales

| Variable | Default | Descripción |
|---|---|---|
| `DEBUG` | `false` | Si `true`, activa modo desarrollo (logs verbosos, env=development en `/health`) |
| `PORT` | `8000` | Puerto de escucha del servidor |
| `CRM_API_URL` | — | URL base del CRM externo (Tarea #5, CRMSimulado no la necesita) |
| `CRM_API_KEY` | — | API key del CRM externo |
| `SENTRY_DSN` | — | DSN de Sentry para monitoreo de errores en producción |

## Verificación rápida

```bash
# Verificar que Postgres responde y la API arrancó correctamente
curl -s http://localhost:8000/health | python3 -m json.tool
```

Respuesta esperada:
```json
{
  "ok": true,
  "db": "connected",
  "version": "1.0.0",
  "env": "development"
}
```

Si `db` es `"error"`, revisa que `DATABASE_URL` apunte a una instancia de Postgres activa y que el usuario tenga permisos.

## Despliegue en Render

Configura **Root Directory** como `backend` y usa este comando de arranque:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

No configures `PYTHONPATH=app`: el directorio de trabajo debe ser `backend`,
que contiene el paquete raíz `app` y el paquete independiente `schemas`.

## Datos de demostración

Carga 15 leads idempotentes (incluye María Villacís, Andrés Cordero y Sofía
Andrade) con:

```bash
cd backend
.venv/bin/python -m app.seed
```

Sofía queda sin consentimiento de comunicaciones comerciales, para demostrar
el bloqueo de aprobación. El comando no sobrescribe leads que ya existan por
email normalizado.
