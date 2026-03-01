<div align="center">

```
██╗   ██╗██╗  ████████╗██████╗  █████╗ ███████╗████████╗ █████╗  ██████╗██╗  ██╗
██║   ██║██║  ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝
██║   ██║██║     ██║   ██████╔╝███████║███████╗   ██║   ███████║██║     █████╔╝ 
██║   ██║██║     ██║   ██╔══██╗██╔══██║╚════██║   ██║   ██╔══██║██║     ██╔═██╗ 
╚██████╔╝███████╗██║   ██║  ██║██║  ██║███████║   ██║   ██║  ██║╚██████╗██║  ██╗
 ╚═════╝ ╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
```

**GPU-Accelerated Image & Video Stacking Pipeline**  
*For Astronomy, Photography, and Everything In Between*

---

![Python](https://img.shields.io/badge/Python-3.8%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-GPU%20Accelerated-ee4c2c?style=for-the-badge&logo=pytorch&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Vision%20Engine-5c3ee8?style=for-the-badge&logo=opencv&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-Desktop%20GUI-41cd52?style=for-the-badge&logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-f5a623?style=for-the-badge)
</div>

---

## What is UltraStack?

UltraStack is a **professional-grade image stacking engine** that combines dozens, hundreds, or even thousands of images or video frames into a single, noise-reduced, detail-rich result. It runs from both a **sleek desktop GUI** (`UI.py`) and a **powerful command-line interface** (`ultrastack.py`), and supports everything from a folder of JPEGs to raw astronomical SER captures.

Whether you're a **photographer** reducing noise from burst shots, a **timelapse creator** merging video frames, or an **amateur astronomer** stacking planetary or deep-sky captures — UltraStack handles it all with the same pipeline.

---

## Why Stack Images?

Every digital image contains random noise. Stacking works on a simple statistical principle: **noise is random, signal is consistent**. When you average 100 frames of the same scene, random noise cancels out while the real detail reinforces itself. The result is an image that looks like it was taken with a far more expensive camera in far better conditions.

| Frames Stacked | Noise Reduction (SNR gain) |
|:--------------:|:---------------------------:|
| 4 frames | 2× |
| 16 frames | 4× |
| 64 frames | 8× |
| 256 frames | 16× |

UltraStack takes this further with **sigma-clipping** — intelligently removing satellites, cosmic rays, hot pixels, and other outliers frame by frame, so only the true signal remains.

---

## Features at a Glance

### Input Sources
| Type | Supported Formats |
|------|-------------------|
| **Image Folders** | JPG, JPEG, PNG, TIFF, BMP, WEBP, FIT/FITS, PPM, PGM, EXR |
| **Video Files** | MP4, AVI, MOV, MKV, WMV, WEBM, M4V, FLV, TS, MTS, M2TS |
| **Astronomical** | SER — full support for Mono, all Bayer patterns, RGB, BGR, YUV; 8-bit & 16-bit |

### Stacking Modes
| Mode | Best For | How It Works |
|------|----------|--------------|
| **Average** | General use, noise reduction | Incremental Welford mean — GPU-accelerated. O(1) RAM regardless of frame count |
| **Median** | Removing satellites, hot pixels, cosmic rays | Horizontal-strip chunked median — never builds a full N×H×W array |
| **Sigma-clipping** | Deep-sky astronomy (DSS/Siril standard) | Online Welford statistics + iterative outlier rejection. Zero RAM scaling with N |
| **Maximum** | Star trails, lightning, aurora | Running max per pixel — pure streaming |
| **Minimum** | Background extraction, gradient removal | Running min per pixel — pure streaming |

### Alignment Methods
| Method | Description |
|--------|-------------|
| **None** | Skip alignment — for pre-aligned stacks or tracked mounts |
| **ORB** | ORB feature matching + RANSAC homography. Fast, robust, works on most subjects |
| **ECC** | Enhanced Correlation Coefficient — sub-pixel accuracy. Best for star fields. Falls back to ORB if convergence fails |

### Pipeline Features
- **SIFT + FLANN intelligent grouping** — automatically clusters overlapping images before stacking
- **Panorama stitching** — stitch stacked groups into a seamless panorama
- **Dark frame calibration** — median-stack a folder of darks and subtract from every light
- **Hot pixel removal** — replace hot pixels with local 3×3 median
- **Histogram stretch** — auto-levels for revealing faint astronomical targets
- **Post-processing** — NLM denoising + unsharp mask sharpening
- **16-bit TIFF output** — full dynamic range preservation for downstream processing in PixInsight, Siril, Lightroom
- **⚡ Quick Stack mode** — skip SIFT grouping for 10–20× faster preview stacking
- **Google Colab support** — interactive mode with Drive mount and file upload
- **RAM-safe architecture** — reads images in chunks sized to available memory; never crashes from OOM

---

## Project Structure

```
UltraStack/
├── ultrastack.py     ← Core engine: all stacking, alignment, and pipeline logic
└── UI.py             ← Desktop GUI built with PyQt5
```

Both files are self-contained. The GUI imports the engine — place them in the same folder.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/NuclearVenom/ultrastack.git
cd ultrastack
```

### 2. Install dependencies

```bash
pip install opencv-contrib-python numpy torch tqdm PyQt5
```

**Optional — FITS file support (astronomical):**
```bash
pip install astropy
```

**GPU acceleration** requires a CUDA-compatible NVIDIA GPU with matching PyTorch build. Visit [pytorch.org](https://pytorch.org/get-started/locally/) and select your CUDA version:

```bash
# Example for CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

> If no GPU is available, UltraStack runs fully on CPU. All features work — GPU only accelerates the average stack mode.

---

## Using the Desktop GUI (`UI.py`)

Launch the GUI with:

```bash
python UI.py
```

### Splash Screen

On launch, a minimal animated splash screen appears while UltraStack probes your GPU. Micro-stars drift across a black background, and the loading status types itself out in real time. When the GPU probe finishes, the splash fades out and the main window appears.

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER: Title · GPU Status Badge · Developer Info              │
├────────────────────────────────┬────────────────────────────────┤
│  LEFT PANEL                    │  RIGHT PANEL                   │
│  ─ Drop Zone                   │  ─ Processing Log (console)    │
│  ─ Input / Output paths        │  ─ Progress bar                │
│  ─ Dark frame folder           │  ─ System / Diagnostics log    │
│  ─ Tabs:                       │                                │
│      Stacking                  │                                │
│      Alignment                 │                                │
│      Video / SER               │                                │
│      Post-Process              │                                │
│      Quick Stack               │                                │
│      Advanced                  │                                │
├────────────────────────────────┴────────────────────────────────┤
│  BOTTOM BAR: Input type label · ⬛ Stop · ▶ Run UltraStack     │
└─────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Usage

#### Step 1 — Load your input

**Option A — Drag & Drop**  
Drag a folder, video file, or `.ser` file into the drop zone at the top of the left panel. The input field populates automatically.

**Option B — Browse**  
Click `📁 Browse` to open a folder picker. For video or SER files, the picker opens a file dialog instead.

**Option C — Type/paste**  
Paste any full path directly into the Input field.

The bottom bar shows what was detected: `📁 Folder`, `🔭 SER`, or `🎬 Video`.

---

#### Step 2 — Set output path

Type a filename in the Output field or click `💾 Save as`. The **extension controls the format**:

| Extension | Format | Notes |
|-----------|--------|-------|
| `.tif` / `.tiff` | 16-bit TIFF | Best for further processing in PixInsight, Siril, Lightroom |
| `.png` | Lossless PNG | Good for sharing, no quality loss |
| `.jpg` / `.jpeg` | JPEG quality 97 | Smallest file size |

---

#### Step 3 — Choose your settings

**⚗ Stacking Tab**

- **Stack mode** — choose from Average, Median, Sigma, Maximum, Minimum (see table above)
- **Sigma settings** — if sigma mode is selected, tune σ-low, σ-high, and iterations
- **Stitch panorama** — merge stacked groups into a panorama (requires image overlap)
- **SIFT group threshold** — minimum feature matches to consider two images as part of the same group

**🎯 Alignment Tab**

- **Alignment method** — None / ORB / ECC
- **Max ORB features** — increase for low-contrast images (default 5000 is good for most cases)

**🎬 Video / SER Tab**

- **Frame skip** — use every Nth frame (skip=2 uses 50% of frames, skip=5 uses 20%)
- **Max frames** — cap the total frames processed (0 = unlimited)

**✨ Post-Process Tab**

- **Denoise + Sharpen** — apply NLM denoising and unsharp mask to the final result
- **Auto histogram stretch** — rescale intensities to reveal faint detail (recommended for astronomy)
- **Hot pixel threshold** — remove hot pixels above this deviation from local median (0 = off; 30 is good for CMOS sensors)

**⚡ Quick Stack Tab**

Enable Quick Stack for a dramatically faster pipeline:
- Skips SIFT feature detection and image grouping entirely
- Runs a pure incremental average stack
- Optional ORB alignment
- Ideal for previewing results, CPU-only machines, or large video/SER files

**⚙ Advanced Tab**

- **Force CPU** — disable GPU even if available (useful for VRAM-limited scenarios)
- Dependency info and memory notes

---

#### Step 4 — Optional: Dark Frame Subtraction

In the Input/Output section, enter a folder of dark calibration frames (same ISO/gain, exposure, temperature as your lights). UltraStack will:
1. Median-stack all darks into a master dark frame
2. Subtract it from every light frame before stacking

---

#### Step 5 — Run

Click `▶ Run UltraStack`. The job runs in a background thread — the UI stays fully responsive. Progress streams into the Processing Log on the right in real time, colour-coded:

| Colour | Meaning |
|--------|---------|
| 🔵 Blue | Standard progress messages |
| 🟢 Green | Success / DONE |
| 🟡 Yellow | Warnings / Quick Stack |
| 🔴 Red | Errors |
| 🟣 Purple | Step headers |

Click `⬛ Stop` to abort at any time.

When finished, a popup confirms the output path and the Processing Log shows final image statistics (resolution, file size, min/max/mean/std).

---

## Using the CLI (`ultrastack.py`)

The engine runs entirely standalone without the GUI. Every feature is accessible via command-line arguments.

### Basic syntax

```bash
python ultrastack.py --input <path> --output <file> [options]
```

### All options

```
Input / Output:
  --input  / -i     Path to image folder, video file, or .ser file
  --output / -o     Output filename (.jpg / .png / .tif)
  --dark            Folder of dark calibration frames

Stacking:
  --mode            average | median | sigma | maximum | minimum  (default: average)
  --sigma-low       Sigma-clip low threshold   (default: 2.0)
  --sigma-high      Sigma-clip high threshold  (default: 2.0)
  --sigma-iters     Sigma-clip iterations      (default: 3)

Alignment:
  --align / -a      none | orb | ecc           (default: none)

Post-Processing:
  --no-enhance      Skip denoising + sharpening
  --stretch         Apply auto histogram stretch
  --stitch / -s     Stitch stacked groups into panorama
  --hot-pixels      Hot pixel removal threshold (0=off, e.g. 30)

Video / SER:
  --skip            Use every Nth frame         (default: 1)
  --max-frames      Stop after N frames

Grouping / Misc:
  --threshold       Min SIFT matches to group   (default: 20)
  --no-gpu          Force CPU mode
```

### Usage Examples

**Stack a folder of images (auto-detect format):**
```bash
python ultrastack.py --input ./frames --output result.png
```

**Astronomical deep-sky stacking (best quality):**
```bash
python ultrastack.py --input ./lights --output deep.tif \
  --mode sigma --align ecc --stretch --hot-pixels 30
```

**With dark frame subtraction:**
```bash
python ultrastack.py --input ./lights --dark ./darks \
  --output result.tif --mode sigma --align orb
```

**Stack a SER planetary capture:**
```bash
python ultrastack.py --input capture.ser --output planet.tif \
  --mode sigma --align orb --stretch
```

**Stack a video, every 3rd frame, max 500 frames:**
```bash
python ultrastack.py --input timelapse.mp4 \
  --skip 3 --max-frames 500 --output timelapse_stack.jpg
```

**Create a panorama from stacked groups:**
```bash
python ultrastack.py --input ./mosaic_tiles --output pano.jpg --stitch
```

**Maximum stack for star trails:**
```bash
python ultrastack.py --input ./star_trail_frames --output trails.jpg \
  --mode maximum --no-enhance
```

**Force CPU for low VRAM systems:**
```bash
python ultrastack.py --input ./lights --output result.tif --no-gpu
```

---

## Google Colab

UltraStack detects Colab automatically. Simply run the script with no arguments and an interactive wizard guides you through the setup:

```python
# In a Colab cell:
!python ultrastack.py
```

The wizard offers:
1. **Upload files** — directly from your computer (supports ZIP archives, automatically extracted)
2. **Google Drive** — mount Drive and point to a folder or file
3. **Manual path** — type any `/content/` path

After processing, you're prompted to download the result directly to your computer.

**Recommended Colab settings for large datasets:**
- Use a T4 GPU runtime for best performance
- Stack mode: `sigma` or `average`
- For very large images (6K+), use `--no-gpu` if VRAM is insufficient
- Use `--max-frames` to limit SER/video processing in memory-constrained sessions

---

## How It Works — The Full Pipeline

### Folder Pipeline

```
1. SCAN          Detect dominant image format in folder (JPG/PNG/TIFF/etc.)
                 Compute safe chunk size from available RAM

2. SIFT PASS     Load each image → downsample to 800px thumbnail → extract SIFT descriptors
                 Delete full-res image immediately after descriptor extraction
                 (This is the key RAM optimization — a 6K image becomes 2 MB for SIFT)

3. GROUPING      FLANN-based descriptor matching → build overlap matrix
                 Cluster images into groups by feature similarity

4. STACK LOOP    For each group, one image at a time:
                 → Load full-res
                 → Apply dark subtraction (if enabled)
                 → Remove hot pixels (if enabled)
                 → Align to reference frame (ORB / ECC)
                 → Incorporate into Welford running accumulator
                 → Delete image, gc.collect() — memory returned to OS before next load

5. MERGE         Combine group results (average or stitch)

6. POST-PROCESS  Histogram stretch → NLM denoise → unsharp mask

7. SAVE          JPG quality 97 / lossless PNG / 16-bit TIFF
```

### Video Pipeline

```
1. OPEN          VideoCapture → read first frame as alignment reference
                 Compute safe chunk size

2. STREAM        For each frame (respecting skip + max_frames):
                 → Apply calibration
                 → Align to reference
                 → Average/max/min: update Welford accumulator instantly (O(1) RAM)
                   Sigma/median: fill chunk buffer → flush + merge when full

3. FINALIZE      Clip accumulator → post-process → save
```

### SER Pipeline

```
1. PARSE HEADER  178-byte SER header → extract dimensions, pixel depth, color ID
                 Handle all Bayer patterns (RGGB/GRBG/GBRG/BGGR), Mono, RGB, BGR
                 Support 8-bit and 16-bit pixel depths

2. STREAM FRAMES Generator reads one frame at a time from disk
                 Debayer raw frames, normalize 16→8-bit
                 Same calibration + alignment + accumulation as video pipeline

3. SAVE          16-bit TIFF by default (preserving full bit depth for astro post-processing)
```

### RAM Safety Architecture

UltraStack was specifically designed to never crash from out-of-memory, even on Google Colab's 12 GB RAM with no swap:

- **`_available_ram_mb()`** — reads `/proc/meminfo` on Linux/Colab (no psutil needed), Windows via psutil, with a safe 800 MB fallback
- **`_safe_chunk_size()`** — uses 12% of available RAM per chunk, accounting for 17 bytes/pixel (uint8 source + float64 accumulator + float32 temp + mask overhead)
- **SIFT on thumbnails** — 800px long edge maximum; a 50 MP image becomes 2 MB for feature extraction
- **Explicit `gc.collect()` after every image** — forces Python to return memory to OS before the next image loads
- **Welford online algorithm** — running mean never needs more than 2×(H×W×C) floats regardless of N

---

## Stacking Mode Selection Guide

```
What are you shooting?
│
├─ Stars / Deep-sky (nebulae, galaxies, clusters)
│   └─ mode: sigma  |  align: ecc  |  stretch: on  |  hot-pixels: 30
│
├─ Planets / Moon / Sun (SER capture)
│   └─ mode: sigma  |  align: orb  |  stretch: on  |  hot-pixels: 30
│
├─ Landscape / Nature (burst shots, handheld)
│   └─ mode: average  |  align: orb  |  enhance: on
│
├─ Star Trails
│   └─ mode: maximum  |  align: none  |  enhance: off
│
├─ Timelapse (video frames)
│   └─ mode: average  |  align: orb  |  skip: 2–5
│
├─ Background Extraction helper
│   └─ mode: minimum  |  align: none
│
└─ Quick Preview / CPU-only machine
    └─ Enable ⚡ Quick Stack tab
```

---

## Output Format Guide

| You want… | Use |
|-----------|-----|
| Further processing in PixInsight / Siril / Lightroom | `.tif` (16-bit, maximum dynamic range) |
| Sharing online / social media | `.jpg` (quality 97, small file) |
| Lossless sharing | `.png` |
| Archiving the full result | `.tif` |

---

## Troubleshooting

**GUI won't launch**
```bash
pip install PyQt5
python UI.py
```

**"Cannot import ultrastack"**  
Make sure `ultrastack.py` and `UI.py` are in the same folder. The GUI imports the engine from the same directory.

**GPU not detected / CUDA error**  
The GPU badge in the header shows `● CPU` with a note in the System log. This usually means your PyTorch CUDA build doesn't match your installed CUDA version. Fix:
```bash
# Check your CUDA version
nvidia-smi

# Reinstall matching PyTorch from pytorch.org
pip install torch --index-url https://download.pytorch.org/whl/cu<YOUR_CUDA_VERSION>
```
UltraStack runs perfectly on CPU — no action required if GPU isn't critical.

**Colab crashes with "RAM exhausted"**  
This typically happens with very large images (6K+). The chunked pipeline handles this automatically, but if it still crashes:
- Use `--no-gpu` to avoid CUDA memory overhead
- Use `--mode average` (lowest RAM of all modes)
- Use `--max-frames 200` to limit SER/video processing
- Restart the runtime to clear leaked memory from previous runs

**FITS files not loading**
```bash
pip install astropy
```

**"No supported images found in folder"**  
The folder contains mixed formats or unsupported extensions. UltraStack uses the most common extension. Ensure all images share the same extension.

**Stitching failed**  
Images need at least 20–30% overlap. Increase overlap or lower `--threshold` to 10.

---

## Requirements Summary

| Package | Purpose | Required |
|---------|---------|----------|
| `opencv-contrib-python` | Image I/O, alignment, stitching, SIFT/ORB | ✅ Yes |
| `numpy` | Array math, stacking core | ✅ Yes |
| `torch` | GPU acceleration for average stack | ✅ Yes (CPU fallback if missing) |
| `PyQt5` | Desktop GUI (`UI.py`) | ✅ For GUI only |
| `tqdm` | Progress bars | ✅ Yes |
| `astropy` | FITS/FIT astronomical image loading | Optional |
| `psutil` | Better RAM detection | Optional (has fallback) |

**Python version:** 3.8 or newer

---

## Acknowledgements

UltraStack builds on the shoulders of the open source computer vision and astronomy communities. The sigma-clipping algorithm mirrors the approach used by **DeepSkyStacker**, **Siril**, and **PixInsight** — the gold standards of astronomical image processing. The SER format parser follows the original **LUCAM-RECORDER** specification.

---

<div align="center">

*Built with obsession for both the technical and the beautiful.*  
*Every photon counts.*

**[github.com/NuclearVenom](https://github.com/NuclearVenom)**

</div>
