"""B5 PIL/RAQM renderer acceptance: synthetic image bytes only, no disk writes."""
import copy
import hashlib
import io
import unittest

from PIL import Image

from test_b3_b7_offline_rehearsal import fixture, registry
from v2_offline_rehearsal import run_offline_rehearsal
from v2_raster_preview import render_preview


class RasterPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rehearsal = run_offline_rehearsal(fixture(),registry())

    def test_both_products_have_expected_full_resolution_pages(self):
        en=render_preview(self.rehearsal["products"]["english"]["layout"])
        ar=render_preview(self.rehearsal["products"]["arabic"]["layout"])
        self.assertEqual(len(en["pages"]),2)
        self.assertEqual(len(ar["pages"]),3)
        for r,size in ((en,(2480,3508)),(ar,(3840,2160))):
            self.assertFalse(r["delivery_authorized"])
            self.assertEqual(r["discord_receipt"],"not_attempted")
            for page in r["pages"]:
                self.assertEqual(page["pixel_size"],size)
                self.assertTrue(page["png"].startswith(bytes([137,80,78,71,13,10,26,10])))
                self.assertEqual(page["sha256"],hashlib.sha256(page["png"]).hexdigest())
                self.assertEqual(page["clipped_items"],0)

    def test_software_scaled_preview_is_valid_png(self):
        r=render_preview(self.rehearsal["products"]["arabic"]["layout"])
        with Image.open(io.BytesIO(r["pages"][0]["scaled_png"])) as im:
            self.assertEqual(im.size,(1600,900))
            self.assertEqual(im.format,"PNG")

    def test_card_color_is_not_background_and_has_content(self):
        r=render_preview(self.rehearsal["products"]["english"]["layout"])
        with Image.open(io.BytesIO(r["pages"][0]["png"])) as im:
            self.assertNotEqual(im.getpixel((0,0)),im.getpixel((160,500)))
            self.assertEqual(r["pages"][0]["cards_rendered"],1)

    def test_publisher_tampered_style_rejected(self):
        layout=copy.deepcopy(self.rehearsal["products"]["arabic"]["layout"])
        layout["style"]["background"]="#FFFFFF"
        with self.assertRaisesRegex(ValueError,"untrusted_style_or_pages"):
            render_preview(layout)

    def test_cannot_render_claimed_publishable_layout(self):
        layout=copy.deepcopy(self.rehearsal["products"]["english"]["layout"])
        layout["delivery_authorized"]=True
        with self.assertRaisesRegex(ValueError,"cannot_render_publishable_payload"):
            render_preview(layout)


    def test_dense_page_six_165_character_cards_fit_without_cropping(self):
        layout=copy.deepcopy(self.rehearsal["products"]["arabic"]["layout"])
        sample=copy.deepcopy(layout["pages"][0]["items"][0])
        sample["quote"]=("تصريحات رسمية أولية بشأن تطورات إقليمية لم تؤكدها مصادر مستقلة. " * 3)[:165]
        layout["pages"][1]["items"]=[{**sample,"event_id":"synthetic.full."+str(i)} for i in range(6)]
        layout["pages"][1]["characters"]=sum(len(x["quote"]) for x in layout["pages"][1]["items"])
        # Pixel fit is checked independently of the character-only admission.
        preview=render_preview(layout)
        self.assertEqual(preview["pages"][1]["cards_rendered"],6)
        self.assertEqual(preview["pages"][1]["clipped_items"],0)

    def test_font_absence_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"approved_preview_font_missing"):
            render_preview(self.rehearsal["products"]["english"]["layout"],
                           font_path="/synthetic/no-such-font.ttf")

    def test_single_unbroken_word_fails_instead_of_cropping(self):
        layout=copy.deepcopy(self.rehearsal["products"]["english"]["layout"])
        layout["pages"][0]["items"][0]["quote"]="W"*240
        with self.assertRaisesRegex(ValueError,"unbreakable_word_overflow"):
            render_preview(layout)

if __name__=="__main__":
    unittest.main()
