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


def pack_tensor_to_ciphertext(tensor: np.ndarray, context: Any) -> Any:
    """Flatten a multi-dimensional numpy tensor and encode it into a TenSEAL CKKS ciphertext vector.
    
    Args:
        tensor: Numpy array representing model layer weights or gradients.
        context: TenSEAL evaluation or secret context.
        
    Returns:
        TenSEAL CKKSVector (or serialized mock ciphertext).
    """
    flat = tensor.flatten().tolist()
    if not TENSEAL_AVAILABLE or getattr(context, "is_mock", False):
        # Stub representation: returns flattened data or mock bytes
        return {"shape": tensor.shape, "data": flat[:10], "is_encrypted_mock": True}

    # TODO(M3): For large layers exceeding slot capacity (poly_modulus_degree // 2),
    # implement chunking across multiple CKKS vectors.
    return ts.ckks_vector(context, flat)


def unpack_ciphertext_to_tensor(ciphertext: Any, original_shape: tuple[int, ...]) -> np.ndarray:
    """Decrypt and unpack a TenSEAL CKKS ciphertext back into a multi-dimensional numpy tensor.
    
    Args:
        ciphertext: TenSEAL CKKSVector (requires secret key in context to decrypt).
        original_shape: Shape of original model layer.
        
    Returns:
        Numpy array with shape == original_shape.
    """
    if not TENSEAL_AVAILABLE or isinstance(ciphertext, dict):
        # Stub mock return with original shape
        return np.zeros(original_shape, dtype=np.float32)

    decrypted_flat = ciphertext.decrypt()
    # Trim padding if slot capacity was larger than array
    total_elements = int(np.prod(original_shape))
    trimmed = np.array(decrypted_flat[:total_elements], dtype=np.float32)
    return trimmed.reshape(original_shape)


def encrypt_parameters(parameters: list[np.ndarray], context: Any) -> list[Any]:
    """Encrypt a full list of model layer numpy arrays."""
    # TODO(M3): Add parallel encryption using ThreadPoolExecutor for faster client upload
    logger.info("Encrypting %d model parameter arrays with CKKS context", len(parameters))
    return [pack_tensor_to_ciphertext(p, context) for p in parameters]


def decrypt_parameters(encrypted_params: list[Any], shapes: list[tuple[int, ...]]) -> list[np.ndarray]:
    """Decrypt a list of encrypted parameter arrays given their target shapes."""
    logger.info("Decrypting %d model parameter arrays", len(encrypted_params))
    return [unpack_ciphertext_to_tensor(c, s) for c, s in zip(encrypted_params, shapes)]
