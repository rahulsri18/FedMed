"""server/server.py - Central Flower Federated Orchestration Server.

Owner: M1 (Server & Orchestration Lead)
Usage:
    python -m server.server --port 8080 --rounds 5 --encrypted
"""

import argparse
import json
import logging
import urllib.request
from pathlib import Path

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


def post_telemetry_event(api_url: str, payload: dict) -> None:
    """Send round completion telemetry payload to FastAPI service."""
    try:
        url = f"{api_url.rstrip('/')}/api/telemetry/round"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            logger.debug("[FedMed-Server] Telemetry webhook delivered (%d)", resp.status)
    except Exception as e:  # noqa: BLE001
        logger.debug("[FedMed-Server] Telemetry webhook skipped: %s", e)


def start_fedmed_server(
    server_address: str = "0.0.0.0:8080",
    num_rounds: int = 5,
    encrypted: bool = True,
    min_clients: int = 3,
    min_quorum: int = 2,
    use_tls: bool = False,
    cert_dir: str = "network/certs",
    api_url: str | None = "http://127.0.0.1:8000",
) -> None:
    """Launch the FedMed Flower Federated Server."""
    logger.info("=" * 65)
    logger.info("   Starting FedMed Cross-Silo Federated Learning Server")
    logger.info("=" * 65)
    logger.info("Address:            %s", server_address)
    logger.info("Target Rounds:      %d", num_rounds)
    logger.info("Homomorphic Enc:    %s", "ENABLED (CKKS Scheme)" if encrypted else "DISABLED (Plaintext)")
    logger.info("Min Active Nodes:   %d", min_clients)
    logger.info("Min Quorum:         %d", min_quorum)
    logger.info("TLS / mTLS:         %s", "ENABLED" if use_tls else "DISABLED")
    logger.info("Flower Framework:   %s", "Loaded" if FLWR_AVAILABLE else "Stub / Simulation Mode")
    logger.info("=" * 65)

    def on_round_complete_handler(metrics: dict) -> None:
        if api_url:
            post_telemetry_event(api_url, metrics)

    strategy = FedMedFedAvg(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=min_clients,
        min_evaluate_clients=min_quorum,
        min_available_clients=min_quorum,
        min_quorum_clients=min_quorum,
        encrypted=encrypted,
        on_round_complete=on_round_complete_handler,
    )

    certificates = None
    if use_tls:
        cert_path = Path(cert_dir)
        ca_file = cert_path / "ca.crt"
        srv_crt = cert_path / "server.crt"
        srv_key = cert_path / "server.key"
        if ca_file.exists() and srv_crt.exists() and srv_key.exists():
            logger.info("[FedMed-Server] Loading mTLS certificates from %s", cert_path)
            certificates = (
                ca_file.read_bytes(),
                srv_crt.read_bytes(),
                srv_key.read_bytes(),
            )
        else:
            logger.warning("[FedMed-Server] Certificates not found in %s. Run generate_certs.py first.", cert_path)

    if FLWR_AVAILABLE:
        config = fl.server.ServerConfig(num_rounds=num_rounds)
        logger.info("[FedMed-Server] Listening for 3 hospital nodes on %s...", server_address)
        try:
            fl.server.start_server(
                server_address=server_address,
                config=config,
                strategy=strategy,
                certificates=certificates,
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
    parser.add_argument("--min-quorum", type=int, default=2, help="Quorum threshold to survive dropouts")
    parser.add_argument("--tls", action="store_true", default=False, help="Enable mTLS transport security")
    parser.add_argument("--cert-dir", type=str, default="network/certs", help="Path to mTLS certificates")
    parser.add_argument("--api-url", type=str, default="http://127.0.0.1:8000", help="FastAPI webhook URL")

    args = parser.parse_args()
    address = f"{args.host}:{args.port}"
    start_fedmed_server(
        server_address=address,
        num_rounds=args.rounds,
        encrypted=args.encrypted,
        min_clients=args.min_clients,
        min_quorum=args.min_quorum,
        use_tls=args.tls,
        cert_dir=args.cert_dir,
        api_url=args.api_url,
    )



if __name__ == "__main__":
    main()
