"""B4 conservative script-consistency check, NOT language identification.

Arabic-script Persian/Urdu/Pashto can pass an Arabic *script* check.  Therefore
passing this guard never proves a declared source language or translation.
"""
from __future__ import annotations

from unicodedata import name


def script_consistent(text: str, declared_language: str) -> bool:
    """Reject obvious mislabelled/garbled English and Arabic source excerpts.

    Ignore numerals, symbols and punctuation. Allow mixed-script proper names,
    but demand a clear majority of letter characters match the declared script.
    """
    if not isinstance(text, str) or not isinstance(declared_language, str):
        return False
    language = declared_language.split("-")[0].lower()
    if language not in {"en", "ar"}:
        return False
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 4:
        return False
    counts = {"LATIN": 0, "ARABIC": 0}
    for char in letters:
        unicode_name = name(char, "")
        for script in counts:
            if script in unicode_name:
                counts[script] += 1
                break
    length = len(letters)
    if language == "en":
        return counts["LATIN"] / length >= 0.70 and counts["ARABIC"] / length <= 0.15
    return counts["ARABIC"] / length >= 0.55 and counts["LATIN"] / length <= 0.40
