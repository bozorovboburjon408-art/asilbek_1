"""CLI: python main.py "draw a red logo with a blue circle" [--dry-run]"""
import argparse

from coreldraw_agent.agent import run
from coreldraw_agent.backend import MockBackend


def main() -> None:
    ap = argparse.ArgumentParser(description="Autonomous CorelDRAW agent")
    ap.add_argument("prompt", nargs="?", help="what to draw (agent mode)")
    ap.add_argument("--image", help="laser mode: trace this image into cut contours")
    ap.add_argument("--width", type=float, default=200, help="laser: part width in mm")
    ap.add_argument("--material", type=float, default=3, help="laser: material thickness in mm")
    ap.add_argument("--invert", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="don't touch CorelDRAW")
    ap.add_argument("--model")
    a = ap.parse_args()
    if a.dry_run:
        backend = MockBackend()
    else:
        from coreldraw_agent.backend import CorelBackend
        backend = CorelBackend()
    if a.image:
        from coreldraw_agent.laser import run_image
        res = run_image(a.image, a.width, backend, material_mm=a.material, invert=a.invert)
        print(f"{len(res.parts)} part(s), {res.width_mm:.0f}x{res.height_mm:.0f} mm; SVG next to the image")
        for w in res.warnings:
            print("WARNING:", w)
    elif a.prompt:
        print(run(a.prompt, backend, model=a.model))
    else:
        ap.error("give a prompt or --image")


if __name__ == "__main__":
    main()
