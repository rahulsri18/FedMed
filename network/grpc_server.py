"""
network/grpc_server.py

FedMed Auxiliary gRPC Server
Owner: M4

Handles:
- Hospital health checks
- Hospital heartbeats
- CKKS evaluation key distribution
- mTLS communication
- Node timeout monitoring
"""

import logging
import threading
import time
from concurrent import futures
from pathlib import Path

import grpc

from .heartbeat import HeartbeatMonitor
from .protos import auxiliary_pb2, auxiliary_pb2_grpc

logger = logging.getLogger("FedMed.Network.GRPC")


class AuxiliaryService(
    auxiliary_pb2_grpc.AuxiliaryServiceServicer
):
    """Implementation of the FedMed auxiliary gRPC service."""

    def __init__(self):
        self.heartbeat_monitor = HeartbeatMonitor()

    def HealthCheck(self, request, context):
        """Return the current health status of a hospital node."""

        logger.info(
            "Health check from node %s (%s)",
            request.node_id,
            request.node_name,
        )

        return auxiliary_pb2.HealthCheckResponse(
            status=auxiliary_pb2.HealthCheckResponse.HEALTHY,
            version="FedMed-1.0",
            server_time=int(time.time()),
            message="FedMed server is healthy",
        )

    def SendHeartbeat(self, request, context):
        """Record heartbeat from a hospital node."""

        logger.info(
            "Heartbeat received from node %s | round=%s",
            request.node_id,
            request.current_round,
        )

        self.heartbeat_monitor.record_heartbeat(
            node_id=request.node_id,
            round_num=request.current_round,
            status="active",
        )

        return auxiliary_pb2.HeartbeatPong(
            acknowledged=True,
            server_time=int(time.time()),
            current_server_round=request.current_round,
            next_action="WAIT_FOR_FIT",
        )

    def DistributeEvaluationKey(self, request, context):
        """Receive and acknowledge a CKKS evaluation key."""

        logger.info(
            "Evaluation key received from node %s | type=%s",
            request.node_id,
            request.key_type,
        )

        return auxiliary_pb2.KeyDistributionResponse(
            acknowledged=True,
            fingerprint="pending",
            message="Evaluation key received",
        )


def create_server(
    host: str = "0.0.0.0",
    port: int = 50051,
):
    """Create and configure the secure gRPC server."""

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

    service = AuxiliaryService()

    auxiliary_pb2_grpc.add_AuxiliaryServiceServicer_to_server(
        service,
        server,
    )

    cert_dir = Path(__file__).parent / "certs"

    # Load server private key
    with open(cert_dir / "server.key", "rb") as f:
        private_key = f.read()

    # Load server certificate
    with open(cert_dir / "server.crt", "rb") as f:
        certificate_chain = f.read()

    # Load trusted CA certificate
    with open(cert_dir / "ca.crt", "rb") as f:
        root_certificates = f.read()

    server_credentials = grpc.ssl_server_credentials(
        [
            (
                private_key,
                certificate_chain,
            )
        ],
        root_certificates=root_certificates,
        require_client_auth=True,
    )

    bound_port = server.add_secure_port(
        f"{host}:{port}",
        server_credentials,
    )

    if bound_port == 0:
        raise RuntimeError(
            f"Failed to bind secure gRPC server to {host}:{port}"
        )

    logger.info(
        "gRPC secure server configured on %s:%s",
        host,
        port,
    )

    return server, service


def monitor_node_timeouts(
    service: AuxiliaryService,
    stop_event: threading.Event,
    check_interval_seconds: int = 5,
):
    """
    Continuously check hospital nodes for missed heartbeats.
    """

    logger.info(
        "Heartbeat timeout monitor started "
        "(interval=%ss, timeout=%ss)",
        check_interval_seconds,
        service.heartbeat_monitor.timeout_threshold,
    )

    while not stop_event.is_set():

        try:
            timed_out = (
                service.heartbeat_monitor.check_timeouts()
            )

            for node_id in timed_out:
                logger.warning(
                    "[Fault Tolerance] "
                    "Hospital Node %s is DISCONNECTED",
                    node_id,
                )

        except Exception:
            logger.exception(
                "Error in heartbeat timeout monitor"
            )

        stop_event.wait(check_interval_seconds)


def serve():
    """Start the FedMed auxiliary gRPC server."""

    server, service = create_server()

    stop_event = threading.Event()

    timeout_thread = threading.Thread(
        target=monitor_node_timeouts,
        args=(service, stop_event),
        daemon=True,
    )

    timeout_thread.start()

    server.start()

    logger.info(
        "FedMed Auxiliary gRPC server started on port 50051"
    )

    try:
        server.wait_for_termination()

    except KeyboardInterrupt:
        logger.info(
            "Stopping FedMed Auxiliary gRPC server..."
        )

    finally:
        stop_event.set()
        server.stop(grace=5)


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    serve()