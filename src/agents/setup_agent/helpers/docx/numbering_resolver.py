# numbering_resolver.py
#
# Parses numbering.xml (if present) into fast lookup tables.
# Built once per document; passed into block_extractor as an optional arg.
#
# Public API
# ----------
#   resolver = NumberingResolver(doc)          # doc: python-docx Document
#   info = resolver.resolve(num_id, level)
#   # → {"num_fmt": "bullet", "lvl_text": "•", "start": 1} | None
#
#   list_type = resolver.list_type(num_id, level)
#   # → "bullet" | "numbered"

from __future__ import annotations

from typing import Dict, Optional, Tuple
from docx.oxml.ns import qn


class NumberingResolver:
    """
    Cross-references numbering.xml so callers can resolve
    (numId, ilvl) → { numFmt, lvlText, start }.

    Falls back gracefully when numbering.xml is absent (e.g. plain docs).
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, doc) -> None:
        # { num_id_str → abstract_num_id_str }
        self._num_to_abstract: Dict[str, str] = {}

        # { abstract_num_id_str → { level_str → { numFmt, lvlText, start } } }
        self._abstract_levels: Dict[str, Dict[str, dict]] = {}

        # per-num level overrides: { num_id_str → { level_str → {...} } }
        self._num_level_overrides: Dict[str, Dict[str, dict]] = {}

        self._load(doc)

    def _load(self, doc) -> None:
        try:
            num_part = doc.part.numbering_part
        except AttributeError:
            return  # document has no numbering.xml — nothing to load

        if num_part is None:
            return

        root = num_part.element  # lxml Element for <w:numbering>

        # 1. Parse all abstractNum definitions
        for abstract_num in root.findall(qn("w:abstractNum")):
            abstract_id = abstract_num.get(qn("w:abstractNumId"))
            if abstract_id is None:
                continue

            levels: Dict[str, dict] = {}
            for lvl in abstract_num.findall(qn("w:lvl")):
                ilvl = lvl.get(qn("w:ilvl"))
                if ilvl is None:
                    continue

                num_fmt_el = lvl.find(qn("w:numFmt"))
                lvl_text_el = lvl.find(qn("w:lvlText"))
                start_el = lvl.find(qn("w:start"))

                num_fmt = num_fmt_el.get(qn("w:val")) if num_fmt_el is not None else None
                lvl_text = lvl_text_el.get(qn("w:val")) if lvl_text_el is not None else None
                start_val = start_el.get(qn("w:val")) if start_el is not None else None

                levels[ilvl] = {
                    "num_fmt": num_fmt,
                    "lvl_text": lvl_text,
                    "start": int(start_val) if start_val is not None and start_val.isdigit() else 1,
                }

            self._abstract_levels[abstract_id] = levels

        # 2. Parse num → abstractNum mappings + optional lvlOverride
        for num in root.findall(qn("w:num")):
            num_id = num.get(qn("w:numId"))
            if num_id is None:
                continue

            abstract_ref = num.find(qn("w:abstractNumId"))
            if abstract_ref is not None:
                self._num_to_abstract[num_id] = abstract_ref.get(qn("w:val"), "")

            # lvlOverride lets individual num instances override level details
            overrides: Dict[str, dict] = {}
            for override in num.findall(qn("w:lvlOverride")):
                ilvl = override.get(qn("w:ilvl"))
                if ilvl is None:
                    continue
                lvl_el = override.find(qn("w:lvl"))
                if lvl_el is None:
                    continue

                num_fmt_el = lvl_el.find(qn("w:numFmt"))
                lvl_text_el = lvl_el.find(qn("w:lvlText"))
                start_el = lvl_el.find(qn("w:startOverride")) or lvl_el.find(qn("w:start"))

                entry: dict = {}
                if num_fmt_el is not None:
                    entry["num_fmt"] = num_fmt_el.get(qn("w:val"))
                if lvl_text_el is not None:
                    entry["lvl_text"] = lvl_text_el.get(qn("w:val"))
                if start_el is not None:
                    val = start_el.get(qn("w:val"))
                    entry["start"] = int(val) if val is not None and val.isdigit() else 1
                if entry:
                    overrides[ilvl] = entry

            if overrides:
                self._num_level_overrides[num_id] = overrides

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def resolve(self, num_id: Optional[str], level: Optional[str]) -> Optional[dict]:
        """
        Return the effective level definition for (num_id, ilvl) or None.

        The returned dict always has keys: num_fmt, lvl_text, start.
        """
        if num_id is None or level is None:
            return None

        abstract_id = self._num_to_abstract.get(num_id)
        if abstract_id is None:
            return None

        base = dict(self._abstract_levels.get(abstract_id, {}).get(level, {}))
        if not base:
            return None

        # Apply per-num level overrides on top
        override = self._num_level_overrides.get(num_id, {}).get(level, {})
        base.update(override)

        return base  # {num_fmt, lvl_text, start}

    def list_type(self, num_id: Optional[str], level: Optional[str]) -> str:
        """
        Returns "bullet" if numFmt == "bullet", otherwise "numbered".
        Falls back to "numbered" when the info cannot be resolved.
        """
        info = self.resolve(num_id, level)
        if info and info.get("num_fmt") == "bullet":
            return "bullet"
        return "numbered"
