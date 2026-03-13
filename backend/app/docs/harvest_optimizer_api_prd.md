# Harvest Optimizer API – Product Requirements Document

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Approved for Implementation

---

## 1. Executive Summary

The **Harvest Optimizer API** transforms the existing optimization library into a multi-user, interactive SaaS backend. It enables users to run complex harvest scenarios in real-time, intervening interval-by-interval to adjust parameters based on intermediate results.

Key capabilities include **WebSocket streaming** of results, **parallel run comparison**, **state management** (pause/resume), and granular **sharing/permissions** for teams.

---

## 2. Key Features

### 2.1 Interactive Optimization (WebSockets)
*   **Real-time Streaming**: Users see harvest results for each interval as they happen, rather than waiting for the full cycle to complete.
*   **Human-in-the-Loop**: Users can configure the system to "pause" after specific intervals to allow for manual review and parameter adjustment (e.g., "Relax weight constraints for the next interval").
*   **Live Metrics**: Stream key metrics (Total Harvested, Avg FCR, Avg Weight) continuously.

### 2.2 Multi-Run Comparison
*   **Parallel Execution**: Run multiple optimization scenarios (e.g., "Aggressive vs. Conservative") simultaneously.
*   **Side-by-Side Diff**: Compare results of different runs to highlight trade-offs (e.g., +5% meat yield vs. +0.02 FCR).
*   **Branching**: Clone an existing run's configuration to test a "what-if" scenario from a specific point.

### 2.3 State Management
*   **Persistence**: In-progress runs are persisted. If a client disconnects, they can reconnect and resume the session.
*   **Lifecycle Control**:
    *   `Start`: Begin processing.
    *   `Pause`: Stop after current interval.
    *   `Resume`: Continue from paused state.
    *   `Cancel`: Abort and cleanup.

### 2.4 Data Integrity & Audit
*   **Audit Trail**: Every automated decision and manual adjustment is logged (User, Timestamp, Action, Reason).
*   **Integrity Reports**: Every plan includes a cryptographic checksum and validation report (stock balance, capacity limits).

### 2.5 User Management & Sharing
*   **Ownership**: Every Plan, Run, and Config is owned by a User.
*   **Sharing Model**:
    *   **Private**: Owner only.
    *   **Shared**: Explicit grant to other users (Read vs. Edit).
    *   **Public**: Accessible by anyone in the organization.
*   **Reusable Configs**: Save "Interval Templates" (e.g., "Summer Standard", "High Capacity") for team-wide use.

---

## 3. User Flows

### 3.1 The "Interactive Run" Flow
1.  **Configure**: User selects a `Cycle` and loads a `IntervalConfig`.
2.  **Connect**: Client opens WebSocket to `/ws/optimize`.
3.  **Start**: Client sends `create_run` -> `start_run`.
4.  **Monitor**: Server streams `interval_complete` events.
5.  **Intervene** (Optional):
    *   User sees Interval 1 result.
    *   User sends `pause`.
    *   User reviews data, sends `adjust` (e.g., change max_weight).
    *   User sends `proceed`.
6.  **Finalize**: Run completes. Server creates a saved `HarvestPlan`.

### 3.2 The "Comparison" Flow
1.  **Selection**: User selects 2-3 previously completed Runs or Plans.
2.  **Compare**: System aligns them by Interval Index.
3.  **Diff**: Returns a difference table focusing on:
    *   Total Net Meat
    *   Average FCR
    *   Days to Completion
    *   Remaining Stock

### 3.3 The "Sharing" Flow
1.  **Share**: User Alice clicks "Share Run" -> enters Bob's email -> selects "View Only".
2.  **Notify**: Bob sees the run in his "Shared with Me" list.
3.  **Access**: Bob can view the playback and metrics, but cannot `adjust` or `delete`.

---

## 4. Technical Requirements

### 4.1 System Architecture
*   **Framework**: FastAPI (Async Python).
*   **Protocol**:
    *   **HTTP**: CRUD for Plans, Configs, Users.
    *   **WebSocket**: Interactive Optimization Control.
*   **Database**: PostgreSQL (via SQLAlchemy) for relational data.
*   **State Store**: In-memory `RunManager` backed by DB for persistence.

### 4.2 Data Models

#### Core Entities
*   **HarvestPlan**: The finalized, immutable record of a harvest.
*   **OptimizationRun**: The mutable, in-progress session.
*   **IntervalConfig**: Reusable optimization settings.
*   **AuditEntry**: Log of a single event/decision.

#### Relationships
*   `User` (1) <---> (N) `HarvestPlan`
*   `User` (1) <---> (N) `IntervalConfig`
*   `HarvestPlan` (1) <---> (1) `AuditTrail`
*   `HarvestPlan` (1) <---> (1) `IntegrityReport`

### 4.3 Security
*   **Authentication**: Bearer Token (JWT) required for all endpoints.
*   **Authorization**: Resource-level permission checks (Owner or Shared-With).

---

## 5. Implementation Roadmap

Phase 1: **Foundation** (State Manager, Domain Models, Persistence)
Phase 2: **API Core** (REST Endpoints for Plans/Configs)
Phase 3: **Interactivity** (WebSocket Protocol & Streamer)
Phase 4: **Collaboration** (User Auth, Sharing Logic)
