# Agent Interview API Documentation

**Base URL**: `http://localhost:8000`  
**Version**: v1

## Overview
This API serves as the interface for the Agent Interview platform. It follows a RESTful design and allows clients to manage user profiles, define context spheres, and interact with the conversational AI agent.

## Authentication
Currently, the API is **open** and does not require authentication headers. 
*Note: This is intended for development and MVP phases. Future versions will likely implement Bearer Token authentication.*

---

## 🛠 Usage with Postman
To interact with this API using Postman, you can generate an OpenAPI specification file using the provided helper script:

1. Run the generation script:
   ```bash
   python scripts/generate_schema.py
   ```
2. Import the generated file `docs/openapi.json` into Postman.
   - Click **Import** -> **File** -> Select `docs/openapi.json`.
3. This will create a collection with all available endpoints pre-configured.

---

## 🟢 System Endpoints

### Health Check
`GET /health/`

Checks the operational status of the application and its dependencies (PostgreSQL, Redis).

**Response (200 OK):**
```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok"
}
```

---

## 💬 Chat Endpoints

### Send Message
`POST /v1/chat/message`

The main entry point for the conversational agent. Sending a message here triggers the LangGraph workflow.

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | The user's UUID (must match a created user). |
| `message` | string | Yes | The text content to send to the agent. |
| `thread_id` | string | No | Custom thread ID for maintaining conversation state. Defaults to "default_thread". |

**Example:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "I want to improve my system design skills.",
  "thread_id": "conversation-123"
}
```

**Response (200 OK):**
```json
{
  "response": "That's a great goal! I can act as an interviewer to help you practice. Shall we start?",
  "step_count": 4
}
```

### Debug Thread State
`GET /v1/chat/debug/state/{thread_id}`

Retrieves the raw internal state of a specific conversation thread. Useful for debugging agent memory and planning.

---

## 👤 User Endpoints

### Create User
`POST /v1/users/`

Creates a new user profile. 
**Note**: This endpoint manually validates the input dictionary.

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string (UUID) | Yes | A unique UUID for the user. |
| `email` | string | Yes | The user's email address. |
| `full_name` | string | No | The user's full name. |
| `profession` | string | No | Example: "Software Engineer". |
| `experience_years` | integer | No | Years of professional experience. |

**Example:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "jane.doe@example.com",
  "full_name": "Jane Doe",
  "profession": "Software Architect",
  "experience_years": 8
}
```

### Get User
`GET /v1/users/{user_id}`  
`GET /v1/users/by-email/{email}`

### Update User
`PUT /v1/users/{user_id}`

Updates an existing user profile. Only provided fields are updated.

**Updatable Fields:** `email`, `full_name`, `profession`, `experience_years`.

---

## 🌐 Sphere Endpoints

Spheres represent distinct contexts, projects, or domains a user is working on.

### Create Sphere
`POST /v1/spheres/`

Creates a new sphere and links it to a user.

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string (UUID) | Yes | The ID of the owner user. |
| `name` | string | Yes | Name of the sphere (e.g., "Main Project"). |
| `description` | string | No | Brief description of the context. |
| `status` | string | No | Status (e.g., "Not Started", "In Progress"). |

**Example:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Backend Refactor",
  "description": "Migrating the legacy monolith to microservices.",
  "status": "In Progress"
}
```

### List User Spheres
`GET /v1/spheres/user/{user_id}`

Returns a list of all spheres associated with a specific user.

---

## 🔌 Integrations

### Telegram Webhook
`POST /telegram/webhook`

**Internal Endpoint**. Receives push updates from the Telegram Bot API.
- Processes messages in the background.
- Returns `200 OK` immediately to acknowledge receipt.
