"""Talking to Figma: three REST calls, every response cached on disk.

The three calls: the file, a PNG of a frame, and the frame's icons as SVG.
Figma's free plan allows very few file reads a month, so every response is
saved under .cache/ and read from there afterwards. Delete the cache (or pass
refresh=True) to fetch again.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import httpx

API = "https://api.figma.com/v1"


def file_key(url_or_key: str) -> str:
    """The file key from a Figma link (figma.com/design/<key>/...) or the key itself."""
    m = re.search(r"figma\.com/(?:design|file|proto)/([A-Za-z0-9]+)", url_or_key)
    return m.group(1) if m else url_or_key.strip()


class Figma:
    def __init__(self, token: str | None, cache_dir: Path):
        self.token = token
        self.cache = cache_dir
        self.cache.mkdir(parents=True, exist_ok=True)

    def _get(self, path: str, **params) -> httpx.Response:
        if not self.token:
            raise RuntimeError("FIGMA_TOKEN is not set and this file isn't cached yet.")
        print(f"figma: GET {path}", file=sys.stderr)  # every real call is logged
        headers = {"X-Figma-Token": self.token}
        r = httpx.get(f"{API}{path}", params=params, headers=headers, timeout=60)
        r.raise_for_status()
        return r

    def file(self, key: str, refresh: bool = False) -> dict:
        """The whole file as JSON (one call, then cached)."""
        path = self.cache / f"{key}.json"
        if refresh or not path.exists():
            path.write_bytes(self._get(f"/files/{key}").content)
        return json.loads(path.read_text())

    def frame_png(self, key: str, node_id: str, refresh: bool = False) -> bytes:
        """A frame rendered as PNG (one call for the URL, then cached)."""
        path = self.cache / f"{key}-{node_id.replace(':', '-')}.png"
        if refresh or not path.exists():
            r = self._get(f"/images/{key}", ids=node_id, format="png", scale=1)
            url = r.json()["images"][node_id]
            path.write_bytes(httpx.get(url, timeout=60).content)
        return path.read_bytes()

    def svgs(self, key: str, node_ids: list[str], refresh: bool = False) -> dict:
        """Several nodes exported as SVG in one call, then cached."""
        path = self.cache / f"{key}-icons.json"
        cached = {} if refresh or not path.exists() else json.loads(path.read_text())
        missing = [i for i in node_ids if i not in cached]
        if missing:
            r = self._get(f"/images/{key}", ids=",".join(missing), format="svg")
            for i, url in r.json()["images"].items():
                cached[i] = httpx.get(url, timeout=60).text
            path.write_text(json.dumps(cached))
        return {i: cached[i] for i in node_ids}
