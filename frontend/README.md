# MergenVision Frontend

**Status:** Boundary-only placeholder. No React/Vite application, no dependency installation, no UI screens in Foundation Sprint 0–1.

## Target stack

- React 18+
- TypeScript
- Vite
- React Router

## Communication boundary

- The frontend talks only to the FastAPI `/api/v1` endpoints.
- It does **not** connect directly to PostgreSQL, MinIO, Qdrant, or the native GPU worker.
- All business state is managed by the backend application services.

## Phase 1 screens (future UI sprint)

- Dashboard / system health
- People list and detail
- Person photo enrollment
- Identify request upload and results
- Identification request history

## Forbidden tools

- **21st.dev** and similar AI UI generators are explicitly forbidden.
- No UI code is scaffolded or installed until a dedicated UI sprint is approved.
