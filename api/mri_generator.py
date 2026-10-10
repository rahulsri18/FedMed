"""api/mri_generator.py - 3D Multi-Planar BraTS Volume & PNG Slice Generator.

Owner: M2 (Models & Data) & M4 (API Lead)
Features:
- Realistic 3D Brain Phantom generator (64x64x64, 4 modalities: FLAIR, T1ce, T2, T1).
- Multi-region tumor masks: WT (Whole Tumor), TC (Tumor Core), ET (Enhancing Tumor).
- Multi-planar slicing: Axial, Sagittal, Coronal planes.
- Pure Python standard library PNG encoder (zlib + struct, zero external imaging libraries needed).
"""

import struct
import zlib
from typing import Any

import numpy as np


def encode_png(raw_pixels: bytes, width: int, height: int, color_type: int = 0) -> bytes:
    """Encodes raw scanline bytes into a standard PNG byte sequence.
    
    Args:
        raw_pixels: Raw pixel bytes. For color_type=0 (grayscale), len = width * height.
                    For color_type=6 (RGBA), len = width * height * 4.
        width: Image width in pixels.
        height: Image height in pixels.
        color_type: 0 for 8-bit grayscale, 6 for 32-bit RGBA.
        
    Returns:
        Standard PNG byte stream.
    """
    bytes_per_pixel = 1 if color_type == 0 else 4
    row_bytes_len = width * bytes_per_pixel
    
    # Prepend filter byte 0x00 (None filter) to each row
    filtered_rows = bytearray()
    for y in range(height):
        filtered_rows.append(0)  # Filter type: None
        start = y * row_bytes_len
        filtered_rows.extend(raw_pixels[start : start + row_bytes_len])

    compressed = zlib.compress(bytes(filtered_rows), level=6)

    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        length = struct.pack(">I", len(data))
        crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        return length + chunk_type + data + crc

    # PNG Signature
    png_sig = b"\x89PNG\r\n\x1a\n"
    
    # IHDR Chunk: width(4), height(4), bit_depth(1), color_type(1), compression(1), filter(1), interlace(1)
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    ihdr_chunk = make_chunk(b"IHDR", ihdr_data)

    # IDAT Chunk
    idat_chunk = make_chunk(b"IDAT", compressed)

    # IEND Chunk
    iend_chunk = make_chunk(b"IEND", b"")

    return png_sig + ihdr_chunk + idat_chunk + iend_chunk


class BraTSVolumeCache:
    """In-memory cache of realistic 3D MRI scans across 3 distinct patient pathologies."""

    def __init__(self, size: int = 64):
        self.size = size
        self.scans: dict[str, dict[str, Any]] = {}
        self._init_synthetic_patients()

    def _init_synthetic_patients(self):
        # Patient 001: Glioblastoma Multiforme (Right Temporal-Parietal)
        self.scans["BraTS2021_00001"] = self._create_phantom(
            patient_id="BraTS2021_00001",
            tumor_center=(32 + 3, 32 + 6, 32 - 4),
            tumor_radius=12,
            has_enhancing_core=True,
            edema_spread=1.6,
        )

        # Patient 002: IDH-Mutant Astrocytoma (Left Frontal)
        self.scans["BraTS2021_00002"] = self._create_phantom(
            patient_id="BraTS2021_00002",
            tumor_center=(32 - 6, 32 - 8, 32 + 3),
            tumor_radius=10,
            has_enhancing_core=False,
            edema_spread=1.3,
        )

        # Patient 003: Oligodendroglioma (Frontal-Parietal)
        self.scans["BraTS2021_00003"] = self._create_phantom(
            patient_id="BraTS2021_00003",
            tumor_center=(32 + 4, 32 - 3, 32 + 6),
            tumor_radius=9,
            has_enhancing_core=True,
            edema_spread=1.2,
        )

    def _create_phantom(
        self,
        patient_id: str,
        tumor_center: tuple[int, int, int],
        tumor_radius: float,
        has_enhancing_core: bool,
        edema_spread: float,
    ) -> dict[str, Any]:
        S = self.size
        # Channels: 0: T1, 1: T1ce, 2: T2, 3: FLAIR
        image = np.zeros((4, S, S, S), dtype=np.float32)
        # Masks: 0: WT (Whole Tumor), 1: TC (Tumor Core), 2: ET (Enhancing Tumor)
        mask = np.zeros((3, S, S, S), dtype=np.uint8)

        z, y, x = np.meshgrid(np.arange(S), np.arange(S), np.arange(S), indexing="ij")
        cz, cy, cx = S // 2, S // 2, S // 2
        rz, ry, rx = S * 0.42, S * 0.46, S * 0.38

        # Ellipsoidal brain boundary
        brain_dist = np.sqrt(
            ((z - cz) / rz) ** 2 + ((y - cy) / ry) ** 2 + ((x - cx) / rx) ** 2
        )
        brain_mask = brain_dist <= 1.0

        # Ventricles
        vz, vy, vx = cz, cy, cx
        left_vent = (((z - vz) / (rz * 0.45)) ** 2 + ((y - (vy - 3)) / (ry * 0.35)) ** 2 + ((x - (vx - 5)) / (rx * 0.15)) ** 2) <= 1.0
        right_vent = (((z - vz) / (rz * 0.45)) ** 2 + ((y - (vy - 3)) / (ry * 0.35)) ** 2 + ((x - (vx + 5)) / (rx * 0.15)) ** 2) <= 1.0
        ventricles = (left_vent | right_vent) & brain_mask

        # Baseline tissue intensities
        np.random.seed(42 + hash(patient_id) % 1000)

        # T1
        image[0][brain_mask] = 0.55 + 0.05 * np.sin(x[brain_mask] * 0.2)
        image[0][ventricles] = 0.12
        # T1ce
        image[1][brain_mask] = 0.58 + 0.04 * np.sin(x[brain_mask] * 0.2)
        image[1][ventricles] = 0.12
        # T2
        image[2][brain_mask] = 0.45 + 0.05 * np.cos(y[brain_mask] * 0.2)
        image[2][ventricles] = 0.90
        # FLAIR
        image[3][brain_mask] = 0.50 + 0.04 * np.sin(z[brain_mask] * 0.15)
        image[3][ventricles] = 0.18


        # Tumor modeling
        tz, ty, tx = tumor_center
        t_dist = np.sqrt((z - tz) ** 2 + (y - ty) ** 2 + (x - tx) ** 2)

        wt_region = (t_dist <= (tumor_radius * edema_spread)) & brain_mask
        tc_region = (t_dist <= (tumor_radius * 0.75)) & brain_mask
        et_region = (t_dist <= (tumor_radius * 0.45)) & brain_mask if has_enhancing_core else np.zeros_like(brain_mask)
        necrotic_region = (t_dist <= (tumor_radius * 0.25)) & tc_region

        mask[0][wt_region] = 1
        mask[1][tc_region] = 1
        mask[2][et_region] = 1

        # Modality signature enhancements for tumor
        image[3][wt_region] += 0.38  # FLAIR hyperintense peritumoral edema
        image[2][wt_region] += 0.32  # T2 hyperintense edema
        if has_enhancing_core:
            image[1][et_region] += 0.45  # T1ce prominent enhancing rim
        image[0][tc_region] -= 0.15  # T1 hypointense core
        image[1][necrotic_region] -= 0.20  # Necrotic center hypo-intense

        # Normalize and clip to [0, 1]
        image = np.clip(image, 0.0, 1.0)

        return {
            "id": patient_id,
            "image": image,
            "mask": mask,
            "shape": (S, S, S),
            "wt_voxels": int(np.sum(mask[0])),
            "tc_voxels": int(np.sum(mask[1])),
            "et_voxels": int(np.sum(mask[2])),
        }

    def get_slice(
        self,
        scan_id: str,
        axis: str = "axial",
        index: int = 32,
        modality: str = "FLAIR",
        window_level: float = 0.5,
        window_width: float = 1.0,
    ) -> bytes:
        """Returns 2D MRI slice as 8-bit grayscale PNG bytes."""
        scan = self.scans.get(scan_id, self.scans["BraTS2021_00001"])
        image_vol = scan["image"]  # shape (4, S, S, S)
        S = self.size

        modality_map = {"T1": 0, "T1ce": 1, "T2": 2, "FLAIR": 3}
        ch_idx = modality_map.get(modality.upper(), 3)
        vol_3d = image_vol[ch_idx]

        idx = max(0, min(S - 1, index - 1))

        if axis.lower() == "axial":
            slice_2d = vol_3d[idx, :, :]
        elif axis.lower() == "coronal":
            slice_2d = vol_3d[:, idx, :]
        elif axis.lower() == "sagittal":
            slice_2d = vol_3d[:, :, idx]
        else:
            slice_2d = vol_3d[idx, :, :]

        # Apply Window Level & Window Width (PACS style)
        low = window_level - (window_width / 2.0)
        high = window_level + (window_width / 2.0)
        windowed = np.clip((slice_2d - low) / max(0.01, high - low), 0.0, 1.0)

        # Scale to 128x128 for crisp viewer display
        upscaled = np.repeat(np.repeat(windowed, 2, axis=0), 2, axis=1)
        uint8_pixels = (upscaled * 255.0).astype(np.uint8)

        return encode_png(uint8_pixels.tobytes(), upscaled.shape[1], upscaled.shape[0], color_type=0)

    def get_mask_slice(
        self,
        scan_id: str,
        axis: str = "axial",
        index: int = 32,
        show_wt: bool = True,
        show_tc: bool = True,
        show_et: bool = True,
        opacity: float = 0.75,
    ) -> bytes:
        """Returns 2D tumor segmentation mask overlay as RGBA PNG bytes."""
        scan = self.scans.get(scan_id, self.scans["BraTS2021_00001"])
        mask_vol = scan["mask"]  # shape (3, S, S, S)
        S = self.size

        idx = max(0, min(S - 1, index - 1))

        if axis.lower() == "axial":
            wt = mask_vol[0, idx, :, :]
            tc = mask_vol[1, idx, :, :]
            et = mask_vol[2, idx, :, :]
        elif axis.lower() == "coronal":
            wt = mask_vol[0, :, idx, :]
            tc = mask_vol[1, :, idx, :]
            et = mask_vol[2, :, idx, :]
        elif axis.lower() == "sagittal":
            wt = mask_vol[0, :, :, idx]
            tc = mask_vol[1, :, :, idx]
            et = mask_vol[2, :, :, idx]
        else:
            wt = mask_vol[0, idx, :, :]
            tc = mask_vol[1, idx, :, :]
            et = mask_vol[2, idx, :, :]

        H, W = wt.shape
        rgba = np.zeros((H, W, 4), dtype=np.uint8)
        alpha_val = int(min(255, max(0, opacity * 255)))

        # WT: Bio-Emerald (#10b981 -> R:16, G:185, B:129)
        if show_wt:
            m = wt == 1
            rgba[m] = [16, 185, 129, int(alpha_val * 0.7)]

        # TC: Cadmium Amber (#f59e0b -> R:245, G:158, B:11)
        if show_tc:
            m = tc == 1
            rgba[m] = [245, 158, 11, int(alpha_val * 0.85)]

        # ET: Crimson Coral (#f43f5e -> R:244, G:63, B:94)
        if show_et:
            m = et == 1
            rgba[m] = [244, 63, 94, int(alpha_val * 0.95)]

        # Upscale 2x
        upscaled = np.repeat(np.repeat(rgba, 2, axis=0), 2, axis=1)
        return encode_png(upscaled.tobytes(), upscaled.shape[1], upscaled.shape[0], color_type=6)


# Singleton volume cache instance
VOLUME_CACHE = BraTSVolumeCache(size=64)
