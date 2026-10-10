# FedMed 🧠
### Cross-Silo Federated Learning Engine for Privacy-Preserving Brain Tumor Segmentation

[![CI](https://github.com/rahulsri18/FedMed/actions/workflows/ci.yml/badge.svg)](https://github.com/rahulsri18/FedMed/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Flower FL](https://img.shields.io/badge/FL-Flower%201.8-orange.svg)](https://flower.ai/)
[![Homomorphic Encryption](https://img.shields.io/badge/HE-TenSEAL%20CKKS-purple.svg)](https://github.com/OpenMined/TenSEAL)
[![Differential Privacy](https://img.shields.io/badge/DP-Opacus%20Compatible-green.svg)](https://opacus.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**FedMed** is an enterprise-grade federated learning engine designed to train deep 3D brain tumor segmentation models (BraTS) across 3 distributed hospital silos without centralizing sensitive patient imaging data.

FedMed combines **Flower (flwr)** orchestration, **TenSEAL CKKS homomorphic encryption**, **Opacus-style Differential Privacy**, a **MONAI Compact 3D U-Net**, a **FastAPI telemetry gateway**, and an interactive **React + Vite + Canvas** operations dashboard.

---

## Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │        CENTRAL AGGREGATION SILO        │
                      │                                        │
                      │    Flower Server (gRPC + mTLS)         │
                      │    - FedMedFedAvg Custom Strategy      │
                      │    - Quorum Enforcement (min 2 of 3)   │
                      │    - Homomorphic Vector Aggregator     │
                      └───────────────▲───┬───▲────────────────┘
                                      │   │   │
                     CKKS Ciphertexts │   │   │ CKKS Ciphertexts
                     + Gaussian Noise │   │   │ + Gaussian Noise
                                      │   │   │
        ┌─────────────────────────────┘   │   └─────────────────────────────┐
        │                                 │                                 │
┌───────▼──────────────┐       ┌──────────▼───────────┐       ┌─────────────▼────────┐
│   HOSPITAL SILO 1    │       │   HOSPITAL SILO 2    │       │   HOSPITAL SILO 3    │
│  St. Jude Medical    │       │   Charité Berlin     │       │ Mayo Clinic Oncology │
│                      │       │                      │       │                      │
│ - Compact 3D U-Net   │       │ - Compact 3D U-Net   │       │ - Compact 3D U-Net   │
│ - InstanceNorm (DP)  │       │ - InstanceNorm (DP)  │       │ - InstanceNorm (DP)  │
│ - 3D Volume Slices   │       │ - 3D Volume Slices   │       │ - 3D Volume Slices   │
│ - L2 Clip + Noise    │       │ - L2 Clip + Noise    │       │ - L2 Clip + Noise    │
│ - Shared Secret Key  │       │ - Shared Secret Key  │       │ - Shared Secret Key  │
└──────────────────────┘       └──────────────────────┘       └──────────────────────┘
                                          │
                            Heartbeats & Round Metrics
                                          ▼
                      ┌────────────────────────────────────────┐
                      │          FASTAPI GATEWAY               │
                      │  - Multi-Planar MRI PNG Streamer       │
                      │  - WebSocket Telemetry Broadcaster     │
                      │  - Chaos Node Dropout / Reconnect API  │
                      │  - RDP Analytical Privacy Auditor      │
                      └───────────────────┬────────────────────┘
                                          │
                                WebSocket & REST
                                          ▼
                      ┌────────────────────────────────────────┐
                      │    FEDMED BESPOKE OPS CONSOLE          │
                      │    (React + Vite + TypeScript)         │
                      │                                        │
                      │ - 3D WebGL Orbit Scene (Three.js/R3F)  │
                      │ - Interactive PACS 3D MRI Viewer       │
                      │ - Live Dice & Loss Convergence Curve   │
                      │ - Hospital Telemetry & Chaos Controls  │
                      │ - Real-Time (ε, δ) Privacy Budget Gauge│
                      └────────────────────────────────────────┘
```

---

## Repository Layout

```
FedMed/
├── server/                     # Flower server, custom FedAvg strategy, encrypted aggregator
│   ├── server.py              # Server entrypoint with mTLS support & webhook reporting
│   ├── strategy.py            # Custom FedMedFedAvg strategy with quorum & dropout handling
│   ├── aggregator.py          # Chunked CKKS homomorphic aggregation & plaintext fallback
│   └── Dockerfile
├── client/                     # Flower NumPyClient node implementation
│   ├── client.py              # Client entrypoint with local training, DP, and CKKS pre-scaling
│   └── Dockerfile
├── models/                     # Deep learning architectures & metrics
│   ├── unet.py                # DP-compatible Compact 3D U-Net (~1.8M params, InstanceNorm)
│   ├── losses.py              # Soft DiceLoss & DiceCELoss
│   └── metrics.py             # Mean Dice, Hausdorff 95, region-specific metrics
├── data/                       # BraTS dataset handling & hospital partitioning
│   ├── brats_dataset.py       # 3D BraTS volume cache & realistic synthetic fallback
│   ├── transforms.py          # Spatial augmentations & intensity normalization
│   └── partitioner.py         # IID and Dirichlet non-IID hospital split generator
├── privacy/                    # TenSEAL CKKS Homomorphic Encryption & Differential Privacy
│   ├── tenseal_context.py     # CKKS context generator (N=8192, scale=2^40) & trust model docs
│   ├── encryption.py          # Tensor-to-ciphertext chunked packing & pre-scaling
│   ├── differential_privacy.py# Global L2 clipping, Gaussian noise & RDP accountant
│   └── audit.py               # Analytical privacy audit & cumulative (ε, δ) budget tracker
├── network/                    # Networking, mTLS security & auxiliary channels
│   ├── certs/
│   │   └── generate_certs.py  # mTLS certificate authority, server & client cert generator
│   ├── heartbeat.py           # Server-side heartbeat monitor & node timeout tracker
│   └── interceptors.py        # gRPC latency & payload telemetry interceptors
├── api/                        # FastAPI backend service
│   ├── main.py                # WebSocket telemetry broadcaster, scan slicer, and chaos controls
│   ├── models.py              # Pydantic schemas for telemetry, scans, and control actions
│   ├── mri_generator.py       # 3D multi-planar BraTS volume cache & PNG slice/mask encoder
│   └── Dockerfile
├── dashboard/                  # Bespoke React + Vite + TypeScript Ops Console
│   ├── src/
│   │   ├── components/
│   │   │   ├── FederatedNetwork3D.tsx # 3D WebGL orbital nodes with animated spline beams
│   │   │   ├── MriSliceViewer3D.tsx   # Multi-planar PACS slice viewer (Axial/Sagittal/Coronal)
│   │   │   ├── ConvergenceChart.tsx   # Live Dice / Loss curves with clinical target line
│   │   │   ├── HospitalNodeCards.tsx  # Node telemetry cards with one-click dropout toggle
│   │   │   ├── PrivacyBudgetGauge.tsx # RDP (ε, δ) meter & TenSEAL cryptographic spec
│   │   │   ├── DemoControlPanel.tsx   # Live chaos controls, CKKS toggle, and manual step
│   │   │   └── Navbar.tsx             # Clinical header with WebSocket liveness indicator
│   │   ├── services/
│   │   │   └── apiService.ts          # Resilient WebSocket client & REST control API
│   │   ├── types.ts                   # Strongly-typed telemetry & scan data models
│   │   ├── App.tsx                    # Central ops cockpit layout
│   │   └── main.tsx                   # Application entrypoint
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── docs/                       # Architecture diagrams, benchmarks, compliance notes, slides
├── scripts/                    # Orchestration runners
│   ├── run_demo.sh            # Bash demo launcher for Linux/macOS/WSL
│   └── run_demo.ps1           # PowerShell demo launcher for Windows
├── tests/                      # PyTest unit test suite (22 tests covering all modules)
├── .github/workflows/
│   └── ci.yml                 # GitHub Actions CI (Python lint/test + Node build)
└── docker-compose.yml          # Offline-capable 6-container production stack
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 20+ & npm 10+
- (Optional) Docker & Docker Compose

### 2. Environment Setup

```bash
# Clone the repository
git clone https://github.com/rahulsri18/FedMed.git
cd FedMed

# Create virtual environment & install Python dependencies
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Install Frontend dependencies
cd dashboard
npm install
cd ..
```

### 3. Generate Development mTLS Certificates

```bash
python -m network.certs.generate_certs
```
Generates the Root CA (`ca.crt`, `ca.key`), server certificate with Subject Alternative Names (`server.crt`, `server.key`), and individual client credentials (`client-node-1/2/3.crt/key`) into `network/certs/`.

---

## Running the Complete Demo

### Option A: One-Command Local Script (Recommended)

**On Linux / macOS / WSL:**
```bash
chmod +x scripts/run_demo.sh
./scripts/run_demo.sh
```

**On Windows (PowerShell):**
```powershell
.\scripts\run_demo.ps1
```

This launches all 6 services simultaneously:
1. `server.server` — Flower Central Server on port `8080`
2. `api.main` — FastAPI Telemetry & Scan service on port `8000`
3. `client.client (Node 1)` — Hospital Silo 1 (St. Jude) on aux port `8081`
4. `client.client (Node 2)` — Hospital Silo 2 (Charité Berlin) on aux port `8082`
5. `client.client (Node 3)` — Hospital Silo 3 (Mayo Clinic) on aux port `8083`
6. `dashboard` — Vite Frontend Dashboard on `http://localhost:3000`

### Option B: Docker Compose

```bash
docker-compose up --build
```

Access the services:
- **Operations Dashboard**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Telemetry WebSocket**: `ws://localhost:8000/ws/telemetry`
- **Flower Federated Server**: `localhost:8080`

---

## Running Tests & Code Quality Checks

```bash
# Run the full unit test suite (22 tests across all modules)
python -m pytest tests/ -v

# Run the Python Ruff linter
python -m ruff check . --ignore E501,E402

# Run frontend TypeScript typecheck & lint
cd dashboard && npm run lint

# Build production frontend bundle
npm run build
```

---

## Cryptographic Trust Model & Differential Privacy

### 1. TenSEAL CKKS Homomorphic Encryption
- **Parameters**: Polynomial modulus degree $N = 8192$, coefficient modulus primes `[60, 40, 40, 60]`, scale $2^{40}$.
- **Slot Capacity**: Each ciphertext slot vector holds $N/2 = 4096$ values. Parameter updates exceeding 4096 dimensions are sliced into chunked ciphertexts.
- **Pre-Scaling**: Client weights are multiplied by a scale factor (`PRESCALE_FACTOR = 1000.0`) prior to encryption to safeguard fixed-point floating precision against noise accumulation.
- **Trust Boundary**: The 3 hospital clients hold the shared secret key. The central Flower server possesses **ONLY** the public evaluation context (Galois + relinearization keys) and computes $\sum w_i \cdot \text{Enc}(W_i)$ homomorphically using server-side addition and scalar multiplication. At no point can the server or any eavesdropper decrypt individual patient weights.

### 2. Opacus-Style Differential Privacy
- **Architectural Constraint**: Strictly enforces **InstanceNorm / GroupNorm** throughout the 3D U-Net. **BatchNorm is strictly prohibited** because batch statistics leak cross-patient information across samples during forward passes.
- **Clipping**: Per-update L2 norm is clipped to $C = 1.0$:
  $$g \leftarrow g / \max(1, \|g\|_2 / C)$$
- **Gaussian Noise**: Calibrated noise $\mathcal{N}(0, \sigma^2 C^2 I)$ is injected before encryption.
- **RDP Privacy Accountant**: Uses analytical Rényi Differential Privacy (RDP) evaluation:
  $$\epsilon(\alpha) = \frac{\alpha \cdot \text{steps}}{2 \sigma^2}$$
  converted to standard $(\epsilon, \delta)$-DP by optimizing over candidate orders $\alpha \in [1.5, 64]$.

---

## API Specification

### Telemetry WebSocket Schema (`/ws/telemetry`)
Emits real-time round-lifecycle packets matching the Pydantic schema in [`api/models.py`](file:///c:/Users/HP/Desktop/FedMed/api/models.py):

```json
{
  "round": 4,
  "phase": "aggregating",
  "global": {
    "loss": 0.2312,
    "dice": 0.8124,
    "rounds_total": 5
  },
  "nodes": [
    {
      "id": 1,
      "name": "St. Jude Medical",
      "status": "active",
      "dice": 0.805,
      "upload_ms": 742,
      "bytes": 5242880
    }
  ],
  "privacy": {
    "epsilon": 5.0,
    "delta": 1e-05,
    "epsilon_spent": 2.45
  },
  "encrypted": true
}
```

### Interactive Chaos & Control Endpoints
- `POST /api/control/dropout/{node_id}` — Trigger simulated mid-round node failure to test quorum survival.
- `POST /api/control/reconnect/{node_id}` — Reconnect a dropped hospital silo.
- `POST /api/control/toggle-encryption` — Toggle CKKS homomorphic encryption vs plaintext baseline live.
- `POST /api/control/step-round` — Manually trigger an FL round advancement step.
- `POST /api/control/select-scan/{id}` — Switch active patient case (`BraTS2021_00001`, `00002`, `00003`).
- `GET /api/control/audit` — Perform instant analytical RDP privacy verification.

### PACS Brain MRI Slice Endpoints
- `GET /scans` — List available patient BraTS volumes with metadata.
- `GET /scans/{id}/slice/{axis}/{index}` — Stream 2D slice PNG along axial, sagittal, or coronal plane with modality selection (`flair`, `t1ce`, `t2`, `t1`).
- `GET /scans/{id}/mask/{axis}/{index}` — Stream 2D RGBA tumor mask PNG with sub-region color coding (Whole Tumor, Tumor Core, Enhancing Tumor).
