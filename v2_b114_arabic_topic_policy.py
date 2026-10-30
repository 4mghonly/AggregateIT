"""B114 bounded, source-grounded Arabic topic and editorial relevance policy.

The classifier is deterministic and conservative: country is established
independently by the article evidence gate. It never infers event truth.
"""
from __future__ import annotations
import re
import unicodedata

# Roots are intentionally small and explicit. Arabic proclitics / definite
# article and common inflections are recognized without arbitrary substrings.
_PREFIX=r"(?:[وفبل]?ال?|لل?)"
_SUFFIX=r"[ء-ي]{0,5}"
_AR_LETTER=r"[ء-ي]"
_SECURITY=(
    "هجوم","هجمات","قصف","غارة","غارات","اشتباك","صاروخ","صواريخ",
    "قتل","قتلي","مقتل","اغتيال","اعتقال","انفجار","عسكر",
    "استهداف","ضربات","هدنة","عقوب","مسيّرة","مسيرة","امن",
)
_DIPLOMACY=("دبلوماس","مباحثات","مفاوض","محادث","مبعوث","سفير")
_POLITICAL=("سياس","انتخاب","برلمان","حكوم","اتفاق","اقتصاد","تجار","رئيس","قرار","قانون")
_STRATEGIC_POLITICAL=("انتخاب","برلمان","عقوب","سياس")
_ROUTINE=("مرور","ازدحام","مباراة","رياض","مطعم","فندق","طقس","مهرجان",
          "موسيقي","ترفيه","تخفيض","خدمات")

def normalize_arabic(value:str)->str:
    if not isinstance(value,str):
        raise ValueError("invalid_arabic_topic_input")
    s=unicodedata.normalize("NFKC",value)
    s=re.sub(r"[ً-ٰٟـ]","",s)
    return s.translate(str.maketrans({"أ":"ا","إ":"ا","آ":"ا","ٱ":"ا",
                                       "ؤ":"و","ئ":"ي","ى":"ي"})).casefold()

def _has_root(text:str,roots:tuple[str,...])->bool:
    for root in roots:
        r=normalize_arabic(root)
        if re.search(r"(?<!"+_AR_LETTER+r")"+_PREFIX+re.escape(r)+_SUFFIX+r"(?!"+_AR_LETTER+r")",text):
            return True
    return False

def _phrase(text:str,values:tuple[str,...])->bool:
    return any(normalize_arabic(phrase) in text for phrase in values)

def classify_arabic_event(headline:str,lead:str="",*,region:str|None=None,
                          uae_secondary:bool=False)->dict:
    """One classifier for article gate and editorial gate, no inferred region.

    A headline cue is sufficient. A cue in the bounded opening article text
    is also usable, but source geography must be verified separately.
    """
    if type(uae_secondary) is not bool:
        raise ValueError("invalid_secondary_context")
    title=normalize_arabic(headline)[:350]
    opening=normalize_arabic(lead)[:1200]
    security_title=_has_root(title,_SECURITY) or _phrase(title,("وقف اطلاق النار","اطلاق النار"))
    security_lead=_has_root(opening,_SECURITY) or _phrase(opening,("وقف اطلاق النار","اطلاق النار"))
    diplomatic_title=_has_root(title,_DIPLOMACY) or _phrase(title,("زيارة رسمية","قمة عربية","قمة دولية"))
    diplomatic_lead=_has_root(opening,_DIPLOMACY) or _phrase(opening,("زيارة رسمية","قمة عربية","قمة دولية"))
    political_title=_has_root(title,_POLITICAL)
    political_lead=_has_root(opening,_POLITICAL)
    strategic_political=_has_root(title,_STRATEGIC_POLITICAL) or _has_root(opening,_STRATEGIC_POLITICAL)
    routine=_has_root(title,_ROUTINE)
    if security_title or security_lead:
        topic="security"
        cue_zone="headline" if security_title else "lead"
    elif diplomatic_title or diplomatic_lead:
        topic="diplomacy"
        cue_zone="headline" if diplomatic_title else "lead"
    elif political_title or political_lead:
        topic="geopolitics"
        cue_zone="headline" if political_title else "lead"
    else:
        topic=None
        cue_zone=None
    if not region:
        reason="unverified_event_geography"
    elif routine and not (security_title or diplomatic_title or strategic_political):
        reason="routine_non_strategic"
    elif topic=="security":
        reason="explicit_security_evidence"
    elif topic=="diplomacy":
        reason="explicit_diplomatic_evidence"
    elif topic=="geopolitics" and (strategic_political or (region=="gcc" and uae_secondary)):
        reason="strategic_political_evidence"
    else:
        reason="not_security_relevant"
    admit=reason in ("explicit_security_evidence","explicit_diplomatic_evidence",
                      "strategic_political_evidence")
    return {"topic":topic,"admit":admit,"reason":reason,
            "cue_zone":cue_zone,"geography_provided":bool(region),
            "truth_verified":False}
