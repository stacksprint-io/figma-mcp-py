"""A Figma MCP server: five read-only tools that give Claude a design it can build from.

Run: python -m figma_mcp.server   (stdio; register with `claude mcp add`)
Needs FIGMA_TOKEN (a read-only personal access token, in the environment or in .env) the first time a file is read.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from . import simplify
from .figma import Figma, file_key

load_dotenv()  # FIGMA_TOKEN from .env, if you keep it there
CACHE = Path(os.environ.get("FIGMA_CACHE", Path(__file__).resolve().parent.parent / ".cache"))
figma = Figma(os.environ.get("FIGMA_TOKEN"), CACHE)
mcp = FastMCP("figma")


@mcp.tool()
def list_frames(file_url: str) -> list[dict]:
    """The frames in a Figma file (page, id, name, size). Start here, then pass a frame id to the other tools."""
    return simplify.frames(figma.file(file_key(file_url)))


@mcp.tool()
def get_layout(file_url: str, frame_id: str) -> dict:
    """One frame as a compact layout tree: auto layout as flexbox (direction, gap, padding, justify, align),
    text with its font, colours as hex, sizes in px. Build the page from this."""
    doc = figma.file(file_key(file_url))
    frame = simplify.find(doc["document"], frame_id)
    if frame is None:
        raise ValueError(f"No frame {frame_id} in this file. Call list_frames first.")
    return simplify.node(frame, doc.get("styles", {}))


@mcp.tool()
def get_tokens(file_url: str) -> dict:
    """The file's colour and text styles as CSS custom properties, to put in :root."""
    return simplify.tokens(figma.file(file_key(file_url)))


@mcp.tool()
def export_icons(file_url: str, frame_id: str) -> dict[str, str]:
    """Every icon in the frame as inline SVG, keyed by the icon's name. Paste them into the page as-is."""
    key = file_key(file_url)
    frame = simplify.find(figma.file(key)["document"], frame_id)
    found = simplify.icons(frame)
    svg = figma.svgs(key, [i["id"] for i in found])
    return {i["name"]: svg[i["id"]] for i in found}


@mcp.tool()
def render_frame(file_url: str, frame_id: str) -> Image:
    """A picture of the frame (PNG), so you can see the design you're building and compare against it."""
    return Image(data=figma.frame_png(file_key(file_url), frame_id), format="png")


if __name__ == "__main__":
    mcp.run()
