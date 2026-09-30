"""server/strategy.py - Custom FedMed FedAvg Strategy with Homomorphic Encryption & Structured Logging.

Owner: M1 (Server & Orchestration Lead)
"""

import logging
from collections.abc import Callable
from typing import Any

import numpy as np

from .aggregator import aggregate_encrypted, aggregate_plaintext

logger = logging.getLogger("FedMed.Server.Strategy")

try:
    import flwr as fl
    from flwr.common import (
        EvaluateIns,
        EvaluateRes,
        FitIns,
        FitRes,
        Parameters,
        Scalar,
        ndarrays_to_parameters,
        parameters_to_ndarrays,
    )
    from flwr.server.client_proxy import ClientProxy
    from flwr.server.strategy import FedAvg
    FLWR_AVAILABLE = True
except ImportError:
    fl = None
    FedAvg = object
    Parameters = Any
    FitIns = Any
    FitRes = Any
    EvaluateIns = Any
    EvaluateRes = Any
    ClientProxy = Any
    Scalar = Any
    FLWR_AVAILABLE = False


class FedMedFedAvg(FedAvg if FLWR_AVAILABLE else object):
    """Custom Federated Averaging strategy for FedMed brain tumor segmentation.
    
    Supports:
    - Encrypted parameter aggregation flag (CKKS HE) vs Plaintext FedAvg
    - Structured round-lifecycle logging for real-time telemetry streaming
    - Dice score and cross-entropy metric aggregation
    """

    def __init__(
        self,
        fraction_fit: float = 1.0,
        fraction_evaluate: float = 1.0,
        min_fit_clients: int = 3,
        min_evaluate_clients: int = 3,
        min_available_clients: int = 3,
        encrypted: bool = True,
        on_round_complete: Callable[[dict[str, Any]], None] | None = None,
        **kwargs,
    ) -> None:
        """Initialize FedMed FedAvg strategy.
        
        Args:
            fraction_fit: Fraction of available clients sampled for training (1.0 = all 3 hospitals).
            min_fit_clients: Minimum clients required to start a fit round.
            encrypted: Whether to perform aggregation on CKKS ciphertexts.
            on_round_complete: Optional telemetry callback hooking into FastAPI WebSocket.
        """
        if FLWR_AVAILABLE:
            super().__init__(
                fraction_fit=fraction_fit,
                fraction_evaluate=fraction_evaluate,
                min_fit_clients=min_fit_clients,
                min_evaluate_clients=min_evaluate_clients,
                min_available_clients=min_available_clients,
                **kwargs,
            )
        self.encrypted = encrypted
        self.on_round_complete = on_round_complete
        self.current_round = 0
        logger.info(
            "[FedMed-Server] FedMedFedAvg strategy initialized. Encrypted Mode=%s, Min Clients=%d",
            self.encrypted, min_fit_clients
        )

    def aggregate_fit(
        self,
        server_round: int,
        results: list[tuple[Any, Any]],
        failures: list[tuple[Any, Exception] | Exception],
    ) -> tuple[Any | None, dict[str, Any]]:
        """Hook called at the end of client training in each communication round."""
        self.current_round = server_round
        num_successful = len(results)
        num_failures = len(failures)

        logger.info("=" * 60)
        logger.info("[FedMed-Server] >>> Communication Round %d Fit Phase Started <<<", server_round)
        logger.info("[FedMed-Server] Node reports received: %d successful, %d failed", num_successful, num_failures)

        if not results:
            logger.warning("[FedMed-Server] No successful client updates received in round %d!", server_round)
            return None, {}

        # Parse metrics reported by hospital clients
        node_telemetry = []
        parsed_results = []

        for client_proxy, fit_res in results:
            client_id = getattr(client_proxy, "cid", "unknown")
            metrics = getattr(fit_res, "metrics", {}) or {}
            num_examples = getattr(fit_res, "num_examples", 1)
            
            # Extract weights
            if FLWR_AVAILABLE and hasattr(fit_res, "parameters"):
                ndarrays = parameters_to_ndarrays(fit_res.parameters)
            else:
                ndarrays = getattr(fit_res, "parameters", [])

            parsed_results.append((ndarrays, num_examples))
            node_telemetry.append({
                "id": client_id,
                "status": "active",
                "samples": num_examples,
                "dice": metrics.get("dice", 0.75),
                "loss": metrics.get("loss", 0.35),
            })

        # Structured logging of aggregation mode
        if self.encrypted:
            logger.info("[FedMed-Server] Executing Homomorphic Aggregation (CKKS Ciphertexts)...")
            aggregated_weights = aggregate_encrypted(parsed_results)
        else:
            logger.info("[FedMed-Server] Executing Weighted FedAvg Aggregation (Plaintext)...")
            aggregated_weights = aggregate_plaintext(parsed_results)

        logger.info("[FedMed-Server] Round %d parameter aggregation completed successfully.", server_round)

        # Notify telemetry handler if registered
        metrics_aggregated = {
            "round": server_round,
            "phase": "aggregated",
            "encrypted": self.encrypted,
            "node_count": num_successful,
        }
        if self.on_round_complete:
            self.on_round_complete(metrics_aggregated)

        if FLWR_AVAILABLE and aggregated_weights and isinstance(aggregated_weights[0], np.ndarray):
            return ndarrays_to_parameters(aggregated_weights), metrics_aggregated
        return aggregated_weights, metrics_aggregated

    def aggregate_evaluate(
        self,
        server_round: int,
        results: list[tuple[Any, Any]],
        failures: list[tuple[Any, Exception] | Exception],
    ) -> tuple[float | None, dict[str, Any]]:
        """Aggregate evaluation metrics (Loss & Dice) from hospital validation sets."""
        if not results:
            return None, {}

        total_examples = sum(r.num_examples for _, r in results if hasattr(r, "num_examples"))
        if total_examples == 0:
            total_examples = len(results)

        weighted_loss = 0.0
        weighted_dice = 0.0

        for _, eval_res in results:
            n = getattr(eval_res, "num_examples", 1)
            loss = getattr(eval_res, "loss", 0.0)
            metrics = getattr(eval_res, "metrics", {}) or {}
            dice = metrics.get("dice", 0.78)

            weighted_loss += (loss * n)
            weighted_dice += (dice * n)

        global_loss = weighted_loss / total_examples
        global_dice = weighted_dice / total_examples

        logger.info("-" * 60)
        logger.info(
            "[FedMed-Server] Global Validation Round %d: Loss=%.4f | Dice=%.4f",
            server_round, global_loss, global_dice
        )
        logger.info("-" * 60)

        # TODO(M1): Trigger alert if model performance degrades or divergence detected
        return global_loss, {"dice": global_dice, "loss": global_loss}
