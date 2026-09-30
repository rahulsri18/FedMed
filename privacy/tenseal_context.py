"""privacy/tenseal_context.py - TenSEAL CKKS Homomorphic Encryption Context Setup.

Owner: M3 (Privacy & Security Lead)

TRUST MODEL:
In FedMed's cross-silo architecture, the 3 hospital client nodes form a secure medical consortium.
The clients share the CKKS secret key (or generate it via distributed key generation / threshold HE).
The central Flower orchestration server is treated as honest-but-curious: it is provisioned ONLY
with the public evaluation context (containing Galois keys for slot rotation and relinearization keys
for multiplication/scale management). The central server performs homomorphic addition and scalar
weighting on encrypted model tensors and has zero ability to decrypt individual hospital updates.
"""

import logging
from collections.abc import Sequence
from typing import Any

logger = logging.getLogger("FedMed.Privacy.TenSEAL")

try:
    import tenseal as ts
    TENSEAL_AVAILABLE = True
except ImportError:
    ts = None
    TENSEAL_AVAILABLE = False


def create_ckks_context(
    poly_modulus_degree: int = 8192,
    coeff_mod_bit_sizes: Sequence[int] = (60, 40, 40, 60),
    global_scale: float = 2**40,
) -> Any:
    """Creates a TenSEAL CKKS encryption context with public and secret keys.
    
    Args:
        poly_modulus_degree: Polynomial modulus degree (e.g., 8192, 16384).
                             Higher provides stronger security and deeper circuit depth.
        coeff_mod_bit_sizes: Coefficient modulus bit sizes (primes matching RNS representation).
        global_scale: Default scale factor for fixed-point floating point numbers.
        
    Returns:
        TenSEALContext object (or mock context object if tenseal is not installed).
    """
    if not TENSEAL_AVAILABLE:
        logger.warning("TenSEAL is not installed in the local environment. Returning mock context.")
        return MockTenSEALContext(poly_modulus_degree, coeff_mod_bit_sizes, global_scale)

    context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=poly_modulus_degree,
        coeff_mod_bit_sizes=list(coeff_mod_bit_sizes),
    )
    context.global_scale = global_scale
    context.generate_galois_keys()
    context.generate_relin_keys()
    return context


def serialize_public_context(context: Any) -> bytes:
    """Serializes the public/evaluation context (WITHOUT the secret key) for the central server."""
    if not TENSEAL_AVAILABLE or isinstance(context, MockTenSEALContext):
        return b"MOCK_PUBLIC_TENSEAL_CONTEXT"
    
    # Save context without secret key
    return context.serialize(save_secret_key=False)


def serialize_secret_context(context: Any) -> bytes:
    """Serializes the complete context (WITH the secret key) for hospital clients."""
    if not TENSEAL_AVAILABLE or isinstance(context, MockTenSEALContext):
        return b"MOCK_SECRET_TENSEAL_CONTEXT"

    return context.serialize(save_secret_key=True)


def deserialize_context(context_bytes: bytes) -> Any:
    """Loads a TenSEAL context from raw bytes."""
    if not TENSEAL_AVAILABLE or context_bytes.startswith(b"MOCK"):
        return MockTenSEALContext()
    return ts.context_from(context_bytes)


class MockTenSEALContext:
    """Mock context allowing local unit tests, CI, and stub clients to run without TenSEAL C++ binaries."""
    def __init__(self, poly_degree=8192, bits=(60, 40, 40, 60), scale=2**40):
        self.poly_modulus_degree = poly_degree
        self.coeff_mod_bit_sizes = bits
        self.global_scale = scale
        self.is_mock = True

    def serialize(self, save_secret_key=False):
        return b"MOCK_PUBLIC_TENSEAL_CONTEXT" if not save_secret_key else b"MOCK_SECRET_TENSEAL_CONTEXT"
