# Harvest Optimizer API – Implementation Plan

**Target Agent**: `claude code`
**Context**: This plan builds upon the existing `backend/app/services/harvest` library.

---

## 1. Architecture Overview

We will wrap the Service Layer with a **FastAPI** application that manages state for long-running processes via a `RunManager`.

```mermaid
flowchart TB
    Client[Frontend/Client] <-->|WebSocket| WS[WebSocket Endpoint]
    Client <-->|HTTP| REST[REST API]
    
    subgraph "API Layer"
        WS <--> RunMgr[RunManager (State)]
        REST --> Repos[Repositories]
    end
    
    subgraph "Service Layer (Existing)"
        RunMgr --> Planner[HarvestPlanningServiceV2]
        Planner --> Optimizer[Optimizer Engine]
        Planner --> Audit[AuditService]
    end
    
    subgraph "Persistence"
        Repos --> DB[(PostgreSQL)]
        RunMgr --> DB
    end
```

---

## 2. Phase 1: Persistence Layer & Schema

**Goal**: Create tables to store plans, runs, configs, and sharing permissions.

### 2.1 Database Models (`app/db/models.py`)

Create SQLAlchemy models for:

1.  **`users`**: `id`, `email`, `hashed_password`, `full_name`, `role`
2.  **`harvest_plans`**: `id`, `owner_id`, `name`, `status`, `config` (JSON), `metrics` (JSON), `is_public`
3.  **`interval_configs`**: `id`, `owner_id`, `name`, `settings` (JSON), `is_public`
4.  **`optimization_runs`**: `id`, `owner_id`, `status`, `current_state` (JSON)
5.  **`shares`**: `id`, `resource_type` (plan/config), `resource_id`, `user_id`, `permission` (view/edit)
6.  **`audit_trails`**: `id`, `plan_id`, `entries` (JSON)

### 2.2 Repositories (`app/repositories/`)

Implement async repositories:
*   `UserRepository`
*   `PlanRepository` (includes logic for fetching shared plans)
*   `ConfigRepository`
*   `RunRepository`

---

## 3. Phase 2: State Management Core

**Goal**: Manage in-memory state for active optimization runs.

### 3.1 `RunManager` (`app/services/harvest/state/run_manager.py`)

Implementation details:
*   **Dictionary** of active `OptimizationRun` objects in memory.
*   **Methods**:
    *   `create_run(config, user)` -> initializes run, saves "PENDING" to DB.
    *   `start_run(run_id)` -> launches async task.
    *   `stream_run(run_id)` -> async generator yielding `IntervalResult`.
    *   `pause/resume/cancel` -> control flags.
*   **Integration**: Injects `AuditService` to log every state transition.

### 3.2 Service Layer Update (`HarvestPlanningServiceV2`)

*   Add `run_optimization_streaming()` method.
    *   *Change*: Instead of a tight loop, yield control after each interval.
    *   *Change*: Accept a `pause_event` to await user signal if configured.

---

## 4. Phase 3: WebSocket API

**Goal**: Enable interactive control.

### 4.1 Endpoint: `/ws/optimize`

**Protocol**:
1.  **Connect**: Auth via Token.
2.  **Client -> Server**:
    *   `{ "action": "create", "config": {...} }`
    *   `{ "action": "start", "run_id": "..." }`
    *   `{ "action": "pause", "run_id": "..." }`
    *   `{ "action": "proceed", "run_id": "..." }`
    *   `{ "action": "adjust", "run_id": "...", "params": {...} }`
3.  **Server -> Client**:
    *   `{ "type": "interval_complete", "data": { ...metrics... } }`
    *   `{ "type": "status_change", "status": "PAUSED" }`
    *   `{ "type": "error", "message": "..." }`

---

## 5. Phase 4: REST API & Sharing

**Goal**: HTTP CRUD management.

### 5.1 Endpoints (`app/api/v1/`)

*   **Users**: `/users/me`, `/users` (Search)
*   **Intervals**:
    *   `GET /intervals` (My + Shared + Public)
    *   `POST /intervals/{id}/share`
*   **Plans**:
    *   `GET /plans` (My + Shared + Public)
    *   `POST /plans/{id}/clone`
    *   `GET /plans/{id}/audit`
    *   `GET /plans/{id}/integrity`
*   **Comparisons**:
    *   `POST /runs/compare` -> Body: `[id1, id2]`. Returns diff object.

### 5.2 Sharing Service (`app/services/sharing_service.py`)

*   Logic to check permissions: `can_view(user, resource)`, `can_edit(user, resource)`.
*   Middleware/Dependency: `get_current_user_with_scope`.

---

## 6. Verification Plan

### 6.1 Automated Testing
1.  **Unit Tests**:
    *   `test_run_manager.py`: Mock service, verify state transitions.
    *   `test_sharing.py`: Verify ACL logic (Alice cannot see Bob's private plan).
2.  **Integration Tests**:
    *   `test_websocket_flow.py`: Use `TestClient` to simulate full WS session: Start -> Pause -> Adjust -> Finish.

### 6.2 Manual Verification Steps for Agent
1.  Spin up DB (`docker-compose` or local).
2.  Start API: `uvicorn app.main:app`.
3.  Create User A and User B.
4.  User A creates a Config, shares with User B.
5.  User B logs in, sees Shared Config.
6.  User B runs optimization using Shared Config via WebSocket.
7.  Verify Audit Trail shows User B as the actor.

---

## 7. Instructions for `claude code`

1.  **Scaffold**: Install `fastapi`, `uvicorn`, `websockets`, `sqlalchemy`.
2.  **Models**: Create `app/db` and migration scripts.
3.  **Core**: Implement `RunManager`.
4.  **Service**: Refactor `HarvestPlanningServiceV2` for streaming.
5.  **API**: Implement Routers.
6.  **Test**: Run `pytest`.
