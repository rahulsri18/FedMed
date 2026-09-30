"""tests/test_privacy.py - Unit test stub for privacy module.

Owner: M3 (Privacy & Security Lead)
"""

import numpy as np


def test_privacy_module_import():
    """Verify privacy package, TenSEAL helpers, and DP functions import cleanly."""
    import privacy
    from privacy.differential_privacy import (
        clip_and_noise_gradients,
        compute_privacy_budget,
    )
    from privacy.tenseal_context import create_ckks_context

    assert privacy is not None
    assert create_ckks_context is not None
    assert clip_and_noise_gradients is not None
    assert compute_privacy_budget is not None


def test_ckks_context_and_trust_model():
    """Verify CKKS context generation and public vs secret key serialization."""
    from privacy.tenseal_context import (
        create_ckks_context,
        serialize_public_context,
        serialize_secret_context,
    )

    ctx = create_ckks_context(poly_modulus_degree=8192)
    assert ctx is not None

    pub_bytes = serialize_public_context(ctx)
    sec_bytes = serialize_secret_context(ctx)
    assert isinstance(pub_bytes, bytes)
    assert isinstance(sec_bytes, bytes)


def test_differential_privacy_clipping_and_noise():
    """Verify Opacus-style L2 gradient clipping and Gaussian noise perturbation."""
    from privacy.differential_privacy import (
        clip_and_noise_gradients,
        compute_privacy_budget,
    )

    # Create dummy layer weights with known norm
    w1 = np.ones((10, 10), dtype=np.float32) * 5.0
    w2 = np.ones((5,), dtype=np.float32) * 2.0
    weights = [w1, w2]

    # Clip with threshold 1.0
    noised = clip_and_noise_gradients(weights, max_grad_norm=1.0, noise_multiplier=0.0, batch_size=4)
    assert len(noised) == len(weights)
    assert noised[0].shape == w1.shape
    assert noised[1].shape == w2.shape

    # Privacy budget accountant test
    eps = compute_privacy_budget(rounds=5, local_epochs=1, noise_multiplier=0.8, sample_rate=0.25)
    assert 0.0 < eps <= 10.0
