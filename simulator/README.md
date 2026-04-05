# 🚂 Locomotive Telemetry Simulator

A standalone, fully async WebSocket service that generates a realistic real-time data stream for a locomotive digital twin. Designed to be run as a separate process alongside a FastAPI backend, with zero shared state and zero database dependency.

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Running the Simulator](#running-the-simulator)
6. [Configuration](#configuration)
7. [WebSocket Endpoint](#websocket-endpoint)
8. [Telemetry Message Format](#telemetry-message-format)
9. [Simulation Modes](#simulation-modes)
10. [Frequency Control](#frequency-control)
11. [Control API Reference](#control-api-reference)
12. [Fault Injection](#fault-injection)
13. [Error Codes Reference](#error-codes-reference)
14. [Backend Integration](#backend-integration)
15. [Architecture Notes](#architecture-notes)

---

## Overview

```
┌─────────────────────────────┐        WebSocket         ┌────────────────────┐
│   Locomotive Simulator      │  ──── ws://…:9001/telemetry ──▶  FastAPI Backend │
│   (this service)            │                          │   (your service)   │
│                             │        HTTP REST         └────────────────────┘
│   port 9001                 │  ◀── POST /mode, /frequency …
└─────────────────────────────┘
```

The simulator runs on **port 9001** as an independent process. Any number of clients — your FastAPI backend, a browser dashboard, a test script — can connect simultaneously and all receive the same broadcast stream.

---

## Project Structure

```
loco_simulator/
├── main.py                   # FastAPI app entry point — WS + lifespan
├── config.yaml               # All tunable parameters (no restart needed via API)
├── requirements.txt
├── backend_client.py         # Drop-in integration snippet for your FastAPI backend
│
├── simulator/
│   ├── engine.py             # Stateful simulation engine — all 4 modes
│   ├── broadcaster.py        # Async WS client manager + broadcast loop
│   └── telemetry.py          # Pydantic models, value ranges, enums
│
├── api/
│   └── routes.py             # HTTP control endpoints (mode, frequency, fault…)
│
└── utils/
    └── logging_config.py     # Logging setup from config.yaml
```

---

## Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt`:

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
websockets==12.0
pydantic==2.7.1
pyyaml==6.0.1
python-dotenv==1.0.1
```

---

## Installation

```bash
git clone <your-repo>
cd loco_simulator

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## Running the Simulator

**Option 1 — direct:**
```bash
python main.py
```

**Option 2 — uvicorn (recommended for dev):**
```bash
uvicorn main:app --host 0.0.0.0 --port 9001 --reload
```

**Option 3 — custom port via environment variable:**
```bash
PORT=9002 python main.py
```

Once running:

| URL | Purpose |
|-----|---------|
| `ws://localhost:9001/telemetry` | WebSocket telemetry stream |
| `http://localhost:9001/docs` | Auto-generated Swagger UI |
| `http://localhost:9001/redoc` | ReDoc API reference |

---

## Configuration

All defaults live in `config.yaml`. Changes made via the REST API take effect immediately without a restart.

```yaml
simulator:
  locomotive_id: "LOCO-7741"     # ID stamped on every message
  host: "0.0.0.0"
  port: 9001

  interval_ms: 300               # Default message interval (overridden by /frequency)
  auto_switch_interval_sec: 30   # Auto-cycle modes every N seconds (0 = disabled)
  burst_multiplier: 10           # Legacy burst multiplier (prefer /frequency now)

fault_injection:
  random_disconnects: false      # Randomly drop WS clients
  disconnect_probability: 0.001  # Per-message probability of a forced disconnect

  jitter_enabled: true           # Add random delay to each message
  jitter_max_ms: 80              # Maximum added delay (uniform 0–N ms)

  missing_fields_enabled: false  # Randomly omit numeric fields (null)
  missing_field_probability: 0.02 # Per-field probability per message

logging:
  level: "INFO"                  # DEBUG | INFO | WARNING | ERROR
  format: "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
```

---

## WebSocket Endpoint

```
ws://localhost:9001/telemetry
```

- Broadcasts to **all connected clients** simultaneously.
- Messages arrive as **UTF-8 JSON strings**.
- The simulator sends at the configured frequency regardless of whether clients send anything. Clients may send any text to keep the connection alive through proxies (the payload is ignored).
- On reconnection, the stream resumes from the current simulator state with no gaps or replay.

**Quick connection test:**
```bash
# Using websocat (https://github.com/vi/websocat)
websocat ws://localhost:9001/telemetry

# Using wscat (npm)
npx wscat -c ws://localhost:9001/telemetry
```

---

## Telemetry Message Format

Every message is a JSON object with the following fields:

```json
{
  "timestamp":      "2026-04-04T11:32:51.445855+00:00",
  "locomotive_id":  "LOCO-7741",
  "speed":          85.30,
  "fuel_level":     71.58,
  "engine_temp":    88.10,
  "oil_pressure":   3.80,
  "voltage":        27.44,
  "current":        422.59,
  "error_codes":    [],
  "health_hint":    "ok",
  "mode":           "normal"
}
```

### Field Reference

| Field | Type | Unit | Normal range | Description |
|-------|------|------|-------------|-------------|
| `timestamp` | `string` | ISO 8601 UTC | — | Message generation time |
| `locomotive_id` | `string` | — | — | Locomotive identifier from config |
| `speed` | `float \| null` | km/h | 80 – 90 | Current speed |
| `fuel_level` | `float \| null` | % | 70 – 74 | Fuel tank level, drains over time |
| `engine_temp` | `float \| null` | °C | 86 – 90 | Engine temperature |
| `oil_pressure` | `float \| null` | bar | 3.7 – 3.9 | Oil pressure |
| `voltage` | `float \| null` | V | 27.1 – 27.9 | System voltage |
| `current` | `float \| null` | A | 390 – 450 | Electrical current draw |
| `error_codes` | `string[]` | — | `[]` | Active fault codes (see reference below) |
| `health_hint` | `string` | — | `"ok"` | Backend-friendly status tag |
| `mode` | `string` | — | `"normal"` | Active simulation mode |

> **Null fields** only appear when `missing_fields_enabled: true` in fault injection. Your backend should treat `null` as a missing/sensor-fault reading.

### `health_hint` Values

| Value | When emitted |
|-------|-------------|
| `ok` | Normal operation, no faults |
| `glitch` | Normal mode with a rare sensor glitch |
| `degrading` | Degradation mode, early stage (< 30% degraded) |
| `warning_low` | Degradation mode, 30–70% degraded |
| `warning_high` | Degradation mode, > 70% degraded |
| `spike` | Spike mode, anomaly currently active |
| `critical` | Failure mode, multiple systems in fault |

---

## Simulation Modes

Modes control the shape of the generated data. They can be set manually via the API or cycle automatically every N seconds (configured via `auto_switch_interval_sec`).

### `normal`

Stable operation. Each parameter wanders slightly around its realistic centre value using Gaussian noise with a gentle mean-reversion pull, so values never drift far from baseline. Fuel drains very slowly.

```json
{
  "speed": 85.30, "engine_temp": 88.10, "oil_pressure": 3.80,
  "voltage": 27.44, "current": 422.59, "error_codes": [], "health_hint": "ok"
}
```

### `degradation`

Simulates a locomotive that is gradually failing. Parameters drift toward warning thresholds using a `sqrt(elapsed / 300s)` curve — reaching ~95% degradation after 5 minutes. This gives a realistic slow-onset failure rather than an instant jump.

| Parameter | Trend |
|-----------|-------|
| `engine_temp` | Climbs from 88 °C toward 120 °C |
| `oil_pressure` | Falls from 3.8 bar toward 1.6 bar |
| `voltage` | Sags from 27.5 V toward 23.5 V |
| `current` | Rises from 420 A toward 705 A |
| `speed` | Drops and becomes erratic |
| `fuel_level` | Drains 4–10× faster than normal |

Error codes begin appearing once thresholds are crossed. `health_hint` progresses: `degrading` → `warning_low` → `warning_high`.

```json
{
  "speed": 73.47, "engine_temp": 101.22, "oil_pressure": 2.91,
  "error_codes": ["E001_OVERHEAT"], "health_hint": "warning_low"
}
```

### `spike`

Normal baseline with sudden anomaly bursts. Every ~15 ticks (~7% chance per tick), one random parameter jumps to 97% of its maximum and holds for 3–7 ticks before recovering. Simulates sensor noise, power transients, or brief mechanical faults.

```json
{
  "speed": 84.91, "engine_temp": 118.34, "oil_pressure": 3.79,
  "error_codes": ["E001_OVERHEAT"], "health_hint": "spike"
}
```

### `failure`

Multiple systems simultaneously at critical values. Intended to test that the backend correctly handles a locomotive-wide failure event.

| Parameter | Critical value |
|-----------|---------------|
| `engine_temp` | ~118 °C |
| `oil_pressure` | ~1.6 bar |
| `voltage` | ~22.5 V |
| `current` | ~780 A |
| `speed` | ~15 km/h (limping) |
| `error_codes` | 3–6 codes per message |

```json
{
  "speed": 12.39, "engine_temp": 120.0, "oil_pressure": 1.42,
  "voltage": 22.28, "current": 785.59,
  "error_codes": ["E001_OVERHEAT", "E002_LOW_OIL", "E008_COOLANT_LEAK",
                  "E007_BRAKE_PRESSURE", "E004_VOLTAGE_DROP"],
  "health_hint": "critical"
}
```

### Auto Mode Cycling

When `auto_switch_interval_sec` is set to a non-zero value in `config.yaml`, the simulator automatically steps through: `normal → degradation → spike → failure → normal → …` every N seconds. Set to `0` to disable and control modes exclusively via the API.

---

## Frequency Control

Message frequency is controlled independently from simulation mode. Three named presets are available:

| Preset | Rate | Interval | Behaviour |
|--------|------|----------|-----------|
| `normal` | 1 Hz | 1 000 ms | Standard telemetry rate. Persistent. |
| `highload` | 10 Hz | 100 ms | High-throughput testing. Persistent. |
| `burst` | 50 Hz | 20 ms | Stress testing. **Lasts 3 seconds**, then automatically reverts to the previous preset. |

**Key design point:** `burst` never overwrites the base preset. If you are on `highload` and trigger `burst`, after 3 seconds the simulator returns to `highload` — not `normal`.

```bash
# Set to highload (persistent)
curl -X POST http://localhost:9001/frequency \
     -H "Content-Type: application/json" \
     -d '{"preset": "highload"}'

# Fire a 3-second burst (auto-reverts to highload)
curl -X POST http://localhost:9001/frequency \
     -d '{"preset": "burst"}'
```

The `GET /status` response shows live countdown while burst is active:

```json
{
  "frequency_preset":      "burst",
  "frequency_hz":          50.0,
  "interval_ms":           20,
  "burst_active":          true,
  "burst_expires_in_sec":  1.84
}
```

For raw millisecond control (backwards compatibility), use `POST /rate`.

---

## Control API Reference

All endpoints accept and return JSON. Interactive docs available at `http://localhost:9001/docs`.

### `POST /frequency`

Set message frequency by named preset.

**Request:**
```json
{ "preset": "normal" | "highload" | "burst" }
```

**Response (normal/highload):**
```json
{ "ok": true, "preset": "highload", "frequency_hz": 10.0, "interval_ms": 100 }
```

**Response (burst):**
```json
{
  "ok": true, "preset": "burst", "frequency_hz": 50.0,
  "interval_ms": 20, "burst_duration_sec": 3, "reverts_to": "highload"
}
```

---

### `POST /mode`

Set simulation mode.

**Request:**
```json
{ "mode": "normal" | "degradation" | "spike" | "failure" }
```

**Response:**
```json
{ "ok": true, "mode": "degradation" }
```

---

### `GET /status`

Returns full simulator state.

**Response:**
```json
{
  "mode":                  "degradation",
  "interval_ms":           100,
  "frequency_hz":          10.0,
  "frequency_preset":      "highload",
  "burst_active":          false,
  "burst_expires_in_sec":  null,
  "connected_clients":     2,
  "messages_sent":         4821,
  "uptime_seconds":        482.1
}
```

---

### `POST /rate`

Set interval in milliseconds directly (20–10 000 ms). Use `/frequency` for preset-based control.

**Request:**
```json
{ "interval_ms": 250 }
```

---

### `POST /reset`

Snap all parameters to nominal values, enter `normal` mode, and reset frequency to 1 Hz.

**Response:**
```json
{ "ok": true, "mode": "normal", "frequency_preset": "normal" }
```

---

### `POST /fault`

Dynamically toggle fault injection settings at runtime.

**Request:**
```json
{
  "random_disconnects":     false,
  "missing_fields_enabled": true,
  "jitter_enabled":         false
}
```

All fields are optional — only the provided keys are updated.

---

### `POST /burst` *(legacy)*

Retained for backwards compatibility. Delegates to `/frequency`.

- `{ "active": true }` → equivalent to `POST /frequency { "preset": "burst" }`
- `{ "active": false }` → reverts to base preset immediately

---

## Fault Injection

Fault injection lets you test how your backend handles imperfect network and sensor conditions. All settings can be toggled at runtime via `POST /fault`.

### Random Disconnects

When enabled, each message sent to a client has a `disconnect_probability` chance of triggering a forced `WS 1001` close. The client must reconnect. Useful for testing your backend's reconnection logic.

```yaml
fault_injection:
  random_disconnects: true
  disconnect_probability: 0.001   # 0.1% per message ≈ once per ~1000 msgs
```

### Message Jitter

Adds a random uniform delay of 0 to `jitter_max_ms` milliseconds before each send. Simulates network latency variability and out-of-order processing scenarios.

```yaml
fault_injection:
  jitter_enabled: true
  jitter_max_ms: 80
```

### Missing Fields

When enabled, each numeric telemetry field independently has a `missing_field_probability` chance of being set to `null`. Tests that your backend handles partial sensor data gracefully and doesn't crash on missing readings.

```yaml
fault_injection:
  missing_fields_enabled: true
  missing_field_probability: 0.02   # 2% per field per message
```

---

## Error Codes Reference

| Code | Meaning | Modes |
|------|---------|-------|
| `E001_OVERHEAT` | Engine temperature above threshold | DEGRADATION, SPIKE, FAILURE |
| `E002_LOW_OIL` | Oil pressure below minimum | DEGRADATION, FAILURE |
| `E003_LOW_FUEL` | Fuel level critically low | DEGRADATION, FAILURE |
| `E004_VOLTAGE_DROP` | System voltage below safe range | DEGRADATION, FAILURE |
| `E005_OVERCURRENT` | Current draw exceeds rated maximum | DEGRADATION, FAILURE |
| `E006_SENSOR_FAULT` | Sensor read error or timeout | All (rare in NORMAL) |
| `E007_BRAKE_PRESSURE` | Brake pressure anomaly detected | FAILURE |
| `E008_COOLANT_LEAK` | Coolant system fault | FAILURE |
| `E009_TRACTION_LOSS` | Loss of traction detected | FAILURE |
| `E010_COMM_TIMEOUT` | Communication link timeout | FAILURE |

---

## Backend Integration

`backend_client.py` is a self-contained drop-in for your existing FastAPI backend. Copy the relevant pieces into your project.

### What it provides

- **`simulator_client_loop()`** — auto-reconnecting WebSocket client that reads from the simulator, updates `latest_frame`, pushes to a queue, and fans out to browser clients.
- **`db_writer_worker()`** — queue-draining worker; replace the stub with your `async_session()` call.
- **`GET /telemetry/latest`** — REST polling endpoint returning the most recent frame.
- **`WS /telemetry/stream`** — fan-out WebSocket for browser / frontend clients.

### Minimal integration example

```python
# In your backend's lifespan:

@asynccontextmanager
async def lifespan(app: FastAPI):
    client_task = asyncio.create_task(simulator_client_loop())
    writer_task = asyncio.create_task(db_writer_worker())
    yield
    client_task.cancel()
    writer_task.cancel()
```

### DB writer stub

Replace the stub in `_write_to_db()` with your actual insert:

```python
async def _write_to_db(frame: TelemetryFrame) -> None:
    async with async_session() as session:
        session.add(TelemetryRecord(**frame.model_dump()))
        await session.commit()
```

### Reconnection behaviour

`simulator_client_loop()` catches `websockets.ConnectionClosed` and `OSError` and retries every 3 seconds. Your backend will never crash due to the simulator being down or restarting.

---

## Architecture Notes

### Why a separate service?

Keeping the simulator as a separate process means:
- The simulator can be started, stopped, or restarted independently without affecting your backend.
- Your backend connects to it exactly like a real locomotive would — as a WebSocket client — so the integration code is reusable in production.
- Load tests on the simulator do not impact backend benchmarks.

### Broadcast loop design

The broadcast loop runs as a single `asyncio` background task. It calls `engine.tick()` once per interval and fans out the result to all connected clients in a single pass. There is no per-client task — this keeps overhead constant regardless of client count.

### Burst expiry

Burst mode expiry is checked inline in the broadcast loop rather than via a separate `asyncio.sleep` task. This avoids timer drift at high frequencies and requires no synchronisation primitives.

### State model

`SimulationEngine` owns a `_state` dict of continuous float values. Each tick mutates the state in place and returns a snapshot as a `TelemetryMessage`. The engine is not thread-safe but does not need to be — all access is from the single broadcast loop coroutine.