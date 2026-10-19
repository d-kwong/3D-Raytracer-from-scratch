#!/usr/bin/env python3
"""Capture one cycle of the unchanged banana.c program as a terminal-style GIF."""

import argparse
import os
from pathlib import Path
import pty
import selectors
import shlex
import subprocess
import termios
import time

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ROWS, COLUMNS, FRAME_COUNT = 20, 40, 63


def capture(binary, timeout):
    """Use a terminal for line-buffered stdout; stop after the first 63 blocks."""
    master, slave = pty.openpty()
    settings = termios.tcgetattr(slave)
    settings[1] &= ~termios.OPOST
    termios.tcsetattr(slave, termios.TCSANOW, settings)
    process = None
    selector = selectors.DefaultSelector()
    pending = b""
    lines = []
    try:
        process = subprocess.Popen([str(binary)], stdout=slave, stderr=subprocess.PIPE)
        os.close(slave)
        slave = None
        os.set_blocking(master, False)
        selector.register(master, selectors.EVENT_READ)
        deadline = time.monotonic() + timeout
        while len(lines) < ROWS * FRAME_COUNT:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError(f"Capture timed out after {timeout:g} seconds")
            events = selector.select(min(remaining, 0.25))
            if not events:
                if process.poll() is not None:
                    raise RuntimeError("banana.c exited before one cycle was captured")
                continue
            try:
                chunk = os.read(master, 65536)
            except OSError as error:
                raise RuntimeError("Terminal closed before capture completed") from error
            if not chunk:
                raise RuntimeError("Unexpected end of terminal output")
            pending += chunk
            while b"\n" in pending and len(lines) < ROWS * FRAME_COUNT:
                line, pending = pending.split(b"\n", 1)
                if len(line) != COLUMNS or any(c not in b" .:-=+*#%@" for c in line):
                    raise RuntimeError(f"Unexpected original output row: {line!r}")
                lines.append(line.decode("ascii"))
        return [lines[i:i + ROWS] for i in range(0, len(lines), ROWS)]
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
            try:
                process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
        selector.close()
        os.close(master)
        if slave is not None:
            os.close(slave)


def font_at(path, size):
    if path:
        return ImageFont.truetype(str(path), size)
    for candidate in (
        "/System/Library/Fonts/Menlo.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
    ):
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    raise RuntimeError("No monospace font found; supply --font /path/to/font.ttf")


def draw_frames(blocks, font):
    cell_width = round(font.getlength("M"))
    line_height = 26
    padding, header = 24, 48
    images = []
    for block in blocks:
        image = Image.new("RGB", (COLUMNS * cell_width + padding * 2,
                                  ROWS * line_height + padding * 2 + header), "#10151d")
        draw = ImageDraw.Draw(image)
        draw.text((padding, 12), "banana.c | terminal output", font=font, fill="#8291a3")
        draw.line((padding, 45, image.width - padding, 45), fill="#293441")
        for row, line in enumerate(block):
            # Each glyph comes directly from the program's printed ASCII rows.
            for column, char in enumerate(line):
                draw.text((padding + column * cell_width, header + padding + row * line_height),
                          char, font=font, fill="#f4d35e")
        images.append(image)
    return images


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/images/banana-terminal.gif")
    parser.add_argument("--font", type=Path, help="Monospace TrueType/OpenType font")
    parser.add_argument("--timeout", type=float, default=15,
                        help="Maximum capture time in seconds (default: 15)")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    binary = build / "banana"
    command = shlex.split(os.environ.get("CC", "cc")) + [
        "-O2", "-std=gnu11", str(ROOT / "experiments/banana.c"), "-lm", "-o", str(binary)]
    subprocess.run(command, check=True, timeout=30)
    blocks = capture(binary, args.timeout)
    (build / "banana-frames.txt").write_text(
        "\n".join(line for block in blocks for line in block) + "\n", encoding="ascii")
    images = draw_frames(blocks, font_at(args.font, 20))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(args.output, save_all=True, append_images=images[1:], duration=100,
                   loop=0, optimize=False, disposal=2)
    with Image.open(args.output) as check:
        if check.n_frames != FRAME_COUNT or check.info.get("loop") != 0:
            raise RuntimeError("GIF verification failed")
        for index in range(check.n_frames):
            check.seek(index)
            if check.info.get("duration") != 100:
                raise RuntimeError("Unexpected GIF frame duration")
        print(f"Captured {check.n_frames} frames, {check.size[0]}x{check.size[1]}, "
              f"100 ms/frame, looping: {args.output}")
    print(f"Raw printed rows: {build / 'banana-frames.txt'}")


if __name__ == "__main__":
    main()
