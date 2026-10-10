"""privacy/encryption.py - Tensor Pack / Unpack and Homomorphic Encryption Helpers.

Owner: M3 (Privacy & Security Lead)
"""

import logging
from typing import Any

import numpy as np

logger = logging.getLogger("FedMed.Privacy.Encryption")

try:
    import tenseal as ts
    TENSEAL_AVAILABLE = True
except ImportError:
    ts = None
    TENSEAL_AVAILABLE = False


# Scaling factor applied before encryption to preserve precision in CKKS fixed-point arithmetic
PRESCALE_FACTOR = 1000.0
DEFAULT_CHUNK_SIZE = 4096  # Matches poly_modulus_degree // 2 for degree 8192


class MockCKKSVector:
    """Mock ciphertext vector supporting homomorphic addition and scalar multiplication."""
    def __init__(self, data: list[float], scale: float = PRESCALE_FACTOR, original_len: int | None = None):
        self.data = np.array(data, dtype=np.float64)
        self.scale = scale
        self.original_len = original_len if original_len is not None else len(data)
        self.is_mock_ciphertext = True

    def __add__(self, other: Any) -> "MockCKKSVector":
        if isinstance(other, MockCKKSVector):
            max_len = max(len(self.data), len(other.data))
            d1 = np.pad(self.data, (0, max_len - len(self.data)))
            d2 = np.pad(other.data, (0, max_len - len(other.data)))
            return MockCKKSVector((d1 + d2).tolist(), self.scale, max(self.original_len, other.original_len))
        return self

    def __radd__(self, other: Any) -> "MockCKKSVector":
        return self if other == 0 else self.__add__(other)

    def __mul__(self, scalar: float) -> "MockCKKSVector":
        return MockCKKSVector((self.data * float(scalar)).tolist(), self.scale, self.original_len)

    def __rmul__(self, scalar: float) -> "MockCKKSVector":
        return self.__mul__(scalar)

    def decrypt(self) -> list[float]:
        return self.data.tolist()


def pack_tensor_to_ciphertext(
    tensor: np.ndarray,
    context: Any,
    scale_factor: float = PRESCALE_FACTOR,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> list[Any]:
    """Flatten a multi-dimensional numpy tensor, apply pre-scaling, and encode into CKKS ciphertext chunks.
    
    Args:
        tensor: Numpy array representing model layer weights or gradients.
        context: TenSEAL evaluation or secret context.
        scale_factor: Pre-scaling multiplier to safeguard precision.
        chunk_size: Maximum slots per CKKS vector (poly_modulus_degree // 2).
        
    Returns:
        List of TenSEAL CKKSVector objects (or MockCKKSVector instances).
    """
    scaled_flat = (tensor.flatten() * scale_factor).astype(np.float64).tolist()
    total_len = len(scaled_flat)
    
    # Split into chunks fitting poly_modulus_degree slot capacity
    chunks = []
    for i in range(0, total_len, chunk_size):
        chunk_slice = scaled_flat[i : i + chunk_size]
        if TENSEAL_AVAILABLE and not getattr(context, "is_mock", False):
            c_vec = ts.ckks_vector(context, chunk_slice)
        else:
            c_vec = MockCKKSVector(chunk_slice, scale=scale_factor, original_len=len(chunk_slice))
        chunks.append(c_vec)

    return chunks


def unpack_ciphertext_to_tensor(
    ciphertext_chunks: list[Any] | Any,
    original_shape: tuple[int, ...],
    scale_factor: float = PRESCALE_FACTOR,
) -> np.ndarray:
    """Decrypt and unpack CKKS ciphertext chunk(s) back into a multi-dimensional numpy tensor.
    
    Args:
        ciphertext_chunks: Single CKKS vector or list of chunked CKKS vectors.
        original_shape: Shape of original model layer.
        scale_factor: Pre-scaling divisor to recover original magnitude.
        
    Returns:
        Numpy array with shape == original_shape.
    """
    if not isinstance(ciphertext_chunks, list):
        ciphertext_chunks = [ciphertext_chunks]

    decrypted_values: list[float] = []
    for chunk in ciphertext_chunks:
        if hasattr(chunk, "decrypt"):
            decrypted_values.extend(chunk.decrypt())
        elif isinstance(chunk, dict) and "data" in chunk:
            decrypted_values.extend(chunk.get("data", []))
        else:
            decrypted_values.extend(np.zeros(DEFAULT_CHUNK_SIZE, dtype=np.float32).tolist())

    total_elements = int(np.prod(original_shape))
    if len(decrypted_values) < total_elements:
        decrypted_values.extend([0.0] * (total_elements - len(decrypted_values)))

    trimmed = np.array(decrypted_values[:total_elements], dtype=np.float64) / scale_factor
    return trimmed.astype(np.float32).reshape(original_shape)


def encrypt_parameters(
    parameters: list[np.ndarray],
    context: Any,
    scale_factor: float = PRESCALE_FACTOR,
) -> list[list[Any]]:
    """Encrypt a full list of model layer numpy arrays into chunked CKKS vectors."""
    logger.info("Encrypting %d model parameter arrays with CKKS context (pre-scale=%.1f)", len(parameters), scale_factor)
    return [pack_tensor_to_ciphertext(p, context, scale_factor=scale_factor) for p in parameters]


def decrypt_parameters(
    encrypted_params: list[list[Any]],
    shapes: list[tuple[int, ...]],
    scale_factor: float = PRESCALE_FACTOR,
) -> list[np.ndarray]:
    """Decrypt a list of encrypted parameter arrays given their target shapes."""
    logger.info("Decrypting %d model parameter arrays", len(encrypted_params))
    return [unpack_ciphertext_to_tensor(c, s, scale_factor=scale_factor) for c, s in zip(encrypted_params, shapes)]

