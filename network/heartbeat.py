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
    """Runtime state and telemetry for one hospital node."""

    node_id: int
    name: str

    # A node is considered disconnected until it sends
    # its first heartbeat.
    status: str = "disconnected"

    last_seen: float = field(default_factory=time.time)

    current_round: int = 0
    dice: float = 0.75
    upload_ms: int = 850
    bytes_transferred: int = 5242880


class HeartbeatMonitor:
    """Monitors live connection states of the hospital silos."""

    def __init__(
        self,
        timeout_threshold_seconds: float = 15.0,
    ) -> None:
        self.timeout_threshold = timeout_threshold_seconds

        self.nodes: dict[int, NodeState] = {
            1: NodeState(
                node_id=1,
                name="Hospital Silo 1 (St. Jude Medical)",
                dice=0.76,
                upload_ms=812,
            ),
            2: NodeState(
                node_id=2,
                name="Hospital Silo 2 (Charité Berlin)",
                dice=0.79,
                upload_ms=920,
            ),
            3: NodeState(
                node_id=3,
                name="Hospital Silo 3 (Mayo Oncology)",
                dice=0.81,
                upload_ms=780,
            ),
        }

    def record_heartbeat(
        self,
        node_id: int,
        round_num: int = 0,
        status: str = "active",
        dice: float | None = None,
        upload_ms: int | None = None,
        bytes_transferred: int | None = None,
    ) -> None:
        """Record a heartbeat and update node telemetry."""

        now = time.time()

        # Register previously unknown nodes.
        if node_id not in self.nodes:
            self.nodes[node_id] = NodeState(
                node_id=node_id,
                name=f"Hospital Node {node_id}",
                status="disconnected",
            )

        node = self.nodes[node_id]

        # Update liveness.
        node.last_seen = now
        node.status = status
        node.current_round = round_num

        # Update optional telemetry.
        if dice is not None:
            node.dice = dice

        if upload_ms is not None:
            node.upload_ms = upload_ms

        if bytes_transferred is not None:
            node.bytes_transferred = bytes_transferred

        logger.info(
            "[Heartbeat] Node %d | status=%s | round=%d",
            node_id,
            node.status,
            node.current_round,
        )

    def check_timeouts(self) -> list[int]:
        """
        Check all nodes for missed heartbeats.

        A node becomes disconnected when it has not sent
        a heartbeat within the configured timeout period.
        """

        now = time.time()
        timed_out: list[int] = []

        for node_id, state in self.nodes.items():
            elapsed = now - state.last_seen

            if (
                elapsed > self.timeout_threshold
                and state.status != "disconnected"
            ):
                logger.warning(
                    "[Heartbeat] Node %d timed out "
                    "(no heartbeat for %.1fs)",
                    node_id,
                    elapsed,
                )

                state.status = "disconnected"
                timed_out.append(node_id)

        return timed_out

    def get_active_nodes_count(self) -> int:
        """Return the number of currently active hospital nodes."""

        self.check_timeouts()

        return sum(
            1
            for node in self.nodes.values()
            if node.status == "active"
        )

    def get_telemetry_summary(self) -> list[dict[str, Any]]:
        """
        Return live telemetry in a format compatible
        with the FastAPI REST and WebSocket APIs.
        """

        self.check_timeouts()

        return [
            {
                "id": node.node_id,
                "name": node.name,
                "status": node.status,
                "current_round": node.current_round,
                "dice": node.dice,
                "upload_ms": node.upload_ms,
                "bytes": node.bytes_transferred,
            }
            for node in self.nodes.values()
        ]
