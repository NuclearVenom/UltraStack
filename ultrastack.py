"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                          U L T R A S T A C K                                     ║
║        GPU-Accelerated Image & Video Stacking / Stitching Pipeline               ║
║                    with full Astronomical SER support                            ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  INPUT SOURCES                                                                   ║
║  • Folder of images — any single format: JPG, PNG, TIFF, BMP, WEBP, FIT/FITS     ║
║  • Video files      — MP4, AVI, MOV, MKV, WMV, WEBM, M4V, SER                    ║
║  • SER files        — astronomical capture format (mono/Bayer/RGB/BGR/YUV)       ║
║                                                                                  ║
║  STACKING MODES                                                                  ║
║  • Average stack    — classic mean, best for photon noise reduction              ║
║  • Median stack     — robust against outliers/satellites/hot pixels              ║
║  • Sigma-clipping   — astronomers' favourite: iterative outlier rejection        ║
║  • Maximum stack    — keep brightest pixel per position (star trails etc.)       ║
║  • Minimum stack    — keep darkest pixel (background subtraction helpers)        ║
║                                                                                  ║
║  ALIGNMENT                                                                       ║
║  • ORB feature matching — fast, great for planetary/landscape                    ║
║  • ECC (Enhanced Correlation Coefficient) — sub-pixel accuracy, ideal for astro  ║
║                                                                                  ║
║  PIPELINE FEATURES                                                               ║
║  • SIFT + FLANN intelligent image grouping before stacking                       ║
║  • Optional panorama stitching of stacked groups                                 ║
║  • Adaptive VRAM-safe batch processing                                           ║
║  • Parallel image loading with ThreadPoolExecutor                                ║
║  • Frame skipping and max_frames controls for video/SER                          ║
║  • Dark frame subtraction (calibration frames)                                   ║
║  • Hot pixel removal (cosmetic correction)                                       ║
║  • Histogram stretch / auto-levels for faint targets                             ║
║  • Post-processing: denoise + sharpen                                            ║
║  • Output: JPG, PNG, TIFF (16-bit TIFF for FITS/SER data)                        ║
║  • Google Colab support + CLI interface                                          ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  Requirements                                                                    ║
║  pip install opencv-contrib-python numpy torch tqdm                              ║
║  Optional for FITS: pip install astropy                                          ║
╚══════════════════════════════════════════════════════════════════════════════════╝

Usage:
  # Stack a folder of PNGs (auto-detected format):
  python ultrastack.py --input ./frames --output result.png

  # Stack with median + sigma clipping (astronomical mode):
  python ultrastack.py --input ./lights --output deep.tif --mode sigma --align ecc

  # Stack with dark frame subtraction:
  python ultrastack.py --input ./lights --dark ./darks --output result.tif

  # Stack a SER file:
  python ultrastack.py --input capture.ser --output stacked.tif --mode sigma

  # Stack + stitch panorama:
  python ultrastack.py --input ./mosaic_tiles --output pano.jpg --stitch

  # Stack video, every 3rd frame, max 500:
  python ultrastack.py --input timelapse.mp4 --skip 3 --max-frames 500 --output out.jpg
"""

import cv2
import numpy as np
import os
import gc
import sys
import struct
import warnings
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore")


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg",
    ".png",
    ".tif", ".tiff",
    ".bmp",
    ".webp",
    ".fit", ".fits",   # astronomical FITS (requires astropy)
    ".ppm", ".pgm",    # portable bitmap formats
    ".exr",            # OpenEXR (HDR)
}

VIDEO_EXTENSIONS = {
    ".mp4", ".avi", ".mov", ".mkv",
    ".wmv", ".webm", ".m4v", ".flv",
    ".ts", ".mts", ".m2ts",            # transport stream / AVCHD
}

SER_EXTENSION = ".ser"

# SER colour IDs (from SER spec)
SER_MONO       = 0
SER_BAYER_RGGB = 8
SER_BAYER_GRBG = 9
SER_BAYER_GBRG = 10
SER_BAYER_BGGR = 11
SER_BAYER_CYYM = 16
SER_BAYER_YCMY = 17
SER_BAYER_YMCY = 18
SER_BAYER_MYYC = 19
SER_RGB        = 100
SER_BGR        = 101

BAYER_CODES = {
    SER_BAYER_RGGB: cv2.COLOR_BayerRG2BGR,
    SER_BAYER_GRBG: cv2.COLOR_BayerGR2BGR,
    SER_BAYER_GBRG: cv2.COLOR_BayerGB2BGR,
    SER_BAYER_BGGR: cv2.COLOR_BayerBG2BGR,
}

STACK_MODES = ["average", "median", "sigma", "maximum", "minimum"]
ALIGN_MODES = ["none", "orb", "ecc"]

OUTPUT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


# ══════════════════════════════════════════════════════════════════════════════
# DISPLAY / UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def banner(text: str, width: int = 64, char: str = "═"):
    print(f"\n{char * width}\n  {text}\n{char * width}")

def info(msg: str):  print(f"  {msg}")
def warn(msg: str):  print(f"  ⚠  {msg}")
def ok(msg: str):    print(f"  ✓  {msg}")
def err(msg: str):   print(f"  ✗  {msg}")

def print_image_stats(img: np.ndarray, filepath: str):
    h, w = img.shape[:2]
    mp = (h * w) / 1_000_000
    size_kb = os.path.getsize(filepath) / 1024
    channels = img.shape[2] if img.ndim == 3 else 1
    print()
    info(f"Resolution : {w} × {h} px  ({mp:.2f} MP)")
    info(f"File size  : {size_kb:.0f} KB  ({size_kb/1024:.2f} MB)")
    info(f"Channels   : {channels}")
    info(f"dtype      : {img.dtype}")
    info(f"Min / Max  : {img.min()} / {img.max()}")
    info(f"Mean       : {float(img.mean()):.2f}")
    info(f"Std dev    : {float(img.std()):.2f}")
    info(f"Saved to   : {filepath}")


# ══════════════════════════════════════════════════════════════════════════════
# GPU SETUP
# ══════════════════════════════════════════════════════════════════════════════

def setup_device(force_cpu: bool = False):
    """Return (device_string, torch_module_or_None)."""
    if force_cpu:
        info("GPU disabled — using CPU (numpy)")
        return "cpu", None
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            ok(f"GPU: {name}  ({vram:.1f} GB VRAM)")
            return "cuda", torch
        else:
            warn("CUDA not available — using CPU")
            return "cpu", torch
    except ImportError:
        warn("PyTorch not installed — using CPU (numpy only)")
        return "cpu", None

def estimate_safe_batch(img_shape: Tuple, device: str, torch_module) -> int:
    if device != "cuda" or torch_module is None:
        return 16
    try:
        props = torch_module.cuda.get_device_properties(0)
        avail = props.total_memory * 0.70
        h, w = img_shape[:2]
        c = img_shape[2] if len(img_shape) == 3 else 1
        bytes_per = h * w * c * 4
        return max(1, int(avail // (bytes_per * 1.5)))
    except Exception:
        return 4


# ══════════════════════════════════════════════════════════════════════════════
# SER FILE READER
# ══════════════════════════════════════════════════════════════════════════════

class SERFile:
    """
    Full SER (Sequence of images for astronomical Recording) file reader.

    SER format specification:
      - 178-byte header
      - Raw frame data (little-endian, 8 or 16 bit)
      - Optional UTC timestamp trailer

    Colour IDs handled: MONO, all Bayer patterns, RGB, BGR.
    16-bit frames are normalised to uint8 or kept as uint16 depending on caller.
    """

    HEADER_SIZE = 178
    HEADER_FMT  = "<14siiiii40s40siqq"   # 14+4+4+4+4+4+40+40+8+8+8 = 178 bytes? let's parse manually

    def __init__(self, path: str):
        self.path   = path
        self.file   = open(path, "rb")
        self._parse_header()

    def _parse_header(self):
        hdr = self.file.read(self.HEADER_SIZE)
        if len(hdr) < self.HEADER_SIZE:
            raise ValueError("File too small to be a valid SER file")

        # FileID: 14 bytes
        file_id = hdr[0:14].decode("ascii", errors="ignore").rstrip("\x00")
        if not file_id.startswith("LUCAM-RECORDER"):
            warn(f"SER FileID is '{file_id}' — may not be a standard SER file, continuing anyway")

        # Unpack fixed fields (all little-endian int32)
        self.lu_id       = struct.unpack_from("<i", hdr, 14)[0]
        self.color_id    = struct.unpack_from("<i", hdr, 18)[0]
        self.little_endian = struct.unpack_from("<i", hdr, 22)[0]  # 0=big, non-0=little
        self.image_width = struct.unpack_from("<i", hdr, 26)[0]
        self.image_height= struct.unpack_from("<i", hdr, 30)[0]
        self.pixel_depth = struct.unpack_from("<i", hdr, 34)[0]   # bits per pixel per plane
        self.frame_count = struct.unpack_from("<i", hdr, 38)[0]

        # Observer / Telescope / Instrument strings (40 bytes each, null-padded)
        self.observer    = hdr[42:82].decode("ascii", errors="ignore").rstrip("\x00")
        self.instrument  = hdr[82:122].decode("ascii", errors="ignore").rstrip("\x00")
        self.telescope   = hdr[122:162].decode("ascii", errors="ignore").rstrip("\x00")

        # Date / DateUTC (8 bytes each, int64 Windows FILETIME)
        # We don't strictly need these for stacking

        # Determine channel count from color_id
        if self.color_id in (SER_RGB, SER_BGR):
            self.channels = 3
        elif self.color_id == SER_MONO:
            self.channels = 1
        elif self.color_id in BAYER_CODES:
            self.channels = 1   # raw Bayer stored as mono, debayered on read
        else:
            warn(f"Unknown SER color_id {self.color_id} — treating as mono")
            self.channels = 1

        self.bytes_per_pixel = (self.pixel_depth + 7) // 8   # e.g. 8→1, 12/16→2
        self.frame_bytes = self.image_width * self.image_height * self.channels * self.bytes_per_pixel
        self.data_offset = self.HEADER_SIZE

        info(f"SER  {self.image_width}×{self.image_height}  "
             f"{self.frame_count} frames  "
             f"{self.pixel_depth}-bit  "
             f"color_id={self.color_id}")
        if self.observer:   info(f"Observer   : {self.observer}")
        if self.instrument: info(f"Instrument : {self.instrument}")
        if self.telescope:  info(f"Telescope  : {self.telescope}")

    def read_frame(self, index: int) -> np.ndarray:
        """
        Read a single frame by index (0-based).
        Returns a BGR uint8 (or uint16 for 16-bit) numpy array.
        """
        if index < 0 or index >= self.frame_count:
            raise IndexError(f"Frame {index} out of range (0..{self.frame_count-1})")

        offset = self.data_offset + index * self.frame_bytes
        self.file.seek(offset)
        raw = self.file.read(self.frame_bytes)
        if len(raw) < self.frame_bytes:
            raise ValueError(f"Unexpected EOF at frame {index}")

        dtype = np.uint8 if self.bytes_per_pixel == 1 else np.uint16
        arr = np.frombuffer(raw, dtype=dtype)

        # Handle endianness for 16-bit
        if dtype == np.uint16 and self.little_endian == 0:
            arr = arr.byteswap()

        # Reshape
        if self.channels == 3:
            frame = arr.reshape((self.image_height, self.image_width, 3))
        else:
            frame = arr.reshape((self.image_height, self.image_width))

        # Normalise 16-bit to 8-bit for downstream processing
        # We keep full 16-bit depth here; callers can normalise if needed
        if dtype == np.uint16 and self.pixel_depth < 16:
            # e.g. 12-bit packed in 16-bit: shift down
            frame = (frame >> (self.pixel_depth - 8)).astype(np.uint16)

        # Debayer if necessary
        if self.color_id in BAYER_CODES:
            if dtype == np.uint16:
                frame8 = (frame >> 8).astype(np.uint8)
                frame = cv2.cvtColor(frame8, BAYER_CODES[self.color_id])
            else:
                frame = cv2.cvtColor(frame, BAYER_CODES[self.color_id])

        # SER_RGB → convert to BGR for OpenCV
        if self.color_id == SER_RGB:
            if frame.ndim == 3:
                frame = frame[:, :, ::-1].copy()

        # Mono: expand to 3-channel BGR for consistent downstream handling
        if frame.ndim == 2:
            frame = cv2.cvtColor(
                frame.astype(np.uint8) if frame.dtype == np.uint8
                else (frame >> 8).astype(np.uint8),
                cv2.COLOR_GRAY2BGR
            )
        elif frame.dtype == np.uint16:
            frame = (frame >> 8).astype(np.uint8)

        return frame  # always uint8 BGR after this point

    def frames(self, frame_skip: int = 1,
               max_frames: Optional[int] = None) -> Generator[Tuple[int, np.ndarray], None, None]:
        """Generator yielding (index, frame_bgr) respecting skip and max."""
        yielded = 0
        for i in range(0, self.frame_count, frame_skip):
            yield i, self.read_frame(i)
            yielded += 1
            if max_frames and yielded >= max_frames:
                break

    def close(self):
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


# ══════════════════════════════════════════════════════════════════════════════
# FITS READER (optional, requires astropy)
# ══════════════════════════════════════════════════════════════════════════════

def load_fits(path: str) -> np.ndarray:
    """
    Load a FITS image using astropy and return a BGR uint8 numpy array.
    Handles 2D (mono) and 3D (RGB cube) FITS files.
    Auto-stretches for display.
    """
    try:
        from astropy.io import fits
    except ImportError:
        raise ImportError("astropy is required to load FITS files.\n"
                          "Install with: pip install astropy")

    with fits.open(path) as hdul:
        data = hdul[0].data

    if data is None:
        # Try first extension with data
        with fits.open(path) as hdul:
            for hdu in hdul:
                if hdu.data is not None:
                    data = hdu.data
                    break

    if data is None:
        raise ValueError(f"No image data found in FITS file: {path}")

    data = data.astype(np.float32)

    # Normalise to 0-255
    lo, hi = np.percentile(data, 1), np.percentile(data, 99)
    if hi > lo:
        data = np.clip((data - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)
    else:
        data = np.zeros_like(data, dtype=np.uint8)

    # Shape handling
    if data.ndim == 2:
        bgr = cv2.cvtColor(data, cv2.COLOR_GRAY2BGR)
    elif data.ndim == 3:
        if data.shape[0] == 3:          # (3, H, W) cube
            data = np.moveaxis(data, 0, -1)   # → (H, W, 3)
        bgr = cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
    else:
        raise ValueError(f"Unsupported FITS data shape: {data.shape}")

    return bgr


# ══════════════════════════════════════════════════════════════════════════════
# IMAGE LOADING
# ══════════════════════════════════════════════════════════════════════════════

def load_single_image(path: Path) -> np.ndarray:
    """Load one image file → BGR uint8, regardless of format."""
    ext = path.suffix.lower()
    if ext in (".fit", ".fits"):
        return load_fits(str(path))

    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        # Try with UNCHANGED and convert (handles 16-bit TIFF etc.)
        img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Cannot read: {path}")
        if img.dtype == np.uint16:
            img = (img >> 8).astype(np.uint8)
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img

def detect_folder_format(folder_path: str) -> Tuple[str, List[Path]]:
    """
    Auto-detect the predominant image format in a folder.
    All images must be the same format.
    Returns (extension, sorted_list_of_paths).
    """
    folder = Path(folder_path)
    counts = {}
    for p in folder.iterdir():
        ext = p.suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            counts[ext] = counts.get(ext, 0) + 1

    if not counts:
        raise FileNotFoundError(f"No supported images found in: {folder_path}")

    # Pick the most common extension
    dominant_ext = max(counts, key=counts.__getitem__)

    if len(counts) > 1:
        other = {k: v for k, v in counts.items() if k != dominant_ext}
        warn(f"Multiple image formats found: {counts}")
        warn(f"Using dominant format: '{dominant_ext}' ({counts[dominant_ext]} files)")
        warn(f"Ignoring: {other}")

    paths = sorted(folder.glob(f"*{dominant_ext}"))
    info(f"Found {len(paths)} '{dominant_ext}' files in folder")
    return dominant_ext, paths

def load_images_parallel(paths: List[Path], max_workers: int = 8) -> List[np.ndarray]:
    """Load a list of image paths in parallel."""
    images = [None] * len(paths)
    done = 0

    def _load(idx_path):
        idx, path = idx_path
        return idx, load_single_image(path)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_load, (i, p)): i for i, p in enumerate(paths)}
        for future in as_completed(futures):
            try:
                idx, img = future.result()
                images[idx] = img
                done += 1
                print(f"\r  Loading... {done}/{len(paths)}", end="", flush=True)
            except Exception as e:
                i = futures[future]
                warn(f"\nSkipping {paths[i].name}: {e}")
    print()

    return [img for img in images if img is not None]


# ══════════════════════════════════════════════════════════════════════════════
# CALIBRATION: DARK FRAME SUBTRACTION + HOT PIXEL REMOVAL
# ══════════════════════════════════════════════════════════════════════════════

def make_master_dark(dark_folder: str) -> np.ndarray:
    """
    Stack all images in dark_folder (median stack) to produce a master dark frame.
    """
    banner("Building Master Dark Frame", char="-")
    _, paths = detect_folder_format(dark_folder)
    darks = load_images_parallel(paths)
    if not darks:
        raise FileNotFoundError("No dark frames found")
    info(f"Stacking {len(darks)} dark frames (median)...")
    stack = np.stack([d.astype(np.float32) for d in darks], axis=0)
    master = np.median(stack, axis=0).astype(np.uint8)
    ok("Master dark ready")
    return master

def subtract_dark(image: np.ndarray, master_dark: np.ndarray) -> np.ndarray:
    """Subtract master dark from image (clamped at 0)."""
    result = image.astype(np.int32) - master_dark.astype(np.int32)
    return np.clip(result, 0, 255).astype(np.uint8)

def remove_hot_pixels(image: np.ndarray, threshold: int = 70) -> np.ndarray:
    """
    Cosmetic correction: replace hot pixels with the local median.
    A pixel is 'hot' if it deviates > threshold from its 3×3 neighbourhood median.
    Operates per-channel.
    """
    result = image.copy()
    for c in range(image.shape[2] if image.ndim == 3 else 1):
        ch = image[:, :, c] if image.ndim == 3 else image
        med = cv2.medianBlur(ch, 3)
        diff = cv2.absdiff(ch, med)
        mask = diff > threshold
        if image.ndim == 3:
            result[:, :, c] = np.where(mask, med, ch)
        else:
            result = np.where(mask, med, ch)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# HISTOGRAM STRETCH (for faint targets)
# ══════════════════════════════════════════════════════════════════════════════

def auto_stretch(image: np.ndarray,
                 lo_pct: float = 0.5,
                 hi_pct: float = 99.5) -> np.ndarray:
    """
    Auto-stretch: remap the lo_pct–hi_pct intensity range to 0–255.
    Useful for revealing faint nebulae / galaxies after stacking.
    Works per-channel to avoid colour shifts.
    """
    result = np.zeros_like(image, dtype=np.uint8)
    for c in range(image.shape[2] if image.ndim == 3 else 1):
        ch = image[:, :, c] if image.ndim == 3 else image
        lo = np.percentile(ch, lo_pct)
        hi = np.percentile(ch, hi_pct)
        if hi > lo:
            stretched = np.clip((ch.astype(np.float32) - lo) / (hi - lo) * 255, 0, 255)
        else:
            stretched = ch.astype(np.float32)
        if image.ndim == 3:
            result[:, :, c] = stretched.astype(np.uint8)
        else:
            result = stretched.astype(np.uint8)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# ALIGNMENT
# ══════════════════════════════════════════════════════════════════════════════

def align_orb(base_gray: np.ndarray, frame_bgr: np.ndarray,
              max_features: int = 5000) -> np.ndarray:
    """
    Align frame_bgr to base_gray using ORB feature matching + homography.
    Grayscale used for detection; full-colour frame is warped.
    """
    orb = cv2.ORB_create(max_features)
    frame_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

    kp1, des1 = orb.detectAndCompute(base_gray, None)
    kp2, des2 = orb.detectAndCompute(frame_gray, None)

    if des1 is None or des2 is None or len(kp1) < 4 or len(kp2) < 4:
        return frame_bgr

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = sorted(matcher.match(des1, des2), key=lambda m: m.distance)

    if len(matches) < 4:
        return frame_bgr

    src = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    if H is None:
        return frame_bgr

    return cv2.warpPerspective(frame_bgr, H,
                               (base_gray.shape[1], base_gray.shape[0]))

def align_ecc(base_gray: np.ndarray, frame_bgr: np.ndarray) -> np.ndarray:
    """
    Sub-pixel alignment using Enhanced Correlation Coefficient (ECC).
    Best for astronomical images with stars — finds translational + rotational shift.
    Falls back to ORB if ECC fails to converge.
    """
    frame_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

    # Use affine (6 DOF) — handles translation + rotation + shear
    warp_mode = cv2.MOTION_EUCLIDEAN  # rotation + translation only for astro
    warp_matrix = np.eye(2, 3, dtype=np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-7)

    try:
        _, warp_matrix = cv2.findTransformECC(
            base_gray.astype(np.float32),
            frame_gray.astype(np.float32),
            warp_matrix,
            warp_mode,
            criteria,
            None, 5
        )
        h, w = base_gray.shape
        aligned = cv2.warpAffine(frame_bgr, warp_matrix, (w, h),
                                 flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
        return aligned
    except cv2.error:
        # ECC failed (low contrast, etc.) — fallback to ORB
        return align_orb(base_gray, frame_bgr)

def align_frame(base_gray: np.ndarray, frame_bgr: np.ndarray,
                method: str = "orb") -> np.ndarray:
    """Dispatch alignment to chosen method."""
    if method == "orb":
        return align_orb(base_gray, frame_bgr)
    elif method == "ecc":
        return align_ecc(base_gray, frame_bgr)
    else:
        return frame_bgr  # "none"


# ══════════════════════════════════════════════════════════════════════════════
# STACKING CORE
# ══════════════════════════════════════════════════════════════════════════════

def stack_images(images_bgr: List[np.ndarray],
                 mode: str = "average",
                 sigma_low: float = 2.0,
                 sigma_high: float = 2.0,
                 sigma_iters: int = 3,
                 device: str = "cpu",
                 torch_module=None) -> np.ndarray:
    """
    Stack a list of BGR images using the chosen mode.

    Modes:
      average  — mean of all frames (GPU-accelerated)
      median   — median per pixel (robust against outliers)
      sigma    — sigma-clipping then mean (astronomical standard)
      maximum  — max per pixel (star trails, lightning)
      minimum  — min per pixel (background extraction)
    """
    if len(images_bgr) == 1:
        return images_bgr[0]

    n = len(images_bgr)

    if mode == "average":
        return _stack_average_gpu(images_bgr, device, torch_module)

    elif mode == "maximum":
        result = images_bgr[0].astype(np.float32)
        for img in images_bgr[1:]:
            result = np.maximum(result, img.astype(np.float32))
        return result.astype(np.uint8)

    elif mode == "minimum":
        result = images_bgr[0].astype(np.float32)
        for img in images_bgr[1:]:
            result = np.minimum(result, img.astype(np.float32))
        return result.astype(np.uint8)

    elif mode == "median":
        # Load into float stack — memory-intensive but accurate
        info(f"  Building median stack ({n} frames)...")
        stack = np.stack([img.astype(np.float32) for img in images_bgr], axis=0)
        result = np.median(stack, axis=0)
        del stack
        gc.collect()
        return np.clip(result, 0, 255).astype(np.uint8)

    elif mode == "sigma":
        return _stack_sigma_clip(images_bgr, sigma_low, sigma_high, sigma_iters)

    else:
        raise ValueError(f"Unknown stack mode '{mode}'. Choose from: {STACK_MODES}")

def _stack_average_gpu(images_bgr: List[np.ndarray],
                       device: str, torch_module) -> np.ndarray:
    """
    GPU-accelerated average stack.
    Converts BGR→RGB internally, accumulates on-device, returns BGR uint8.
    """
    if torch_module is not None:
        t = torch_module
        total = None
        for img in images_bgr:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            tensor = t.from_numpy(rgb).float().to(device)
            total = tensor if total is None else total + tensor
        avg = (total / len(images_bgr)).clamp(0, 255).byte().cpu().numpy()
        del total
        if device == "cuda":
            t.cuda.empty_cache()
        return cv2.cvtColor(avg, cv2.COLOR_RGB2BGR)
    else:
        # Stable incremental mean (avoids float64 overflow on large stacks)
        acc = images_bgr[0].astype(np.float64)
        for k, img in enumerate(images_bgr[1:], start=1):
            acc += (img.astype(np.float64) - acc) / (k + 1)
        gc.collect()
        return np.clip(acc, 0, 255).astype(np.uint8)

def _stack_sigma_clip(images_bgr: List[np.ndarray],
                      sigma_low: float, sigma_high: float,
                      n_iters: int) -> np.ndarray:
    """
    Sigma-clipping stack:
      1. Compute mean + std across all frames per pixel per channel
      2. Mask pixels outside [mean - sigma_low*std, mean + sigma_high*std]
      3. Recompute mean using only unmasked pixels
      4. Repeat for n_iters iterations
    The standard approach used by DSS, Siril, and other astro stacking software.
    """
    info(f"  Sigma-clipping stack ({len(images_bgr)} frames, "
         f"σ={sigma_low}/{sigma_high}, iters={n_iters})...")

    stack = np.stack([img.astype(np.float32) for img in images_bgr], axis=0)
    # stack shape: (N, H, W, C)

    # Start with all pixels included
    mask = np.ones(stack.shape[0], dtype=bool)   # per-frame mask (simplified)

    # Per-pixel mask: (N, H, W, C)
    valid = np.ones_like(stack, dtype=bool)

    for iteration in range(n_iters):
        # Compute masked mean and std
        # Use np.ma for proper masked-array stats
        masked = np.ma.array(stack, mask=~valid)
        mean = masked.mean(axis=0).data
        std  = masked.std(axis=0).data

        lo = mean - sigma_low  * std
        hi = mean + sigma_high * std

        # Update validity mask
        valid = (stack >= lo[np.newaxis]) & (stack <= hi[np.newaxis])

        n_clipped = np.sum(~valid)
        info(f"    Iter {iteration+1}: clipped {n_clipped:,} pixel-samples")

    # Final mean of valid pixels
    masked_final = np.ma.array(stack, mask=~valid)
    result = masked_final.mean(axis=0).filled(fill_value=0)

    del stack, valid, masked, masked_final
    gc.collect()

    return np.clip(result, 0, 255).astype(np.uint8)


# ══════════════════════════════════════════════════════════════════════════════
# ENHANCEMENT
# ══════════════════════════════════════════════════════════════════════════════

def enhance_image(image: np.ndarray,
                  denoise: bool = True,
                  sharpen: bool = True,
                  stretch: bool = False) -> np.ndarray:
    """
    Post-process the final stacked image.
    - denoise : fastNlMeansDenoisingColored
    - sharpen : unsharp mask via filter2D (Laplacian kernel)
    - stretch : auto histogram stretch (for faint astronomical targets)
    """
    result = image.copy()

    if stretch:
        info("Applying histogram stretch...")
        result = auto_stretch(result)

    if denoise:
        info("Applying denoising...")
        result = cv2.fastNlMeansDenoisingColored(
            result, None,
            h=5, hColor=5,
            templateWindowSize=7,
            searchWindowSize=21
        )

    if sharpen:
        info("Applying unsharp mask...")
        kernel = np.array([[-1, -1, -1],
                           [-1,  9, -1],
                           [-1, -1, -1]], dtype=np.float32)
        result = cv2.filter2D(result, -1, kernel)

    return result


# ══════════════════════════════════════════════════════════════════════════════
# STITCHING
# ══════════════════════════════════════════════════════════════════════════════

def stitch_images(images: List[np.ndarray]) -> np.ndarray:
    """Stitch images into a panorama using cv2.Stitcher."""
    if len(images) == 1:
        return images[0]

    banner("STITCHING PANORAMA", char="-")
    stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
    stitcher.setPanoConfidenceThresh(0.5)
    stitcher.setWaveCorrection(True)
    stitcher.setWaveCorrectKind(cv2.detail.WAVE_CORRECT_HORIZ)

    status, pano = stitcher.stitch(images)

    if status != cv2.Stitcher_OK:
        codes = {
            cv2.Stitcher_ERR_NEED_MORE_IMGS:
                "Need more images with sufficient overlap",
            cv2.Stitcher_ERR_HOMOGRAPHY_EST_FAIL:
                "Homography estimation failed — images may not overlap enough",
            cv2.Stitcher_ERR_CAMERA_PARAMS_ADJUST_FAIL:
                "Camera parameter adjustment failed",
        }
        raise RuntimeError(f"Stitching failed: {codes.get(status, f'code {status}')}")

    ok("Stitching successful")
    return pano


# ══════════════════════════════════════════════════════════════════════════════
# SIFT GROUPING
# ══════════════════════════════════════════════════════════════════════════════

def build_sift_matcher():
    detector = cv2.SIFT_create(nfeatures=5000, contrastThreshold=0.03, edgeThreshold=15)
    FLANN_INDEX_KDTREE = 1
    matcher = cv2.FlannBasedMatcher(
        dict(algorithm=FLANN_INDEX_KDTREE, trees=5),
        dict(checks=50)
    )
    return detector, matcher

def detect_features(images: List[np.ndarray], detector):
    kps, descs = [], []
    for i, img in enumerate(images):
        kp, des = detector.detectAndCompute(img, None)
        kps.append(kp)
        descs.append(des)
        print(f"\r  Feature detection... {i+1}/{len(images)}", end="", flush=True)
    print()
    return kps, descs

def find_overlap_groups(descs: List[np.ndarray], matcher,
                        ratio_thresh: float = 0.7,
                        min_matches: int = 20) -> List[List[int]]:
    n = len(descs)
    match_matrix = np.zeros((n, n), dtype=int)

    for i in range(n):
        for j in range(i + 1, n):
            if descs[i] is None or descs[j] is None:
                continue
            raw = matcher.knnMatch(descs[i], descs[j], k=2)
            good = []
            for pair in raw:
                if len(pair) == 2:
                    m, n2 = pair
                    if m.distance < ratio_thresh * n2.distance:
                        good.append(m)
            match_matrix[i, j] = match_matrix[j, i] = len(good)

    visited = set()
    groups = []
    for i in range(n):
        if i in visited:
            continue
        group = [i]
        visited.add(i)
        for j in range(i + 1, n):
            if j not in visited and match_matrix[i, j] >= min_matches:
                group.append(j)
                visited.add(j)
        groups.append(group)

    return groups


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT SAVING
# ══════════════════════════════════════════════════════════════════════════════

def save_output(image: np.ndarray, output_path: str):
    """
    Save the final image.
    - .jpg/.jpeg : JPEG quality 97
    - .png       : lossless PNG
    - .tif/.tiff : 16-bit TIFF (converts uint8 → uint16 by scaling ×257)
                   Useful for preserving dynamic range for further processing.
    """
    ext = Path(output_path).suffix.lower()

    if ext in (".tif", ".tiff"):
        # Save as 16-bit TIFF for maximum downstream flexibility
        img16 = image.astype(np.uint16) * 257   # 0-255 → 0-65535
        cv2.imwrite(output_path, img16)
        info(f"Saved 16-bit TIFF: {output_path}")
    elif ext in (".jpg", ".jpeg"):
        cv2.imwrite(output_path, image, [cv2.IMWRITE_JPEG_QUALITY, 97])
    elif ext == ".png":
        cv2.imwrite(output_path, image, [cv2.IMWRITE_PNG_COMPRESSION, 6])
    else:
        cv2.imwrite(output_path, image)


# ══════════════════════════════════════════════════════════════════════════════
# FOLDER PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def run_folder_pipeline(folder_path: str,
                        output_path: str,
                        stack_mode: str = "average",
                        align_method: str = "orb",
                        stitch: bool = False,
                        enhance: bool = True,
                        stretch: bool = False,
                        stack_threshold: int = 20,
                        master_dark: Optional[np.ndarray] = None,
                        hot_pixel_thresh: int = 0,
                        sigma_low: float = 2.0,
                        sigma_high: float = 2.0,
                        sigma_iters: int = 3,
                        device: str = "cpu",
                        torch_module=None):
    """
    Full pipeline for stacking a folder of images.

      1  Auto-detect image format in folder
      2  Parallel load all images
      3  Optional: dark subtraction + hot pixel removal
      4  SIFT feature detection + overlap grouping
      5  For each group: align then stack (chosen mode + adaptive batching)
      6  Optional: stitch groups into panorama
      7  Optional: enhance (denoise, sharpen, stretch)
      8  Save + stats
    """
    banner("FOLDER STACKING PIPELINE")
    info(f"Input   : {folder_path}")
    info(f"Output  : {output_path}")
    info(f"Mode    : {stack_mode}  |  Align: {align_method}  |  Stitch: {stitch}")

    # Step 1 & 2 — Detect format + Load
    banner("STEP 1 — Detecting Format & Loading Images", char="-")
    _, paths = detect_folder_format(folder_path)
    images = load_images_parallel(paths)
    info(f"Loaded {len(images)} images  ({images[0].shape[1]}×{images[0].shape[0]} px each)")

    # Step 3 — Calibration
    if master_dark is not None:
        info("Subtracting master dark frame...")
        images = [subtract_dark(img, master_dark) for img in images]
        ok("Dark subtraction done")

    if hot_pixel_thresh > 0:
        info(f"Removing hot pixels (threshold={hot_pixel_thresh})...")
        images = [remove_hot_pixels(img, hot_pixel_thresh) for img in images]
        ok("Hot pixel removal done")

    # Step 4 — SIFT grouping
    banner("STEP 2 — Feature Detection & Grouping (SIFT)", char="-")
    detector, matcher = build_sift_matcher()
    _, descs = detect_features(images, detector)
    groups = find_overlap_groups(descs, matcher, min_matches=stack_threshold)
    info(f"Found {len(groups)} group(s):")
    for i, g in enumerate(groups):
        info(f"  Group {i+1}: {len(g)} image(s)")

    # Step 5 — Align + Stack
    banner("STEP 3 — Aligning & Stacking", char="-")
    batch_size = estimate_safe_batch(images[0].shape, device, torch_module)
    info(f"Adaptive batch size: {batch_size}")

    stacked_results = []
    for gi, group in enumerate(groups):
        group_imgs = [images[i] for i in group]
        info(f"\nGroup {gi+1}/{len(groups)}  ({len(group_imgs)} images)...")

        if align_method != "none" and len(group_imgs) > 1:
            base_gray = cv2.cvtColor(group_imgs[0], cv2.COLOR_BGR2GRAY)
            aligned = [group_imgs[0]]
            for j, img in enumerate(group_imgs[1:], 1):
                aligned.append(align_frame(base_gray, img, align_method))
                print(f"\r    Aligning {j}/{len(group_imgs)-1}...", end="", flush=True)
            print()
            group_imgs = aligned

        # Batch stacking for memory safety
        if len(group_imgs) <= batch_size:
            stacked = stack_images(group_imgs, stack_mode,
                                   sigma_low, sigma_high, sigma_iters,
                                   device, torch_module)
        else:
            # Weighted incremental mean across batches
            running = group_imgs[0].astype(np.float64)
            for b in range(1, len(group_imgs), batch_size):
                batch = group_imgs[b:b + batch_size]
                br = stack_images(batch, stack_mode,
                                  sigma_low, sigma_high, sigma_iters,
                                  device, torch_module).astype(np.float64)
                n_so_far, n_batch = b, len(batch)
                running = (running * n_so_far + br * n_batch) / (n_so_far + n_batch)
                print(f"\r    Batched {min(b+batch_size, len(group_imgs))}/{len(group_imgs)}...",
                      end="", flush=True)
            print()
            stacked = np.clip(running, 0, 255).astype(np.uint8)

        stacked_results.append(stacked)
        ok(f"Group {gi+1} stacked")

    # Step 6 — Stitch or merge
    if stitch and len(stacked_results) > 1:
        final = stitch_images(stacked_results)
    elif len(stacked_results) == 1:
        final = stacked_results[0]
    else:
        info("Merging all groups (average)...")
        final = stack_images(stacked_results, "average", device=device,
                             torch_module=torch_module)

    # Step 7 — Enhance
    if enhance or stretch:
        banner("STEP 4 — Post-Processing", char="-")
        final = enhance_image(final,
                              denoise=enhance, sharpen=enhance, stretch=stretch)

    # Step 8 — Save
    save_output(final, output_path)
    banner("DONE ✓")
    print_image_stats(final, output_path)


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO PIPELINE (MP4, AVI, MOV, etc.)
# ══════════════════════════════════════════════════════════════════════════════

def run_video_pipeline(video_path: str,
                       output_path: str,
                       stack_mode: str = "average",
                       align_method: str = "orb",
                       enhance: bool = True,
                       stretch: bool = False,
                       frame_skip: int = 1,
                       max_frames: Optional[int] = None,
                       master_dark: Optional[np.ndarray] = None,
                       hot_pixel_thresh: int = 0,
                       device: str = "cpu",
                       torch_module=None):
    """
    Stack frames from a standard video file.
    Uses running-sum GPU accumulation for memory efficiency.
    Note: sigma/median modes buffer all frames — use max_frames for long videos.
    """
    banner("VIDEO STACKING PIPELINE")
    info(f"Input      : {video_path}")
    info(f"Mode       : {stack_mode}  |  Align: {align_method}")
    info(f"Frame skip : every {frame_skip}  |  Max: {max_frames or 'unlimited'}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps   = cap.get(cv2.CAP_PROP_FPS)
    info(f"Video info : {total} frames @ {fps:.2f} fps")

    banner("Reading Frames", char="-")

    # Read first frame as reference base
    ret, base_bgr = cap.read()
    if not ret:
        cap.release()
        raise ValueError("Video has no readable frames")

    if master_dark is not None:
        base_bgr = subtract_dark(base_bgr, master_dark)
    if hot_pixel_thresh > 0:
        base_bgr = remove_hot_pixels(base_bgr, hot_pixel_thresh)

    base_gray = cv2.cvtColor(base_bgr, cv2.COLOR_BGR2GRAY)

    # For average: GPU running sum. For others: buffer frames (use max_frames!)
    if stack_mode == "average":
        frames_buf = None
        base_rgb = cv2.cvtColor(base_bgr, cv2.COLOR_BGR2RGB)
        if torch_module is not None:
            t = torch_module
            acc = t.from_numpy(base_rgb).float().to(device)
        else:
            acc = base_rgb.astype(np.float64)
    else:
        frames_buf = [base_bgr]

    count = 1
    fidx  = 1

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if fidx % frame_skip != 0:
            fidx += 1
            continue

        if master_dark is not None:
            frame = subtract_dark(frame, master_dark)
        if hot_pixel_thresh > 0:
            frame = remove_hot_pixels(frame, hot_pixel_thresh)

        if align_method != "none":
            frame = align_frame(base_gray, frame, align_method)

        if stack_mode == "average":
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if torch_module is not None:
                acc = acc + t.from_numpy(rgb).float().to(device)
            else:
                acc = acc + (rgb.astype(np.float64) - acc) / (count + 1)
        else:
            frames_buf.append(frame)

        count += 1
        fidx  += 1

        if count % 50 == 0:
            pct = f"{fidx/total*100:.0f}%" if total > 0 else "?"
            print(f"\r  Processed {count} frames ({pct})...", end="", flush=True)

        if max_frames and count >= max_frames:
            info(f"\nReached max_frames limit ({max_frames})")
            break

    cap.release()
    print(f"\n  Total frames stacked: {count}")

    # Finalise
    if stack_mode == "average":
        if torch_module is not None:
            avg = (acc / count).clamp(0, 255).byte().cpu().numpy()
            if device == "cuda":
                torch_module.cuda.empty_cache()
        else:
            avg = np.clip(acc, 0, 255).astype(np.uint8)
        final = cv2.cvtColor(avg, cv2.COLOR_RGB2BGR)
    else:
        info(f"Running {stack_mode} stack on {len(frames_buf)} buffered frames...")
        final = stack_images(frames_buf, stack_mode,
                             device=device, torch_module=torch_module)

    if enhance or stretch:
        banner("Post-Processing", char="-")
        final = enhance_image(final,
                              denoise=enhance, sharpen=enhance, stretch=stretch)

    save_output(final, output_path)
    banner("DONE ✓")
    print_image_stats(final, output_path)


# ══════════════════════════════════════════════════════════════════════════════
# SER PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def run_ser_pipeline(ser_path: str,
                     output_path: str,
                     stack_mode: str = "sigma",
                     align_method: str = "orb",
                     enhance: bool = True,
                     stretch: bool = True,
                     frame_skip: int = 1,
                     max_frames: Optional[int] = None,
                     master_dark: Optional[np.ndarray] = None,
                     hot_pixel_thresh: int = 30,
                     sigma_low: float = 2.0,
                     sigma_high: float = 2.0,
                     sigma_iters: int = 3,
                     device: str = "cpu",
                     torch_module=None):
    """
    Stack frames from a SER file — the standard format for planetary / lunar /
    solar / deep-sky video astronomy captures.

    Defaults for SER differ from regular video:
      - stack_mode defaults to 'sigma' (best for astro)
      - stretch defaults to True (reveals faint details)
      - hot_pixel_thresh = 30 (common with CMOS sensors)
    """
    banner("SER ASTRONOMICAL STACKING PIPELINE")
    info(f"Input      : {ser_path}")
    info(f"Mode       : {stack_mode}  |  Align: {align_method}")
    info(f"Stretch    : {stretch}  |  Hot px threshold: {hot_pixel_thresh}")

    with SERFile(ser_path) as ser:
        banner("Reading SER Frames", char="-")

        frames = []
        base_gray = None

        for i, (fidx, frame) in enumerate(ser.frames(frame_skip, max_frames)):
            if master_dark is not None:
                frame = subtract_dark(frame, master_dark)
            if hot_pixel_thresh > 0:
                frame = remove_hot_pixels(frame, hot_pixel_thresh)

            if base_gray is None:
                base_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frames.append(frame)
            else:
                if align_method != "none":
                    frame = align_frame(base_gray, frame, align_method)
                frames.append(frame)

            if (i + 1) % 50 == 0:
                print(f"\r  Read {i+1} frames...", end="", flush=True)

        print(f"\n  Total frames read: {len(frames)}")

    # Stack
    banner(f"Stacking {len(frames)} SER frames ({stack_mode})", char="-")
    final = stack_images(frames, stack_mode,
                         sigma_low, sigma_high, sigma_iters,
                         device, torch_module)

    # Post-processing (stretch on by default for SER / astro)
    if enhance or stretch:
        banner("Post-Processing", char="-")
        final = enhance_image(final,
                              denoise=enhance, sharpen=enhance, stretch=stretch)

    save_output(final, output_path)
    banner("DONE ✓")
    print_image_stats(final, output_path)


# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE COLAB
# ══════════════════════════════════════════════════════════════════════════════

def is_colab() -> bool:
    try:
        import google.colab  # noqa
        return True
    except ImportError:
        return False

def colab_setup() -> dict:
    """Interactive Colab prompt. Returns a dict of args."""
    info("Running in Google Colab")
    print("\n  Choose input source:")
    print("  1. Upload images / ZIP / SER / video")
    print("  2. Mount Google Drive")
    print("  3. Enter path manually")

    choice = input("\n  Choice (1/2/3): ").strip()
    input_path = None

    if choice == "1":
        from google.colab import files
        import zipfile, shutil
        uploaded = files.upload()
        input_dir = "/content/ultrastack_input"
        Path(input_dir).mkdir(exist_ok=True)
        for fname in uploaded:
            src = f"/content/{fname}"
            if fname.lower().endswith(".zip"):
                with zipfile.ZipFile(src, "r") as z:
                    z.extractall(input_dir)
                ok(f"Extracted {fname}")
                input_path = input_dir
            else:
                dest = f"{input_dir}/{fname}"
                shutil.move(src, dest)
                input_path = dest if fname.lower().endswith(
                    (".ser",) + tuple(VIDEO_EXTENSIONS)) else input_dir

    elif choice == "2":
        from google.colab import drive
        drive.mount("/content/drive")
        raw = input("  Path to folder/file in Drive: ").strip()
        input_path = raw if raw.startswith("/") else f"/content/drive/MyDrive/{raw}"

    elif choice == "3":
        input_path = input("  Input path (folder, video, or .ser): ").strip()

    output_path = input("  Output filename [stacked_output.tif]: ").strip()
    if not output_path:
        output_path = "/content/stacked_output.tif"
    elif not output_path.startswith("/"):
        output_path = f"/content/{output_path}"

    def ask(prompt, default):
        r = input(f"  {prompt} [{default}]: ").strip()
        return r if r else str(default)

    mode        = ask(f"Stack mode ({'/'.join(STACK_MODES)})", "sigma")
    align       = ask(f"Align method ({'/'.join(ALIGN_MODES)})", "orb")
    stitch      = ask("Stitch panorama? (y/n)", "n").lower() == "y"
    enhance     = ask("Enhance (denoise+sharpen)? (y/n)", "y").lower() != "n"
    stretch     = ask("Auto histogram stretch? (y/n)", "n").lower() == "y"
    skip        = int(ask("Frame skip (video/SER)", "1"))
    max_f       = ask("Max frames (blank=all)", "")
    max_f       = int(max_f) if max_f else None

    return dict(
        input=input_path, output=output_path,
        mode=mode, align=align, stitch=stitch,
        enhance=enhance, stretch=stretch,
        skip=skip, max_frames=max_f,
        threshold=20, dark=None, hot_pixels=0,
        sigma_low=2.0, sigma_high=2.0, sigma_iters=3,
        no_gpu=False
    )


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ultrastack",
        description="GPU-accelerated image / video / SER stacking & stitching",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Stacking modes:
  average   Mean of all frames — classic, fast, GPU-accelerated
  median    Median per pixel   — robust against hot pixels & satellites
  sigma     Sigma-clipping mean — astronomical standard (best SNR)
  maximum   Brightest pixel    — star trails, lightning
  minimum   Darkest pixel      — background extraction

Alignment methods:
  orb       ORB feature matching (fast, good for most subjects)
  ecc       Enhanced Correlation Coefficient (sub-pixel, best for astro)
  none      No alignment

Examples:
  python ultrastack.py --input ./lights --output result.tif --mode sigma --align ecc
  python ultrastack.py --input ./mosaic  --output pano.jpg  --stitch
  python ultrastack.py --input capture.ser --output planet.tif --mode sigma --stretch
  python ultrastack.py --input ./lights --dark ./darks --output result.tif
  python ultrastack.py --input video.mp4 --skip 3 --max-frames 600 --mode average
        """
    )
    io = p.add_argument_group("Input / Output")
    io.add_argument("--input",  "-i", required=False,
                    help="Image folder, video file, or .ser file")
    io.add_argument("--output", "-o", default=None,
                    help="Output path (.jpg/.png/.tif — tif saves 16-bit)")
    io.add_argument("--dark",   default=None, metavar="FOLDER",
                    help="Folder of dark calibration frames for subtraction")

    stack = p.add_argument_group("Stacking")
    stack.add_argument("--mode", default="average",
                       choices=STACK_MODES,
                       help="Stacking algorithm (default: average)")
    stack.add_argument("--sigma-low",   type=float, default=2.0,
                       help="Sigma-clip low  threshold (default: 2.0)")
    stack.add_argument("--sigma-high",  type=float, default=2.0,
                       help="Sigma-clip high threshold (default: 2.0)")
    stack.add_argument("--sigma-iters", type=int, default=3,
                       help="Sigma-clip iterations (default: 3)")

    align = p.add_argument_group("Alignment")
    align.add_argument("--align", "-a", default="none",
                       choices=ALIGN_MODES,
                       help="Alignment method (default: none)")

    post = p.add_argument_group("Post-Processing")
    post.add_argument("--no-enhance", dest="enhance", action="store_false",
                      help="Skip denoising + sharpening")
    post.add_argument("--stretch", action="store_true",
                      help="Auto histogram stretch (for faint astronomical targets)")
    post.add_argument("--stitch", "-s", action="store_true",
                      help="Stitch stacked groups into panorama (folder mode)")
    post.add_argument("--hot-pixels", type=int, default=0, metavar="THRESH",
                      help="Hot pixel removal threshold (0=off, e.g. 30 for astro)")

    vid = p.add_argument_group("Video / SER")
    vid.add_argument("--skip", type=int, default=1, metavar="N",
                     help="Use every Nth frame (default: 1)")
    vid.add_argument("--max-frames", type=int, default=None, metavar="N",
                     help="Stop after N frames")

    misc = p.add_argument_group("Grouping / Misc")
    misc.add_argument("--threshold", type=int, default=20, metavar="N",
                      help="Min SIFT matches to group images (default: 20)")
    misc.add_argument("--no-gpu", action="store_true",
                      help="Force CPU")

    p.set_defaults(enhance=True)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    banner("U L T R A S T A C K   v2", width=66, char="═")
    info(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
    info("GPU-Accelerated Image & Video Stacking / Stitching Pipeline")

    # ── Colab interactive mode ───────────────────────────────────────────────
    if is_colab() and len(sys.argv) == 1:
        banner("Google Colab Detected", char="-")
        cfg = colab_setup()
    else:
        parser = build_parser()
        ns = parser.parse_args()
        if ns.input is None:
            parser.print_help()
            sys.exit(0)
        cfg = vars(ns)

    # ── Resolve output path ──────────────────────────────────────────────────
    if not cfg.get("output"):
        ts = datetime.now().strftime("%m%d_%H%M%S")
        cfg["output"] = f"ultrastack_{ts}.tif"

    # ── Device ───────────────────────────────────────────────────────────────
    banner("System", char="-")
    device, torch_module = setup_device(force_cpu=cfg.get("no_gpu", False))

    # ── Master dark ──────────────────────────────────────────────────────────
    master_dark = None
    if cfg.get("dark"):
        master_dark = make_master_dark(cfg["dark"])

    # ── Detect input type ────────────────────────────────────────────────────
    input_path = Path(cfg["input"])
    ext = input_path.suffix.lower()

    # Shared kwargs
    common = dict(
        output_path    = cfg["output"],
        stack_mode     = cfg.get("mode", "average"),
        align_method   = cfg.get("align", "none"),
        enhance        = cfg.get("enhance", True),
        stretch        = cfg.get("stretch", False),
        master_dark    = master_dark,
        hot_pixel_thresh = cfg.get("hot_pixels", 0),
        device         = device,
        torch_module   = torch_module,
    )

    if input_path.is_dir():
        run_folder_pipeline(
            folder_path     = str(input_path),
            stitch          = cfg.get("stitch", False),
            stack_threshold = cfg.get("threshold", 20),
            sigma_low       = cfg.get("sigma_low", 2.0),
            sigma_high      = cfg.get("sigma_high", 2.0),
            sigma_iters     = cfg.get("sigma_iters", 3),
            **common
        )

    elif ext == SER_EXTENSION:
        run_ser_pipeline(
            ser_path        = str(input_path),
            frame_skip      = cfg.get("skip", 1),
            max_frames      = cfg.get("max_frames"),
            sigma_low       = cfg.get("sigma_low", 2.0),
            sigma_high      = cfg.get("sigma_high", 2.0),
            sigma_iters     = cfg.get("sigma_iters", 3),
            **common
        )

    elif ext in VIDEO_EXTENSIONS:
        run_video_pipeline(
            video_path      = str(input_path),
            frame_skip      = cfg.get("skip", 1),
            max_frames      = cfg.get("max_frames"),
            **common
        )

    else:
        err(f"'{input_path}' is not a recognised folder, video, or .ser file.")
        info(f"Supported video : {', '.join(sorted(VIDEO_EXTENSIONS))}")
        info(f"Supported images: {', '.join(sorted(IMAGE_EXTENSIONS))}")
        info("For a single .ser file, pass it directly as --input.")
        sys.exit(1)

    # ── Colab download ───────────────────────────────────────────────────────
    if is_colab():
        if input("  Download result? (y/n): ").strip().lower() == "y":
            from google.colab import files
            files.download(cfg["output"])
            ok("Download started")


if __name__ == "__main__":
    main()
