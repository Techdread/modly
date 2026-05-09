# Modly — FastAPI Backend

Local Python server started and managed by Electron.

## Setup

```bash
cd api
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run (development)

```bash
uvicorn main:app --host 127.0.0.1 --port 8765 --reload
```

## Run for LAN / dashboards

Wan2GP can keep running on its own port, usually `8100`. Modly should use its
own port, usually `8765`.

If the Electron app is already running the backend, launch Modly with a LAN
bind host instead of starting a second backend on the same port:

```powershell
$env:MODLY_API_BIND_HOST = "0.0.0.0"
npm run preview
```

For a standalone Modly API service, run:

```bash
python serve.py --host 0.0.0.0 --port 8765
```

Optional bearer token for other computers on the LAN:

```bash
python serve.py --host 0.0.0.0 --port 8765 --token your-token
```

When a token is configured, every endpoint except `/health` and `/api/health`
requires:

```http
Authorization: Bearer your-token
```

Existing endpoints are also mirrored under `/api`, for example
`/api/generate/from-image` and `/api/generate/status/{job_id}`.

## Key endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (used by Electron to detect readiness) |
| GET | `/model/status` | Model download / load status |
| GET | `/model/download` | SSE stream of download progress |
| POST | `/generate/from-image` | Start image-to-3D job |
| GET | `/generate/status/{job_id}` | Poll job status |

## Model

Default: **TripoSR** (`stabilityai/TripoSR`, ~2.4 GB)
Downloaded on first launch to `~/.modly/models/TripoSR/`.
To change model: edit `services/model_manager.py`.
