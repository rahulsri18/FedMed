"""network/interceptors.py - gRPC Interceptors for Telemetry & Authentication.

Owner: M4 (Network & API Lead)
"""

import logging
import time
from collections.abc import Callable

logger = logging.getLogger("FedMed.Network.Interceptors")


class TelemetryServerInterceptor:
    """Server-side interceptor measuring RPC invocation latency and message sizes."""

    def __init__(self, on_call_callback: Callable | None = None):
        self.on_call_callback = on_call_callback

    def intercept_service(self, continuation, handler_call_details):
        # TODO(M4): Hook into OpenTelemetry / Prometheus metrics collector
        time.time()
        logger.debug("[gRPC Interceptor] Received RPC method: %s", handler_call_details.method)
        return continuation(handler_call_details)
