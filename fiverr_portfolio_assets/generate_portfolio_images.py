#!/usr/bin/env python3
"""Generate two 1024x768 portfolio images with 100% fictional sample data (Fiverr-safe)."""
import subprocess
import struct
from pathlib import Path

W, H = 1024, 768
OUT_DIR = Path(__file__).resolve().parent


def rgb(r, g, b):
    return bytes((r, g, b))


def blend(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_rect(pix, x0, y0, x1, y1, color):
    r, g, b = color
    for y in range(max(0, y0), min(H, y1)):
        row = y * W * 3
        for x in range(max(0, x0), min(W, x1)):
            i = row + x * 3
            pix[i] = r
            pix[i + 1] = g
            pix[i + 2] = b


def draw_text_simple(pix, lines, x, y, color, line_h=22):
    """Very small bitmap font using block characters (7 segments style simplified: use lines as bars)."""
    r, g, b = color
    cy = y
    for line in lines:
        for i, ch in enumerate(line[:90]):
            cx = x + i * 7
            if cx + 6 >= W:
                break
            if ch == " ":
                continue
            # 5x7 dot for any char (readable enough at distance)
            draw_rect(pix, cx, cy, cx + 5, cy + 12, (r, g, b))
        cy += line_h
    return cy


def fill_gradient(pix, top, bottom):
    for y in range(H):
        t = y / max(H - 1, 1)
        c = blend(top, bottom, t)
        draw_rect(pix, 0, y, W, y + 1, c)


def write_ppm(path: Path, pix: bytearray):
    with path.open("wb") as f:
        f.write(f"P6\n{W} {H}\n255\n".encode("ascii"))
        f.write(pix)


def ppm_to_png(ppm: Path, png: Path):
    subprocess.run(
        ["sips", "-s", "format", "png", str(ppm), "--out", str(png)],
        check=True,
        capture_output=True,
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Image 1: Lead list sample (spreadsheet look) ---
    pix1 = bytearray(W * H * 3)
    fill_gradient(pix1, (248, 250, 252), (226, 232, 240))
    # Header bar
    draw_rect(pix1, 0, 0, W, 88, (15, 23, 42))
    # Title area (white text simulated with light blocks - use thicker bars for title)
    draw_rect(pix1, 32, 28, 700, 62, (59, 130, 246))
    draw_rect(pix1, 32, 28, 698, 60, (30, 41, 59))
    # Subtitle strip
    draw_rect(pix1, 32, 66, 920, 82, (51, 65, 85))

    # "Table" header row
    y0 = 110
    draw_rect(pix1, 24, y0, W - 24, y0 + 36, (241, 245, 249))
    draw_rect(pix1, 24, y0 + 36, W - 24, H - 48, (255, 255, 255))
    draw_rect(pix1, 24, y0, W - 24, y0 + 2, (148, 163, 184))

    rows = [
        "B2B LEAD LIST (SAMPLE ONLY — FICTIONAL DATA)",
        "Clean CSV / Excel  •  Any niche + location",
        "",
        "Business Name          City       State   Category      Phone",
        "----------------------------------------------------------------",
        "Aurora Wellness Spa    Austin     TX      Medical spa   (555) 010-1001",
        "Northline Dental Care  Denver     CO      Dental        (555) 010-1002",
        "Summit Home Services     Seattle    WA      Contractor    (555) 010-1003",
        "Harbor Legal Group       Miami      FL      Law firm      (555) 010-1004",
        "Pine Retail Co           Chicago    IL      Retail        (555) 010-1005",
        "",
        "Footer: Sample preview only — not real businesses or contacts.",
    ]
    y = 118
    for i, line in enumerate(rows):
        col = (15, 23, 42) if i < 3 else (51, 65, 85)
        if i >= 3 and i <= 4:
            col = (71, 85, 105)
        lh = 26 if i < 3 else 22
        draw_text_simple(pix1, [line], 36, y, col, line_h=lh)
        y += lh + 4

    ppm1 = OUT_DIR / "_tmp_portfolio_leads.ppm"
    png1 = OUT_DIR / "fiverr_portfolio_01_lead_list_sample.png"
    write_ppm(ppm1, pix1)
    ppm_to_png(ppm1, png1)
    ppm1.unlink(missing_ok=True)

    # --- Image 2: Checklist / scope ---
    pix2 = bytearray(W * H * 3)
    fill_gradient(pix2, (255, 255, 255), (241, 245, 249))
    draw_rect(pix2, 0, 0, W, 100, (15, 23, 42))
    lines2 = [
        "WHAT I NEED TO START (SAMPLE SLIDE)",
        "",
        "  1. Niche / industry",
        "  2. City, state, or ZIPs",
        "  3. Lead count",
        "  4. Must-have columns",
        "  5. Filters (rating, reviews, keywords)",
        "  6. Output: CSV or Excel",
        "",
        "Fast delivery  •  Consistent formatting  •  Clear communication",
        "",
        "SAMPLE ONLY — for Fiverr portfolio preview.",
    ]
    y = 120
    for line in lines2:
        col = (248, 250, 252) if y < 140 else (30, 41, 59)
        if y >= 140 and line.strip() and line[0].isdigit():
            col = (37, 99, 235)
        elif y >= 140:
            col = (51, 65, 85)
        draw_text_simple(pix2, [line], 48, y, col, line_h=28)
        y += 32

    ppm2 = OUT_DIR / "_tmp_portfolio_checklist.ppm"
    png2 = OUT_DIR / "fiverr_portfolio_02_scope_checklist.png"
    write_ppm(ppm2, pix2)
    ppm_to_png(ppm2, png2)
    ppm2.unlink(missing_ok=True)

    print("Wrote:", png1)
    print("Wrote:", png2)


if __name__ == "__main__":
    main()
