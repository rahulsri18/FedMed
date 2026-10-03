"""
api/main.py

FastAPI Application for FedMed Telemetry & Slice Viewer.

Owner: M4 (Network & API Lead)

Usage:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

import asyncio
import json
import logging
import threading
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from network.grpc_server import (
    create_server,
    monitor_node_timeouts,
)

from .models import (
    GlobalMetrics,
    NodeTelemetry,
    PrivacyBudget,
    ScanMetadata,
    TelemetryPayload,
)


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("FedMed.API")


# ---------------------------------------------------------
# Global gRPC server references
# ---------------------------------------------------------

grpc_server = None
grpc_service = None
timeout_thread = None
heartbeat_thread = None



# ---------------------------------------------------------
# FastAPI Lifespan
# ---------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global grpc_server, grpc_service, heartbeat_thread

    logger.info("[M4] Starting gRPC auxiliary server...")

    grpc_server, grpc_service = create_server()

    grpc_server.start()

    logger.info(
        "[M4] gRPC server started on port 50051"
    )

    # Start heartbeat timeout monitoring
    heartbeat_thread = threading.Thread(
        target=monitor_node_timeouts,
        args=(grpc_service,),
        daemon=True,
        name="FedMed-Heartbeat-Monitor",
    )

    heartbeat_thread.start()

    logger.info(
        "[M4] Heartbeat timeout monitor started"
    )

    yield

    logger.info(
        "[M4] Stopping gRPC auxiliary server..."
    )

    if grpc_server is not None:
        grpc_server.stop(grace=5)

    logger.info(
        "[M4] FastAPI shutdown complete"
    )

    # -----------------------------------------------------
    # Start heartbeat timeout monitor
    # -----------------------------------------------------

    timeout_thread = threading.Thread(
        target=monitor_node_timeouts,
        args=(grpc_service,),
        daemon=True,
        name="FedMed-HeartbeatMonitor",
    )

    timeout_thread.start()

    logger.info(
        "[M4] Heartbeat timeout monitor started"
    )

    try:
        yield

    finally:
        logger.info(
            "[M4] Stopping gRPC auxiliary server..."
        )

        if grpc_server is not None:
            grpc_server.stop(grace=5)

        logger.info(
            "[M4] gRPC auxiliary server stopped"
        )


# ---------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------

app = FastAPI(
    title="FedMed Federated Learning API",
    description=(
        "Cross-Silo Federated Learning Telemetry "
        "& MRI Brain Tumor Scan REST API"
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Mock MRI scan registry
# ---------------------------------------------------------

MOCK_SCANS = [
    ScanMetadata(
        id="BraTS2021_00001",
        name="Patient 001 - High-Grade Glioblastoma",
        assigned_hospital=1,
    ),
    ScanMetadata(
        id="BraTS2021_00002",
        name="Patient 002 - Astrocytoma IDH-Mutant",
        assigned_hospital=2,
    ),
    ScanMetadata(
        id="BraTS2021_00003",
        name="Patient 003 - Oligodendroglioma",
        assigned_hospital=3,
    ),
]


# ---------------------------------------------------------
# Synthetic MRI generator
# ---------------------------------------------------------

def generate_synthetic_mri_png(
    slice_idx: int,
    is_mask: bool = False,
) -> bytes:
    """
    Generate a synthetic 128x128 MRI slice or tumor mask.

    Note:
        Despite the historical function name, the returned
        data is actually BMP format.
    """

    size = 128

    y, x = np.ogrid[:size, :size]

    center = (
        size // 2,
        size // 2,
    )

    radius = size // 2 - 12

    # -----------------------------------------------------
    # Brain boundary
    # -----------------------------------------------------

    dist_from_center = np.sqrt(
        (x - center[0]) ** 2
        + (y - center[1]) ** 2
    )

    brain_mask = dist_from_center <= radius

    # -----------------------------------------------------
    # MRI image
    # -----------------------------------------------------

    if not is_mask:

        img = np.zeros(
            (size, size),
            dtype=np.uint8,
        )

        img[brain_mask] = (
            130
            + np.random.randint(
                -15,
                15,
                size=np.sum(brain_mask),
            )
        )

        # Synthetic tumor
        tumor_distance = np.sqrt(
            (
                x
                - (center[0] + 16)
            ) ** 2
            + (
                y
                - (center[1] - 12)
            ) ** 2
        )

        tumor_region = (
            (tumor_distance <= 18)
            & brain_mask
        )

        img[tumor_region] = 235

    # -----------------------------------------------------
    # Tumor mask
    # -----------------------------------------------------

    else:

        rgba = np.zeros(
            (size, size, 4),
            dtype=np.uint8,
        )

        tumor_distance = np.sqrt(
            (
                x
                - (center[0] + 16)
            ) ** 2
            + (
                y
                - (center[1] - 12)
            ) ** 2
        )

        whole_tumor = (
            (tumor_distance <= 20)
            & brain_mask
        )

        tumor_core = (
            (tumor_distance <= 14)
            & brain_mask
        )

        enhancing_tumor = (
            (tumor_distance <= 8)
            & brain_mask
        )

        # Whole Tumor - Green
        rgba[whole_tumor] = [
            34,
            197,
            94,
            160,
        ]

        # Tumor Core - Yellow
        rgba[tumor_core] = [
            234,
            179,
            8,
            200,
        ]

        # Enhancing Tumor - Red
        rgba[enhancing_tumor] = [
            239,
            68,
            68,
            240,
        ]

    # -----------------------------------------------------
    # Grayscale BMP
    # -----------------------------------------------------

    if not is_mask:

        header = bytearray(
            54 + 1024
        )

        header[0:2] = b"BM"

        file_size = (
            54
            + 1024
            + size * size
        )

        header[2:6] = file_size.to_bytes(
            4,
            "little",
        )

        header[10:14] = (
            54 + 1024
        ).to_bytes(
            4,
            "little",
        )

        header[14:18] = (
            40
        ).to_bytes(
            4,
            "little",
        )

        header[18:22] = size.to_bytes(
            4,
            "little",
        )

        header[22:26] = size.to_bytes(
            4,
            "little",
        )

        header[26:28] = (
            1
        ).to_bytes(
            2,
            "little",
        )

        header[28:30] = (
            8
        ).to_bytes(
            2,
            "little",
        )

        # Grayscale palette
        for i in range(256):

            header[
                54 + i * 4:
                54 + i * 4 + 4
            ] = bytes(
                [i, i, i, 0]
            )

        return (
            bytes(header)
            + np.flipud(img).tobytes()
        )

    # -----------------------------------------------------
    # RGBA BMP
    # -----------------------------------------------------

    header = bytearray(54)

    header[0:2] = b"BM"

    file_size = (
        54
        + size * size * 4
    )

    header[2:6] = file_size.to_bytes(
        4,
        "little",
    )

    header[10:14] = (
        54
    ).to_bytes(
        4,
        "little",
    )

    header[14:18] = (
        40
    ).to_bytes(
        4,
        "little",
    )

    header[18:22] = size.to_bytes(
        4,
        "little",
    )

    header[22:26] = size.to_bytes(
        4,
        "little",
    )

    header[26:28] = (
        1
    ).to_bytes(
        2,
        "little",
    )

    header[28:30] = (
        32
    ).to_bytes(
        2,
        "little",
    )

    flipped = np.flipud(rgba)

    # RGBA -> BGRA
    bgra = np.zeros_like(flipped)

    bgra[:, :, 0] = flipped[:, :, 2]
    bgra[:, :, 1] = flipped[:, :, 1]
    bgra[:, :, 2] = flipped[:, :, 0]
    bgra[:, :, 3] = flipped[:, :, 3]

    return bytes(header) + bgra.tobytes()


# ---------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "FedMed Backend API",
        "version": "0.1.0",
        "description": (
            "Federated Brain Tumor Segmentation API"
        ),
    }


# ---------------------------------------------------------
# Scan endpoints
# ---------------------------------------------------------

@app.get(
    "/scans",
    response_model=list[ScanMetadata],
)
def get_scans():
    """Return available BraTS patient cases."""

    return MOCK_SCANS


@app.get(
    "/scans/{scan_id}/slice/{axis}/{index}"
)
def get_scan_slice(
    scan_id: str,
    axis: str,
    index: int,
):
    """
    Return a synthetic MRI slice.

    TODO:
        Replace with real NIfTI/MONAI extraction.
    """

    img_bytes = generate_synthetic_mri_png(
        slice_idx=index,
        is_mask=False,
    )

    return Response(
        content=img_bytes,
        media_type="image/bmp",
    )


@app.get(
    "/scans/{scan_id}/mask/{index}"
)
def get_scan_mask(
    scan_id: str,
    index: int,
):
    """
    Return a synthetic tumor segmentation mask.

    TODO:
        Replace with real model prediction /
        ground-truth mask extraction.
    """

    mask_bytes = generate_synthetic_mri_png(
        slice_idx=index,
        is_mask=True,
    )

    return Response(
        content=mask_bytes,
        media_type="image/bmp",
    )


# ---------------------------------------------------------
# Network node telemetry
# ---------------------------------------------------------

@app.get(
    "/network/nodes",
    response_model=list[NodeTelemetry],
)
def get_network_nodes():
    """
    Return live telemetry for all hospital nodes.

    Data comes directly from HeartbeatMonitor.
    """

    if grpc_service is None:
        return []

    telemetry = (
        grpc_service
        .heartbeat_monitor
        .get_telemetry_summary()
    )

    return [
        NodeTelemetry(
            id=node["id"],
            name=node["name"],
            status=node["status"],
            current_round=node["current_round"],
            dice=node["dice"],
            upload_ms=node["upload_ms"],
            bytes=node["bytes"],
        )
        for node in telemetry
    ]


# ---------------------------------------------------------
# WebSocket telemetry
# ---------------------------------------------------------

@app.websocket("/ws/telemetry")
async def websocket_telemetry(
    websocket: WebSocket,
):
    """
    Stream live federated learning telemetry.

    The WebSocket sends one telemetry payload every
    2.5 seconds.
    """

    await websocket.accept()

    logger.info(
        "[WebSocket] Client connected "
        "to /ws/telemetry"
    )

    current_round = 1

    try:

        while True:

            # -------------------------------------------------
            # Get live hospital telemetry
            # -------------------------------------------------

            live_nodes: list[NodeTelemetry] = []

            if grpc_service is not None:

                node_data = (
                    grpc_service
                    .heartbeat_monitor
                    .get_telemetry_summary()
                )

                live_nodes = [
                    NodeTelemetry(
                        id=node["id"],
                        name=node["name"],
                        status=node["status"],
                        current_round=node[
                            "current_round"
                        ],
                        dice=node["dice"],
                        upload_ms=node[
                            "upload_ms"
                        ],
                        bytes=node["bytes"],
                    )
                    for node in node_data
                ]

            # -------------------------------------------------
            # Generate global telemetry
            # -------------------------------------------------

            global_metrics = GlobalMetrics(
                loss=round(
                    0.45
                    / (
                        1.0
                        + current_round * 0.15
                    ),
                    4,
                ),
                dice=round(
                    min(
                        0.92,
                        0.68
                        + current_round * 0.035,
                    ),
                    4,
                ),
            )

            # -------------------------------------------------
            # Privacy telemetry
            # -------------------------------------------------

            privacy = PrivacyBudget(
                epsilon=5.0,
                delta=1e-5,
                epsilon_spent=round(
                    min(
                        5.0,
                        0.8
                        + current_round * 0.35,
                    ),
                    2,
                ),
            )

            # -------------------------------------------------
            # Build complete payload
            # -------------------------------------------------

            telemetry_data = TelemetryPayload(
                round=current_round,
                phase=(
                    "aggregating"
                    if current_round % 2 == 0
                    else "training"
                ),
                global_metrics=global_metrics,
                nodes=live_nodes,
                privacy=privacy,
                encrypted=True,
            )

            # -------------------------------------------------
            # Serialize using "global" alias
            # -------------------------------------------------

            payload_json = telemetry_data.model_dump(
                by_alias=True
            )

            await websocket.send_text(
                json.dumps(payload_json)
            )

            logger.debug(
                "[WebSocket] Sent telemetry "
                "for round %d",
                current_round,
            )

            # -------------------------------------------------
            # Next FL round
            # -------------------------------------------------

            current_round = (
                current_round % 10
            ) + 1

            await asyncio.sleep(2.5)

    except WebSocketDisconnect:

        logger.info(
            "[WebSocket] Client disconnected "
            "from /ws/telemetry"
        )

    except Exception as exc:

        logger.exception(
            "[WebSocket] Telemetry stream error: %s",
            exc,
        )

        try:
            await websocket.close()
        except Exception:
            pass
