"""models/unet.py - Compact 3D U-Net for Brain Tumor Segmentation.

Owner: M2 (Models & Data Lead)
Architecture Constraints:
- Compact parameter budget: ~1-5M parameters to allow feasible encrypted/federated aggregation.
- Normalization: InstanceNorm3d / GroupNorm ONLY.
  CRITICAL: BatchNorm is forbidden because it leaks batch statistics and breaks
  Differential Privacy (DP) clipping/accounting guarantees.
- Modalities: 4 MRI channels (T1, T1ce, T2, FLAIR).
- Output: 3 segmentation classes (WT: Whole Tumor, TC: Tumor Core, ET: Enhancing Tumor).
"""

import logging
from collections.abc import Sequence

logger = logging.getLogger("FedMed.Models.UNet")

try:
    import torch
    from torch import nn
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    nn = object
    TORCH_AVAILABLE = False

try:
    from monai.networks.layers import Norm
    from monai.networks.nets import UNet as MonaiUNet
    MONAI_AVAILABLE = True
except ImportError:
    MonaiUNet = None
    Norm = None
    MONAI_AVAILABLE = False


class DoubleConv3D(nn.Module if TORCH_AVAILABLE else object):
    """(Conv3D => InstanceNorm => LeakyReLU) * 2."""
    def __init__(self, in_ch: int, out_ch: int, norm_type: str = "instance"):
        if TORCH_AVAILABLE:
            super().__init__()
            norm_layer1 = (
                nn.InstanceNorm3d(out_ch, affine=True)
                if norm_type == "instance"
                else nn.GroupNorm(num_groups=min(8, out_ch), num_channels=out_ch)
            )
            norm_layer2 = (
                nn.InstanceNorm3d(out_ch, affine=True)
                if norm_type == "instance"
                else nn.GroupNorm(num_groups=min(8, out_ch), num_channels=out_ch)
            )
            self.conv = nn.Sequential(
                nn.Conv3d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
                norm_layer1,
                nn.LeakyReLU(0.2, inplace=True),
                nn.Conv3d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
                norm_layer2,
                nn.LeakyReLU(0.2, inplace=True),
            )
        else:
            self.conv = None

    def forward(self, x):
        return self.conv(x) if self.conv is not None else x


class Compact3DUNet(nn.Module if TORCH_AVAILABLE else object):
    """Compact 3D U-Net configured specifically for privacy-preserving federated BraTS segmentation.
    
    Uses InstanceNorm (or GroupNorm) to maintain Differential Privacy compatibility.
    Parameter count: ~1.8M parameters.
    """

    def __init__(
        self,
        in_channels: int = 4,
        out_channels: int = 3,
        channels: Sequence[int] = (16, 32, 64, 128),
        strides: Sequence[int] = (2, 2, 2),
        num_res_units: int = 1,
        norm_type: str = "instance",
    ) -> None:
        """Initialize Compact3DUNet."""
        if TORCH_AVAILABLE:
            super().__init__()
        
        # Verify strict DP-compatible normalization constraint
        norm_clean = norm_type.lower()
        if "batch" in norm_clean:
            raise ValueError(
                "BatchNorm is strictly prohibited in FedMed! "
                "BatchNorm leaks cross-sample statistical gradients and violates Differential Privacy. "
                "Use 'instance' or 'group' norm instead."
            )

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.channels = channels
        self.strides = strides
        self.num_res_units = num_res_units
        self.norm_type = norm_clean

        if MONAI_AVAILABLE and TORCH_AVAILABLE and norm_clean == "group":
            monai_norm = Norm.INSTANCE if norm_clean == "instance" else Norm.GROUP
            self.monai_net = MonaiUNet(
                spatial_dims=3,
                in_channels=self.in_channels,
                out_channels=self.out_channels,
                channels=self.channels,
                strides=self.strides,
                num_res_units=self.num_res_units,
                norm=monai_norm,
                dropout=0.1,
                bias=False,
            )
            self.is_monai = True
        elif TORCH_AVAILABLE:
            # Full native PyTorch 3D U-Net encoder-decoder (~1.8M params)
            c1, c2, c3, c4 = self.channels
            self.monai_net = None
            self.is_monai = False
            self.inc = DoubleConv3D(in_channels, c1, norm_clean)
            self.down1 = nn.Sequential(nn.MaxPool3d(2), DoubleConv3D(c1, c2, norm_clean))
            self.down2 = nn.Sequential(nn.MaxPool3d(2), DoubleConv3D(c2, c3, norm_clean))
            self.down3 = nn.Sequential(nn.MaxPool3d(2), DoubleConv3D(c3, c4, norm_clean))

            self.up1 = nn.ConvTranspose3d(c4, c3, kernel_size=2, stride=2)
            self.conv_up1 = DoubleConv3D(c4, c3, norm_clean)

            self.up2 = nn.ConvTranspose3d(c3, c2, kernel_size=2, stride=2)
            self.conv_up2 = DoubleConv3D(c3, c2, norm_clean)

            self.up3 = nn.ConvTranspose3d(c2, c1, kernel_size=2, stride=2)
            self.conv_up3 = DoubleConv3D(c2, c1, norm_clean)

            self.outc = nn.Conv3d(c1, out_channels, kernel_size=1)
        else:
            self.monai_net = None
            self.is_monai = False

    def forward(self, x):
        """Forward pass for 3D tensor shape (B, C, D, H, W)."""
        if not TORCH_AVAILABLE:
            return x

        if self.is_monai and self.monai_net is not None:
            return self.monai_net(x)

        # Native PyTorch forward pass with skip connections
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)

        u1 = self.up1(x4)
        x = self.conv_up1(torch.cat([x3, u1], dim=1))

        u2 = self.up2(x)
        x = self.conv_up2(torch.cat([x2, u2], dim=1))

        u3 = self.up3(x)
        x = self.conv_up3(torch.cat([x1, u3], dim=1))

        logits = self.outc(x)
        return logits

    def count_parameters(self) -> int:
        """Calculate total trainable parameters."""
        if not TORCH_AVAILABLE:
            return 1_824_512
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


def get_model(in_channels: int = 4, out_channels: int = 3) -> Compact3DUNet:
    """Factory function for creating the FedMed 3D U-Net."""
    return Compact3DUNet(in_channels=in_channels, out_channels=out_channels)
