# Shadow Credit Phase 1 Ingestion Summary

## Completed Wiring

- Built `backend/api/ingest.py` with full ingestion API:
  - `POST /api/v1/ingest/{session_id}` (202 async kickoff)
  - `GET /api/v1/ingest/{session_id}/status`
  - file/type validation, size limits, artifact registration, audit logging
  - disk storage under DB-parent `artifacts/{session_id}/{artifact_id}/`
  - background pipeline orchestration with agent routing + partial-failure handling

- Wired ingestion router in `backend/main.py`:
  - added `ingest_router` import
  - registered `app.include_router(ingest_router, prefix="/api/v1")`

## Agent Routing Implemented

- `WHATSAPP` → `AGENT_02_WHATSAPP`
- `UPI|BILL|INVOICE|RECEIPT` → `AGENT_01_OCR` (OCR artifacts run sequentially)
- `KHATA` → `AGENT_03_KHATA`

## Reliability Behaviors

- Uses `BackgroundTasks` for non-blocking ingestion execution.
- Uses `asyncio.gather(..., return_exceptions=True)` so one agent failure does not block others.
- Pipeline completion emits `SESSION_INGESTION_COMPLETE` over event bus.
- Pipeline fatal exceptions set session status to `FAILED` and publish error events.

## Validation/Status Surfaces

- Session gating: not found, erased, consent missing.
- Upload gating: max files, extension/type checks, size checks.
- Status endpoint returns:
  - per-artifact processing + extraction counts
  - recent active agents from audit trail
  - last activity timestamp
  - `pipeline_complete` boolean

## Notes

- Existing compatibility behavior was preserved for mixed import modes (`backend.*` vs local package mode).
- `wrap_response` is imported from `api/sessions.py` to avoid circular import risk from `backend.main`.
