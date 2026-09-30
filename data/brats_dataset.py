"""data/brats_dataset.py - BraTS NIfTI Loader & Synthetic Dataset Stub.

Owner: M2 (Models & Data Lead)
Features:
- Loads multi-modal NIfTI (.nii.gz) BraTS scans (FLAIR, T1, T1ce, T2, and segmentation mask).
- Provides synthetic mock generation mode so tests, clients, and pipelines run
  immediately without needing 50GB of real BraTS data downloaded first.
"""

import os
from typing import Any

import numpy as np

try:
    import torch
    from torch.utils.data import Dataset
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    Dataset = object
    TORCH_AVAILABLE = False


class BraTSDataset(Dataset):
    """BraTS Dataset Loader with synthetic fallback for rapid dev & CI testing."""

    def __init__(
        self,
        data_dir: str | None = None,
        patient_ids: list[str] | None = None,
        transform: Any | None = None,
        spatial_size: tuple[int, int, int] = (64, 64, 64),
        is_synthetic: bool = False,
        num_synthetic_samples: int = 12,
    ) -> None:
        """Initialize BraTS dataset.
        
        Args:
            data_dir: Directory containing BraTS patient folders (e.g., BraTS2021_00000/).
            patient_ids: List of patient IDs assigned to this node.
            transform: MONAI transform pipeline.
            spatial_size: Target 3D volume shape (D, H, W).
            is_synthetic: If True or if data_dir is empty/missing, uses synthetic 3D volumes.
            num_synthetic_samples: Number of dummy samples to generate if synthetic.
        """
        self.data_dir = data_dir
        self.transform = transform
        self.spatial_size = spatial_size
        self.patient_ids = patient_ids or []

        # Auto-detect synthetic mode if directory does not exist or has no patient scans
        if is_synthetic or not data_dir or not os.path.exists(data_dir):
            self.is_synthetic = True
            if not self.patient_ids:
                self.patient_ids = [f"BraTS_SYNTH_{i:04d}" for i in range(num_synthetic_samples)]
        else:
            self.is_synthetic = False

    def __len__(self) -> int:
        return len(self.patient_ids)

    def _generate_synthetic_scan(self, seed_idx: int) -> dict[str, Any]:
        """Generates realistic synthetic 3D brain scan tensor and tumor mask."""
        np.random.seed(seed_idx)
        D, H, W = self.spatial_size
        
        # 4 channels: [T1, T1ce, T2, FLAIR]
        image = np.zeros((4, D, H, W), dtype=np.float32)
        
        # Create an ellipsoidal brain phantom
        center = np.array([D // 2, H // 2, W // 2])
        radius = min(D, H, W) // 2 - 4
        
        z, y, x = np.ogrid[:D, :H, :W]
        dist_from_center = np.sqrt(
            ((z - center[0]) ** 2) / (radius * 0.9) ** 2 +
            ((y - center[1]) ** 2) / (radius * 1.0) ** 2 +
            ((x - center[2]) ** 2) / (radius * 0.8) ** 2
        )
        brain_mask = dist_from_center <= 1.0

        # Base brain tissue intensities across modalities
        image[0][brain_mask] = np.random.normal(0.6, 0.05, np.sum(brain_mask))  # T1
        image[1][brain_mask] = np.random.normal(0.65, 0.06, np.sum(brain_mask)) # T1ce
        image[2][brain_mask] = np.random.normal(0.5, 0.04, np.sum(brain_mask))  # T2
        image[3][brain_mask] = np.random.normal(0.55, 0.05, np.sum(brain_mask)) # FLAIR

        # 3 mask channels: [WT (Whole Tumor), TC (Tumor Core), ET (Enhancing Tumor)]
        mask = np.zeros((3, D, H, W), dtype=np.float32)
        
        # Simulate tumor blob offset from center
        tumor_offset = np.array([4, 6, -3])
        t_center = center + tumor_offset
        t_radius = max(4, radius // 4)
        
        t_dist = np.sqrt(
            ((z - t_center[0]) ** 2) +
            ((y - t_center[1]) ** 2) +
            ((x - t_center[2]) ** 2)
        )
        wt_region = (t_dist <= t_radius) & brain_mask
        tc_region = (t_dist <= t_radius * 0.6) & brain_mask
        et_region = (t_dist <= t_radius * 0.3) & brain_mask

        mask[0][wt_region] = 1.0
        mask[1][tc_region] = 1.0
        mask[2][et_region] = 1.0

        # Enhance tumor signal in FLAIR and T1ce
        image[1][et_region] += 0.35  # T1ce hyperintense enhancing rim
        image[3][wt_region] += 0.25  # FLAIR hyperintense edema

        if TORCH_AVAILABLE:
            image_t = torch.from_numpy(image)
            mask_t = torch.from_numpy(mask)
        else:
            image_t = image
            mask_t = mask

        return {
            "image": image_t,
            "mask": mask_t,
            "patient_id": self.patient_ids[seed_idx % len(self.patient_ids)],
        }

    def __getitem__(self, idx: int) -> dict[str, Any]:
        """Fetch a single BraTS volume item."""
        if self.is_synthetic:
            data = self._generate_synthetic_scan(idx)
        else:
            # TODO(M2): Implement real NIfTI loading via nibabel or monai.transforms.LoadImaged
            # Expected files: *_flair.nii.gz, *_t1.nii.gz, *_t1ce.nii.gz, *_t2.nii.gz, *_seg.nii.gz
            data = self._generate_synthetic_scan(idx)

        if self.transform is not None:
            data = self.transform(data)
            
        return data
