# Dashboard Update: Add Modly API Service

This guide adds Modly as a second network service alongside Wan2GP.

Wan2GP and Modly should run on different ports:

| Service | Default Port | Health Endpoint |
| --- | ---: | --- |
| Wan2GP | `8100` | `/api/health` |
| Modly | `8765` | `/api/health` |

## Start Modly On The Service Machine

On the machine that has Modly installed, start the standalone API:

```powershell
F:\modly\scripts\start-modly-network-api.ps1 -Port 8765 -Token "your-secret-token"
```

Or set the token as an environment variable first:

```powershell
$env:MODLY_API_TOKEN = "your-secret-token"
F:\modly\scripts\start-modly-network-api.ps1 -Port 8765
```

To persist the token for future terminals:

```powershell
[Environment]::SetEnvironmentVariable("MODLY_API_TOKEN", "your-secret-token", "User")
```

Then open a new terminal and start Modly:

```powershell
F:\modly\scripts\start-modly-network-api.ps1 -Port 8765
```

## Linux Setup On An RTX 3060 Machine

These steps assume Ubuntu or another Debian-based Linux install with an NVIDIA
driver already working. First confirm the GPU is visible:

```bash
nvidia-smi
```

Install basic system packages:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nodejs npm ffmpeg
```

Clone Modly:

```bash
git clone https://github.com/Techdread/modly.git ~/modly
cd ~/modly
```

Install the Python API dependencies:

```bash
cd ~/modly/api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If you also want to run the Electron desktop app on this Linux machine, install
the Node dependencies from the repo root:

```bash
cd ~/modly
npm install
```

The Dashboard does not require Electron to be running. For Dashboard-only use,
the standalone API is enough.

Create data directories for models, generated files, and extensions:

```bash
mkdir -p ~/Modly/models ~/Modly/workspace ~/Modly/extensions
```

Start the Modly API on the LAN:

```bash
cd ~/modly/api
source .venv/bin/activate
python serve.py \
  --host 0.0.0.0 \
  --port 8765 \
  --token "your-secret-token" \
  --models-dir ~/Modly/models \
  --workspace-dir ~/Modly/workspace \
  --extensions-dir ~/Modly/extensions
```

From another computer on the LAN, check health:

```bash
curl http://<modly-linux-ip>:8765/api/health
```

Then test an authenticated call:

```bash
curl \
  -H "Authorization: Bearer your-secret-token" \
  http://<modly-linux-ip>:8765/api/model/all
```

If the Linux firewall is enabled, allow the Modly API port:

```bash
sudo ufw allow 8765/tcp
```

### Optional: Run Modly API With systemd

Create an environment file:

```bash
sudo tee /etc/modly-api.env >/dev/null <<'EOF'
MODLY_API_TOKEN=your-secret-token
MODELS_DIR=/home/<linux-user>/Modly/models
WORKSPACE_DIR=/home/<linux-user>/Modly/workspace
EXTENSIONS_DIR=/home/<linux-user>/Modly/extensions
EOF
```

Create the service:

```bash
sudo tee /etc/systemd/system/modly-api.service >/dev/null <<'EOF'
[Unit]
Description=Modly LAN API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<linux-user>
WorkingDirectory=/home/<linux-user>/modly/api
EnvironmentFile=/etc/modly-api.env
ExecStart=/home/<linux-user>/modly/api/.venv/bin/python serve.py --host 0.0.0.0 --port 8765
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Replace `<linux-user>` with the actual Linux username, then enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now modly-api
sudo systemctl status modly-api
```

View logs:

```bash
journalctl -u modly-api -f
```

### Linux Notes

- The RTX 3060 should have enough VRAM for lighter Modly models, but model
  choice still matters.
- If a model extension has its own `setup.py`, run/install that extension before
  expecting it to appear in `/api/model/all`.
- Keep Modly on `8765` if Wan2GP is already using `8100`.
- Do not expose this API directly to the public internet; keep it on a trusted
  LAN or behind a proper VPN/reverse proxy.

## Dashboard Service Config

Add Modly as a separate service entry:

```json
{
  "id": "modly",
  "name": "Modly",
  "baseUrl": "http://<modly-machine-ip>:8765/api",
  "healthPath": "/health",
  "token": "your-secret-token"
}
```

Health does not require a token:

```http
GET http://<modly-machine-ip>:8765/api/health
```

Every other request must send:

```http
Authorization: Bearer your-secret-token
```

## Useful Modly Calls

Check API health:

```http
GET /api/health
```

List models the Dashboard can use:

```http
GET /api/model/all
Authorization: Bearer your-secret-token
```

This is the discovery endpoint for the Dashboard model picker. Each item is a
registered Modly model extension/node:

```json
[
  {
    "id": "model-extension/model-node",
    "name": "Model name",
    "description": "Short description",
    "version": "1.0.0",
    "vram_gb": 8,
    "hf_repo": "owner/repo",
    "tags": [],
    "downloaded": true,
    "loaded": false,
    "active": false
  }
]
```

Use `id` as the `model_id` field when starting generation. `downloaded` tells
whether the weights are present on disk, `loaded` tells whether the model is
currently in memory, and `active` marks the currently selected model.

Check active model:

```http
GET /api/model/status
Authorization: Bearer your-secret-token
```

Start image-to-3D generation:

```http
POST /api/generate/from-image
Authorization: Bearer your-secret-token
Content-Type: multipart/form-data
```

Form fields:

| Field | Required | Example |
| --- | --- | --- |
| `image` | yes | uploaded `.png`, `.jpg`, or `.webp` |
| `model_id` | no | `sf3d` or another installed Modly model id |
| `collection` | no | `Dashboard` |
| `remesh` | no | `quad`, `triangle`, or `none` |
| `enable_texture` | no | `false` |
| `texture_resolution` | no | `1024` |
| `params` | no | `{}` JSON string |

Example response:

```json
{
  "job_id": "generated-job-id"
}
```

Poll job status:

```http
GET /api/generate/status/<job_id>
Authorization: Bearer your-secret-token
```

Possible statuses:

```text
pending
running
done
error
cancelled
```

When complete, Modly returns an `output_url`, usually like:

```text
/workspace/Dashboard/example.glb
```

Download or display the generated file:

```http
GET /api/workspace/Dashboard/example.glb
Authorization: Bearer your-secret-token
```

Cancel a job:

```http
POST /api/generate/cancel/<job_id>
Authorization: Bearer your-secret-token
```

## Dashboard Call Chain

1. Read the Modly service config.
2. Call `GET /api/health` without auth to check service availability.
3. For all other calls, add `Authorization: Bearer <token>`.
4. Submit image generation with `POST /api/generate/from-image`.
5. Poll `GET /api/generate/status/<job_id>`.
6. When `status` is `done`, fetch the returned `output_url` through the Modly API base URL.

## Notes

- The Electron app does not need to be running when using the standalone API.
- Do not run Electron and the standalone API on the same port at the same time.
- If Wan2GP is already using `8100`, keep Modly on `8765`.
- If Windows Firewall prompts on first launch, allow access for trusted private networks.
