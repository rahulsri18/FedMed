"""api/models.py - Pydantic Schemas for FedMed Telemetry and REST APIs.

Owner: M4 (Network & API Lead)
"""


from pydantic import BaseModel, ConfigDict, Field


class GlobalMetrics(BaseModel):
    loss: float = Field(..., description="Global cross-entropy/Dice training loss", json_schema_extra={"example": 0.31})
    dice: float = Field(..., description="Global mean Dice similarity coefficient", json_schema_extra={"example": 0.78})


class NodeTelemetry(BaseModel):
    id: int = Field(..., description="Hospital node silo identifier", json_schema_extra={"example": 1})
    status: str = Field(..., description="Node operational state", json_schema_extra={"example": "active"})
    dice: float = Field(..., description="Local validation Dice score", json_schema_extra={"example": 0.76})
    upload_ms: int = Field(..., description="Upload latency in milliseconds", json_schema_extra={"example": 812})
    bytes: int = Field(..., description="Payload size in bytes", json_schema_extra={"example": 5242880})


class PrivacyBudget(BaseModel):
    epsilon: float = Field(..., description="Max target differential privacy epsilon", json_schema_extra={"example": 5.0})
    delta: float = Field(..., description="Privacy leakage delta", json_schema_extra={"example": 1e-5})
    epsilon_spent: float = Field(..., description="Accumulated epsilon spent across rounds", json_schema_extra={"example": 2.3})


class TelemetryPayload(BaseModel):
    """Exact schema required for FedMed live telemetry streaming over WebSocket."""
    model_config = ConfigDict(populate_by_name=True)

    round: int = Field(..., description="Current communication round", json_schema_extra={"example": 4})
    phase: str = Field(..., description="Current FL lifecycle phase", json_schema_extra={"example": "aggregating"})
    global_metrics: GlobalMetrics = Field(..., alias="global", description="Global model metrics")
    nodes: list[NodeTelemetry] = Field(..., description="Per-hospital silo telemetry")
    privacy: PrivacyBudget = Field(..., description="Current privacy budget status")
    encrypted: bool = Field(..., description="Whether weights are homomorphically encrypted", json_schema_extra={"example": True})


class ScanMetadata(BaseModel):
    id: str = Field(..., json_schema_extra={"example": "BraTS2021_00001"})
    name: str = Field(..., json_schema_extra={"example": "Patient 001 - High-Grade Glioma"})
    modalities: list[str] = Field(default_factory=lambda: ["T1", "T1ce", "T2", "FLAIR"])
    dimensions: list[int] = Field(default_factory=lambda: [64, 64, 64])
    assigned_hospital: int = Field(1, description="Hospital silo owning this scan")
