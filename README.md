# Netless

Remove protective baseball netting from videos and images using OpenCV.

Designed for footage shot from behind home plate at outdoor baseball games,
where the black braided netting is slightly out of focus (closer to the camera
than the field).

## How It Works

1. **Threshold** — dark pixels (the black net) are isolated from the frame
2. **Morphological filtering** — large dark regions (people, umpires, shadows) are removed, keeping only thin strand structures
3. **Dilation** — the mask is expanded slightly to cover soft/blurry net edges caused by shallow depth of field
4. **Inpainting** — masked pixels are filled in using OpenCV's Telea algorithm, which reconstructs the area from surrounding pixels

## Web App

Open `index.html` in a browser — no server or installation required. OpenCV.js
loads from CDN and everything runs client-side.

1. Choose an image or video file
2. Adjust sliders (threshold, radius, morph size, dilate)
3. Click **Process**
4. Click **Save Result** to download

Check **Show Mask** to see exactly which pixels are detected as netting.

## CLI Tool

### Installation

```bash
pip install -r requirements.txt
```

### Usage

#### Images

```bash
# Basic usage — outputs photo_clean.jpg
python remove_net.py photo.jpg

# Custom output path
python remove_net.py photo.jpg -o photo_no_net.jpg

# Save the detected mask for debugging
python remove_net.py photo.jpg --save-mask

# Show before/after preview window
python remove_net.py photo.jpg --preview
```

#### Videos

```bash
# Process a video — outputs game_clean.mp4
python remove_net.py game.mp4

# With tuned parameters
python remove_net.py game.mp4 --threshold 60 --radius 7
```

## Parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--threshold` | 50 | Dark pixel threshold (0–255). Higher values detect more pixels as "net" but may catch non-net dark areas. |
| `--radius` | 5 | Inpainting radius in pixels. Larger values fill wider gaps but may blur details. |
| `--morph-size` | 3 | Morphological kernel size for filtering out large dark blobs. Increase if players/umpires are being detected as net. |
| `--dilate` | 1 | Dilation iterations. Increase if net edges remain visible after processing. |
| `--save-mask` | — | Save the detected net mask alongside the output for inspection. |
| `--preview` | — | Show a before/after comparison window (images only). |

## Tuning Tips

- **Net still visible?** Raise `--threshold` (try 60–80) and/or increase `--dilate` to 2.
- **Too much removed (players/dark areas affected)?** Lower `--threshold` (try 30–40) or increase `--morph-size` to 5–7 to better filter large blobs.
- **Inpainted areas look blurry?** Reduce `--radius` to 3. Smaller radius preserves more detail but may leave artifacts.
- **Use `--save-mask`** to visualize exactly what the tool detects as netting. White pixels in the mask are what gets inpainted.
- For **video**, process a short clip first to dial in parameters before running on the full game.
