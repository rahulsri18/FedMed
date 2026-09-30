"""api/main.py - FastAPI Application for FedMed Telemetry & Slice Viewer.

Owner: M4 (Network & API Lead)
Usage:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

import asyncio
import json
import logging

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .models import (
    GlobalMetrics,
    NodeTelemetry,
    PrivacyBudget,
    ScanMetadata,
    TelemetryPayload,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FedMed.API")

app = FastAPI(
    title="FedMed Federated Learning API",
    description="Cross-Silo FL Telemetry WebSocket & MRI Brain Tumor Scan REST API",
    version="0.1.0",
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated in-memory database of BraTS scans
MOCK_SCANS = [
    ScanMetadata(id="BraTS2021_00001", name="Patient 001 - High-Grade Glioblastoma", assigned_hospital=1),
    ScanMetadata(id="BraTS2021_00002", name="Patient 002 - Astrocytoma IDH-Mutant", assigned_hospital=2),
    ScanMetadata(id="BraTS2021_00003", name="Patient 003 - Oligodendroglioma", assigned_hospital=3),
]


def generate_synthetic_mri_png(slice_idx: int, is_mask: bool = False) -> bytes:
    """Generates a synthetic 2D 128x128 grayscale MRI slice or colored tumor mask as PNG bytes."""
    size = 128
    y, x = np.ogrid[:size, :size]
    center = (size // 2, size // 2)
    radius = size // 2 - 12
    
    # Brain boundary
    dist_from_center = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    brain_mask = dist_from_center <= radius

    if not is_mask:
        # Grayscale MRI brain tissue
        img = np.zeros((size, size), dtype=np.uint8)
        img[brain_mask] = 130 + np.random.randint(-15, 15, size=np.sum(brain_mask))
        
        # Tumor hyperintensity
        t_dist = np.sqrt((x - (center[0] + 16))**2 + (y - (center[1] - 12))**2)
        tumor_region = (t_dist <= 18) & brain_mask
        img[tumor_region] = 235
    else:
        # 3-channel RGBA mask: Green = WT (Whole Tumor), Red = ET (Enhancing)
        rgba = np.zeros((size, size, 4), dtype=np.uint8)
        t_dist = np.sqrt((x - (center[0] + 16))**2 + (y - (center[1] - 12))**2)
        wt = (t_dist <= 20) & brain_mask
        tc = (t_dist <= 14) & brain_mask
        et = (t_dist <= 8) & brain_mask

        # Whole Tumor (Green)
        rgba[wt] = [34, 197, 94, 160]
        # Tumor Core (Yellow)
        rgba[tc] = [234, 179, 8, 200]
        # Enhancing Tumor (Red)
        rgba[et] = [239, 68, 68, 240]

    # Simple PNG format encoder (raw uncompressed BMP or minimal PNG chunk)
    # Using lightweight BMP header for zero-dependency native byte generation:
    if not is_mask:
        # 8-bit grayscale BMP
        header = bytearray(54 + 1024)
        header[0:2] = b'BM'
        file_size = 54 + 1024 + size * size
        header[2:6] = file_size.to_bytes(4, 'little')
        header[10:14] = (54 + 1024).to_bytes(4, 'little')
        header[14:18] = (40).to_bytes(4, 'little')
        header[18:22] = size.to_bytes(4, 'little')
        header[22:26] = size.to_bytes(4, 'little')
        header[26:28] = (1).to_bytes(2, 'little')
        header[28:30] = (8).to_bytes(2, 'little')
        header[30:34] = (0).to_bytes(4, 'little')
        # Palette
        for i in range(256):
            header[54 + i * 4 : 54 + i * 4 + 4] = bytes([i, i, i, 0])
        return bytes(header) + np.flipud(img).tobytes()
    else:
        # 32-bit RGBA BMP
        header = bytearray(54)
        header[0:2] = b'BM'
        file_size = 54 + size * size * 4
        header[2:6] = file_size.to_bytes(4, 'little')
        header[10:14] = (54).to_bytes(4, 'little')
        header[14:18] = (40).to_bytes(4, 'little')
        header[18:22] = size.to_bytes(4, 'little')
        header[22:26] = size.to_bytes(4, 'little')
        header[26:28] = (1).to_bytes(2, 'little')
        header[28:30] = (32).to_bytes(2, 'little')
        # Flip vertically for BMP
        flipped = np.flipud(rgba)
        # Convert RGBA to BGRA
        bgra = np.zeros_like(flipped)
        bgra[:, :, 0] = flipped[:, :, 2]
        bgra[:, :, 1] = flipped[:, :, 1]
        bgra[:, :, 2] = flipped[:, :, 0]
        bgra[:, :, 3] = flipped[:, :, 3]
        return bytes(header) + bgra.tobytes()


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "FedMed Backend API",
        "version": "0.1.0",
        "description": "Federated Brain Tumor Segmentation API",
    }


@app.get("/scans", response_model=list[ScanMetadata])
def get_scans():
    """List available BraTS patient cases."""
    # TODO(M4): Query data/ directory or database for registered patient volumes
    return MOCK_SCANS


@app.get("/scans/{scan_id}/slice/{axis}/{index}")
def get_scan_slice(scan_id: str, axis: str, index: int):
    """Retrieve a 2D MRI slice along an axis (axial, sagittal, coronal)."""
    # TODO(M4): Implement real NIfTI slice extraction via nibabel/MONAI
    img_bytes = generate_synthetic_mri_png(slice_idx=index, is_mask=False)
    return Response(content=img_bytes, media_type="image/bmp")


@app.get("/scans/{scan_id}/mask/{index}")
def get_scan_mask(scan_id: str, index: int):
    """Retrieve the multi-class tumor segmentation mask overlay for a slice."""
    # TODO(M4): Extract predicted or ground-truth tumor masks (WT, TC, ET)
    mask_bytes = generate_synthetic_mri_png(slice_idx=index, is_mask=True)
    return Response(content=mask_bytes, media_type="image/bmp")


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """WebSocket endpoint emitting real-time federated round metrics matching the FedMed schema."""
    await websocket.accept()
    logger.info("[WebSocket] Client connected to /ws/telemetry")
    current_round = 1

    try:
        while True:
            # Emit live telemetry cycle
            telemetry_data = TelemetryPayload(
                round=current_round,
                phase="aggregating" if current_round % 2 == 0 else "training",
                global_metrics=GlobalMetrics(
                    loss=float(round(0.45 / (1.0 + current_round * 0.15), 4)),
                    dice=float(round(min(0.92, 0.68 + current_round * 0.035), 4)),
                ),
                nodes=[
                    NodeTelemetry(
                        id=1,
                        status="active",
                        dice=float(round(0.72 + current_round * 0.03, 4)),
                        upload_ms=812 + (current_round % 3) * 15,
                        bytes=5242880,
                    ),
                    NodeTelemetry(
                        id=2,
                        status="active",
                        dice=float(round(0.74 + current_round * 0.032, 4)),
                        upload_ms=920 - (current_round % 4) * 20,
                        bytes=5242880,
                    ),
                    NodeTelemetry(
                        id=3,
                        status="active",
                        dice=float(round(0.76 + current_round * 0.028, 4)),
                        upload_ms=780 + (current_round % 2) * 30,
                        bytes=5242880,
                    ),
                ],
                privacy=PrivacyBudget(
                    epsilon=5.0,
                    delta=1e-5,
                    epsilon_spent=float(round(min(5.0, 0.8 + current_round * 0.35), 2)),
                ),
                encrypted=True,
            )

            # Dump using exact alias so 'global' is emitted
            payload_json = telemetry_data.model_dump(by_alias=True)
            await websocket.send_text(json.dumps(payload_json))

            current_round = (current_round % 10) + 1
            await asyncio.sleep(2.5)

    except WebSocketDisconnect:
        logger.info("[WebSocket] Client disconnected from /ws/telemetry")
    except Exception as e:  # noqa: BLE001
        logger.error("[WebSocket] Telemetry stream error: %s", e)
