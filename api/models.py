"""api/models.py

Pydantic schemas for FedMed APIs.
Owner: M4
"""

from pydantic import BaseModel, ConfigDict, Field


class GlobalMetrics(BaseModel):

    loss: float = Field(
        ...,
        description="Global training loss",
        json_schema_extra={
            "example": 0.31
        },
    )

    dice: float = Field(
        ...,
        description="Global Dice score",
        json_schema_extra={
            "example": 0.78
        },
    )


class NodeTelemetry(BaseModel):

    id: int = Field(
        ...,
        description="Hospital node silo identifier",
        json_schema_extra={
            "example": 1
        },
    )

    name: str = Field(
        default="Hospital Node",
        description="Hospital node name",
        json_schema_extra={
            "example": "Hospital Silo 1"
        },
    )

    status: str = Field(
        ...,
        description="Node operational state",
        json_schema_extra={
            "example": "active"
        },
    )

    current_round: int = Field(
        default=0,
        description="Current federated learning round",
        json_schema_extra={
            "example": 1
        },
    )

    dice: float = Field(
        ...,
        description="Local validation Dice score",
        json_schema_extra={
            "example": 0.76
        },
    )

    upload_ms: int = Field(
        ...,
        description="Upload latency in milliseconds",
        json_schema_extra={
            "example": 812
        },
    )

    bytes: int = Field(
        ...,
        description="Payload size in bytes",
        json_schema_extra={
            "example": 5242880
        },
    )


class PrivacyBudget(BaseModel):

    epsilon: float = Field(
        ...,
        description="Maximum privacy epsilon",
        json_schema_extra={
            "example": 5.0
        },
    )

    delta: float = Field(
        ...,
        description="Privacy leakage delta",
        json_schema_extra={
            "example": 1e-5
        },
    )

    epsilon_spent: float = Field(
        ...,
        description="Accumulated epsilon spent",
        json_schema_extra={
            "example": 2.3
        },
    )


class TelemetryPayload(BaseModel):

    model_config = ConfigDict(
        populate_by_name=True
    )

    round: int = Field(
        ...,
        description="Current communication round",
        json_schema_extra={
            "example": 4
        },
    )

    phase: str = Field(
        ...,
        description="Current FL lifecycle phase",
        json_schema_extra={
            "example": "aggregating"
        },
    )

    global_metrics: GlobalMetrics = Field(
        ...,
        alias="global",
        description="Global model metrics",
    )

    nodes: list[NodeTelemetry] = Field(
        default_factory=list,
        description="Hospital node telemetry",
    )

    privacy: PrivacyBudget = Field(
        ...,
        description="Current privacy budget",
    )

    encrypted: bool = Field(
        ...,
        description="Whether weights are encrypted",
        json_schema_extra={
            "example": True
        },
    )


class ScanMetadata(BaseModel):

    id: str = Field(
        ...,
        json_schema_extra={
            "example": "BraTS2021_00001"
        },
    )

    name: str = Field(
        ...,
        json_schema_extra={
            "example": "Patient 001 - High-Grade Glioma"
        },
    )

    diagnosis: str = Field(
        default="Glioblastoma Multiforme (WHO Grade IV)",
        description="Clinical tumor diagnosis",
    )

    modalities: list[str] = Field(
        default_factory=lambda: [
            "FLAIR",
            "T1ce",
            "T2",
            "T1",
        ]
    )

    dimensions: list[int] = Field(
        default_factory=lambda: [
            64,
            64,
            64,
        ]
    )

    assigned_hospital: int = Field(
        1,
        description="Hospital silo owning this scan",
    )

    tumor_volume_cm3: float = Field(
        14.8,
        description="Estimated tumor volume",
    )


class HeartbeatPayload(BaseModel):
    node_id: int
    status: str = "active"
    round: int = 1
    dice: float | None = None
    upload_ms: int | None = None


class ControlActionResponse(BaseModel):
    success: bool
    action: str
    message: str
    current_round: int
    encrypted: bool
