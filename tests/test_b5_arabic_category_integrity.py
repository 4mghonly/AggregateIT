"""Arabic page-3 subject panels must not invent militant/conflict/maritime links."""
import unittest

from arabic_layout.render_pages import (
    _militant_rows, _conflict_rows, _maritime_rows,
    _is_militant_story, _is_conflict_story, _is_maritime_tension,
)


def event(title, *, region="gcc", topic="security", assessment=""):
    return {"title_ar": title, "summary_ar": title, "region": region,
            "topic": topic, "assessment_ar": assessment, "watch_ar": ""}


class ArabicCategoryIntegrityTests(unittest.TestCase):
    def test_safe_maritime_drill_and_generic_security_are_not_tensions_or_conflicts(self):
        rows = [
            event("أجرت هيئة ميناء خيالية تمريناً للسلامة البحرية."),
            event("اجتماع للتنسيق في تبادل المعلومات الأمنية.", region="iraq"),
            event("ناقشت لجنة محلية مسألة صيانة شبكات الاتصالات.", region="somalia"),
        ]
        self.assertEqual(_militant_rows(rows), [])
        self.assertEqual(_maritime_rows(rows), [])
        self.assertEqual(_conflict_rows(rows), [])
        self.assertFalse(any(_is_militant_story(e) or _is_conflict_story(e) or
                             _is_maritime_tension(e) for e in rows))

    def test_explicit_militant_and_conflict_evidence_still_qualifies(self):
        row = event("ذكر البيان هجوماً نفذه تنظيم داعش على موقع عسكري في العراق.", region="iraq", topic="military")
        self.assertTrue(_militant_rows([row]))
        self.assertTrue(_conflict_rows([row]))
        self.assertFalse(_maritime_rows([row]))

    def test_maritime_tension_needs_explicit_harm_or_disruption(self):
        safe = event("أعلن ميناء خليجي برنامجاً تدريبياً للسلامة البحرية.")
        hostile = event("أُبلغ عن هجوم على سفينة في البحر الأحمر.", region="yemen")
        self.assertEqual(_maritime_rows([safe]), [])
        self.assertTrue(_maritime_rows([hostile]))

    def test_assessment_mention_alone_cannot_promote_subject_bucket(self):
        row = event("اجتماع دوري لمناقشة تدابير السلامة.", region="gcc",
                    assessment="قد تؤثر احتمالات هجوم بحري من داعش في المجال الأمني")
        self.assertFalse(_militant_rows([row]))
        self.assertFalse(_maritime_rows([row]))
        self.assertFalse(_conflict_rows([row]))


if __name__ == "__main__":
    unittest.main()
