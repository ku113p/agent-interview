# API Documentation

**Base URL:** `/v1`
**Format:** JSON

## 1. Chat (Agent Interaction)

### Send Message
`POST /chat/message`

Starts or continues a conversation with the agent.

**Request:**
```json
{
  "user_id": "uuid-string",
  "thread_id": "uuid-string",
  "message": "I want to talk about my career."
}
```

**Response:**
```json
{
  "thread_id": "uuid-string",
  "response": "Sure, tell me about your first job.",
  "step_count": 4,
  "agent_state": "interviewer"
}
```

### Debug State
`GET /chat/debug/state/{thread_id}`

Returns the full internal state of the LangGraph agent for debugging.

---

## 2. Spheres (Biography Topics)

### List User Spheres
`GET /spheres/user/{user_id}`

### Create Sphere
`POST /spheres/`

**Request:**
```json
{
  "user_id": "uuid-string",
  "name": "Career",
  "description": "My professional life",
  "status": "In Progress"
}
```

---

## 3. Users

### Create User
`POST /users/`

**Request:**
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "full_name": "Alice Bob",
  "profession": "Engineer"
}
```

### Get User
`GET /users/{user_id}`
`GET /users/by-email/{email}`
