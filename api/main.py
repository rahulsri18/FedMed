"""api/main.py - FastAPI Application for FedMed Telemetry & Slice Viewer.

Owner: M4 (Network & API Lead)
Usage:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from privacy import compute_privacy_budget
from privacy.audit import run_privacy_audit

from .models import (
    ControlActionResponse,
    GlobalMetrics,
    HeartbeatPayload,
    NodeTelemetry,
    PrivacyBudget,
    ScanMetadata,
    TelemetryPayload,
)
from .mri_generator import VOLUME_CACHE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FedMed.API")

app = FastAPI(
    title="FedMed Federated Learning API",
    description="Cross-Silo FL Telemetry WebSocket & MRI Brain Tumor Scan REST API",
    version="1.0.0",
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PATIENT_METADATA = [
    ScanMetadata(
        id="BraTS2021_00001",
        name="Patient 001 - High-Grade Glioblastoma",
        diagnosis="Glioblastoma Multiforme (WHO Grade IV) - Right Temporal",
        modalities=["FLAIR", "T1ce", "T2", "T1"],
        dimensions=[64, 64, 64],
        assigned_hospital=1,
        tumor_volume_cm3=18.4,
    ),
    ScanMetadata(
        id="BraTS2021_00002",
        name="Patient 002 - Astrocytoma IDH-Mutant",
        diagnosis="Astrocytoma IDH-Mutant (WHO Grade III) - Left Frontal",
        modalities=["FLAIR", "T1ce", "T2", "T1"],
        dimensions=[64, 64, 64],
        assigned_hospital=2,
        tumor_volume_cm3=12.1,
    ),
    ScanMetadata(
        id="BraTS2021_00003",
        name="Patient 003 - Oligodendroglioma",
        diagnosis="Oligodendroglioma 1p/19q-codeleted (WHO Grade II)",
        modalities=["FLAIR", "T1ce", "T2", "T1"],
        dimensions=[64, 64, 64],
        assigned_hospital=3,
        tumor_volume_cm3=8.7,
    ),
]

HOSPITAL_NAMES = {
    1: "St. Jude Medical Silo",
    2: "Charité Berlin Silo",
    3: "Mayo Clinic Oncology",
}


class FederatedTelemetryState:
    """Thread-safe centralized telemetry state synchronizing Flower orchestrator and dashboard."""

    def __init__(self):
        self.current_round = 1
        self.phase = "training"  # training, uploading, aggregating, evaluating, idle
        self.encrypted = True
        self.active_scan_id = "BraTS2021_00001"
        self.auto_step = True
        self.connected_clients: list[WebSocket] = []

        # Hospital nodes tracking
        self.nodes: dict[int, dict[str, Any]] = {
            1: {
                "id": 1,
                "name": HOSPITAL_NAMES[1],
                "status": "active",
                "dice": 0.76,
                "upload_ms": 812,
                "bytes": 5242880,
                "dropped_out": False,
            },
            2: {
                "id": 2,
                "name": HOSPITAL_NAMES[2],
                "status": "active",
                "dice": 0.78,
                "upload_ms": 890,
                "bytes": 5242880,
                "dropped_out": False,
            },
            3: {
                "id": 3,
                "name": HOSPITAL_NAMES[3],
                "status": "active",
                "dice": 0.81,
                "upload_ms": 765,
                "bytes": 5242880,
                "dropped_out": False,
            },
        }

        # Convergence history
        self.history = [
            {"round": 1, "dice": 0.68, "loss": 0.44},
            {"round": 2, "dice": 0.72, "loss": 0.39},
            {"round": 3, "dice": 0.75, "loss": 0.34},
            {"round": 4, "dice": 0.79, "loss": 0.30},
        ]

    def get_global_metrics(self) -> GlobalMetrics:
        # Active nodes average
        active_nodes = [n for n in self.nodes.values() if n["status"] != "offline"]
        if active_nodes:
            mean_dice = sum(n["dice"] for n in active_nodes) / len(active_nodes)
        else:
            mean_dice = 0.70
        loss = max(0.12, 0.48 / (1.0 + self.current_round * 0.16))
        return GlobalMetrics(loss=float(round(loss, 4)), dice=float(round(mean_dice, 4)))

    def get_privacy_budget(self) -> PrivacyBudget:
        spent = compute_privacy_budget(
            rounds=self.current_round,
            local_epochs=2,
            noise_multiplier=0.8,
            sample_rate=0.25,
            delta=1e-5,
        )
        return PrivacyBudget(epsilon=5.0, delta=1e-5, epsilon_spent=float(round(spent, 2)))

    def get_node_telemetry_list(self) -> list[NodeTelemetry]:
        res = []
        for n_id, data in self.nodes.items():
            res.append(
                NodeTelemetry(
                    id=n_id,
                    name=data["name"],
                    status="offline" if data.get("dropped_out", False) else data["status"],
                    dice=float(round(data["dice"], 4)),
                    upload_ms=int(data["upload_ms"]),
                    bytes=int(data["bytes"] if self.encrypted else data["bytes"] // 5),
                )
            )
        return res

    def get_payload(self) -> TelemetryPayload:
        return TelemetryPayload(
            round=self.current_round,
            phase=self.phase,
            global_metrics=self.get_global_metrics(),
            nodes=self.get_node_telemetry_list(),
            privacy=self.get_privacy_budget(),
            encrypted=self.encrypted,
        )

    def step_round(self):
        self.current_round = (self.current_round % 15) + 1
        r = self.current_round

        # Update node scores
        for nid, node in self.nodes.items():
            if not node.get("dropped_out", False):
                node["dice"] = min(0.94, float(round(0.72 + nid * 0.02 + r * 0.022, 4)))
                node["upload_ms"] = 750 + nid * 40 + (r % 3) * 15

        gm = self.get_global_metrics()
        self.history.append({"round": r, "dice": gm.dice, "loss": gm.loss})
        if len(self.history) > 20:
            self.history.pop(0)

    async def broadcast_telemetry(self):
        payload = self.get_payload().model_dump(by_alias=True)
        message = json.dumps(payload)
        for ws in list(self.connected_clients):
            try:
                await ws.send_text(message)
            except Exception:  # noqa: BLE001
                if ws in self.connected_clients:
                    self.connected_clients.remove(ws)


TELEMETRY_STATE = FederatedTelemetryState()


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "FedMed Federated Learning API",
        "version": "1.0.0",
        "active_nodes": len([n for n in TELEMETRY_STATE.nodes.values() if not n.get("dropped_out")]),
        "current_round": TELEMETRY_STATE.current_round,
        "encryption": "CKKS Homomorphic" if TELEMETRY_STATE.encrypted else "Plaintext FedAvg",
    }


@app.get("/scans", response_model=list[ScanMetadata])
def get_scans():
    """List available BraTS patient cases."""
    return PATIENT_METADATA


@app.get("/scans/{scan_id}/slice/{axis}/{index}")
def get_scan_slice(
    scan_id: str,
    axis: str = "axial",
    index: int = 32,
    modality: str = Query("FLAIR", description="Acquisition modality: FLAIR, T1ce, T2, T1"),
    wl: float = Query(0.5, description="Window Level"),
    ww: float = Query(1.0, description="Window Width"),
):
    """Retrieve a 2D MRI slice along an axis (axial, sagittal, coronal) as PNG."""
    png_bytes = VOLUME_CACHE.get_slice(
        scan_id=scan_id,
        axis=axis,
        index=index,
        modality=modality,
        window_level=wl,
        window_width=ww,
    )
    return Response(content=png_bytes, media_type="image/png")


@app.get("/scans/{scan_id}/mask/{index}")
def get_scan_mask_axial_default(
    scan_id: str,
    index: int,
    wt: bool = Query(True, description="Whole Tumor (Green)"),
    tc: bool = Query(True, description="Tumor Core (Amber)"),
    et: bool = Query(True, description="Enhancing Tumor (Coral)"),
    opacity: float = Query(0.75, description="Overlay opacity [0..1]"),
):
    """Retrieve axial tumor segmentation overlay mask (RGBA PNG)."""
    mask_bytes = VOLUME_CACHE.get_mask_slice(
        scan_id=scan_id,
        axis="axial",
        index=index,
        show_wt=wt,
        show_tc=tc,
        show_et=et,
        opacity=opacity,
    )
    return Response(content=mask_bytes, media_type="image/png")


@app.get("/scans/{scan_id}/mask/{axis}/{index}")
def get_scan_mask(
    scan_id: str,
    axis: str = "axial",
    index: int = 32,
    wt: bool = Query(True, description="Whole Tumor (Green)"),
    tc: bool = Query(True, description="Tumor Core (Amber)"),
    et: bool = Query(True, description="Enhancing Tumor (Coral)"),
    opacity: float = Query(0.75, description="Overlay opacity [0..1]"),
):
    """Retrieve multi-class tumor segmentation overlay mask (RGBA PNG)."""
    mask_bytes = VOLUME_CACHE.get_mask_slice(
        scan_id=scan_id,
        axis=axis,
        index=index,
        show_wt=wt,
        show_tc=tc,
        show_et=et,
        opacity=opacity,
    )
    return Response(content=mask_bytes, media_type="image/png")



# -------------------------------------------------------------
# Demo Interactive Control Panel REST Endpoints
# -------------------------------------------------------------

@app.post("/api/control/dropout/{node_id}", response_model=ControlActionResponse)
async def trigger_node_dropout(node_id: int):
    """Simulate mid-round network dropout or server crash for a hospital silo."""
    if node_id in TELEMETRY_STATE.nodes:
        TELEMETRY_STATE.nodes[node_id]["dropped_out"] = True
        TELEMETRY_STATE.nodes[node_id]["status"] = "offline"
        await TELEMETRY_STATE.broadcast_telemetry()
        return ControlActionResponse(
            success=True,
            action="dropout",
            message=f"Hospital Node {node_id} ({HOSPITAL_NAMES.get(node_id, '')}) dropped out. Minimum quorum survived.",
            current_round=TELEMETRY_STATE.current_round,
            encrypted=TELEMETRY_STATE.encrypted,
        )
    return ControlActionResponse(
        success=False,
        action="dropout",
        message=f"Node {node_id} not recognized",
        current_round=TELEMETRY_STATE.current_round,
        encrypted=TELEMETRY_STATE.encrypted,
    )


@app.post("/api/control/reconnect/{node_id}", response_model=ControlActionResponse)
async def trigger_node_reconnect(node_id: int):
    """Reconnect a previously disconnected hospital silo."""
    if node_id in TELEMETRY_STATE.nodes:
        TELEMETRY_STATE.nodes[node_id]["dropped_out"] = False
        TELEMETRY_STATE.nodes[node_id]["status"] = "active"
        await TELEMETRY_STATE.broadcast_telemetry()
        return ControlActionResponse(
            success=True,
            action="reconnect",
            message=f"Hospital Node {node_id} ({HOSPITAL_NAMES.get(node_id, '')}) reconnected successfully.",
            current_round=TELEMETRY_STATE.current_round,
            encrypted=TELEMETRY_STATE.encrypted,
        )
    return ControlActionResponse(
        success=False,
        action="reconnect",
        message=f"Node {node_id} not recognized",
        current_round=TELEMETRY_STATE.current_round,
        encrypted=TELEMETRY_STATE.encrypted,
    )


@app.post("/api/control/toggle-encryption", response_model=ControlActionResponse)
async def toggle_encryption():
    """Toggle between TenSEAL CKKS Homomorphic Encryption and Plaintext FedAvg."""
    TELEMETRY_STATE.encrypted = not TELEMETRY_STATE.encrypted
    mode_str = "TenSEAL CKKS Homomorphic Encryption" if TELEMETRY_STATE.encrypted else "Plaintext FedAvg"
    await TELEMETRY_STATE.broadcast_telemetry()
    return ControlActionResponse(
        success=True,
        action="toggle_encryption",
        message=f"Aggregation scheme switched to: {mode_str}",
        current_round=TELEMETRY_STATE.current_round,
        encrypted=TELEMETRY_STATE.encrypted,
    )


@app.post("/api/control/step-round", response_model=ControlActionResponse)
async def step_round():
    """Manually step forward one federated communication round."""
    TELEMETRY_STATE.step_round()
    TELEMETRY_STATE.phase = "aggregating"
    await TELEMETRY_STATE.broadcast_telemetry()
    return ControlActionResponse(
        success=True,
        action="step_round",
        message=f"Stepped forward to Communication Round {TELEMETRY_STATE.current_round}",
        current_round=TELEMETRY_STATE.current_round,
        encrypted=TELEMETRY_STATE.encrypted,
    )


@app.post("/api/control/select-scan/{scan_id}", response_model=ControlActionResponse)
async def select_scan(scan_id: str):
    """Switch the active patient scan in the 3D MRI viewer."""
    if scan_id in VOLUME_CACHE.scans:
        TELEMETRY_STATE.active_scan_id = scan_id
        await TELEMETRY_STATE.broadcast_telemetry()
        return ControlActionResponse(
            success=True,
            action="select_scan",
            message=f"Active scan set to {scan_id}",
            current_round=TELEMETRY_STATE.current_round,
            encrypted=TELEMETRY_STATE.encrypted,
        )
    return ControlActionResponse(
        success=False,
        action="select_scan",
        message=f"Scan {scan_id} not found",
        current_round=TELEMETRY_STATE.current_round,
        encrypted=TELEMETRY_STATE.encrypted,
    )


@app.post("/api/heartbeat")
async def receive_heartbeat(hb: HeartbeatPayload):
    """Ingest live heartbeat from client node process."""
    if hb.node_id in TELEMETRY_STATE.nodes and not TELEMETRY_STATE.nodes[hb.node_id].get("dropped_out"):
        node = TELEMETRY_STATE.nodes[hb.node_id]
        node["status"] = hb.status
        if hb.dice is not None:
            node["dice"] = hb.dice
        if hb.upload_ms is not None:
            node["upload_ms"] = hb.upload_ms
        await TELEMETRY_STATE.broadcast_telemetry()
    return {"status": "ok"}


@app.post("/api/telemetry/round")
async def receive_round_event(payload: dict):
    """Ingest round completion webhook from central Flower server."""
    r = payload.get("round", TELEMETRY_STATE.current_round)
    TELEMETRY_STATE.current_round = r
    TELEMETRY_STATE.phase = payload.get("phase", "aggregated")
    TELEMETRY_STATE.encrypted = payload.get("encrypted", TELEMETRY_STATE.encrypted)
    await TELEMETRY_STATE.broadcast_telemetry()
    return {"status": "recorded"}


@app.get("/api/privacy/audit")
def get_privacy_audit():
    """Execute cryptographic trust model and differential privacy audit."""
    return run_privacy_audit(target_epsilon=5.0, delta=1e-5, rounds=TELEMETRY_STATE.current_round)


@app.get("/api/history")
def get_convergence_history():
    """Return historical loss and Dice records across rounds."""
    return TELEMETRY_STATE.history


# -------------------------------------------------------------
# Throttled Live Telemetry WebSocket
# -------------------------------------------------------------

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """Throttled WebSocket endpoint streaming live round telemetry matching FedMed schema."""
    await websocket.accept()
    TELEMETRY_STATE.connected_clients.append(websocket)
    logger.info("[WebSocket] New client connected to /ws/telemetry (Total: %d)", len(TELEMETRY_STATE.connected_clients))

    # Send immediate state on connect
    init_payload = TELEMETRY_STATE.get_payload().model_dump(by_alias=True)
    await websocket.send_text(json.dumps(init_payload))

    phases = ["training", "encrypting", "uploading", "aggregating", "evaluating"]
    phase_idx = 0

    try:
        while True:
            # Smoothly transition phases
            phase_idx = (phase_idx + 1) % len(phases)
            TELEMETRY_STATE.phase = phases[phase_idx]

            # When completing a full phase cycle, advance communication round if auto_step is on
            if phase_idx == 0 and TELEMETRY_STATE.auto_step:
                TELEMETRY_STATE.step_round()

            payload = TELEMETRY_STATE.get_payload().model_dump(by_alias=True)
            await websocket.send_text(json.dumps(payload))

            # Throttled interval (~2.2 seconds) to avoid UI jitter and ensure smooth 60fps rendering
            await asyncio.sleep(2.2)

    except WebSocketDisconnect:
        logger.info("[WebSocket] Client disconnected from /ws/telemetry")
    except Exception as e:  # noqa: BLE001
        logger.error("[WebSocket] Stream exception: %s", e)
    finally:
        if websocket in TELEMETRY_STATE.connected_clients:
            TELEMETRY_STATE.connected_clients.remove(websocket)
