"""tests/test_models.py - Unit test stub for models module.

Owner: M2 (Models & Data Lead)
"""

import pytest


def test_models_module_import():
    """Verify models package, U-Net, loss, and metrics import cleanly."""
    import models
    from models.losses import DiceCELoss, DiceLoss
    from models.unet import Compact3DUNet, get_model

    assert models is not None
    assert Compact3DUNet is not None
    assert get_model is not None
    assert DiceLoss is not None
    assert DiceCELoss is not None


def test_model_architecture_and_dp_constraints():
    """Verify Compact 3D U-Net rejects BatchNorm (strictly DP compatible) and parameter count is ~1.8M."""
    from models.unet import Compact3DUNet, get_model

    # Must reject BatchNorm to preserve Differential Privacy
    with pytest.raises(ValueError, match="BatchNorm is strictly prohibited"):
        Compact3DUNet(norm_type="batch")

    # InstanceNorm model instantiation
    model = get_model(in_channels=4, out_channels=3)
    assert model.in_channels == 4
    assert model.out_channels == 3
    params = model.count_parameters()
    # Parameters should be between 1M and 5M
    assert 1_000_000 <= params <= 5_000_000
