"""data/transforms.py - MONAI Preprocessing and Augmentation Pipeline.

Owner: M2 (Models & Data Lead)
"""

from typing import Any

try:
    from monai.transforms import (
        Compose,
        EnsureTyped,
        NormalizeIntensityd,
        RandFlipd,
        RandSpatialCropd,
        SpatialPadd,
    )
    MONAI_AVAILABLE = True
except ImportError:
    Compose = None
    MONAI_AVAILABLE = False


def get_train_transforms(roi_size: tuple[int, int, int] = (64, 64, 64)) -> Any:
    """Returns training transforms pipeline for BraTS multi-modal volumes."""
    # TODO(M2): Add RandRotated, RandGaussianNoised, and RandAffined augmentations
    if not MONAI_AVAILABLE:
        # Pass-through stub if MONAI is not yet installed
        return lambda x: x

    return Compose([
        EnsureTyped(keys=["image", "mask"]),
        SpatialPadd(keys=["image", "mask"], spatial_size=roi_size),
        NormalizeIntensityd(keys="image", nonzero=True, channel_wise=True),
        RandSpatialCropd(keys=["image", "mask"], roi_size=roi_size, random_size=False),
        RandFlipd(keys=["image", "mask"], prob=0.5, spatial_axis=0),
        RandFlipd(keys=["image", "mask"], prob=0.5, spatial_axis=1),
        RandFlipd(keys=["image", "mask"], prob=0.5, spatial_axis=2),
    ])


def get_val_transforms() -> Any:
    """Returns validation/evaluation transforms pipeline."""
    if not MONAI_AVAILABLE:
        return lambda x: x

    return Compose([
        EnsureTyped(keys=["image", "mask"]),
        NormalizeIntensityd(keys="image", nonzero=True, channel_wise=True),
    ])
