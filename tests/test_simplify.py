import json

from figma_mcp import simplify

from .conftest import FIXTURES, FRAME

DOC = json.loads((FIXTURES / "TallyhiveDemoFile01.json").read_text())
LAYOUT = simplify.node(simplify.find(DOC["document"], FRAME), DOC["styles"])


def test_frames():
    assert simplify.frames(DOC) == [{"page": "Page 1", "id": FRAME, "name": "Tallyhive / Landing / Desktop", "size": [1440, 1690]}]


def test_auto_layout_becomes_flex():
    nav, hero, features, pricing, footer = LAYOUT["children"]
    assert nav["flex"] == {"direction": "row", "gap": 0, "padding": [24, 120, 24, 120], "justify": "space-between", "align": "center"}
    assert hero["flex"]["direction"] == "column" and hero["flex"]["align"] == "center"
    assert [c["width"] for c in features["children"]] == ["fill"] * 3
    assert sum(c["size"][1] for c in LAYOUT["children"]) == 1690


def test_text_keeps_its_font_colour_and_style_names():
    logo = LAYOUT["children"][0]["children"][0]
    assert logo == {
        "name": "Logo", "type": "text", "color": "#3B5CF6", "text": "Tallyhive",
        "font": {"family": "Inter", "size": 28, "weight": 600, "lineHeight": 36},
        "styles": {"fill": "Brand", "text": "Heading"},
    }


def test_an_icon_is_one_node_not_its_paths():
    chip = LAYOUT["children"][2]["children"][0]["children"][0]
    assert chip["children"] == [{"name": "Icon / bolt", "type": "icon", "id": "1:190", "size": [24, 24]}]
    assert [i["name"] for i in simplify.icons(simplify.find(DOC["document"], FRAME))] == ["Icon / bolt", "Icon / bell", "Icon / chart", "Icon / check"]


def test_the_layout_is_a_fraction_of_the_raw_file():
    assert len(json.dumps(LAYOUT)) * 5 < len(json.dumps(DOC))


def test_tokens_are_css_custom_properties():
    assert simplify.tokens(DOC) == {
        "--color-brand": "#3B5CF6", "--color-ink": "#111827", "--color-muted": "#606B7E",
        "--font-display": "700 56px/64px Inter", "--font-heading": "600 28px/36px Inter",
        "--font-body": "400 18px/28px Inter", "--font-label": "600 16px/24px Inter",
    }


def test_hex_color_with_alpha():
    assert simplify.hex_color({"r": 1, "g": 1, "b": 1, "a": 1}) == "#FFFFFF"
    assert simplify.hex_color({"r": 0, "g": 0, "b": 0, "a": 1}, opacity=0.5) == "#00000080"
