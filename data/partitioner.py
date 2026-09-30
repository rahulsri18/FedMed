"""data/partitioner.py - IID and Dirichlet Non-IID Hospital Data Partitioner.

Owner: M2 (Models & Data Lead)
Supports:
- IID: Uniform random distribution of patient cases across N hospital nodes.
- Dirichlet Non-IID: Simulates real-world cross-silo heterogeneity parameterized by alpha.
"""

from collections.abc import Sequence
from typing import Any

import numpy as np


def partition_data(
    dataset_or_indices: Sequence[Any] | int,
    num_nodes: int = 3,
    partition_type: str = "dirichlet",
    alpha: float = 0.5,
    seed: int = 42,
) -> dict[int, list[int]]:
    """Partition patient indices across simulated hospital nodes.
    
    Args:
        dataset_or_indices: List of patient IDs, or total count of samples (integer).
        num_nodes: Number of hospital silos (default: 3).
        partition_type: 'iid' for uniform, or 'dirichlet' for non-IID heterogeneity.
        alpha: Concentration parameter for Dirichlet distribution (smaller = more non-IID).
        seed: Random seed for reproducible partitioning.
        
    Returns:
        Dict mapping node_id (1-indexed) to list of assigned sample indices.
    """
    np.random.seed(seed)
    
    if isinstance(dataset_or_indices, int):
        total_samples = dataset_or_indices
        indices = np.arange(total_samples)
    else:
        total_samples = len(dataset_or_indices)
        indices = np.arange(total_samples)

    node_partitions: dict[int, list[int]] = {i + 1: [] for i in range(num_nodes)}
    
    if total_samples == 0:
        return node_partitions

    if partition_type.lower() == "iid":
        shuffled = np.random.permutation(indices)
        splits = np.array_split(shuffled, num_nodes)
        for i, split in enumerate(splits):
            node_partitions[i + 1] = split.tolist()
            
    elif partition_type.lower() == "dirichlet":
        proportions = np.random.dirichlet(np.repeat(alpha, num_nodes))
        counts = (proportions * total_samples).astype(int)
        
        remainder = total_samples - np.sum(counts)
        for i in range(remainder):
            counts[i % num_nodes] += 1
            
        for i in range(num_nodes):
            if counts[i] == 0 and total_samples >= num_nodes:
                donor = int(np.argmax(counts))
                if counts[donor] > 1:
                    counts[donor] -= 1
                    counts[i] += 1

        shuffled = np.random.permutation(indices)
        current_idx = 0
        for i in range(num_nodes):
            take = counts[i]
            node_partitions[i + 1] = shuffled[current_idx : current_idx + take].tolist()
            current_idx += take
    else:
        raise ValueError(f"Unknown partition_type '{partition_type}'. Use 'iid' or 'dirichlet'.")

    return node_partitions
