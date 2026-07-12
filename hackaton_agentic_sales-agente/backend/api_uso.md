# Agentic Sales API — uso actual

Base local: `http://localhost:8000`. Consulta los contratos completos en
[`/docs`](http://localhost:8000/docs).

```bash
cd backend
bash start.sh

BASE="http://localhost:8000"
JSON=(-H "Content-Type: application/json")
curl -i "$BASE/health"
```

`GET /health` ejecuta `SELECT 1` contra PostgreSQL. Responde `200` con
`{"ok":true}` cuando conecta y `503` cuando la BD no está disponible.

## Autenticación

```bash
curl -X POST "$BASE/auth/register" "${JSON[@]}" \
  -d '{"name":"Ana Ejecutiva","email":"ana@empresa.ec","password":"clave-segura"}'

TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=ana@empresa.ec&password=clave-segura" | jq -r .access_token)
AUTH=(-H "Authorization: Bearer $TOKEN")
```

`/api/consola/*` requiere el JWT de ejecutivo. El password se maneja con
`bcrypt` directo; no se usa passlib para hash ni verificación.

## Semillas y scoring

```bash
.venv/bin/python -m app.seed

curl "$BASE/api/consola/leads" "${AUTH[@]}"
curl "$BASE/api/consola/leads/2/score" "${AUTH[@]}"
curl "$BASE/api/consola/leads/3/score" "${AUTH[@]}"
```

Las señales ancla se procesan con el motor real: María da `88/caliente` y
Andrés `65/tibio`, con dimensiones no nulas. Los IDs dependen de la BD; usa la
lista de leads para encontrarlos en otra instalación.

Actualización B2C:

```bash
curl -X PATCH "$BASE/api/consola/leads/2/senales" "${JSON[@]}" "${AUTH[@]}" -d '{
  "pidio_asesor":true,
  "completo_quiz":true,
  "objetivo":"invertir",
  "monto_declarado_usd":10000,
  "experiencia_inversion":"ninguna",
  "horizonte":"1-3m"
}'
```

Actualización B2B:

```bash
curl -X PATCH "$BASE/api/consola/leads/3/senales" "${JSON[@]}" "${AUTH[@]}" -d '{
  "objetivo":"capacitar_equipo",
  "num_colaboradores":120,
  "presupuesto_capacitacion_usd":8000,
  "es_decisor":true,
  "solicito_propuesta":false,
  "horizonte":"3-6m"
}'
```

## Conversación y token de sesión

Las conversaciones comerciales aceptan IDs de `leads_v2`:

```bash
CONV=$(curl -s -X POST "$BASE/conversations/" "${JSON[@]}" -d '{"lead_id":2}')
CONV_ID=$(printf '%s' "$CONV" | jq -r .id)

SESSION=$(curl -s -X POST "$BASE/api/consola/conversaciones/$CONV_ID/token-sesion" \
  "${AUTH[@]}" | jq -r .token_sesion)
CHAT=(-H "X-Session-Token: $SESSION")

curl -i "$BASE/api/chat/conversacion" "${CHAT[@]}"
curl -X POST "$BASE/api/chat/mensajes?contenido=Quiero%20hablar%20con%20un%20asesor" "${CHAT[@]}"

curl -X PATCH "$BASE/conversations/$CONV_ID" "${JSON[@]}" \
  -d '{"ended_at":"2026-07-12T13:42:35Z"}'
curl -i "$BASE/api/chat/conversacion" "${CHAT[@]}"
```

El primer GET devuelve el historial real. Tras cerrar la conversación, el mismo
token responde `401`. El chat no acepta conversation_id del cliente ni expone
score, oportunidad o auditoría.

## Consentimiento, CRM, corpus y pruebas

```bash
curl -X POST "$BASE/api/consola/leads/2/consentimiento" "${JSON[@]}" "${AUTH[@]}" -d '{
  "tratamiento_datos_otorgado":true,
  "tratamiento_datos_canal":"web",
  "comunicaciones_comerciales_otorgado":true,
  "comunicaciones_comerciales_canal":"web",
  "version_politica":"v1"
}'

curl -X POST "$BASE/api/consola/crm/upsert" "${JSON[@]}" "${AUTH[@]}" -d '{"lead_id":2}'
curl "$BASE/api/consola/corpus" "${AUTH[@]}"

.venv/bin/python -m pytest app/tests -v
```

CRM exige lead no anónimo, email y tratamiento de datos. Aprobar acciones exige
consentimiento de comunicaciones. Para PostgreSQL existente aplica también
`fix_columnas_faltantes.sql` y `migrate_conversations_to_leads_v2.sql`.
