"""Autonomous tool-use loop: prompt in, CorelDRAW drawing out."""
from __future__ import annotations

import os

import anthropic

from .backend import Backend
from .tools import TOOLS, dispatch

SYSTEM = """You are an autonomous vector-drawing agent controlling CorelDRAW.
Plan the drawing, then build it with the tools: start with new_document, draw
back-to-front (backgrounds first), use consistent #RRGGBB palettes, keep every
shape inside the page, and finish by calling save (and export if asked).
Coordinates are millimetres, origin bottom-left, Y up. Reply briefly when done."""


def run(prompt: str, backend: Backend, *, model: str | None = None,
        max_steps: int = 60, verbose: bool = True) -> str:
    client = anthropic.Anthropic()
    model = model or os.environ.get("CORELAGENT_MODEL", "claude-opus-5-5")
    messages: list[dict] = [{"role": "user", "content": prompt}]

    for _ in range(max_steps):
        resp = client.messages.create(
            model=model, max_tokens=4096, system=SYSTEM, tools=TOOLS, messages=messages)
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")

        results = []
        for block in resp.content:
            if block.type == "tool_use":
                out = dispatch(backend, block.name, block.input)
                if verbose:
                    print(f"{block.name}({block.input}) -> {out}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": out})
        messages.append({"role": "user", "content": results})
    return "stopped: max_steps reached"
