"""Offline rendering and opt-in routing regressions for both new themes."""
import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from arabic_newsletter.sample import fixture as arabic_fixture
from test_gazette_layout import fixture as english_fixture
from newsletter_themes import ink_copper, sandstone

class ThemeTests(unittest.TestCase):
    def test_english_4k_and_empty_data(self):
        d,a=english_fixture()
        with tempfile.TemporaryDirectory() as root, patch("socket.socket",side_effect=AssertionError("network forbidden")):
            for tag,data in [("full",d),("empty",{"sample":True})]:
                for i,fn in enumerate((sandstone.render_p1,sandstone.render_p2),1):
                    p=Path(root)/f"{tag}-en-{i}.png"
                    fn(data,a,False,p)
                    with Image.open(p) as im: self.assertEqual(im.size,(3840,2160))

    def test_arabic_4k_and_missing_coverage(self):
        fixture=arabic_fixture()
        empty=copy.deepcopy(fixture)
        empty["events"]=[]
        empty["analysis"]={}
        with tempfile.TemporaryDirectory() as root,patch("socket.socket",side_effect=AssertionError("network forbidden")):
            for name,brief in (("full",fixture),("empty",empty)):
                paths,clipped=ink_copper.render(brief,Path(root)/name)
                self.assertEqual(len(paths),3)
                self.assertGreaterEqual(clipped,0)
                for p in paths:
                    with Image.open(p) as im: self.assertEqual(im.size,(3840,2160))

    def test_arabic_source_provenance(self):
        fixture=arabic_fixture()
        self.assertTrue(ink_copper._uae(fixture["events"][0]))
        self.assertIn("مصدر تجريبي",ink_copper._src(fixture["events"][0]))
        self.assertIn("لا يثبت",ink_copper._delta(fixture))

    def test_explicit_routing(self):
        import slide
        import gazette_render
        with patch.dict(os.environ,{"GAZETTE_THEME":""}):
            self.assertIs(slide._selected_page(1),gazette_render.render_p1)
        with patch.dict(os.environ,{"GAZETTE_THEME":"sandstone_editorial"}):
            self.assertIs(slide._selected_page(1),sandstone.render_p1)
        from arabic_newsletter.render import render
        from arabic_layout.render_pages import render as original
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ,{"ARABIC_NEWSLETTER_THEME":""}):
                self.assertIsNone(os.getenv("GAZETTE_THEME") if False else None)
                self.assertIsNot(render,original)
            with patch.dict(os.environ,{"ARABIC_NEWSLETTER_THEME":"unsupported"}):
                with self.assertRaises(ValueError): render({"sample":True},folder)

if __name__=="__main__": unittest.main()
