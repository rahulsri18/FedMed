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

## 5-Person Team Ownership & Architecture Split

FedMed is engineered as a clean modular scaffold so a 5-person team can develop features concurrently without merge conflicts:

| Member | Focus Area | Modules Owned | Key Responsibilities |
| :--- | :--- | :--- | :--- |
| **M1** | **Server & Orchestration** | [`server/`](file:///c:/Users/HP/Desktop/FedMed/server), [`docker-compose.yml`](file:///c:/Users/HP/Desktop/FedMed/docker-compose.yml), [`scripts/`](file:///c:/Users/HP/Desktop/FedMed/scripts), CI | Flower server entrypoint, custom `FedMedFedAvg` strategy, lifecycle logging, Docker orchestration. |
| **M2** | **Models & Data** | [`models/`](file:///c:/Users/HP/Desktop/FedMed/models), [`data/`](file:///c:/Users/HP/Desktop/FedMed/data) | Compact 3D U-Net (InstanceNorm / GroupNorm only), DiceCELoss, BraTS NIfTI loader, Dirichlet non-IID partitioner. |
| **M3** | **Privacy & Cryptography** | [`privacy/`](file:///c:/Users/HP/Desktop/FedMed/privacy) | TenSEAL CKKS encryption context, tensor pack/unpack, Opacus-style DP clipping + Gaussian noise, privacy accountant. |
| **M4** | **Networking & Telemetry** | [`network/`](file:///c:/Users/HP/Desktop/FedMed/network), [`api/`](file:///c:/Users/HP/Desktop/FedMed/api) | gRPC auxiliary channel proto, mTLS certificate generation script, heartbeat monitor, FastAPI WebSocket & REST endpoints. |
| **M5** | **Dashboard & Frontend** | [`dashboard/`](file:///c:/Users/HP/Desktop/FedMed/dashboard) | React + Vite UI, TailwindCSS, Recharts convergence graphs, HTML5 Canvas 3D MRI slice & tumor mask viewer, mock telemetry generator. |

---

## Repository Layout

```
FedMed/
├── server/                     # [M1] Flower server, custom FedAvg strategy, encrypted aggregator
│   ├── __init__.py
│   ├── server.py              # Server entrypoint (python -m server.server)
│   ├── strategy.py            # Custom FedMedFedAvg strategy with structured round logging
│   ├── aggregator.py          # Plaintext & CKKS homomorphic aggregation logic
│   └── Dockerfile
├── client/                     # [M1, M2, M3] Flower NumPyClient node implementation
│   ├── __init__.py
│   ├── client.py              # Client entrypoint parameterized by --node-id & --port
│   └── Dockerfile
├── models/                     # [M2] Deep learning architectures & metrics
│   ├── __init__.py
│   ├── unet.py                # DP-compatible Compact 3D U-Net (~1.8M params, InstanceNorm)
│   ├── losses.py              # Soft DiceLoss & DiceCELoss
│   └── metrics.py             # Mean Dice, Hausdorff 95, region-specific metrics
├── data/                       # [M2] BraTS dataset handling & hospital partitioning
│   ├── __init__.py
│   ├── brats_dataset.py       # NIfTI loader with zero-dependency synthetic 3D volume fallback
│   ├── transforms.py          # MONAI augmentation & preprocessing pipeline
│   └── partitioner.py         # IID and Dirichlet non-IID hospital split generator
├── privacy/                    # [M3] TenSEAL CKKS Homomorphic Encryption & DP
│   ├── __init__.py
│   ├── tenseal_context.py     # CKKS context generator (N=8192, scale=2^40) & trust model docs
│   ├── encryption.py          # Tensor-to-ciphertext pack/unpack helpers
│   ├── differential_privacy.py# Global L2 clipping & Gaussian noise perturbation
│   └── audit.py               # Compliance audit & privacy budget tracker
├── network/                    # [M4] Networking, mTLS security & auxiliary channels
│   ├── __init__.py
│   ├── protos/
│   │   └── auxiliary.proto    # gRPC definitions for health checks & key distribution
│   ├── certs/
│   │   └── generate_certs.py  # mTLS certificate authority, server & client cert generator
│   ├── heartbeat.py           # Server-side heartbeat monitor & node timeout tracker
│   └── interceptors.py        # gRPC latency & payload telemetry interceptors
├── api/                        # [M4] FastAPI backend service
│   ├── __init__.py
│   ├── main.py                # FastAPI app: /ws/telemetry WebSocket & REST slice endpoints
│   ├── models.py              # Pydantic telemetry & scan metadata schemas
│   └── Dockerfile
├── dashboard/                  # [M5] React + Vite + Tailwind frontend application
│   ├── src/
│   │   ├── components/        # MetricsChart, NodeCards, PrivacyGauge, CanvasMRIViewer
│   │   ├── services/          # mockTelemetry.js (fallback mock + live WebSocket client)
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
├── docs/                       # Architecture diagrams, benchmarks, compliance notes, slides
│   ├── architecture.md
│   ├── benchmarks.md
│   ├── compliance.md
│   └── slides.md
├── scripts/                    # Orchestration runners
│   ├── run_demo.sh            # Bash demo launcher for Linux/macOS/WSL
│   └── run_demo.ps1           # PowerShell demo launcher for Windows
├── tests/                      # PyTest unit test suite per module
│   ├── test_server.py
│   ├── test_client.py
│   ├── test_models.py
│   ├── test_data.py
│   ├── test_privacy.py
│   ├── test_network.py
│   └── test_api.py
├── .github/workflows/
│   └── ci.yml                 # GitHub Actions CI (Python 3.11 lint/test + Node 20 build)
├── docker-compose.yml          # Containerized deployment of server, 3 hospital nodes, api, dashboard
├── requirements.txt            # Pinned dependencies for Python 3.11
├── .gitignore
└── README.md
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
This generates the Root CA (`ca.crt`, `ca.key`), server certificate with SANs (`server.crt`, `server.key`), and client certificates for the 3 hospital silos into `network/certs/` (gitignored).

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

This launches all 6 microservices simultaneously:
1. `server.server` — Flower Central Server on port `8080`
2. `api.main` — FastAPI Telemetry & Scan service on port `8000`
3. `client.client (Node 1)` — Hospital Silo 1 (St. Jude) on port `8081`
4. `client.client (Node 2)` — Hospital Silo 2 (Charité Berlin) on port `8082`
5. `client.client (Node 3)` — Hospital Silo 3 (Mayo Clinic) on port `8083`
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
# Run the full unit test suite (17 tests across all modules)
python -m pytest tests/ -v

# Run the Ruff linter
python -m ruff check .

# Test frontend build
cd dashboard && npm run build
```

---

## Cryptographic Trust Model & Differential Privacy

1. **CKKS Homomorphic Encryption (TenSEAL)**:
   - Poly modulus degree $N = 8192$, coefficient modulus primes `[60, 40, 40, 60]`, scale $2^{40}$.
   - **Trust Boundary**: The 3 hospital clients hold the shared secret key. The central Flower server possesses ONLY the public evaluation context (Galois + relinearization keys) and computes $\sum w_i \cdot \text{Enc}(W_i)$ homomorphically without ever decrypting or learning individual patient model updates.

2. **Opacus-Style Differential Privacy**:
   - Strictly enforces **InstanceNorm / GroupNorm** (BatchNorm is mathematically prohibited to prevent cross-sample gradient leakage).
   - Global L2-norm clipping threshold $C = 1.0$, calibrated Gaussian noise multiplier $\sigma = 0.8$, guaranteeing $(\epsilon \le 5.0, \delta = 10^{-5})$ over 15 training rounds.

---

## API Specification

### Telemetry WebSocket Schema (`/ws/telemetry`)
Emits real-time round-lifecycle packets matching the Pydantic schema in [`api/models.py`](file:///c:/Users/HP/Desktop/FedMed/api/models.py):

```json
{
  "round": 4,
  "phase": "aggregating",
  "global": { "loss": 0.31, "dice": 0.78 },
  "nodes": [
    { "id": 1, "status": "active", "dice": 0.76, "upload_ms": 812, "bytes": 5242880 }
  ],
  "privacy": { "epsilon": 5.0, "delta": 1e-5, "epsilon_spent": 2.3 },
  "encrypted": true
}
```

### REST Endpoints
- `GET /` — Health check & service metadata
- `GET /scans` — List available patient BraTS cases
- `GET /scans/{id}/slice/{axis}/{index}` — Fetch 2D slice along axial, sagittal, or coronal plane
- `GET /scans/{id}/mask/{index}` — Fetch multi-region color tumor segmentation overlay mask

---

## Next Steps for the Team (M1–M5)

Each module contains explicit `TODO(M1)` through `TODO(M5)` markers. To begin feature implementation:
- **M1**: Integrate native SSL/TLS credentials in `flwr.server.start_server`.
- **M2**: Mount real BraTS 2021 `.nii.gz` volumes in `data/brats_dataset.py` and implement Hausdorff 95 in `models/metrics.py`.
- **M3**: Benchmark CKKS ciphertext serialization latency in `privacy/encryption.py`.
- **M4**: Wire `network/heartbeat.py` into FastAPI's WebSocket broadcaster.
- **M5**: Connect the interactive slice viewer directly to the REST scan endpoints when available.
