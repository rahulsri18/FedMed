"""privacy - TenSEAL CKKS Homomorphic Encryption and Differential Privacy module.

Owner: M3 (Privacy & Security Lead)
"""

from .differential_privacy import (
    clip_and_noise_gradients,
    compute_privacy_budget,
)
from .encryption import (
    decrypt_parameters,
    encrypt_parameters,
    pack_tensor_to_ciphertext,
    unpack_ciphertext_to_tensor,
)
from .tenseal_context import (
    create_ckks_context,
    deserialize_context,
    serialize_public_context,
    serialize_secret_context,
)

__all__ = [
    "clip_and_noise_gradients",
    "compute_privacy_budget",
    "create_ckks_context",
    "decrypt_parameters",
    "deserialize_context",
    "encrypt_parameters",
    "pack_tensor_to_ciphertext",
    "serialize_public_context",
    "serialize_secret_context",
    "unpack_ciphertext_to_tensor",
]
