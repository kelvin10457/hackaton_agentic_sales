# Agentic Sales API — Guía de Uso

> **Base URL:** `http://localhost:8000`  
> **Versión:** 1.0.0  
> **Framework:** FastAPI + SQLAlchemy  
> **Documentación interactiva:** `http://localhost:8000/docs` (Swagger UI) · `http://localhost:8000/redoc` (ReDoc)

---

## Índice

1. [Inicio rápido](#1-inicio-rápido)
2. [Autenticación](#2-autenticación)
3. [Usuarios — `/users`](#3-usuarios--users)
4. [Leads — `/leads`](#4-leads--leads)
5. [Conversaciones — `/conversations`](#5-conversaciones--conversations)
6. [Mensajes — `/messages`](#6-mensajes--messages)
7. [Modelos de datos](#7-modelos-de-datos)
8. [Códigos de error comunes](#8-códigos-de-error-comunes)
9. [Ejemplos de flujo completo](#9-ejemplos-de-flujo-completo)

---

## 1. Inicio rápido

### Levantar el servidor

```bash
# Desde la raíz de /backend
bash start.sh
```

El servidor arranca en `http://0.0.0.0:8000` con hot-reload habilitado.

### Variables de entorno requeridas (`.env`)

```ini
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=tu_clave_secreta_muy_larga
ACCESS_TOKEN_EXPIRE_MINUTES=60   # opcional, default 60
PORT=8000
```

> Copia `.env.example` → `.env` y rellena los valores antes de iniciar.

### Verificar que funciona

```bash
curl http://localhost:8000/
# → {"message": "API funcionando"}
```

---

## 2. Autenticación

La API usa **JWT Bearer Tokens** (HS256). El token se obtiene en `/auth/login` y debe enviarse en el header `Authorization` en las rutas protegidas.

### 2.1 Registrar usuario

```
POST /auth/register
Content-Type: application/json
```

**Body:**
```json
{
  "name": "María López",
  "email": "maria@ejemplo.com",
  "password": "miPassword123"
}
```

**Respuesta `201 Created`:**
```json
{
  "id": 1,
  "name": "María López",
  "email": "maria@ejemplo.com",
  "created_at": "2026-07-11T21:00:00"
}
```

> ⚠️ Si el email ya existe, retorna `400 Bad Request` con `"El email ya está registrado."`.

---

### 2.2 Iniciar sesión (obtener token)

```
POST /auth/login
Content-Type: application/x-www-form-urlencoded
```

**Body (form-data, no JSON):**
```
username=maria@ejemplo.com
password=miPassword123
```

> El campo se llama `username` pero debe contener el **email** del usuario.

**Respuesta `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Ejemplo con `curl`:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=maria@ejemplo.com&password=miPassword123"
```

**Ejemplo con JavaScript (fetch):**
```js
const form = new URLSearchParams();
form.append("username", "maria@ejemplo.com");
form.append("password", "miPassword123");

const res = await fetch("http://localhost:8000/auth/login", {
  method: "POST",
  body: form,
});
const { access_token } = await res.json();
```

---

### 2.3 Obtener usuario autenticado

```
GET /auth/me
Authorization: Bearer <token>
```

**Respuesta `200 OK`:** objeto `UserRead` (ver [§7](#7-modelos-de-datos)).

---

### Cómo enviar el token en cada petición

Agrega el header en **todas las llamadas protegidas**:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```js
// Helper de fetch con auth
async function apiFetch(path, options = {}) {
  return fetch(`http://localhost:8000${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("token")}`,
      ...options.headers,
    },
  });
}
```

---

## 3. Usuarios — `/users`

### 3.1 Crear usuario

```
POST /users/
Content-Type: application/json
```

**Body:**
```json
{
  "name": "Carlos Ruiz",
  "email": "carlos@empresa.com",
  "password": "securePass!"
}
```

**Respuesta `201`:** `UserRead`

---

### 3.2 Listar usuarios

```
GET /users/?skip=0&limit=100
```

| Parámetro | Tipo  | Default | Descripción                     |
|-----------|-------|---------|---------------------------------|
| `skip`    | `int` | `0`     | Offset de paginación            |
| `limit`   | `int` | `100`   | Número máximo de resultados     |

**Respuesta `200`:** `UserRead[]`

---

### 3.3 Obtener usuario por ID

```
GET /users/{user_id}
```

**Respuesta `200`:** `UserRead`  
**Error `404`:** `{"detail": "Usuario no encontrado."}`

---

### 3.4 Estadísticas de dashboard del usuario ⭐

```
GET /users/{user_id}/stats
```

Devuelve métricas agregadas del usuario: total de leads, leads por estado, conversaciones activas y mensajes enviados.

**Respuesta `200`:**
```json
{
  "total_leads": 15,
  "leads_by_status": {
    "nuevo": 5,
    "contactado": 7,
    "cerrado": 3
  },
  "active_conversations": 4,
  "total_messages_sent": 132,
  "avg_messages_per_lead": 8.8
}
```

---

### 3.5 Actualizar usuario (parcial)

```
PATCH /users/{user_id}
Content-Type: application/json
```

**Body** (todos los campos son opcionales):
```json
{
  "name": "Carlos R. Actualizado",
  "email": "nuevo@correo.com",
  "password": "nuevaPass"
}
```

> Las contraseñas se re-hashean automáticamente con bcrypt.

**Respuesta `200`:** `UserRead`

---

### 3.6 Eliminar usuario

```
DELETE /users/{user_id}
```

**Respuesta `204 No Content`** (sin body).  
> Elimina en cascada todos los **leads** (y sus conversaciones y mensajes) del usuario.

---

## 4. Leads — `/leads`

### 4.1 Crear lead

```
POST /leads/
Content-Type: application/json
```

**Body:**
```json
{
  "name": "Ana Torres",
  "email": "ana@cliente.com",
  "phone": "+52 55 1234 5678",
  "lead_type": "inbound",
  "company": "Torres Tech",
  "interest": "software de gestión",
  "budget": 15000.00,
  "urgency": "alta",
  "lead_score": 8.5,
  "status": "nuevo",
  "user_id": 1
}
```

> `user_id` debe corresponder a un usuario existente, de lo contrario retorna `404`.

**Respuesta `201`:** `LeadRead`

---

### 4.2 Listar leads (con actividad)

```
GET /leads/?skip=0&limit=100&user_id=1&sort=last_activity
```

| Parámetro     | Tipo     | Descripción                                                  |
|---------------|----------|--------------------------------------------------------------|
| `skip`        | `int`    | Offset de paginación                                         |
| `limit`       | `int`    | Máximo de resultados (default `100`)                         |
| `user_id`     | `int`    | Filtra leads por propietario                                 |
| `sort`        | `string` | `"last_activity"` → ordena por conversación más reciente     |

**Respuesta `200`:** `LeadActivity[]` — incluye `open_conversations` y `last_conversation_at`.

```json
[
  {
    "id": 1,
    "name": "Ana Torres",
    "email": "ana@cliente.com",
    "phone": "+52 55 1234 5678",
    "lead_type": "inbound",
    "company": "Torres Tech",
    "interest": "software de gestión",
    "budget": 15000.0,
    "urgency": "alta",
    "lead_score": 8.5,
    "status": "nuevo",
    "user_id": 1,
    "open_conversations": 2,
    "last_conversation_at": "2026-07-10T18:30:00"
  }
]
```

---

### 4.3 Obtener lead por ID

```
GET /leads/{lead_id}
```

**Respuesta `200`:** `LeadRead`

---

### 4.4 Lead completo con conversaciones ⭐

```
GET /leads/{lead_id}/full
```

Retorna el lead junto con un **resumen de todas sus conversaciones**: cantidad de mensajes y el último mensaje de cada una.

**Respuesta `200`:** `LeadWithConversations`
```json
{
  "id": 1,
  "name": "Ana Torres",
  "...": "...",
  "conversations": [
    {
      "id": 10,
      "started_at": "2026-07-08T10:00:00",
      "ended_at": null,
      "lead_id": 1,
      "message_count": 5,
      "last_message": "Entendido, les enviamos la propuesta."
    }
  ]
}
```

---

### 4.5 Timeline cronológico del lead ⭐

```
GET /leads/{lead_id}/timeline
```

Retorna **todos los mensajes** del lead, de todas sus conversaciones, ordenados cronológicamente. Ideal para construir una vista de historial unificado.

**Respuesta `200`:** `TimelineMessage[]`
```json
[
  {
    "conversation_id": 10,
    "message_id": 42,
    "sender": "agent",
    "content": "Hola Ana, ¿en qué podemos ayudarte?",
    "created_at": "2026-07-08T10:01:00"
  },
  {
    "conversation_id": 10,
    "message_id": 43,
    "sender": "lead",
    "content": "Necesito información sobre precios.",
    "created_at": "2026-07-08T10:02:30"
  }
]
```

---

### 4.6 Actualizar lead (parcial)

```
PATCH /leads/{lead_id}
Content-Type: application/json
```

**Body** (todos opcionales):
```json
{
  "status": "contactado",
  "lead_score": 9.2,
  "budget": 20000.00
}
```

**Respuesta `200`:** `LeadRead`

---

### 4.7 Eliminar lead

```
DELETE /leads/{lead_id}
```

**Respuesta `204 No Content`**.  
> Elimina en cascada todas las **conversaciones** y **mensajes** del lead.

---

## 5. Conversaciones — `/conversations`

### 5.1 Crear conversación

```
POST /conversations/
Content-Type: application/json
```

**Body:**
```json
{
  "lead_id": 1,
  "ended_at": null
}
```

> `ended_at` es opcional. Si se omite o es `null`, la conversación queda **abierta**.

**Respuesta `201`:** `ConversationRead`
```json
{
  "id": 10,
  "started_at": "2026-07-11T21:05:00",
  "ended_at": null,
  "lead_id": 1
}
```

---

### 5.2 Listar conversaciones

```
GET /conversations/?skip=0&limit=100&lead_id=1&active=true
```

| Parámetro  | Tipo      | Descripción                                              |
|------------|-----------|----------------------------------------------------------|
| `skip`     | `int`     | Offset de paginación                                     |
| `limit`    | `int`     | Máximo de resultados                                     |
| `lead_id`  | `int`     | Filtra por lead                                          |
| `active`   | `bool`    | `true` = solo abiertas (`ended_at IS NULL`); `false` = cerradas |

**Respuesta `200`:** `ConversationRead[]`

---

### 5.3 Obtener conversación por ID

```
GET /conversations/{conversation_id}
```

**Respuesta `200`:** `ConversationRead`

---

### 5.4 Conversación completa con mensajes ⭐

```
GET /conversations/{conversation_id}/messages
```

Retorna la conversación enriquecida: datos del **lead** (resumen) + lista de **mensajes** en orden cronológico.

**Respuesta `200`:** `ConversationWithMessages`
```json
{
  "id": 10,
  "started_at": "2026-07-11T21:05:00",
  "ended_at": null,
  "lead_id": 1,
  "lead": {
    "id": 1,
    "name": "Ana Torres",
    "company": "Torres Tech",
    "status": "nuevo",
    "lead_score": 8.5
  },
  "messages": [
    {
      "id": 42,
      "sender": "agent",
      "content": "Hola Ana, ¿en qué podemos ayudarte?",
      "created_at": "2026-07-11T21:06:00",
      "conversation_id": 10
    }
  ]
}
```

---

### 5.5 Actualizar conversación (cerrarla)

```
PATCH /conversations/{conversation_id}
Content-Type: application/json
```

**Body:**
```json
{
  "ended_at": "2026-07-11T22:00:00"
}
```

> Pasar `ended_at` con una fecha **cierra** la conversación. Pasar `null` la **reabre**.

**Respuesta `200`:** `ConversationRead`

---

### 5.6 Eliminar conversación

```
DELETE /conversations/{conversation_id}
```

**Respuesta `204 No Content`**.  
> Elimina en cascada todos los **mensajes** de la conversación.

---

## 6. Mensajes — `/messages`

### 6.1 Crear mensaje

```
POST /messages/
Content-Type: application/json
```

**Body:**
```json
{
  "sender": "agent",
  "content": "Hola, ¿en qué te puedo ayudar hoy?",
  "conversation_id": 10
}
```

> `sender` puede ser cualquier string descriptivo, p.ej. `"agent"`, `"lead"`, `"bot"`.

**Respuesta `201`:** `MessageRead`
```json
{
  "id": 42,
  "sender": "agent",
  "content": "Hola, ¿en qué te puedo ayudar hoy?",
  "created_at": "2026-07-11T21:06:00",
  "conversation_id": 10
}
```

---

### 6.2 Listar mensajes

```
GET /messages/?skip=0&limit=100&conversation_id=10
```

| Parámetro         | Tipo  | Descripción                         |
|-------------------|-------|-------------------------------------|
| `conversation_id` | `int` | Filtra mensajes de una conversación |
| `skip`            | `int` | Offset de paginación                |
| `limit`           | `int` | Máximo de resultados                |

**Respuesta `200`:** `MessageRead[]`

---

### 6.3 Obtener mensaje por ID

```
GET /messages/{message_id}
```

**Respuesta `200`:** `MessageRead`

---

### 6.4 Actualizar mensaje (parcial)

```
PATCH /messages/{message_id}
Content-Type: application/json
```

**Body** (todos opcionales):
```json
{
  "content": "Contenido corregido del mensaje."
}
```

**Respuesta `200`:** `MessageRead`

---

### 6.5 Eliminar mensaje

```
DELETE /messages/{message_id}
```

**Respuesta `204 No Content`**.

---

## 7. Modelos de datos

### `UserRead`
| Campo        | Tipo       | Descripción                        |
|--------------|------------|------------------------------------|
| `id`         | `int`      | Identificador único                |
| `name`       | `string`   | Nombre completo                    |
| `email`      | `string`   | Email único                        |
| `created_at` | `datetime` | Fecha de creación (UTC)            |

### `LeadRead`
| Campo        | Tipo     | Descripción                                       |
|--------------|----------|---------------------------------------------------|
| `id`         | `int`    | Identificador único                               |
| `name`       | `string` | Nombre del lead                                   |
| `email`      | `string` | Correo del lead                                   |
| `phone`      | `string` | Teléfono                                          |
| `lead_type`  | `string` | Tipo de lead (ej. `"inbound"`, `"outbound"`)      |
| `company`    | `string` | Empresa                                           |
| `interest`   | `string` | Área de interés                                   |
| `budget`     | `float`  | Presupuesto estimado                              |
| `urgency`    | `string` | Urgencia (ej. `"alta"`, `"media"`, `"baja"`)      |
| `lead_score` | `float`  | Puntuación del lead (0–10)                        |
| `status`     | `string` | Estado del lead (ej. `"nuevo"`, `"contactado"`)   |
| `user_id`    | `int`    | ID del usuario propietario                        |

### `ConversationRead`
| Campo        | Tipo            | Descripción                          |
|--------------|-----------------|--------------------------------------|
| `id`         | `int`           | Identificador único                  |
| `started_at` | `datetime`      | Inicio de conversación (UTC)         |
| `ended_at`   | `datetime\|null`| Fin de conversación (`null` = abierta)|
| `lead_id`    | `int`           | ID del lead asociado                 |

### `MessageRead`
| Campo             | Tipo       | Descripción                          |
|-------------------|------------|--------------------------------------|
| `id`              | `int`      | Identificador único                  |
| `sender`          | `string`   | Emisor del mensaje                   |
| `content`         | `string`   | Contenido del mensaje                |
| `created_at`      | `datetime` | Timestamp (UTC)                      |
| `conversation_id` | `int`      | Conversación a la que pertenece      |

### `UserStats`
| Campo                  | Tipo              | Descripción                            |
|------------------------|-------------------|----------------------------------------|
| `total_leads`          | `int`             | Total de leads del usuario             |
| `leads_by_status`      | `dict[str, int]`  | Conteo de leads agrupados por estado   |
| `active_conversations` | `int`             | Conversaciones aún abiertas            |
| `total_messages_sent`  | `int`             | Total de mensajes en todas las convs.  |
| `avg_messages_per_lead`| `float`           | Promedio de mensajes por lead          |

---

## 8. Códigos de error comunes

| Código | Significado           | Causa típica                                        |
|--------|-----------------------|-----------------------------------------------------|
| `400`  | Bad Request           | Email duplicado, payload inválido                   |
| `401`  | Unauthorized          | Token ausente, inválido o expirado                  |
| `404`  | Not Found             | Recurso no existe (user, lead, conv., mensaje)      |
| `422`  | Unprocessable Entity  | Body con tipos incorrectos o campos requeridos faltantes |
| `204`  | No Content            | Eliminación exitosa (respuesta sin body)            |

**Formato estándar de error:**
```json
{
  "detail": "Descripción legible del error."
}
```

---

## 9. Ejemplos de flujo completo

### Flujo típico: registrar → crear lead → iniciar conversación → enviar mensajes

```bash
BASE="http://localhost:8000"

# 1. Registrar usuario
curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Vendedor Pro","email":"pro@ventas.com","password":"pass123"}' | jq

# 2. Login y guardar token
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -d "username=pro@ventas.com&password=pass123" | jq -r .access_token)

# 3. Ver mi perfil
curl -s $BASE/auth/me -H "Authorization: Bearer $TOKEN" | jq

# 4. Crear un lead (USER_ID=1)
curl -s -X POST $BASE/leads/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name":"Juan Pérez","email":"juan@corp.com","phone":"+52 55 9999 8888",
    "lead_type":"inbound","company":"Corp SA","interest":"CRM",
    "budget":5000,"urgency":"media","lead_score":7.0,"status":"nuevo","user_id":1
  }' | jq

# 5. Iniciar conversación con ese lead (LEAD_ID=1)
curl -s -X POST $BASE/conversations/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"lead_id":1}' | jq

# 6. Enviar mensaje del agente (CONVERSATION_ID=1)
curl -s -X POST $BASE/messages/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"sender":"agent","content":"Hola Juan, ¿te interesa una demo?","conversation_id":1}' | jq

# 7. Ver conversación completa con mensajes
curl -s $BASE/conversations/1/messages \
  -H "Authorization: Bearer $TOKEN" | jq

# 8. Ver el timeline completo del lead
curl -s $BASE/leads/1/timeline \
  -H "Authorization: Bearer $TOKEN" | jq

# 9. Cerrar la conversación
curl -s -X PATCH $BASE/conversations/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"ended_at":"2026-07-11T22:00:00"}' | jq

# 10. Ver estadísticas del usuario
curl -s $BASE/users/1/stats \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

### Flujo con JavaScript / fetch

```js
const BASE = "http://localhost:8000";

// Autenticar
const loginRes = await fetch(`${BASE}/auth/login`, {
  method: "POST",
  body: new URLSearchParams({ username: "pro@ventas.com", password: "pass123" }),
});
const { access_token } = await loginRes.json();

const headers = {
  "Content-Type": "application/json",
  Authorization: `Bearer ${access_token}`,
};

// Crear lead
const lead = await (
  await fetch(`${BASE}/leads/`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      name: "Juan Pérez", email: "juan@corp.com", phone: "+52 55 9999 8888",
      lead_type: "inbound", company: "Corp SA", interest: "CRM",
      budget: 5000, urgency: "media", lead_score: 7.0, status: "nuevo", user_id: 1,
    }),
  })
).json();

// Iniciar conversación
const conv = await (
  await fetch(`${BASE}/conversations/`, {
    method: "POST",
    headers,
    body: JSON.stringify({ lead_id: lead.id }),
  })
).json();

// Enviar mensaje
const msg = await (
  await fetch(`${BASE}/messages/`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      sender: "agent",
      content: "Hola, ¿te interesa una demo?",
      conversation_id: conv.id,
    }),
  })
).json();

// Obtener conversación completa
const fullConv = await (
  await fetch(`${BASE}/conversations/${conv.id}/messages`, { headers })
).json();
console.log(fullConv);
```

---

*Generado automáticamente a partir del código fuente. Para más detalles interactivos visita `http://localhost:8000/docs`.*
