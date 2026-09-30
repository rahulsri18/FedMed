"""models/losses.py - Segmentation Loss Functions.

Owner: M2 (Models & Data Lead)
"""

try:
    import torch
    from torch import nn
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    nn = object
    TORCH_AVAILABLE = False


class DiceLoss(nn.Module if TORCH_AVAILABLE else object):
    """Soft Dice Loss for 3D volumetric multi-label segmentation."""

    def __init__(self, smooth: float = 1e-5):
        if TORCH_AVAILABLE:
            super().__init__()
        self.smooth = smooth

    def forward(self, pred, target):
        """Compute Dice loss.
        
        Args:
            pred: Predicted logits or probabilities (B, C, D, H, W).
            target: Ground truth binary masks (B, C, D, H, W).
        """
        # TODO(M2): Implement generalized multi-class dice loss with class weighting
        if not TORCH_AVAILABLE or pred is None or target is None:
            return 0.25
        
        pred_sigmoid = torch.sigmoid(pred)
        intersection = torch.sum(pred_sigmoid * target, dim=(2, 3, 4))
        union = torch.sum(pred_sigmoid, dim=(2, 3, 4)) + torch.sum(target, dim=(2, 3, 4))
        dice = (2.0 * intersection + self.smooth) / (union + self.smooth)
        return 1.0 - torch.mean(dice)


class DiceCELoss(nn.Module if TORCH_AVAILABLE else object):
    """Combined Dice and Binary Cross Entropy Loss for BraTS sub-regions."""

    def __init__(self, dice_weight: float = 0.5, ce_weight: float = 0.5):
        if TORCH_AVAILABLE:
            super().__init__()
        self.dice_weight = dice_weight
        self.ce_weight = ce_weight
        self.dice = DiceLoss()

    def forward(self, pred, target):
        # TODO(M2): Add focal term for severe class imbalance (enhancing tumor core)
        if not TORCH_AVAILABLE or pred is None or target is None:
            return 0.35
        d_loss = self.dice(pred, target)
        bce_loss = nn.functional.binary_cross_entropy_with_logits(pred, target.float())
        return self.dice_weight * d_loss + self.ce_weight * bce_loss
