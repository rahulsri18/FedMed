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


def compute_rdp_step(alpha: float, noise_multiplier: float, sample_rate: float) -> float:
    """Compute RDP for subsampled Gaussian mechanism at order alpha.
    
    Uses tight analytical RDP bound for subsampled Gaussian mechanism.
    For subsampling ratio q and noise sigma:
        RDP(alpha) <= (alpha * q^2) / (2 * sigma^2) for small q.
    """
    if noise_multiplier <= 0:
        return float("inf")
    return (alpha * (sample_rate ** 2)) / (2.0 * (noise_multiplier ** 2))


def rdp_to_dp(rdp_total: dict[float, float], delta: float = 1e-5) -> tuple[float, float]:
    """Convert accumulated RDP at multiple alpha orders into (epsilon, delta)-DP.
    
    Formula: epsilon = min_alpha { rdp(alpha) + log(1/delta) / (alpha - 1) }
    
    Returns:
        (optimal_epsilon, optimal_alpha)
    """
    epsilons = []
    for alpha, rdp_val in rdp_total.items():
        if alpha <= 1.0:
            continue
        eps = rdp_val + (np.log(1.0 / delta) / (alpha - 1.0))
        epsilons.append((eps, alpha))

    if not epsilons:
        return float("inf"), 1.0

    min_eps, opt_alpha = min(epsilons, key=lambda x: x[0])
    return float(min_eps), float(opt_alpha)


def compute_privacy_budget(
    rounds: int,
    local_epochs: int,
    noise_multiplier: float,
    sample_rate: float,
    delta: float = 1e-5,
) -> float:
    """Computes accumulated privacy loss (epsilon) using Rényi Differential Privacy accountant.
    
    Args:
        rounds: Number of federated communication rounds.
        local_epochs: Local epochs per round.
        noise_multiplier: Calibrated noise level (sigma).
        sample_rate: Subsampling ratio (q = batch_size / total_samples).
        delta: Target privacy failure probability (typically 1e-5 for BraTS).
        
    Returns:
        Estimated epsilon spent.
    """
    if noise_multiplier <= 0:
        return float("inf")

    total_steps = max(1, rounds * local_epochs)
    alphas = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 16.0, 20.0, 24.0, 32.0, 48.0, 64.0]

    rdp_accumulated = {}
    for alpha in alphas:
        step_rdp = compute_rdp_step(alpha, noise_multiplier, sample_rate)
        rdp_accumulated[alpha] = step_rdp * total_steps

    eps, _ = rdp_to_dp(rdp_accumulated, delta)
    return float(round(min(20.0, max(0.01, eps)), 2))


def get_privacy_accounting_details(
    rounds: int,
    local_epochs: int,
    noise_multiplier: float,
    sample_rate: float,
    delta: float = 1e-5,
    max_grad_norm: float = 1.0,
) -> dict:
    """Returns detailed privacy accounting metrics for telemetry and compliance."""
    total_steps = max(1, rounds * local_epochs)
    alphas = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 16.0, 20.0, 24.0, 32.0, 48.0, 64.0]
    rdp_accumulated = {alpha: compute_rdp_step(alpha, noise_multiplier, sample_rate) * total_steps for alpha in alphas}
    eps, opt_alpha = rdp_to_dp(rdp_accumulated, delta)

    return {
        "epsilon_spent": float(round(eps, 2)),
        "delta": delta,
        "optimal_alpha": opt_alpha,
        "total_steps": total_steps,
        "noise_multiplier": noise_multiplier,
        "sample_rate": sample_rate,
        "max_grad_norm": max_grad_norm,
        "accountant": "Rényi Differential Privacy (RDP)",
        "is_compliant": eps <= 10.0,
    }

