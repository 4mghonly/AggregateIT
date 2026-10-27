"""B59: source-authored semantic translation counterexample checks, no model API.

Works only for explicitly defined self-authored challenge fixtures. A pass is
NOT quality evidence for publisher articles or a free-form model translation.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
import re

AR_DIGITS=str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹","01234567890123456789")
NEGATIVE=r"(?:لم|ليس|غير|لا\s|دون|لم\s+يتم|لم\s+تتم)"
PROPOSAL=r"(?:مقترح|مقترحة|اقتراح|مقترحاً|خطة|خطط|يخطط|تخطط)"
FORBIDDEN_CONFIRMED=r"(?:تم\s+الافتتاح|افتتحت\s+بالفعل|تمت\s+الموافقة|أقر\s+بالفعل)"
FIXTURES={
 "en-plan": {"language":"en",
   "title":"Somalia officials proposed 12 clinics on 27 October.",
   "summary":"The plan was not approved. No clinic opening was confirmed.",
   "required":[NEGATIVE,PROPOSAL],"forbidden":[FORBIDDEN_CONFIRMED]},
 "so-plan": {"language":"so",
   "title":"Mas'uuliyiinta Soomaaliya waxay soo jeediyeen 12 xarumood 27 Oktoobar.",
   "summary":"Qorshaha lama ansixin. Lama xaqiijin in xarumo la furay.",
   "required":[NEGATIVE,PROPOSAL],"forbidden":[FORBIDDEN_CONFIRMED]}
}
def _numbers(value):
    return Counter(re.findall(r"\d+(?:[.,]\d+)*",value.translate(AR_DIGITS)))

def inspect_known_translation(fixture_id:str, title_ar:str, summary_ar:str,
                              *,original_sha256:str)->dict:
    if fixture_id not in FIXTURES:raise ValueError("unknown_semantic_fixture")
    item=FIXTURES[fixture_id]
    expected=sha256((item["title"]+"\n"+item["summary"]).encode("utf8")).hexdigest()
    if original_sha256!=expected:raise ValueError("original_fixture_digest_mismatch")
    if not isinstance(title_ar,str) or not isinstance(summary_ar,str):
        raise ValueError("invalid_translation_text")
    if not 1<=len(title_ar)<=280 or not 1<=len(summary_ar)<=900:
        raise ValueError("unbounded_translation_text")
    text=title_ar+" "+summary_ar
    source=item["title"]+" "+item["summary"]
    issues=[]
    if _numbers(text)!=_numbers(source):issues.append("numbers_mismatched")
    for regex in item["required"]:
        if not re.search(regex,text,re.I):issues.append("missing_known_semantic_feature")
    for regex in item["forbidden"]:
        if re.search(regex,text,re.I):issues.append("invented_confirmation")
    arabic=sum("\u0600"<=c<="\u06ff" for c in text)
    latin=sum("a"<=c.lower()<="z" for c in text)
    if arabic/max(arabic+latin,1)<.65:issues.append("insufficient_arabic")
    return {"schema":"aggregateit-v2-b59-fixture-contract/1",
            "fixture_id":fixture_id,"source_sha256":expected,
            "checks_passed":not issues,"issues":sorted(set(issues)),
            "validated_scope":"fixed_source_authored_semantic_regressions",
            "publisher_story_semantic_fidelity_verified":False,
            "model_output_authenticated":False,"can_release":False}

def fixture_digest(name):
    if name not in FIXTURES:raise ValueError("unknown_semantic_fixture")
    f=FIXTURES[name]
    return sha256((f["title"]+"\n"+f["summary"]).encode("utf8")).hexdigest()
