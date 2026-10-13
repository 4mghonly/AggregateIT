"""Renderer routing for Arabic briefings.

Default production path is unchanged. Select INK & COPPER only with
ARABIC_NEWSLETTER_THEME=ink_copper on a reviewed deployment.
"""
import os
from arabic_layout.render_pages import render as _original_render, references

def render(brief, output):
    theme=os.getenv("ARABIC_NEWSLETTER_THEME","").strip().lower()
    if theme in ("","classic","original"):
        return _original_render(brief,output)
    if theme == "ink_copper":
        from newsletter_themes.ink_copper import render as _ink_copper
        return _ink_copper(brief,output)
    raise ValueError("Unsupported ARABIC_NEWSLETTER_THEME: "+theme)

__all__=["render","references"]
