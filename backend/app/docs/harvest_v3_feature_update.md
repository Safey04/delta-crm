# Harvest Optimizer V3 - Feature Update & Bug Fixes

## 1. Overview
This document outlines the implementation plan to address critical bugs and introduce new "Step-by-Step" execution logic to the Harvest Optimizer.

**References**:
- `harvest_optimizer_v2_prd.md`
- `harvest_v2_implmentation_plan.md`

---

## 2. Bug Fixes

### 2.1 Save Config Failure (422 Unprocessable Content)
**Issue**: The frontend sends an Array of intervals as the `settings` payload, but the backend Pydantic schema expects a Dictionary (`dict`).
**Fix**:
- **Frontend**: Update `SavedConfigPanel.tsx` to wrap intervals in a root object: `{ "intervals": [...] }`.
- **Backend**: Ensure `IntervalConfigCreate` schema remains `dict` or explicitly typed to `dict[str, Any]`.

### 2.2 Infinite Polling (UI Hook)
**Issue**: The frontend hook `useOptimizationREST` keeps polling because the run status never transitions to a terminal state (completed/failed) in a way the frontend recognizes, or the backend fails to commit the completion state.
**Fix**:
- **Backend Refactor**: Ensure `RunManager.stream_run` explicitly commits the "completed" status to the DB at the end of the generator.
- **Frontend**: Verify `RunStatus` type matching (case-sensitivity) in `useOptimizationREST.ts`.

### 2.3 Visual & UX Issues
**Issue A (Theme)**: Optimizer page hardcoded to `bg-zinc-950`, ignoring user's light/dark preference.
**Fix**:
- Use Tailwind CSS variables (`bg-background` or `bg-card`) instead of hardcoded colors.
- Ensure text colors use `text-foreground` or `text-muted-foreground`.

**Issue B (Font)**: Font doesn't match project standard.
**Fix**:
- Remove hardcoded `font-mono` from the main container unless specifically desired for data tables. Use `font-sans` for UI chrome.

**Issue C (Weight Tuner)**: Slider gets stuck.
**Fix**:
- The `Slider` component in `IntervalForm.tsx` likely has a conflict between `value` (controlled) and internal state, or excessive re-renders. Ensure `onValueChange` updates state efficiently without blocking the UI thread.

### 2.4 Harvest Plans Display & Storage
**Issue**: Plans appear as `[object Object]` in the frontend list.
**Fix**:
- **Frontend**: Update `RunHistoryTable` (or `ResultsStream`) to properly render the "config" and "metrics" columns (e.g., show "Net Meat" instead of the entire config object).
- **Backend Storage**:
    - Implement `StorageService` to save:
        1. `plan.json` (Full data)
        2. `report.pdf` (Human-readable summary)
        3. `metrics.json`
    - Upload these to S3 bucket `harvest-plans/{cycle_id}/{plan_id}/`.
    - Update `HarvestPlanDB` to store the S3 paths.

---

## 3. New Feature: Step-by-Step Execution logic

**Requirement**: Users need to split intervals into independent "Runs" or manipulate the optimization between intervals.

### 3.1 Architectural Change
Currently, `RunManager` processes all intervals in a single loop. We will introduce a **Stepped Execution Mode**.

**Changes**:
1.  **Optimization Config**: Add `execution_mode: "batch" | "step_by_step"`.
2.  **Run State**: Add `current_interval_index` and `paused_at_interval`.
3.  **Backend Logic**:
    - In `step_by_step` mode, the `stream_run` generator yields a `PAUSED` event after completing one interval.
    - The Run Status updates to `paused`.
    - User can calls `POST /runs/{id}/resume` (potentially with updated config) to proceed to the next interval.

### 3.2 Frontend Workflow
1.  **Toggle**: User selects "Step-by-Step" on `ConfigSelector`.
2.  **Run Start**: Optimizes *Interval 1*, then pauses. Status -> `PAUSED`.
3.  **Review**: User sees results for Interval 1.
4.  **Edit**: User can (optionally) tweak parameters for Interval 2 (requires new endpoint `PATCH /runs/{id}/config`).
5.  **Proceed**: User clicks "Proceed" (calls `resume`).
6.  **Loop**: Repeats until all intervals processing.

---

## 4. Implementation Checklist

### Phase 1: Critical Bug Fixes
- [ ] **Fix Save Config**: Update `SavedConfigPanel.tsx` payload.
- [ ] **Fix Polling**: Debug `RunManager` completion event & DB commit.
- [ ] **Fix Visuals**: Update `optimizer.tsx` theme classes & `IntervalForm.tsx` slider.
- [ ] **Fix Plan Display**: Update frontend table rendering.

### Phase 2: Storage & Reporting
- [ ] **S3 Integration**: Verify `StorageService` uploads.
- [ ] **PDF Generation**: Add `reportlab` or similar to generate PDF reports.
- [ ] **DB Update**: Store report URLs in `HarvestPlan` model.

### Phase 3: Step-by-Step Logic
- [ ] **Backend**: Update `RunManager` to handle `execution_mode`.
- [ ] **API**: Add `PATCH /runs/{id}/config` to allow mid-run edits.
- [ ] **Frontend**: Update `useOptimizationREST` to handle "paused" state and "Resume/Proceed" flow correctly.

---

**Author**: Antigravity Agent
**Date**: 2026-01-30
