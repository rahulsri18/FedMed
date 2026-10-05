"""
network/grpc_client.py

FedMed Hospital Node gRPC Client
Owner: M4

Used by hospital silos to:
- Perform health checks
- Send heartbeats
- Communicate securely using mTLS
"""

import logging
import time
from pathlib import Path

import grpc

from .protos import auxiliary_pb2
from .protos import auxiliary_pb2_grpc


logger = logging.getLogger("FedMed.Network.GRPCClient")


class HospitalGrpcClient:
    """Secure gRPC client for a hospital node."""

    def __init__(
        self,
        node_id: int,
        server_address: str = "localhost:50051",
    ):
        self.node_id = node_id
        self.server_address = server_address

        cert_dir = Path(__file__).parent / "certs"

        # Load CA certificate
        with open(cert_dir / "ca.crt", "rb") as f:
            ca_certificate = f.read()

        # Load hospital certificate
        with open(
            cert_dir / f"client-node-{node_id}.crt",
            "rb",
        ) as f:
            client_certificate = f.read()

        # Load hospital private key
        with open(
            cert_dir / f"client-node-{node_id}.key",
            "rb",
        ) as f:
            client_private_key = f.read()

        # Configure mTLS credentials
        credentials = grpc.ssl_channel_credentials(
            root_certificates=ca_certificate,
            private_key=client_private_key,
            certificate_chain=client_certificate,
        )

        self.channel = grpc.secure_channel(
            server_address,
            credentials,
        )

        self.stub = auxiliary_pb2_grpc.AuxiliaryServiceStub(
            self.channel
        )

    def health_check(self):
        """Check whether the FedMed server is healthy."""

        request = auxiliary_pb2.HealthCheckRequest(
            node_id=self.node_id,
            node_name=f"Hospital Node {self.node_id}",
            timestamp=int(time.time()),
        )

        response = self.stub.HealthCheck(request)

        logger.info(
            "Health check response: %s",
            response.message,
        )

        return response

    def send_heartbeat(
        self,
        current_round: int = 0,
        memory_usage_mb: float = 0.0,
        gpu_utilization: float = 0.0,
    ):
        """Send one heartbeat to the FedMed server."""

        request = auxiliary_pb2.HeartbeatPing(
            node_id=self.node_id,
            current_round=current_round,
            timestamp=int(time.time()),
            memory_usage_mb=memory_usage_mb,
            gpu_utilization=gpu_utilization,
        )

        response = self.stub.SendHeartbeat(request)

        logger.info(
            "Heartbeat acknowledged=%s | round=%s | action=%s",
            response.acknowledged,
            response.current_server_round,
            response.next_action,
        )

        return response

    def heartbeat_loop(
        self,
        current_round: int = 1,
        interval_seconds: int = 5,
    ):
        """Continuously send heartbeats to the FedMed server."""

        logger.info(
            "Starting heartbeat loop for Hospital Node %s",
            self.node_id,
        )

        try:
            while True:
                response = self.send_heartbeat(
                    current_round=current_round,
                    memory_usage_mb=512,
                    gpu_utilization=35,
                )

                print(
                    f"[Node {self.node_id}] "
                    f"Heartbeat acknowledged={response.acknowledged} "
                    f"| round={response.current_server_round} "
                    f"| action={response.next_action}"
                )

                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info(
                "Heartbeat loop stopped for Node %s",
                self.node_id,
            )

    def close(self):
        """Close the gRPC channel."""

        self.channel.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    client = HospitalGrpcClient(node_id=1)

    try:
        print(f"\n--- Hospital Node {client.node_id} ---")
        print("\n--- Health Check ---")

        health = client.health_check()

        print("Status:", health.status)
        print("Version:", health.version)
        print("Message:", health.message)

        print("\n--- Continuous Heartbeat ---")

        client.heartbeat_loop(
            current_round=1,
            interval_seconds=5,
        )

    finally:
        client.close()