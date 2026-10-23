"""B5 typography safety: the UAE story text needs legible contrast."""
import unittest

from arabic_layout.render_pages import UAE_HEADLINE_COLOR, _footer
from arabic_layout.render_engine import PAPER, REGION_COLORS


def luminance(color):
    parts = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
              for c in parts]
    return sum(a * b for a, b in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast(foreground, background):
    bright, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (bright + 0.05) / (dark + 0.05)


class UAEContrastTests(unittest.TestCase):
    def test_uae_headlines_reach_normal_text_contrast(self):
        self.assertGreaterEqual(contrast(UAE_HEADLINE_COLOR, PAPER), 4.5)

    def test_dark_geographic_accent_is_never_used_as_headline_color(self):
        self.assertLess(contrast(REGION_COLORS["gcc"], PAPER), 4.5)
        self.assertNotEqual(UAE_HEADLINE_COLOR, REGION_COLORS["gcc"])

    def test_synthetic_footer_is_explicitly_marked_and_live_footer_is_not(self):
        class Recorder:
            def __init__(self):
                self.lines = []

            def text(self, value, *_args, **_kwargs):
                self.lines.append(value)

        synthetic = Recorder()
        _footer(synthetic, 2, sample=True)
        self.assertTrue(any("بيانات اختبار" in line for line in synthetic.lines))
        normal = Recorder()
        _footer(normal, 2, sample=False)
        self.assertFalse(any("بيانات اختبار" in line for line in normal.lines))


if __name__ == "__main__":
    unittest.main()
