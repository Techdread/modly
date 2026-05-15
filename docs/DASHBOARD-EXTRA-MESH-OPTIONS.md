# Dashboard Extra Mesh Options Implementation Brief

This note is for implementing additional Modly API controls in the dashboard.
The dashboard currently exposes only the basic generation controls:

- `model_id`
- `collection`
- `remesh`
- `enable_texture`
- `texture_resolution`

Add model-specific Trellis.2 parameters and post-generation mesh processing controls.

## API Base

The standalone API service normally runs on:

```txt
http://<modly-host>:8765
```

All main endpoints are mirrored under `/api`. Prefer `/api/*` for dashboard use:

```txt
/api/generate/from-image
/api/generate/status/{job_id}
/api/optimize/mesh
/api/optimize/smooth
/api/workspace/{collection}/{filename}
```

If `MODLY_API_TOKEN` is configured, send:

```http
Authorization: Bearer <token>
```

## Generate From Image

Endpoint:

```http
POST /api/generate/from-image
```

Request type: `multipart/form-data`

Fields:

```txt
image              file, required
model_id           string, e.g. trellis2
collection         string, e.g. Dashboard
remesh             quad | triangle | none
enable_texture     true | false
texture_resolution integer, usually 512 or 1024
params             JSON string for model-specific options
```

The API-level `remesh` field only accepts:

```txt
quad
triangle
none
```

Response:

```json
{
  "job_id": "..."
}
```

Poll status:

```http
GET /api/generate/status/{job_id}
```

Done response includes:

```json
{
  "status": "done",
  "progress": 100,
  "output_url": "/workspace/Dashboard/example.glb"
}
```

For post-process endpoints, convert the output URL into a workspace path:

```txt
/workspace/Dashboard/example.glb -> Dashboard/example.glb
```

## Trellis.2 Params

These values go into the `params` form field as JSON.

Recommended dashboard controls:

```json
{
  "pipeline_type": "1024_cascade",
  "gguf_quant": "Q5_K_M",
  "ss_steps": 25,
  "slat_steps": 25,
  "foreground_ratio": 0.85,
  "remesh_resolution": 768,
  "seed": -1
}
```

Allowed `pipeline_type` values:

```txt
512
1024
1024_cascade
1536_cascade
```

Suggested labels:

```txt
Fast (512)
Balanced (1024)
High (1024 cascade)
Ultra (1536 cascade)
```

Allowed `gguf_quant` values:

```txt
Q4_K_M
Q5_K_M
Q6_K
Q8_0
```

Notes:

- `Q4_K_M`: lower VRAM, fastest, slightly lower detail.
- `Q5_K_M`: good default.
- `Q6_K`: higher quality/cost.
- `Q8_0`: highest GGUF quality/cost.

Step controls:

```txt
ss_steps      integer, min 1, max 50, default 25
slat_steps    integer, min 1, max 50, default 25
```

Other controls:

```txt
foreground_ratio  float, min 0.5, max 1.0, step 0.05, default 0.85
seed              integer, min -1, max 4294967295, default -1
```

Allowed `remesh_resolution` values:

```txt
512
768
1024
```

`remesh_resolution` is not a triangle budget. It controls the voxel grid resolution used by Trellis.2 post-generation remeshing. Lower values usually create lighter meshes; higher values usually preserve more detail.

## Texture Params

These can also go into the `params` JSON when texture is enabled.

```json
{
  "texture_resolution": 1024,
  "texture_size": 2048,
  "texture_steps": 12,
  "texture_guidance": 1.0
}
```

Allowed `texture_resolution` values:

```txt
512
1024
```

Allowed `texture_size` values:

```txt
1024
2048
```

Notes:

- `texture_resolution` is the Trellis texture diffusion resolution.
- `texture_size` is the exported texture atlas size.
- There is no 2048 Trellis GGUF model; 2048 here means a 2048px output atlas.

Texture step controls:

```txt
texture_steps     integer, min 4, max 50, default 12
texture_guidance  float, min 0, max 5, step 0.1, default 1.0
```

## Post-Generation Triangle Budget

Use this endpoint after generation to reduce the mesh to a target triangle count.

Endpoint:

```http
POST /api/optimize/mesh
```

Body:

```json
{
  "path": "Dashboard/example.glb",
  "target_faces": 10000
}
```

Allowed `target_faces` range:

```txt
100 to 500000
```

The API clamps values outside this range.

Response:

```json
{
  "url": "/workspace/Dashboard/example_opt10000.glb",
  "face_count": 10000
}
```

Dashboard implementation suggestion:

- Add a `Target triangles` number input.
- Add an `Optimize mesh` button.
- Only enable it after a generation output exists.
- After optimization, replace or add the returned optimized mesh URL in the viewer/download state.

## Post-Generation Smoothing

Endpoint:

```http
POST /api/optimize/smooth
```

Body:

```json
{
  "path": "Dashboard/example.glb",
  "iterations": 3
}
```

Allowed `iterations` range:

```txt
1 to 20
```

The API clamps values outside this range.

Response:

```json
{
  "url": "/workspace/Dashboard/example_smooth3.glb"
}
```

Dashboard implementation suggestion:

- Add a `Smooth iterations` number input.
- Add a `Smooth mesh` button.
- Only enable it after a generation output exists.

## Suggested Dashboard UI Additions

Generation controls:

```txt
Quality              select: 512, 1024, 1024_cascade, 1536_cascade
GGUF quant           select: Q4_K_M, Q5_K_M, Q6_K, Q8_0
Sparse steps         number: 1-50
Shape steps          number: 1-50
Foreground ratio     number/slider: 0.5-1.0
Remesh resolution    select: 512, 768, 1024
Seed                 number: -1 for random
```

Texture controls:

```txt
Texture resolution   select: 512, 1024
Texture atlas size   select: 1024, 2048
Texture steps        number: 4-50
Texture guidance     number/slider: 0-5
```

Post-process controls:

```txt
Target triangles     number: 100-500000
Optimize mesh        button
Smooth iterations    number: 1-20
Smooth mesh          button
```

## Example End-To-End Flow

1. Submit `POST /api/generate/from-image`.
2. Poll `GET /api/generate/status/{job_id}` until `status` is `done`.
3. Extract the workspace path from `output_url`.
4. Optionally call `POST /api/optimize/mesh` with `target_faces`.
5. Optionally call `POST /api/optimize/smooth` with `iterations`.
6. Use the returned `/workspace/...` URL as the active mesh URL.

Example `params` form value:

```json
{
  "pipeline_type": "1024_cascade",
  "gguf_quant": "Q5_K_M",
  "ss_steps": 25,
  "slat_steps": 25,
  "foreground_ratio": 0.85,
  "remesh_resolution": 768,
  "seed": -1,
  "texture_size": 2048,
  "texture_steps": 12,
  "texture_guidance": 1.0
}
```

