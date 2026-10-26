"""Every test runs offline against a saved copy of the Tallyhive mock (tests/fixtures/).

The server reads FIGMA_TOKEN and FIGMA_CACHE when it's imported, so they're set here, before any test imports it:
no token (a cache miss raises instead of calling Figma) and a throwaway copy of the fixtures as the cache.
"""

import os
import shutil
import tempfile
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
URL = "https://www.figma.com/design/TallyhiveDemoFile01/Tallyhive?node-id=0-1"
FRAME = "1:170"

_cache = Path(tempfile.mkdtemp()) / "cache"
shutil.copytree(FIXTURES, _cache)
os.environ["FIGMA_CACHE"] = str(_cache)
os.environ["FIGMA_TOKEN"] = ""
