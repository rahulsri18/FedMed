# FedMed System Architecture

FedMed is a privacy-preserving cross-silo federated learning engine designed for multi-institutional brain tumor segmentation on the BraTS (Brain Tumor Segmentation) multi-modal 3D MRI dataset.

## High-Level Topology

```mermaid
graph TD
    subgraph Central_Cloud ["Central Cloud / Flower Orchestrator"]
        Server["Flower Server<br/>(FedMedFedAvg Strategy)"]
        HE_Agg["CKKS Homomorphic<br/>Aggregator"]
        HB_Mon["Heartbeat & Liveness<br/>Monitor"]
        FastAPI["FastAPI Gateway<br/>(:8000)"]
        WS["/ws/telemetry<br/>WebSocket"]
    end

    subgraph Consortium_Perimeter ["Encrypted Cross-Silo Perimeter (mTLS + CKKS)"]
        H1["Hospital Silo 1<br/>St. Jude Medical<br/>(Client Node 1 :8081)"]
        H2["Hospital Silo 2<br/>Charité Berlin<br/>(Client Node 2 :8082)"]
        H3["Hospital Silo 3<br/>Mayo Clinic<br/>(Client Node 3 :8083)"]
    end

    subgraph Clinical_Dashboard ["Frontend Telemetry & Visualization"]
        Dash["React + Vite Dashboard<br/>(:3000)"]
        Canvas["HTML5 Canvas 3D<br/>MRI & Tumor Mask Viewer"]
        Charts["Convergence Charts<br/>(Recharts)"]
    end

    H1 -- "Enc(W₁) via gRPC/mTLS" --> Server
    H2 -- "Enc(W₂) via gRPC/mTLS" --> Server
    H3 -- "Enc(W₃ via gRPC/mTLS" --> Server

    Server --> HE_Agg
    HE_Agg --> Server
    Server -- "Telemetry Events" --> FastAPI
    FastAPI --> WS
    WS --> Dash
    Dash --> Canvas
    Dash --> Charts

    Server -- "Aggregated Enc(W)" --> H1
    Server -- "Aggregated Enc(W)" --> H2
    Server -- "Aggregated Enc(W)" --> H3
```

## Security & Trust Model

| Actor | Access Level | Stored Credentials / Keys | Security Constraints |
| :--- | :--- | :--- | :--- |
| **Flower Server** | Honest-but-curious | Public Evaluation Context (Galois + Relin Keys), Server TLS cert | Zero access to raw patient MRI data or plaintext model parameters. Performs homomorphic addition only. |
| **Hospital Nodes (1-3)** | Trusted Consortium | Consortium Secret Key (CKKS), Node mTLS cert & private key | Retain 100% of raw patient data on-premise; execute local DP gradient clipping and Gaussian noise before CKKS encryption. |
| **FastAPI Gateway** | Ephemeral Telemetry | Telemetry stream buffer, mock MRI cache | Emits anonymized aggregated round statistics only. |
| **React Dashboard** | Read-Only Client | None | Consumes telemetry feed and displays rendered slices. |

## Network Protocols & Ports

- **Flower Federated gRPC**: `:8080` (native gRPC with mutual TLS)
- **Node Auxiliary Channels**: `:8081` (Node 1), `:8082` (Node 2), `:8083` (Node 3)
- **FastAPI Telemetry & REST**: `:8000` (HTTP & WebSocket)
- **React Frontend Dashboard**: `:3000` (HTTP)

## Data Pipeline & Model Architecture

1. **Input**: Multi-modal 3D MRI volumes: 4 channels (T1, T1ce, T2, FLAIR).
2. **Backbone**: Compact 3D U-Net (~1.8M parameters) with MONAI building blocks.
3. **Normalization**: **InstanceNorm3d / GroupNorm ONLY**. BatchNorm is forbidden to guarantee compatibility with Differential Privacy (DP) sample isolation.
4. **Target Sub-regions**:
   - **WT**: Whole Tumor (Green)
   - **TC**: Tumor Core (Yellow)
   - **ET**: Enhancing Tumor (Red)
