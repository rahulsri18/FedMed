"""server/server.py - Central Flower Federated Orchestration Server.

Owner: M1 (Server & Orchestration Lead)
Usage:
    python -m server.server --port 8080 --rounds 5 --encrypted
"""

import argparse
import logging

from .strategy import FedMedFedAvg

# Configure structured lifecycle logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("FedMed.Server")

try:
    import flwr as fl
    FLWR_AVAILABLE = True
except ImportError:
    fl = None
    FLWR_AVAILABLE = False


def start_fedmed_server(
    server_address: str = "0.0.0.0:8080",
    num_rounds: int = 5,
    encrypted: bool = True,
    min_clients: int = 3,
    certificates: bytes | None = None,
) -> None:
    """Launch the FedMed Flower Federated Server."""
    logger.info("=" * 65)
    logger.info("   Starting FedMed Cross-Silo Federated Learning Server")
    logger.info("=" * 65)
    logger.info("Address:            %s", server_address)
    logger.info("Target Rounds:      %d", num_rounds)
    logger.info("Homomorphic Enc:    %s", "ENABLED (CKKS Scheme)" if encrypted else "DISABLED (Plaintext)")
    logger.info("Min Active Nodes:   %d", min_clients)
    logger.info("Flower Framework:   %s", "Loaded" if FLWR_AVAILABLE else "Stub / Simulation Mode")
    logger.info("=" * 65)

    strategy = FedMedFedAvg(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=min_clients,
        min_evaluate_clients=min_clients,
        min_available_clients=min_clients,
        encrypted=encrypted,
    )

    if FLWR_AVAILABLE:
        # TODO(M1): Add SSL/TLS certificates support for native gRPC mTLS
        # flwr.server.ServerConfig(num_rounds=num_rounds)
        config = fl.server.ServerConfig(num_rounds=num_rounds)
        logger.info("[FedMed-Server] Listening for 3 hospital nodes on %s...", server_address)
        try:
            fl.server.start_server(
                server_address=server_address,
                config=config,
                strategy=strategy,
            )
        except Exception as e:
            logger.error("[FedMed-Server] Server encountered error: %s", e)
            raise
    else:
        logger.info("[FedMed-Server] Flower not detected in environment. Running standalone simulation stub.")
        for r in range(1, num_rounds + 1):
            logger.info("[FedMed-Server] Simulated Round %d / %d starting...", r, num_rounds)
            strategy.aggregate_fit(r, [], [])
            strategy.aggregate_evaluate(r, [], [])
        logger.info("[FedMed-Server] Simulated federated training finished successfully.")


def main():
    parser = argparse.ArgumentParser(description="FedMed Flower Central Server")
    parser.add_argument("--port", type=int, default=8080, help="Server gRPC port (default: 8080)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    parser.add_argument("--rounds", type=int, default=5, help="Number of FL rounds (default: 5)")
    parser.add_argument("--encrypted", action="store_true", default=True, help="Enable homomorphic encryption (default: True)")
    parser.add_argument("--plaintext", action="store_false", dest="encrypted", help="Disable encryption for plaintext baseline")
    parser.add_argument("--min-clients", type=int, default=3, help="Minimum clients required per round")

    args = parser.parse_args()
    address = f"{args.host}:{args.port}"
    start_fedmed_server(
        server_address=address,
        num_rounds=args.rounds,
        encrypted=args.encrypted,
        min_clients=args.min_clients,
    )


if __name__ == "__main__":
    main()
