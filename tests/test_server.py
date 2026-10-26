"""The five tools, called the way Claude Code calls them: through an MCP client (FastMCP's in-memory one)."""

import asyncio
import json

from fastmcp import Client

from figma_mcp.server import mcp

from .conftest import FRAME, URL


def call(tool, **args):
    async def go():
        async with Client(mcp) as c:
            return await c.call_tool(tool, args)
    return asyncio.run(go())


def test_five_read_only_tools():
    async def go():
        async with Client(mcp) as c:
            return await c.list_tools()
    tools = {t.name: t for t in asyncio.run(go())}
    assert set(tools) == {"list_frames", "get_layout", "get_tokens", "export_icons", "render_frame"}
    assert all(t.description for t in tools.values())  # Claude reads these to pick a tool


def test_list_frames():
    assert call("list_frames", file_url=URL).structured_content["result"][0]["id"] == FRAME


def test_get_layout():
    layout = call("get_layout", file_url=URL, frame_id=FRAME).structured_content
    assert [c["name"] for c in layout["children"]] == ["Nav", "Hero", "Features", "Pricing", "Footer"]


def test_get_layout_unknown_frame():
    result = asyncio.run(_raw("get_layout", file_url=URL, frame_id="9:999"))
    assert result.is_error and "list_frames" in result.content[0].text


async def _raw(tool, **args):
    async with Client(mcp) as c:
        return await c.call_tool(tool, args, raise_on_error=False)


def test_get_tokens():
    assert call("get_tokens", file_url=URL).structured_content["--color-brand"] == "#3B5CF6"


def test_export_icons():
    icons = call("export_icons", file_url=URL, frame_id=FRAME).structured_content
    assert set(icons) == {"Icon / bolt", "Icon / bell", "Icon / chart", "Icon / check"}
    assert all(svg.lstrip().startswith("<svg") for svg in icons.values())


def test_render_frame_is_an_image():
    image = call("render_frame", file_url=URL, frame_id=FRAME).content[0]
    assert image.type == "image" and image.mime_type == "image/png"
