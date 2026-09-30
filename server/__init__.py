"""server - Central Flower orchestrator, FedMed FedAvg strategy, and HE aggregator.

Owner: M1 (Server & Orchestration Lead)
"""

from .aggregator import aggregate_encrypted, aggregate_plaintext
from .server import start_fedmed_server
from .strategy import FedMedFedAvg

__all__ = [
    "FedMedFedAvg",
    "aggregate_encrypted",
    "aggregate_plaintext",
    "start_fedmed_server",
]
