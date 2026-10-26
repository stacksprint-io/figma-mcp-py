"""From Figma's file JSON to what a developer needs to build the page.

Figma describes every node with dozens of fields. Claude needs the layout (auto layout becomes
flexbox), the text, the colours and the sizes. Everything else is dropped.
"""

from __future__ import annotations


def hex_color(c: dict, opacity: float = 1.0) -> str:
    r, g, b = (round(c[k] * 255) for k in "rgb")
    a = c.get("a", 1) * opacity
    return f"#{r:02X}{g:02X}{b:02X}" + ("" if a >= 0.999 else f"{round(a * 255):02X}")


def solid_fill(paints: list[dict]) -> str | None:
    for p in paints or []:
        if p.get("type") == "SOLID" and p.get("visible", True):
            return hex_color(p["color"], p.get("opacity", 1))
    return None


JUSTIFY = {"MIN": "start", "CENTER": "center", "MAX": "end", "SPACE_BETWEEN": "space-between"}
ALIGN = {"MIN": "start", "CENTER": "center", "MAX": "end", "BASELINE": "baseline"}


def node(n: dict, styles: dict) -> dict | None:
    """One node, simplified. Hidden nodes are skipped."""
    if not n.get("visible", True):
        return None
    box = n.get("absoluteBoundingBox") or {}
    size = [round(box.get("width", 0)), round(box.get("height", 0))]
    if n["name"].startswith("Icon /"):  # an icon is one asset, not its vector paths: export_icons gives the SVG
        return {"name": n["name"], "type": "icon", "id": n["id"], "size": size}
    out: dict = {"name": n["name"], "type": n["type"].lower(), "size": size}

    if n.get("layoutMode") in ("HORIZONTAL", "VERTICAL"):
        out["flex"] = {
            "direction": "row" if n["layoutMode"] == "HORIZONTAL" else "column",
            "gap": n.get("itemSpacing", 0),
            "padding": [n.get(k, 0) for k in ("paddingTop", "paddingRight", "paddingBottom", "paddingLeft")],
            "justify": JUSTIFY.get(n.get("primaryAxisAlignItems", "MIN")),
            "align": ALIGN.get(n.get("counterAxisAlignItems", "MIN")),
        }
    if n.get("layoutGrow") == 1 or n.get("layoutSizingHorizontal") == "FILL":
        out["width"] = "fill"

    if fill := solid_fill(n.get("fills")):
        out["background" if n["type"] != "TEXT" else "color"] = fill
    if (stroke := solid_fill(n.get("strokes"))) and n.get("strokeWeight"):
        out["border"] = f"{n['strokeWeight']:g}px solid {stroke}"
    if n.get("cornerRadius"):
        out["radius"] = n["cornerRadius"]

    if n["type"] == "TEXT":
        s = n.get("style", {})
        out["text"] = n.get("characters", "")
        out["font"] = {"family": s.get("fontFamily"), "size": s.get("fontSize"), "weight": s.get("fontWeight"), "lineHeight": round(s.get("lineHeightPx", 0))}
        if s.get("textAlignHorizontal") not in (None, "LEFT"):
            out["textAlign"] = s["textAlignHorizontal"].lower()
        del out["size"]

    for kind, sid in (n.get("styles") or {}).items():
        if sid in styles:
            out.setdefault("styles", {})[kind] = styles[sid]["name"]

    kids = [c for c in (node(k, styles) for k in n.get("children", [])) if c]
    if kids:
        out["children"] = kids
    return out


def find(n: dict, node_id: str) -> dict | None:
    if n.get("id") == node_id:
        return n
    for k in n.get("children", []):
        if hit := find(k, node_id):
            return hit
    return None


def frames(doc: dict) -> list[dict]:
    """Top-level frames on every page: what you'd hand to a developer."""
    return [
        {"page": p["name"], "id": f["id"], "name": f["name"], "size": [round(f["absoluteBoundingBox"]["width"]), round(f["absoluteBoundingBox"]["height"])]}
        for p in doc["document"]["children"]
        for f in p.get("children", [])
        if f["type"] in ("FRAME", "COMPONENT", "SECTION")
    ]


def tokens(doc: dict) -> dict:
    """Colour and text styles as CSS custom properties, read from the nodes that use them."""
    styles, seen = doc.get("styles", {}), {}

    def walk(n: dict) -> None:
        for kind, sid in (n.get("styles") or {}).items():
            if sid in styles and sid not in seen:
                if kind == "fill" and (c := solid_fill(n.get("fills"))):
                    seen[sid] = c
                elif kind == "text" and n.get("style"):
                    s = n["style"]
                    seen[sid] = f"{s['fontWeight']} {round(s['fontSize'])}px/{round(s['lineHeightPx'])}px {s['fontFamily']}"
        for k in n.get("children", []):
            walk(k)

    walk(doc["document"])
    slug = lambda name: name.lower().replace(" ", "-").replace("/", "-")
    return {f"--{'color' if styles[sid]['styleType'] == 'FILL' else 'font'}-{slug(styles[sid]['name'])}": v for sid, v in seen.items()}


def icons(n: dict) -> list[dict]:
    """Every icon in a frame (nodes named "Icon / ..."), once per name."""
    found: dict[str, dict] = {}

    def walk(x: dict) -> None:
        if x["name"].startswith("Icon /"):
            found.setdefault(x["name"], {"name": x["name"], "id": x["id"]})
            return
        for k in x.get("children", []):
            walk(k)

    walk(n)
    return list(found.values())
