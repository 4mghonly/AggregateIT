"""Native held preview must retain admitted source evidence rather than generic disclaimers."""
import inspect
import unittest
import v2_native_evidence_render as native

class NativeEvidenceRetention(unittest.TestCase):
    def test_renderer_does_not_overwrite_source_summary_with_generic_disclaimer(self):
        code=inspect.getsource(native.render_held_editions)
        self.assertNotIn("event['summary_ar']='نقل حرفي من تقرير صحفي",code)
    def test_source_excerpt_used_in_arabic_summary(self):
        from v2_arabic_application_rehearsal import _render_brief
        code=inspect.getsource(_render_brief)
        self.assertIn('"summary_ar": quote',code)
if __name__=="__main__":unittest.main()
