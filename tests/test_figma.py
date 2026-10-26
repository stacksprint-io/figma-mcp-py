import httpx
import pytest

from figma_mcp.figma import Figma, file_key

from .conftest import FIXTURES


@pytest.mark.parametrize("url", [
    "https://www.figma.com/design/TallyhiveDemoFile01/Tallyhive?node-id=0-1&t=abc",
    "https://www.figma.com/file/TallyhiveDemoFile01/Tallyhive",
    "figma.com/proto/TallyhiveDemoFile01/Tallyhive",
    "TallyhiveDemoFile01",
], ids=["design-link", "file-link", "proto-link", "bare-key"])
def test_file_key_from_any_link(url):
    assert file_key(url) == "TallyhiveDemoFile01"


def test_cached_reads_never_call_figma(monkeypatch):
    def no_network(*a, **k):
        raise AssertionError("called Figma")
    monkeypatch.setattr(httpx, "get", no_network)
    f = Figma(token="not-used", cache_dir=FIXTURES)
    assert f.file("TallyhiveDemoFile01")["name"] == "Tallyhive"
    assert f.frame_png("TallyhiveDemoFile01", "1:170")[:8] == b"\x89PNG\r\n\x1a\n"
    assert set(f.svgs("TallyhiveDemoFile01", ["1:190", "1:216"])) == {"1:190", "1:216"}


def test_cache_miss_without_a_token_says_so(tmp_path):
    with pytest.raises(RuntimeError, match="FIGMA_TOKEN"):
        Figma(token=None, cache_dir=tmp_path).file("SomeOtherFile")


def test_a_miss_is_one_call_then_cached(tmp_path, monkeypatch):
    calls = []

    def fake_get(url, **k):
        calls.append(url)
        return httpx.Response(200, content=b'{"name": "Fresh"}', request=httpx.Request("GET", url))
    monkeypatch.setattr(httpx, "get", fake_get)
    f = Figma(token="t", cache_dir=tmp_path)
    assert f.file("NewFile")["name"] == "Fresh"
    assert f.file("NewFile")["name"] == "Fresh"
    assert calls == ["https://api.figma.com/v1/files/NewFile"]
