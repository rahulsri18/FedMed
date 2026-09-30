"""client - Hospital node client package.

Owner: M1 (Orchestration Lead), M2 (Models & Data), M3 (Privacy & Security)
"""

from .client import FedMedClient, start_hospital_client

__all__ = ["FedMedClient", "start_hospital_client"]
