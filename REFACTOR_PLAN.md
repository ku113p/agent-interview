# Refactor Plan: Raw-First Data Collection Pipeline

## 1. Current State
The system currently operates as a text-only interview agent using LangGraph for orchestration.

*   **Ingestion:** Supports Telegram and HTTP API, but handles **text only**. Audio or other media inputs are currently ignored.
*   **State Management:** Uses `langgraph-checkpoint-postgres` to persist the conversation state (message history) as opaque blobs.
*   **Data Persistence:**
    *   `users` and `spheres` tables exist in PostgreSQL.
    *   **Missing:** There is no structural persistence for raw messages, transcripts, embeddings, or extracted facts in the relational database.
*   **Memory / Vector Search:**
    *   Code exists for `Mem0` (Qdrant) and `Redis` memory services in `src/infra`.
    *   **Disconnected Write Path:** The application logic (`src/app/graph`) does *not* currently write to these memory services. The `add()` methods are unused in the active flow.
    *   **Read Path:** The `Architect` node attempts to read from memory, but since nothing is written, it likely returns empty results.
*   **Summarization & Pruning:**
    *   Implemented in `src/app/graph/nodes/summarizer.py`.
    *   **Risk:** It prunes messages from the LangGraph state (`RemoveMessage`) *without* first ensuring they are durably archived in a queryable "raw" format. It relies solely on LangGraph checkpoints, which are designed for state recovery, not long-term data warehousing or re-indexing.

## 2. Target Architecture
The system will be refactored into a **Raw-First Data Collection Pipeline**.

### Data Flow
1.  **Ingestion:** Receives Text or Audio.
2.  **Immediate Persistence:** 
    *   Raw payload (audio blob) saved to **MinIO** (local Docker).
    *   Raw metadata/references saved to Postgres `raw_interactions`.
3.  **Processing (In-Flow):**
    *   If Audio -> Transcribe -> Save to `transcripts`.
    *   If Text -> Save to `transcripts`.
4.  **Enrichment:**
    *   Compute Embeddings (pgvector) using a configurable model (default: `text-embedding-3-small`) -> Save to `embeddings`.
    *   Extract Facts (LLM) -> Save to `facts` with provenance linking to `transcripts` offsets.
5.  **Runtime Barrier (`PersistRawNode`):**
    *   A dedicated LangGraph node runs before summarization.
    *   It guarantees that all messages currently in the context window are durably synced to the Postgres `transcripts` table.
6.  **Pruning (`SummarizerNode`):**
    *   Safe to remove messages from LangGraph state because they are secured in Postgres.

### PostgreSQL Schema

We will use `pgvector` for embeddings.

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Raw Interactions (The immutable source of truth)
CREATE TABLE raw_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    source_type VARCHAR NOT NULL, -- 'telegram', 'api', 'audio_upload'
    external_id VARCHAR, -- e.g., Telegram Message ID
    raw_content TEXT, -- For text messages
    audio_path VARCHAR, -- Path to MinIO object
    created_at TIMESTAMPTZ DEFAULT now(),
    meta JSONB DEFAULT '{}' -- Headers, extra metadata
);

-- 2. Transcripts / Normalized Segments
CREATE TABLE transcript_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interaction_id UUID REFERENCES raw_interactions(id),
    user_id UUID NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    role VARCHAR NOT NULL, -- 'user', 'assistant'
    segment_order INT NOT NULL, -- To reconstruct flow
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Embeddings (pgvector)
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_id UUID REFERENCES transcript_segments(id) ON DELETE CASCADE,
    model_name VARCHAR NOT NULL, -- e.g., 'text-embedding-3-small'
    model_version VARCHAR,
    vector VECTOR(1536), -- Adjust dim based on model
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON embeddings USING hnsw (vector vector_l2_ops);

-- 4. Facts (Structured Knowledge)
CREATE TABLE facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    category VARCHAR, -- e.g., 'biography', 'preference'
    content JSONB NOT NULL, -- The structured fact data
    confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. Provenance (Linking Facts to Source)
CREATE TABLE fact_provenance (
    fact_id UUID REFERENCES facts(id) ON DELETE CASCADE,
    segment_id UUID REFERENCES transcript_segments(id),
    start_offset INT, -- Character offset in segment
    end_offset INT,
    PRIMARY KEY (fact_id, segment_id)
);
```

## 3. Step-by-Step Refactor Plan

### Phase 1: Cleanup & Setup
- [x] **Remove Legacy Modules:**
    - Delete `src/infra/mem0` (✅).
    - Delete `src/infra/vector` (✅).
    - Remove `mem0ai` and `qdrant-client` from `pyproject.toml` (✅).
- [x] **Infrastructure:**
    - Add **MinIO** service to `docker-compose.yml`. (Done)
    - Update `pyproject.toml` to include `pgvector` and `minio` client. (Done)
- [x] **Database Schema Prep (Manual):**
    - Define `raw_interactions`, `transcript_segments`, `embeddings`, `facts`, `fact_provenance` in `src/infra/db/models.py`. (Done)
    - Delete legacy Alembic migrations; recreate schema manually from metadata or SQL. (Done)

### Phase 2: Core Persistence Infrastructure
- [ ] **Implement Repositories:**
    - Create `src/infra/db/repositories/interaction_repo.py` to handle `raw_interactions` and `transcript_segments`.
    - Create `src/infra/db/repositories/fact_repo.py` for `facts` and `provenance`.
    - Create `src/infra/db/repositories/vector_repo.py` for `embeddings` using `pgvector`.
    - Create `src/infra/storage/blob_storage.py` (MinIO implementation).
- [ ] **Refactor Memory Service:**
    - Re-implement `MemoryServiceProtocol` as `PostgresMemoryService` in `src/infra/db/memory_service.py`.
    - Implement `add()` to write to `facts` and `embeddings` tables.
    - Implement `search()` to query `embeddings` using SQL+pgvector.

### Phase 3: Pipeline Integration
- [ ] **Ingestion Upgrade:**
    - Modify `src/entrypoints/telegram` and `api` to write to `raw_interactions` *immediately* upon receipt.
- [ ] **Create `PersistRawNode`:**
    - Add `src/app/graph/nodes/persistence.py`.
    - Logic: Input `state['messages']` -> Iterate -> Write missing messages to `transcript_segments`.
    - Ensure Idempotency: Check if message ID already exists to avoid duplicates.
- [ ] **Fact Extraction Node (New):**
    - Add `ExtractorNode` (or integrate into `PersistRawNode` async):
        - Take recent segments.
        - Call LLM to extract facts.
        - Compute Embeddings (configurable model).
        - Write to `facts`, `provenance`, and `embeddings`.
- [ ] **Rewire Graph:**
    - Update `src/app/graph/workflow.py`:
        - Insert `PersistRawNode` before `SummarizerNode`.
        - Ensure flow is `... -> Interviewer -> PersistRaw -> Summarizer -> End`.

## 4. Risks & Rollback
- [ ] **Performance:** Synchronous embedding generation might add latency.
    - *Mitigation:* Make embedding/fact extraction an async background task, blocking only the *pruning* step on the *raw persistence* step.
- [ ] **Migration:** Starting fresh with new tables. No data migration required for conversation history (none exists structured).
- [ ] **Rollback:** Revert Git changes and downgrade Alembic migration.

## 5. Testing Strategy
- [ ] **Unit Tests:**
    - Test `PostgresMemoryService` with a mocked DB session.
    - Test `PersistRawNode` logic for idempotency.
- [ ] **Integration Tests:**
    - **Test Container:** Use `testcontainers-postgres` with `pgvector`.
    - **Full Cycle:** Send a message -> Verify `raw_interactions` (Postgres) -> Verify `audio` (MinIO, if applicable) -> Verify `transcript_segments` -> Verify `embeddings`.
- [ ] **Invariant Test:**
    - Simulate a long conversation.
    - Trigger `SummarizerNode`.
    - Assert that pruned messages are present in `transcript_segments`.
