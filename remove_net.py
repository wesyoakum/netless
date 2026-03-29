#!/usr/bin/env python3
"""Remove protective baseball netting from videos and images using OpenCV."""

import argparse
import sys
import os

import cv2
import numpy as np


def build_net_mask(frame, threshold, morph_size, dilate_iterations):
    """Detect the net by thresholding dark pixels and filtering thin strands."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Threshold for dark pixels (the black netting)
    _, dark_mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)

    # Morphological opening to remove large dark blobs (people, umpires, etc.)
    # and keep only thin strand structures
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (morph_size, morph_size)
    )
    opened = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, kernel)

    # Subtract opened from dark_mask to isolate thin structures
    # Large blobs survive opening; thin strands don't
    net_mask = cv2.subtract(dark_mask, opened)

    # Dilate slightly to cover soft/blurry edges from out-of-focus netting
    if dilate_iterations > 0:
        dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        net_mask = cv2.dilate(net_mask, dilate_kernel, iterations=dilate_iterations)

    return net_mask


def inpaint_frame(frame, net_mask, radius):
    """Inpaint masked pixels using Telea algorithm."""
    return cv2.inpaint(frame, net_mask, radius, cv2.INPAINT_TELEA)


def process_image(input_path, output_path, args):
    """Process a single image."""
    frame = cv2.imread(input_path)
    if frame is None:
        print(f"Error: Cannot read image '{input_path}'", file=sys.stderr)
        sys.exit(1)

    net_mask = build_net_mask(frame, args.threshold, args.morph_size, args.dilate)
    result = inpaint_frame(frame, net_mask, args.radius)

    cv2.imwrite(output_path, result)
    print(f"Saved result to {output_path}")

    if args.save_mask:
        mask_path = _mask_path(output_path)
        cv2.imwrite(mask_path, net_mask)
        print(f"Saved mask to {mask_path}")

    if args.preview:
        combined = np.hstack([frame, result])
        cv2.imshow("Before | After", combined)
        print("Press any key to close preview...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def process_video(input_path, output_path, args):
    """Process a video frame by frame."""
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video '{input_path}'", file=sys.stderr)
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    mask_writer = None
    if args.save_mask:
        mask_path = _mask_path(output_path)
        mask_writer = cv2.VideoWriter(mask_path, fourcc, fps, (width, height), False)
        print(f"Mask video will be saved to {mask_path}")

    frame_num = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_num += 1
        net_mask = build_net_mask(frame, args.threshold, args.morph_size, args.dilate)
        result = inpaint_frame(frame, net_mask, args.radius)

        out.write(result)
        if mask_writer is not None:
            mask_writer.write(net_mask)

        if frame_num % 10 == 0 or frame_num == total_frames:
            pct = frame_num / total_frames * 100 if total_frames > 0 else 0
            print(f"\rProcessing: frame {frame_num}/{total_frames} ({pct:.1f}%)", end="", flush=True)

    print()
    cap.release()
    out.release()
    if mask_writer is not None:
        mask_writer.release()

    print(f"Saved result to {output_path}")


def _mask_path(output_path):
    """Generate a mask file path from the output path."""
    base, ext = os.path.splitext(output_path)
    return f"{base}_mask{ext}"


def _default_output(input_path):
    """Generate default output path."""
    base, ext = os.path.splitext(input_path)
    return f"{base}_clean{ext}"


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}


def main():
    parser = argparse.ArgumentParser(
        description="Remove baseball netting from images and videos using OpenCV."
    )
    parser.add_argument("input", help="Path to input image or video")
    parser.add_argument("-o", "--output", help="Path to output file (default: <input>_clean.<ext>)")
    parser.add_argument("--threshold", type=int, default=50,
                        help="Dark pixel threshold 0-255 (default: 50). Lower = less aggressive.")
    parser.add_argument("--radius", type=int, default=5,
                        help="Inpainting radius in pixels (default: 5)")
    parser.add_argument("--morph-size", type=int, default=3,
                        help="Morphological kernel size for filtering large blobs (default: 3)")
    parser.add_argument("--dilate", type=int, default=1,
                        help="Dilation iterations to cover blurry net edges (default: 1)")
    parser.add_argument("--save-mask", action="store_true",
                        help="Save the detected net mask for debugging")
    parser.add_argument("--preview", action="store_true",
                        help="Show before/after comparison (images only)")

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: File '{args.input}' not found", file=sys.stderr)
        sys.exit(1)

    ext = os.path.splitext(args.input)[1].lower()
    output_path = args.output or _default_output(args.input)

    if ext in IMAGE_EXTS:
        process_image(args.input, output_path, args)
    elif ext in VIDEO_EXTS:
        process_video(args.input, output_path, args)
    else:
        print(f"Error: Unsupported file extension '{ext}'", file=sys.stderr)
        print(f"Supported images: {', '.join(sorted(IMAGE_EXTS))}")
        print(f"Supported videos: {', '.join(sorted(VIDEO_EXTS))}")
        sys.exit(1)


if __name__ == "__main__":
    main()
