"""privacy/differential_privacy.py - Opacus-Style Gradient Clipping & Gaussian Noise.

Owner: M3 (Privacy & Security Lead)
Features:
- Global L2-norm clipping across layers.
- Calibrated Gaussian perturbation matching Rényi Differential Privacy (RDP).
- Privacy budget accountant stub (epsilon tracking over communication rounds).
"""

import logging

import numpy as np

logger = logging.getLogger("FedMed.Privacy.DP")


def clip_and_noise_gradients(
    gradients_or_weights: list[np.ndarray],
    max_grad_norm: float = 1.0,
    noise_multiplier: float = 0.8,
    batch_size: int = 4,
) -> list[np.ndarray]:
    """Applies Opacus-style global L2 clipping and Gaussian noise perturbation.
    
    Args:
        gradients_or_weights: List of numpy arrays representing model weight updates.
        max_grad_norm: Maximum L2 norm clipping threshold (C).
        noise_multiplier: Ratio of Gaussian noise std to clipping threshold (sigma).
        batch_size: Effective local batch size used for normalization.
        
    Returns:
        List of clipped and perturbed numpy arrays.
    """
    # 1. Compute global L2 norm across all parameters
    total_norm = 0.0
    for param in gradients_or_weights:
        param_norm = np.linalg.norm(param)
        total_norm += param_norm ** 2
    total_norm = np.sqrt(total_norm)

    # 2. Compute clipping factor
    clip_factor = min(1.0, float(max_grad_norm) / (total_norm + 1e-6))
    
    # 3. Clip and add calibrated Gaussian noise
    noised_parameters: list[np.ndarray] = []
    # Sigma for Gaussian noise: sigma * C / batch_size
    noise_std = (noise_multiplier * max_grad_norm) / max(1, batch_size)

    for param in gradients_or_weights:
        clipped_param = param * clip_factor
        noise = np.random.normal(0.0, noise_std, size=param.shape).astype(param.dtype)
        noised_parameters.append(clipped_param + noise)

    logger.debug(
        "DP applied: Total norm=%.4f, Clip factor=%.4f, Noise std=%.6f",
        total_norm, clip_factor, noise_std
    )
    return noised_parameters


def compute_privacy_budget(
    rounds: int,
    local_epochs: int,
    noise_multiplier: float,
    sample_rate: float,
    delta: float = 1e-5,
) -> float:
    """Computes accumulated privacy loss (epsilon) using Moments Accountant / RDP stub.
    
    Args:
        rounds: Number of federated communication rounds.
        local_epochs: Local epochs per round.
        noise_multiplier: Calibrated noise level.
        sample_rate: Subsampling ratio (q = batch_size / total_samples).
        delta: Target privacy failure probability (typically 1e-5 for BraTS).
        
    Returns:
        Estimated epsilon spent.
    """
    # TODO(M3): Integrate Opacus RDP / GaussianDifferentialPrivacy accountant for exact bounds
    total_steps = rounds * local_epochs
    if noise_multiplier <= 0:
        return float("inf")

    # Simplified asymptotic formula for stubbing telemetry and CI checks
    epsilon_approx = (
        sample_rate
        * np.sqrt(2 * total_steps * np.log(1 / delta))
        / noise_multiplier
    )
    return float(round(min(10.0, max(0.1, epsilon_approx)), 2))
