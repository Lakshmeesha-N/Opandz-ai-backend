# theme_resolver.py
#
# Parses theme/theme1.xml (if present) so we can resolve:
#   - wdThemeColor enum  + brightness  → concrete hex RGB
#   - theme font slot name             → concrete font family name
#
# Built once per document and passed into block_extractor as an optional arg.
#
# Public API
# ----------
#   resolver = ThemeResolver(doc)
#   hex_rgb  = resolver.resolve_color(theme_color_enum, brightness)  # str | None
#   font_name = resolver.resolve_font(slot_name)                      # str | None

from __future__ import annotations

from typing import Dict, Optional
from docx.oxml.ns import qn

# python-docx WD_COLOR_INDEX is not the same as theme colors.
# Theme color slot names in OOXML (w:themeColor / a:clrScheme child tags):
_THEME_COLOR_SLOTS = {
    "dark1":  "dk1",
    "light1": "lt1",
    "dark2":  "dk2",
    "light2": "lt2",
    "accent1": "accent1",
    "accent2": "accent2",
    "accent3": "accent3",
    "accent4": "accent4",
    "accent5": "accent5",
    "accent6": "accent6",
    "hyperlink": "hlink",
    "followedHyperlink": "folHlink",
}

# python-docx exposes WD_COLOR.theme_color as an enum; its name attr matches
# the lowercase OOXML slot name (with some variations).  We normalise below.


def _normalise_slot(slot: str) -> str:
    """Map various representations to the a:clrScheme child tag name."""
    lower = slot.lower().replace("-", "").replace("_", "")
    _MAP = {
        "dark1": "dk1", "dk1": "dk1",
        "light1": "lt1", "lt1": "lt1",
        "dark2": "dk2", "dk2": "dk2",
        "light2": "lt2", "lt2": "lt2",
        "accent1": "accent1", "accent2": "accent2",
        "accent3": "accent3", "accent4": "accent4",
        "accent5": "accent5", "accent6": "accent6",
        "hyperlink": "hlink", "hlink": "hlink",
        "followedhyperlink": "folhlink", "folhlink": "folhlink",
        # WD_THEME_COLOR enum names (python-docx >= 0.9)
        "background1": "lt1", "background2": "lt2",
        "text1": "dk1", "text2": "dk2",
    }
    return _MAP.get(lower, lower)


def _apply_brightness(hex_rgb: str, brightness: float | None) -> str:
    """
    Apply OOXML luminance-shift brightness to a hex RGB string.

    brightness > 0 → lighten (blend toward white by that fraction)
    brightness < 0 → darken  (blend toward black by that fraction)
    brightness == 0 or None → no change
    """
    if not hex_rgb or len(hex_rgb) != 6:
        return hex_rgb
    if not brightness:
        return hex_rgb

    try:
        r = int(hex_rgb[0:2], 16)
        g = int(hex_rgb[2:4], 16)
        b = int(hex_rgb[4:6], 16)
    except ValueError:
        return hex_rgb

    if brightness > 0:
        # lighten: blend toward 255
        r = round(r + (255 - r) * brightness)
        g = round(g + (255 - g) * brightness)
        b = round(b + (255 - b) * brightness)
    else:
        # darken: blend toward 0
        factor = 1 + brightness  # e.g. brightness=-0.25 → factor=0.75
        r = round(r * factor)
        g = round(g * factor)
        b = round(b * factor)

    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))

    return f"{r:02X}{g:02X}{b:02X}"


# Namespace for DrawingML (theme XML)
_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _a(tag: str) -> str:
    return f"{{{_A_NS}}}{tag}"


class ThemeResolver:
    """
    Reads theme/theme1.xml once and provides concrete color/font lookups.

    Falls back gracefully when theme XML is absent.
    """

    def __init__(self, doc) -> None:
        # { normalised_slot → hex_rgb_string (no #) }
        self._colors: Dict[str, str] = {}
        # { slot_name → font_family_string }
        self._fonts: Dict[str, str] = {}

        self._load(doc)

    def _load(self, doc) -> None:
        try:
            # python-docx exposes the theme part via the document part's relationships
            theme_part = doc.part.theme_part  # may raise AttributeError if no theme
        except AttributeError:
            theme_part = None

        if theme_part is None:
            # Try alternative access path
            try:
                from docx.opc.constants import RELATIONSHIP_TYPE as RT
                rel = next(
                    (r for r in doc.part.rels.values()
                     if "theme" in r.reltype),
                    None,
                )
                if rel is not None:
                    theme_part = rel.target_part
            except Exception:
                return

        if theme_part is None:
            return

        try:
            root = theme_part._element  # lxml Element
        except AttributeError:
            try:
                root = theme_part.element
            except AttributeError:
                return

        self._parse_colors(root)
        self._parse_fonts(root)

    def _parse_colors(self, root) -> None:
        # a:theme/a:themeElements/a:clrScheme
        clr_scheme = root.find(f".//{_a('clrScheme')}")
        if clr_scheme is None:
            return

        for child in clr_scheme:
            # child.tag looks like {ns}accent1
            local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            # Color is either <a:srgbClr val="..."/> or <a:sysClr lastClr="..."/>
            srgb = child.find(_a("srgbClr"))
            if srgb is not None:
                val = srgb.get("val")
                if val:
                    self._colors[local] = val.upper()
                continue

            sys_clr = child.find(_a("sysClr"))
            if sys_clr is not None:
                last = sys_clr.get("lastClr")
                if last:
                    self._colors[local] = last.upper()

    def _parse_fonts(self, root) -> None:
        # a:theme/a:themeElements/a:fontScheme
        font_scheme = root.find(f".//{_a('fontScheme')}")
        if font_scheme is None:
            return

        for group_tag in ("majorFont", "minorFont"):
            group = font_scheme.find(_a(group_tag))
            if group is None:
                continue
            # <a:latin typeface="..."/>
            latin = group.find(_a("latin"))
            if latin is not None:
                typeface = latin.get("typeface")
                if typeface:
                    # Map common slot aliases used in w:rFonts
                    for alias in (group_tag, group_tag.lower()):
                        self._fonts[alias] = typeface
                    # OOXML uses majorAscii / minorAscii etc — handled via slot name
                    prefix = "major" if "major" in group_tag else "minor"
                    self._fonts[prefix] = typeface

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve_color(self, theme_color, brightness: float | None) -> str | None:
        """
        theme_color: a WD_COLOR enum value or its string name / OOXML slot name.
        Returns a 6-char uppercase hex RGB string, or None.
        """
        if theme_color is None:
            return None

        # Get the string representation — python-docx enums have .name
        if hasattr(theme_color, "name"):
            slot_raw = theme_color.name
        else:
            slot_raw = str(theme_color)

        slot = _normalise_slot(slot_raw)
        hex_rgb = self._colors.get(slot)
        if hex_rgb is None:
            return None

        return _apply_brightness(hex_rgb, brightness)

    def resolve_font(self, slot_name: str) -> str | None:
        """
        slot_name: value of w:asciiTheme / w:hAnsiTheme (e.g. "majorAscii", "minorHAnsi").
        Returns the concrete font family name, or None.
        """
        if not slot_name:
            return None

        # Normalise: "majorAscii" → "major", "minorHAnsi" → "minor"
        lower = slot_name.lower()
        if lower.startswith("major"):
            key = "major"
        elif lower.startswith("minor"):
            key = "minor"
        else:
            key = lower

        return self._fonts.get(key) or self._fonts.get(slot_name)
