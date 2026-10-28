"""B63: reject untrustworthy 4K layout metadata before visual QA."""
import unittest

from v2_b60_original_edition_qa import inspect_layout_geometry


def _pages():
    return [
        {
            "product": product,
            "page": page,
            "width": 3840,
            "height": 2160,
            "sha256": "a" * 64,
            "boxes": [{"x": 50, "y": 60, "w": 700, "h": 60, "font_px": 34}],
        }
        for product, count in (("english", 2), ("arabic", 3))
        for page in range(1, count + 1)
    ]


class B63GeometryEvidenceTests(unittest.TestCase):
    def test_valid_metadata_is_only_a_structural_pass(self):
        result = inspect_layout_geometry(_pages())
        self.assertEqual(result["violations"], [])
        self.assertTrue(result["synthetic_metadata_only"])
        self.assertFalse(result["can_release"])

    def test_nonfinite_geometry_is_rejected(self):
        for value in (float("nan"), float("inf"), -float("inf")):
            for field in ("x", "y", "w", "h", "font_px"):
                with self.subTest(value=value, field=field):
                    pages = _pages()
                    pages[0]["boxes"][0][field] = value
                    with self.assertRaisesRegex(ValueError, "invalid_text_geometry"):
                        inspect_layout_geometry(pages)

    def test_page_digest_requires_actual_lowercase_hex_shape(self):
        for bad_digest in ("z" * 64, "A" * 64, "0" * 63, " 0" + "0" * 63):
            with self.subTest(bad_digest=bad_digest[:8]):
                pages = _pages()
                pages[2]["sha256"] = bad_digest
                with self.assertRaisesRegex(ValueError, "page_digest_missing"):
                    inspect_layout_geometry(pages)

    def test_empty_page_cannot_pass_text_geometry_review(self):
        pages = _pages()
        pages[4]["boxes"] = []
        with self.assertRaisesRegex(ValueError, "missing_page_text_geometry"):
            inspect_layout_geometry(pages)


if __name__ == "__main__":
    unittest.main()
