# Harvest Planning Optimizer v2.0 - Implementation Plan

## Overview

This document provides a step-by-step implementation plan for refactoring the Harvest Planning Optimizer from MVP to a fully class-based, SOLID-compliant architecture. Each task includes a checkbox for tracking progress.

**Source PRD**: `harvest_optimizer_v2_prd.md`

---

## Phase 1: Domain Models (No Logic Changes)

**Goal**: Create domain objects as wrappers around existing DataFrames without changing optimization logic.

**Directory**: `backend/app/services/harvest/domain/`

### 1.1 Create Base Domain Infrastructure

- [x] **Task 1.1.1**: Create `domain/` directory structure
  ```
  domain/
  ├── __init__.py
  ├── models/
  │   ├── __init__.py
  │   ├── cycle.py
  │   ├── farm.py
  │   ├── house.py
  │   ├── harvest_plan.py
  │   ├── harvest_day.py
  │   ├── harvest_entry.py
  │   ├── harvest_event.py
  │   └── daily_forecast.py
  ├── enums/
  │   ├── __init__.py
  │   └── types.py
  └── exceptions/
      ├── __init__.py
      └── domain_exceptions.py
  ```

- [x] **Task 1.1.2**: Create `enums/types.py` with domain enumerations
  - `IntervalType` (SLAUGHTERHOUSE, MARKET)
  - `OptimizerStrategy` (BASE, WEIGHT, PCT, WEIGHT_AND_PCT)
  - `AuditAction` (OPTIMIZATION_STARTED, HOUSE_SELECTED, CONSTRAINT_RELAXED, OPTIMIZATION_COMPLETE)
  - `ExportFormat` (CSV, EXCEL, JSON)

- [x] **Task 1.1.3**: Create `exceptions/domain_exceptions.py`
  - `DomainValidationError`
  - `StockBalanceError`
  - `CapacityExceededError`
  - `InvalidDateRangeError`

### 1.2 Implement Core Domain Models

- [x] **Task 1.2.1**: Implement `DailyForecast` dataclass
  - Fields (mapped from CSV):
    - `date: datetime`
    - `weight: float` (from `avg_weight`)
    - `fcr: float`
    - `mortality: int` (from `expected_mortality`)
    - `projected_stock: int` (from `expected_stock`)
    - `feed_consumed: float` (from `cumulative_feed`)
    - `price: float`
    - `total_profit: float`
    - `profit_per_bird: float`
    - `profit_loss: float`
    - `priority: int`
    - `net_meat: float`
  - No methods required (pure data holder)

- [x] **Task 1.2.2**: Implement `HarvestEvent` dataclass
  - Fields: `event_id`, `house_id`, `farm_id`, `date`, `quantity`, `weight_at_harvest`, `fcr_at_harvest`, `created_at`
  - Method: `to_dict() -> Dict[str, Any]`

- [x] **Task 1.2.3**: Implement `HarvestEntry` dataclass
  - Fields: `entry_id`, `farm_id`, `house_id`, `date`, `quantity`, `weight`, `fcr`, `broiler_index`, `selection_score`, `selection_reason`
  - Method: `to_dict() -> Dict[str, Any]`

- [x] **Task 1.2.4**: Implement `House` class
  - Fields: `house_id`, `farm_id`, `initial_stock`, `current_stock`, `placement_date`, `daily_forecasts`, `harvest_history`
  - Methods:
    - `get_stock_on_date(date: datetime) -> int`
    - `get_weight_on_date(date: datetime) -> float`
    - `get_fcr_on_date(date: datetime) -> float`
    - `get_profit_on_date(date: datetime) -> float` - Returns `total_profit` from forecast
    - `get_profit_loss_on_date(date: datetime) -> float` - Returns `profit_loss` from forecast
    - `get_priority_on_date(date: datetime) -> int` - Returns `priority` from forecast
    - `apply_harvest(quantity: int, date: datetime) -> HarvestEvent`
    - `propagate_harvest() -> None`
    - `get_cumulative_harvested() -> int`
    - `get_remaining_capacity(max_pct: float) -> int`
    - `to_dict() -> Dict[str, Any]`

- [x] **Task 1.2.5**: Implement `Farm` class
  - Fields: `farm_id`, `name`, `houses` (List[House]), `organization_code`
  - Methods:
    - `get_house(house_id: str) -> House`
    - `get_available_stock(date: datetime) -> int`
    - `apply_harvest(harvest_event: HarvestEvent) -> None`
    - `get_harvested_summary() -> FarmHarvestSummary`
    - `to_dict() -> Dict[str, Any]`

- [x] **Task 1.2.6**: Implement `Cycle` class
  - Fields: `cycle_number`, `year`, `farms` (List[Farm]), `start_date`, `end_date`
  - Methods:
    - `get_farm(farm_id: str) -> Farm`
    - `get_total_stock() -> int`
    - `get_harvested_stock() -> int`
    - `to_dict() -> Dict[str, Any]`

- [x] **Task 1.2.7**: Implement `HarvestDay` class
  - Fields: `date`, `entries` (List[HarvestEntry]), `daily_capacity_used`, `capacity_limit`, `selection_reason`
  - Properties: `is_at_capacity: bool`
  - Methods:
    - `get_fcr() -> float`
    - `get_broiler_index() -> float`
    - `add_entry(entry: HarvestEntry) -> None`
    - `to_dict() -> Dict[str, Any]`

- [x] **Task 1.2.8**: Implement `HarvestPlan` class
  - Fields: `plan_id`, `cycle`, `intervals`, `harvest_days`, `config`, `created_at`, `created_by`, `checksum`
  - Methods:
    - `get_daily_summary() -> List[DailySummary]`
    - `get_farm_summary() -> List[FarmSummary]`
    - `get_house_summary() -> List[HouseSummary]`
    - `get_total_metrics() -> PlanMetrics`
    - `validate() -> ValidationResult`
    - `export_to_dataframe() -> pd.DataFrame`
    - `to_dict() -> Dict[str, Any]`

### 1.3 Implement Summary & Metrics Classes

- [x] **Task 1.3.1**: Implement `DailySummary` dataclass
  - Fields: `date`, `total_harvested`, `farm_count`, `house_count`, `avg_weight`, `avg_fcr`, `capacity_utilization`

- [x] **Task 1.3.2**: Implement `FarmSummary` dataclass
  - Fields: `farm_id`, `farm_name`, `total_harvested`, `house_count`, `avg_weight`, `avg_fcr`, `harvest_days`

- [x] **Task 1.3.3**: Implement `HouseSummary` dataclass
  - Fields: `house_id`, `farm_id`, `initial_stock`, `total_harvested`, `remaining_stock`, `harvest_events`

- [x] **Task 1.3.4**: Implement `PlanMetrics` dataclass
  - Fields: `total_harvested`, `total_farms`, `total_houses`, `harvest_days_count`, `avg_daily_harvest`, `avg_weight`, `avg_fcr`, `capacity_utilization`

- [x] **Task 1.3.5**: Implement `ValidationResult` dataclass
  - Fields: `is_valid`, `errors` (List[str]), `warnings` (List[str])

### 1.4 Data Loader

**Data Source**: `data/raw/predicted_data_combined.csv`

The DataLoader is responsible for loading the prediction CSV and initializing all domain objects (`Cycle`, `Farm`, `House` with `DailyForecast`).

- [x] **Task 1.4.1**: Create `loaders/` directory structure
  ```
  loaders/
  ├── __init__.py
  ├── data_loader.py
  └── dataframe_exporter.py
  ```

- [x] **Task 1.4.2**: Implement `DataLoader` class in `loaders/data_loader.py`
  - **Constructor**: `data_path: str = "data/raw/predicted_data_combined.csv"`
  - **Methods**:
    - `load() -> pd.DataFrame` - Load and cache the prediction data
    - `get_raw_dataframe() -> pd.DataFrame` - Return raw DataFrame for backward compatibility
    - `build_cycle(cycle_number: int, year: int) -> Cycle` - Build complete Cycle with Farms/Houses
    - `_build_farms(df: pd.DataFrame) -> List[Farm]` - Build Farm objects from DataFrame
    - `_build_houses(farm_df: pd.DataFrame, farm_id: str) -> List[House]` - Build House objects
    - `_build_forecasts(house_df: pd.DataFrame) -> List[DailyForecast]` - Build DailyForecast objects

- [x] **Task 1.4.3**: Update `DailyForecast` dataclass to include all CSV columns
  - Fields from CSV:
    - `date: datetime`
    - `weight: float` (from `avg_weight`)
    - `fcr: float`
    - `mortality: int` (from `expected_mortality`)
    - `projected_stock: int` (from `expected_stock`)
    - `feed_consumed: float` (from `cumulative_feed`)
    - `price: float`
    - `total_profit: float`
    - `profit_per_bird: float`
    - `profit_loss: float`
    - `priority: int`
    - `net_meat: float`

- [x] **Task 1.4.4**: Add profit/priority methods to `House` class
  - `get_profit_on_date(date: datetime) -> float`
  - `get_profit_loss_on_date(date: datetime) -> float`
  - `get_priority_on_date(date: datetime) -> int`

- [x] **Task 1.4.5**: Create test file `tests/loaders/test_data_loader.py`
  - Test CSV loading
  - Test Cycle/Farm/House construction
  - Test DailyForecast field mapping
  - Validate data integrity (all farms/houses present)

### 1.5 Domain Model Tests

- [x] **Task 1.5.1**: Create test file `tests/domain/test_house.py`
  - Test stock balance invariants
  - Test harvest application
  - Test forecast lookups
  - Test profit/priority methods

- [x] **Task 1.5.2**: Create test file `tests/domain/test_farm.py`
  - Test house aggregation
  - Test available stock calculation

- [x] **Task 1.5.3**: Create test file `tests/domain/test_cycle.py`
  - Test farm aggregation
  - Test total stock calculation

- [x] **Task 1.5.4**: Create test file `tests/domain/test_harvest_plan.py`
  - Test summary generation
  - Test validation logic
  - Test DataFrame export

---

## Phase 2: Harvest Interval Configuration

**Goal**: Create rich configuration objects for harvest intervals.

**Directory**: `backend/app/services/harvest/domain/models/`

### 2.1 Implement Interval Configuration

- [x] **Task 2.1.1**: Implement `HarvestInterval` dataclass
  - Fields:
    - `name`, `interval_type` (IntervalType)
    - `daily_capacity` (default 30000)
    - `min_weight`, `max_weight`, `weight_step` (default 0.05)
    - `starting_pct`, `pct_step`, `max_pct`, `max_pct_per_house`
    - `start_date`, `end_date`, `excluded_days`, `excluded_weekdays`
    - `optimizer_strategy` (OptimizerStrategy)
  - Methods:
    - `get_valid_dates(cycle: Cycle) -> List[datetime]`
    - `validate_constraints() -> ValidationResult`
    - `to_dict() -> Dict[str, Any]`

- [x] **Task 2.1.2**: Implement `OptimizationConfig` dataclass
  - Fields: `optimization_mode`, `intervals`, `price_forecast_source`, `target_fcr`, `additional_params`
  - Method: `validate() -> ValidationResult`

### 2.2 Interval Configuration Tests

- [x] **Task 2.2.1**: Create test file `tests/domain/test_harvest_interval.py`
  - Test valid date generation
  - Test constraint validation
  - Test excluded days logic

---

## Phase 3: Abstract Optimizer Interface

**Goal**: Create pluggable optimization strategies via abstract base class.

**Directory**: `backend/app/services/harvest/optimizers/`

### 3.1 Create Optimizer Infrastructure

- [x] **Task 3.1.1**: Create `optimizers/` directory structure
  ```
  optimizers/
  ├── __init__.py
  ├── base.py
  ├── net_meat_optimizer.py
  ├── min_fcr_optimizer.py
  ├── target_fcr_optimizer.py
  ├── profit_optimizer.py
  ├── daily_profit_loss_optimizer.py
  └── legacy_wrapper.py
  ```

- [x] **Task 3.1.2**: Implement `BaseHarvestOptimizer` ABC in `base.py`
  - Abstract methods:
    - `optimize(cycle, interval, existing_harvest) -> HarvestPlan`
    - `score_candidate(house, date, quantity) -> float`
    - `get_optimization_mode() -> str`
    - `assign_priorities(candidates: List[HouseCandidate]) -> List[HouseCandidate]` - Rank candidates and assign priority
  - Concrete helper methods:
    - `_get_candidates(cycle, interval, date) -> List[HouseCandidate]`
    - `_create_harvest_day(date, allocations) -> HarvestDay`
    - `_select_by_priority(candidates, capacity) -> List[HouseCandidate]` - Select top priority candidates up to capacity

- [x] **Task 3.1.3**: Implement `HouseCandidate` dataclass
  - Fields: `house`, `farm`, `date`, `available_quantity`, `weight`, `fcr`, `score`, `priority` (mutable, assigned by optimizer)

### 3.2 Implement Concrete Optimizers

- [x] **Task 3.2.1**: Implement `NetMeatOptimizer`
  - Scoring: `quantity * weight`
  - Mode: "net_meat"

- [x] **Task 3.2.2**: Implement `MinFCROptimizer`
  - **Purpose**: Minimize Feed Conversion Ratio by assigning priority based on FCR ranking
  - **Scoring**: `-fcr` (lower FCR is better)
  - **Methods**:
    - `score_candidate(house, date, quantity) -> float`
    - `assign_priorities(candidates) -> List[HouseCandidate]` - Ranks by FCR ascending, assigns priority 1 to best
  - **Mode**: "min_fcr"

- [x] **Task 3.2.3**: Implement `TargetFCROptimizer`
  - **Purpose**: Achieve target FCR by assigning priority based on distance from target
  - **Constructor**: `target_fcr: float`
  - **Scoring**: `-abs(fcr - target_fcr)` (closest to target is better)
  - **Methods**:
    - `score_candidate(house, date, quantity) -> float`
    - `assign_priorities(candidates) -> List[HouseCandidate]` - Ranks by proximity to target FCR
  - **Mode**: "target_fcr"

- [x] **Task 3.2.4**: Implement `ProfitPriorityOptimizer`
  - **Purpose**: Combined optimizer that ranks houses by both total profit and daily profit loss
  - **Priority Calculation**:
    1. Rank all houses by `total_profit` (descending) → `profit_rank`
    2. Rank all houses by `profit_loss` (descending) → `profit_loss_rank`
    3. Combined priority = weighted average of ranks
    4. Lower priority number = higher selection preference
  - **Constructor**: `profit_weight: float = 0.5, profit_loss_weight: float = 0.5`
  - **Methods**:
    - `score_candidate(house, date, quantity) -> float` - Returns `-priority` (lower priority = higher score)
    - `assign_priorities(candidates) -> List[HouseCandidate]` - Computes combined priority from profit and profit_loss ranks
  - **Mode**: "profit_priority"
  - **Note**: This replaces the separate `ProfitOptimizer` and `DailyProfitLossOptimizer` from the original design. The optimizer reads `total_profit` and `profit_loss` from the house's daily forecasts (loaded from CSV).

### 3.3 Legacy Wrapper

- [ ] **Task 3.3.1**: Implement `LegacyProfitOptimizerWrapper` *(skipped - no legacy code)*
  - Wraps existing `ProfitHarvestOptimizer`
  - Implements `BaseHarvestOptimizer` interface
  - Used for parallel validation

- [ ] **Task 3.3.2**: Implement `LegacySlaughterhouseOptimizerWrapper` *(skipped - no legacy code)*
  - Wraps existing `SlaughterhouseOptimizer`
  - Implements `BaseHarvestOptimizer` interface

### 3.4 Optimizer Factory

- [x] **Task 3.4.1**: Implement `OptimizerFactory`
  - Method: `create(mode: str, config: OptimizationConfig) -> BaseHarvestOptimizer`
  - Supported modes:
    - `"net_meat"` - NetMeatOptimizer
    - `"min_fcr"` - MinFCROptimizer
    - `"target_fcr"` - TargetFCROptimizer (requires `target_fcr` in config)
    - `"profit_priority"` - ProfitPriorityOptimizer (combined profit + profit_loss ranking)
    - `"legacy_profit"` - LegacyProfitOptimizerWrapper
    - `"legacy_slaughterhouse"` - LegacySlaughterhouseOptimizerWrapper

### 3.5 Optimizer Tests

- [x] **Task 3.5.1**: Create test file `tests/optimizers/test_base_optimizer.py`
  - Test candidate generation
  - Test harvest day creation

- [x] **Task 3.5.2**: Create test file `tests/optimizers/test_scoring.py`
  - Test each optimizer's scoring logic

- [ ] **Task 3.5.3**: Create integration test `tests/optimizers/test_legacy_comparison.py`
  - Compare new optimizers against legacy for identical inputs
  - Generate diff reports

---

## Phase 4: Constraint-Breaking Strategies

**Goal**: Extract allocation strategies from SlaughterhouseOptimizer.

**Directory**: `backend/app/services/harvest/strategies/`

### 4.1 Create Strategy Infrastructure

- [x] **Task 4.1.1**: Create `strategies/` directory structure
  ```
  strategies/
  ├── __init__.py
  ├── base.py
  ├── base_strategy.py
  ├── weight_expansion_strategy.py
  └── weight_and_pct_strategy.py
  ```

- [x] **Task 4.1.2**: Implement `AllocationStrategy` ABC in `base.py`
  - Abstract method: `allocate(candidates, daily_capacity, interval) -> List[HarvestAllocation]`

- [x] **Task 4.1.3**: Implement `HarvestAllocation` dataclass
  - Fields: `house`, `farm`, `quantity`, `weight`, `fcr`, `constraint_relaxation` (Optional[str])
  - Additional fields for constraint tracking: `original_min_weight`, `original_max_weight`, `relaxed_min_weight`, `relaxed_max_weight`, `original_max_pct`, `relaxed_max_pct`

### 4.2 Implement Concrete Strategies

- [x] **Task 4.2.1**: Implement `BaseStrategy`
  - Respects all weight/pct parameters strictly
  - No constraint relaxation

- [x] **Task 4.2.2**: Implement `WeightExpansionStrategy`
  - Expands weight range by `weight_step` increments
  - Tracks relaxation in allocation

- [x] **Task 4.2.3**: Implement `WeightAndPctStrategy`
  - Expands weight range AND increases pct
  - Stops when daily capacity met
  - Tracks all relaxations

### 4.3 Strategy Factory

- [x] **Task 4.3.1**: Implement `StrategyFactory`
  - Method: `create(strategy: OptimizerStrategy) -> AllocationStrategy`

### 4.4 Strategy Tests

- [x] **Task 4.4.1**: Create test file `tests/strategies/test_base_strategy.py`
- [x] **Task 4.4.2**: Create test file `tests/strategies/test_weight_expansion.py`
- [x] **Task 4.4.3**: Create test file `tests/strategies/test_weight_and_pct.py`
- [ ] **Task 4.4.4**: Create integration test comparing against legacy SlaughterhouseOptimizer *(skipped - no legacy code)*

---

## Phase 5: Audit & Data Integrity

**Goal**: Implement comprehensive audit trail and data validation.

**Directory**: `backend/app/services/harvest/audit/`

### 5.1 Create Audit Infrastructure

- [x] **Task 5.1.1**: Create `audit/` directory structure
  ```
  audit/
  ├── __init__.py
  ├── models.py
  ├── audit_service.py
  └── data_integrity_service.py
  ```

### 5.2 Implement Audit Models

- [x] **Task 5.2.1**: Implement `AuditEntry` dataclass
  - Fields: `entry_id`, `timestamp`, `action`, `user_id`, `cycle_id`, `interval_name`, `farm_id`, `house_id`, `date`, `parameters`, `reason`, `before_state`, `after_state`
  - Methods: `to_dict()`, `to_json()`, `from_dict()`

- [x] **Task 5.2.2**: Implement `Discrepancy` dataclass
  - Fields: `farm_id`, `house_id`, `date`, `field_name`, `planned_value`, `actual_value`, `variance`, `variance_pct`, `severity`
  - Auto-calculates variance and severity classification

- [x] **Task 5.2.3**: Implement `ReconciliationReport` dataclass
  - Fields: `plan_id`, `reconciled_at`, `total_planned`, `total_actual`, `variance`, `discrepancies`
  - Properties: `high_severity_discrepancies`, `has_critical_issues`
  - Methods: `to_dict()`, `to_json()`

### 5.3 Implement Audit Service

- [x] **Task 5.3.1**: Implement `AuditService` class
  - Methods:
    - `log_optimization_start(config) -> str` (returns optimization_id)
    - `log_house_selection(optimization_id, house_id, farm_id, date, quantity, score, reason, ...)`
    - `log_constraint_relaxed(optimization_id, constraint_name, old_value, new_value, reason, ...)`
    - `log_optimization_complete(optimization_id, plan, metrics)`
    - `log_custom_event(...)` for flexible logging
    - `get_audit_trail(optimization_id) -> List[AuditEntry]`
    - `get_entries_by_action(optimization_id, action) -> List[AuditEntry]`
    - `get_entries_for_house(optimization_id, farm_id, house_id) -> List[AuditEntry]`
    - `export_audit_trail(optimization_id, format) -> str` (JSON, CSV)
    - `get_optimization_summary(optimization_id) -> dict`
    - `clear_audit_trail(optimization_id)`

- [ ] **Task 5.3.2**: Implement audit persistence (database integration) *(deferred to Phase 6)*
  - Table: `harvest_audit_log`
  - Columns: match AuditEntry fields

### 5.4 Implement Data Integrity Service

- [x] **Task 5.4.1**: Implement `DataIntegrityService` class
  - Methods:
    - `validate_stock_balance(cycle) -> ValidationResult`
    - `validate_capacity_limits(plan) -> ValidationResult`
    - `calculate_checksum(plan) -> str` (SHA-256)
    - `verify_checksum(plan) -> bool`
    - `reconcile_with_actuals(plan, actuals) -> ReconciliationReport`
    - `validate_plan_consistency(plan) -> ValidationResult`

### 5.5 Audit Tests

- [x] **Task 5.5.1**: Create test file `tests/audit/test_audit_service.py` (17 tests)
- [x] **Task 5.5.2**: Create test file `tests/audit/test_data_integrity.py` (28 tests)
- [x] **Task 5.5.3**: Test checksum determinism (same input = same checksum)

---

## Phase 6: Standalone Service

**Goal**: Create complete standalone service with persistence.

**Directory**: `backend/app/services/harvest/`

### 6.1 Database Schema

- [ ] **Task 6.1.1**: Create Alembic migration for `harvest_plans` table *(deferred - requires DB setup)*
  - Columns: `id`, `plan_id`, `cycle_id`, `config_json`, `metrics_json`, `checksum`, `created_at`, `created_by`, `status`

- [ ] **Task 6.1.2**: Create Alembic migration for `harvest_plan_entries` table *(deferred - requires DB setup)*
  - Columns: `id`, `plan_id`, `date`, `farm_id`, `house_id`, `quantity`, `weight`, `fcr`, `selection_reason`

- [ ] **Task 6.1.3**: Create Alembic migration for `harvest_audit_log` table *(deferred - requires DB setup)*
  - Columns: match AuditEntry fields

### 6.2 Storage Service

- [x] **Task 6.2.1**: Implement `StorageService` for S3 integration
  - Implemented `StorageBackend` ABC
  - Implemented `LocalStorageBackend` for development/testing
  - Implemented `S3StorageBackend` for production (lazy boto3 loading)
  - Methods:
    - `upload_plan_export(plan_id, cycle_id, file_bytes, format) -> str`
    - `get_signed_url(plan_id, cycle_id, filename, expiration) -> str`
    - `download_export(plan_id, cycle_id, filename) -> bytes`
    - `delete_plan_exports(plan_id, cycle_id) -> int`
    - `list_plan_exports(plan_id, cycle_id) -> list[dict]`
    - `upload_audit_export(optimization_id, cycle_id, audit_json) -> str`

- [x] **Task 6.2.2**: Configure S3 bucket structure
  - Path: `harvest-plans/{cycle_id}/{plan_id}/{filename}`

### 6.3 Implement HarvestPlanningServiceV2

- [x] **Task 6.3.1**: Implement service constructor
  - Dependencies: `data_loader`, `audit_service`, `integrity_service`, `storage_service`
  - In-memory plan storage for testing (DB integration deferred)

- [x] **Task 6.3.2**: Implement `create_optimization(cycle_number, year, config, user_id) -> HarvestPlan`
  - Load cycle data via DataLoader
  - Create optimizer via OptimizerFactory
  - Execute optimization for each interval
  - Log audit trail
  - Calculate checksum
  - Return plan

- [x] **Task 6.3.3**: Implement `save_plan(plan, user_id) -> str`
  - Validate plan via DataIntegrityService
  - Calculate/update checksum
  - Save to in-memory storage (DB integration deferred)
  - Return plan_id

- [x] **Task 6.3.4**: Implement `get_plan(plan_id) -> dict | None`
  - Load from in-memory storage
  - Return plan data or None

- [x] **Task 6.3.5**: Implement `list_plans(cycle_id, user_id, status) -> list[dict]`
  - Filter stored plans
  - Return summaries

- [x] **Task 6.3.6**: Implement `export_plan(plan, format) -> str`
  - Generate export (CSV/JSON)
  - Upload to storage
  - Return URL

- [x] **Task 6.3.7**: Implement additional methods:
  - `validate_plan(plan) -> ValidationResult`
  - `reconcile_plan(plan, actuals) -> dict`
  - `delete_plan(plan_id) -> bool`
  - `export_audit_trail(optimization_id, cycle_id) -> str`
  - `get_optimization_summary(optimization_id) -> dict`
  - `quick_optimize(...)` convenience method

### 6.4 Data Loader Integration

- [x] **Task 6.4.1**: DataLoader already implemented in Phase 1
  - Method: `build_cycle(cycle_number, year) -> Cycle`
  - Converts CSV data to domain objects

- [x] **Task 6.4.2**: DataFrameExporter via HarvestPlan.export_to_dataframe()
  - Converts domain objects back to DataFrames

### 6.5 API Endpoints (Optional)

- [ ] **Task 6.5.1**: Create FastAPI router `api/v2/harvest/` *(deferred)*
- [ ] **Task 6.5.2**: Implement `POST /optimize` endpoint *(deferred)*
- [ ] **Task 6.5.3**: Implement `GET /plans` endpoint *(deferred)*
- [ ] **Task 6.5.4**: Implement `GET /plans/{plan_id}` endpoint *(deferred)*
- [ ] **Task 6.5.5**: Implement `GET /plans/{plan_id}/export` endpoint *(deferred)*
- [ ] **Task 6.5.6**: Implement `GET /plans/{plan_id}/audit` endpoint *(deferred)*

### 6.6 Service Tests

- [x] **Task 6.6.1**: Create test file `tests/storage/test_storage_service.py` (18 tests)
- [x] **Task 6.6.2**: Create test file `tests/services/test_harvest_planning_service_v2.py` (15 tests)
- [ ] **Task 6.6.3**: Create integration test with real database *(deferred)*
- [ ] **Task 6.6.4**: Create integration test with S3 (localstack) *(deferred)*

---

## Phase 7: Migration & Validation ⏭️ SKIPPED

**Status**: Skipped - No legacy code exists for this greenfield implementation.

**Original Goal**: Ensure new system produces identical results to legacy.

> [!NOTE]
> Phase 7 was designed for parallel validation against legacy code. Since this is a completely new implementation without existing legacy code to compare against, this phase has been skipped.

### 7.1 Parallel Execution Framework *(Not Required)*

- [~] **Task 7.1.1**: Implement `ParallelValidator` *(skipped - no legacy code)*
- [~] **Task 7.1.2**: Create comparison metrics *(skipped - no legacy code)*

### 7.2 Migration Scripts *(Not Required)*

- [~] **Task 7.2.1**: Script to migrate existing plans to v2 schema *(skipped - no existing plans)*
- [~] **Task 7.2.2**: Script to validate migrated data integrity *(skipped)*

### 7.3 Feature Flag *(Not Required)*

- [~] **Task 7.3.1**: Implement feature flag for v2 service *(skipped - v2 is the only version)*

---

## Completion Checklist

### Phase Completion Status

- [x] **Phase 1 Complete**: All domain models implemented and tested
- [x] **Phase 2 Complete**: Interval configuration implemented and tested
- [x] **Phase 3 Complete**: Abstract optimizer interface implemented with all concrete optimizers
- [x] **Phase 4 Complete**: Allocation strategies extracted and tested (192 tests passing)
- [x] **Phase 5 Complete**: Audit and data integrity systems operational (237 tests passing)
- [x] **Phase 6 Complete**: Standalone service with storage implemented (270 tests passing)
  - Note: Database migrations and API endpoints deferred for later integration
- [~] **Phase 7 Skipped**: No legacy code to validate against

### Final Validation

- [x] All unit tests passing (270 tests)
- [~] All integration tests passing *(DB/S3 integration tests deferred)*
- [~] Legacy comparison shows identical results *(skipped - no legacy)*
- [x] Audit trail captures all decisions
- [x] Data integrity checks pass
- [~] S3 exports working *(LocalStorageBackend tested, S3 backend implemented but not integration tested)*
- [~] API endpoints functional *(deferred)*

### Implementation Complete ✅

**Date**: January 2026  
**Total Tests**: 270 passing  
**Code Coverage**: Domain, Optimizers, Strategies, Audit, Storage, Services

---

## Notes for Agents

1. **Check off tasks** as you complete them by changing `- [ ]` to `- [x]`
2. **Follow phase order** - each phase builds on the previous
3. **Run tests** after completing each task
4. **Commit frequently** with descriptive messages
5. **Update this document** if you discover additional tasks needed
6. **Reference PRD** for detailed specifications: `harvest_optimizer_v2_prd.md`

---

## File Structure Reference

```
backend/app/services/harvest/
├── domain/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── cycle.py
│   │   ├── farm.py
│   │   ├── house.py
│   │   ├── harvest_plan.py
│   │   ├── harvest_day.py
│   │   ├── harvest_entry.py
│   │   ├── harvest_event.py
│   │   ├── harvest_interval.py
│   │   ├── daily_forecast.py
│   │   └── summaries.py
│   ├── enums/
│   │   ├── __init__.py
│   │   └── types.py
│   └── exceptions/
│       ├── __init__.py
│       └── domain_exceptions.py
├── optimizers/
│   ├── __init__.py
│   ├── base.py
│   ├── factory.py
│   ├── net_meat_optimizer.py
│   ├── min_fcr_optimizer.py
│   ├── target_fcr_optimizer.py
│   ├── profit_priority_optimizer.py   # Combined profit + profit_loss optimizer
│   └── legacy_wrapper.py
├── strategies/
│   ├── __init__.py
│   ├── base.py
│   ├── factory.py
│   ├── base_strategy.py
│   ├── weight_expansion_strategy.py
│   └── weight_and_pct_strategy.py
├── audit/
│   ├── __init__.py
│   ├── models.py
│   ├── audit_service.py
│   └── data_integrity_service.py
├── storage/
│   ├── __init__.py
│   └── storage_service.py
├── loaders/
│   ├── __init__.py
│   ├── data_loader.py          # Loads CSV and builds domain objects
│   └── dataframe_exporter.py   # Exports domain objects back to DataFrames
├── services/
│   ├── __init__.py
│   └── harvest_planning_service_v2.py
└── api/
    └── v2/
        ├── __init__.py
        └── harvest_router.py
```

---

*Last Updated: 2026-01-23*
