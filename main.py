"""CLI: python main.py "draw a red logo with a blue circle" [--dry-run]"""
import argparse

from coreldraw_agent.agent import run
from coreldraw_agent.backend import MockBackend


def main() -> None:
    ap = argparse.ArgumentParser(description="Autonomous CorelDRAW agent")
    ap.add_argument("prompt")
    ap.add_argument("--dry-run", action="store_true", help="don't touch CorelDRAW")
    ap.add_argument("--model")
    a = ap.parse_args()
    if a.dry_run:
        backend = MockBackend()
    else:
        from coreldraw_agent.backend import CorelBackend
        backend = CorelBackend()
    print(run(a.prompt, backend, model=a.model))


if __name__ == "__main__":
    main()
