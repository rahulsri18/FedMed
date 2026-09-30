"""network/heartbeat.py - Server-Side Hospital Node Heartbeat and Liveness Tracker.

Owner: M4 (Network & API Lead)
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("FedMed.Network.Heartbeat")


@dataclass
class NodeState:
    node_id: int
    name: str
    status: str = "active"  # "active", "busy", "disconnected", "error"
    last_seen: float = field(default_factory=time.time)
    current_round: int = 0
    dice: float = 0.75
    upload_ms: int = 850
    bytes_transferred: int = 5242880


class HeartbeatMonitor:
    """Monitors live connection states of the 3 hospital silos."""

    def __init__(self, timeout_threshold_seconds: float = 15.0) -> None:
        self.timeout_threshold = timeout_threshold_seconds
        self.nodes: dict[int, NodeState] = {
            1: NodeState(node_id=1, name="Hospital Silo 1 (St. Jude Medical)", dice=0.76, upload_ms=812),
            2: NodeState(node_id=2, name="Hospital Silo 2 (Charité Berlin)", dice=0.79, upload_ms=920),
            3: NodeState(node_id=3, name="Hospital Silo 3 (Mayo Oncology)", dice=0.81, upload_ms=780),
        }

    def record_heartbeat(
        self,
        node_id: int,
        round_num: int = 0,
        status: str = "active",
        dice: float | None = None,
        upload_ms: int | None = None,
    ) -> None:
        """Update node heartbeat timestamp and telemetry."""
        now = time.time()
        if node_id not in self.nodes:
            self.nodes[node_id] = NodeState(node_id=node_id, name=f"Hospital Node {node_id}")

        node = self.nodes[node_id]
        node.last_seen = now
        node.status = status
        node.current_round = round_num
        if dice is not None:
            node.dice = dice
        if upload_ms is not None:
            node.upload_ms = upload_ms

        logger.debug("[Heartbeat] Node %d heartbeat recorded at %.2f", node_id, now)

    def check_timeouts(self) -> list[int]:
        """Check all nodes for timeout and update status to 'disconnected'."""
        now = time.time()
        timed_out: list[int] = []
        for node_id, state in self.nodes.items():
            if (now - state.last_seen > self.timeout_threshold) and state.status != "disconnected":
                logger.warning("[Heartbeat] Node %d timed out (no ping for %.1fs)!",
                               node_id, now - state.last_seen)
                state.status = "disconnected"
                timed_out.append(node_id)
        return timed_out

    def get_active_nodes_count(self) -> int:
        """Return count of healthy active nodes."""
        self.check_timeouts()
        return sum(1 for n in self.nodes.values() if n.status == "active")

    def get_telemetry_summary(self) -> list[dict[str, Any]]:
        """Return telemetry format compatible with dashboard and FastAPI WebSocket."""
        self.check_timeouts()
        return [
            {
                "id": node.node_id,
                "name": node.name,
                "status": node.status,
                "dice": node.dice,
                "upload_ms": node.upload_ms,
                "bytes": node.bytes_transferred,
            }
            for node in self.nodes.values()
        ]
