"""Single active Arabic renderer entry point.

All previous renderer implementations have been retired. The production briefing
uses only the approved executive-dashboard renderer in arabic_layout.
"""
from arabic_layout.render_pages import render, references

__all__ = ['render', 'references']
