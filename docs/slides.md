# FedMed: Project Presentation Slides Outline

## Slide 1: Title & Executive Summary
- **Title**: FedMed: Cross-Silo Federated Learning for Privacy-Preserving Brain Tumor Segmentation
- **Core Mission**: Break hospital data silos to train state-of-the-art 3D brain tumor segmentation models without centralizing sensitive patient imaging data.
- **Team Roles**: M1 (Orchestration), M2 (Models & Data), M3 (Privacy), M4 (Network & API), M5 (Dashboard).

---

## Slide 2: The Healthcare Dilemma
- Brain tumor segmentation (Glioblastoma) demands multi-institutional volumetric MRI data.
- Centralization is legally and ethically impossible under HIPAA & GDPR.
- Direct model weight sharing without encryption remains vulnerable to reconstruction / gradient inversion attacks.

---

## Slide 3: The FedMed Solution
- **Flower Federated Engine**: Coordinated cross-silo aggregation across 3 simulated medical centers.
- **MONAI Compact 3D U-Net**: GroupNorm/InstanceNorm architecture ensuring full DP compatibility.
- **TenSEAL CKKS**: Cryptographic homomorphic aggregation on ciphertexts without server decryption.
- **Opacus-Style DP**: Strict Rényi Differential Privacy ($\epsilon=5.0, \delta=1e-5$).

---

## Slide 4: System Architecture
- 3 Hospital Silos: St. Jude, Charité Berlin, Mayo Clinic.
- Central Flower Orchestrator with custom `FedMedFedAvg` strategy.
- FastAPI auxiliary gateway with real-time WebSocket telemetry.
- Vite + React clinical operations dashboard with Canvas MRI slice viewer.

---

## Slide 5: Current Milestones & Parallel Workstreams
- Scaffolding complete; hello-world entrypoints and CI green.
- M1-M5 ownership interfaces well-defined with clear TODO markers.
- Ready for full model convergence and clinical dataset mounting.
