# SiteShield AI frontend

React 18 + Vite frontend for the FastAPI backend in the repository root. The UI reads all operational data from the API; it includes Dashboard, Live Monitor, Violations, Analytics, and Model Info views.

## Windows setup

1. Install Node.js 20.19+ or 22.12+ (Vite 8 requirement).
2. Open PowerShell in `D:\SiteShield_AI\frontend`.
3. Copy `.env.example` to `.env` if the backend is not at `http://localhost:8000`, then set `VITE_API_URL` to the API base URL.
4. Install dependencies and start Vite:

```powershell
npm install
npm run dev
```

5. Open `http://localhost:5173`. In another PowerShell window from `D:\SiteShield_AI`, start the backend with `uvicorn app.main:app --reload` (activate the project's virtual environment first if needed).

## Five-step demo

1. Start the backend and confirm its model and database are available at `/health`.
2. Start the frontend with `npm run dev` and open `http://localhost:5173`.
3. Open **Live Monitor**, choose **Video file**, select a local PPE video, and set the camera and site fields.
4. Start monitoring; detections are submitted sequentially and new violations appear in the Live alerts list and WebSocket stream.
5. Open **Violations** to inspect events and resolve/reopen them, then return to **Dashboard** for summary cards and charts.

## Notes

- Set `VITE_API_URL` at build/dev startup; the WebSocket URL is derived from it.
- Violation timestamps and relative times are shown in the browser's local timezone. Analytics API summary values follow backend semantics; the summary's daily count is based on UTC midnight.
- The hourly endpoint groups all records unless date bounds are sent. The Analytics date picker passes those bounds; `/analytics/by-type` and `/analytics/summary` do not accept date filters in the current API.
