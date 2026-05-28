from __future__ import annotations

from pathlib import Path


def main() -> None:
    try:
        import imageio.v3 as iio
    except Exception as e:
        raise SystemExit(
            "Missing dependency. Run:\n"
            "  .venv/bin/pip install imageio imageio-ffmpeg pillow\n"
            "Then rerun:\n"
            "  .venv/bin/python scripts/extract_video_frames.py"
        ) from e

    root = Path(__file__).resolve().parents[1]
    video_path = root / "tmp" / "charles_video" / "charles_review.mov"
    out_dir = root / "tmp" / "charles_video" / "frames"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        raise SystemExit(f"Video not found: {video_path}")

    # Extract a handful of frames across the timeline.
    # We avoid decoding every frame to keep this fast.
    # Indices below are "reasonable guesses"; if video is short/long, we'll adjust on error.
    indices = [0, 150, 300, 450, 600, 750, 900, 1050, 1200, 1350]
    written = 0

    for idx in indices:
        try:
            frame = iio.imread(video_path, index=idx)
        except Exception:
            # If index out of range or decode issue, skip.
            continue
        out_path = out_dir / f"frame_{idx:05d}.png"
        iio.imwrite(out_path, frame)
        written += 1

    if written == 0:
        raise SystemExit("No frames were extracted. The video may use an unsupported codec.")

    print(f"Extracted {written} frames to: {out_dir}")


if __name__ == "__main__":
    main()

