"""Conservative R2 semantic-risk screening; never substitutes for independent fact checking."""
import re

_ARABIC = re.compile(r"[\u0600-\u06ff]")
_LATIN = re.compile(r"[A-Za-z]")
_NUMBERS = re.compile(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)")
_NEGATIONS = {
    "english": re.compile(r"\b(?:not|never|no|denied|without|failed|unlikely)\b", re.I),
    "arabic": re.compile(r"(?<![\u0621-\u064a])(?:لم|لن|ليس|ليست|لا|غير|نفى|نفت|دون)(?![\u0621-\u064a])")
}
_UNCERTAINTY = {
    "english": re.compile(r"\b(?:may|might|could|possible|proposed|proposal|reportedly|alleged|planned)\b", re.I),
    "arabic": re.compile(r"(?<![\u0621-\u064a])(?:قد|ربما|محتمل|مقترح|خطة|يعتزم|أفادت|بحسب)(?![\u0621-\u064a])")
}
def screen(*, product, quote, assessment):
    """Return review flags, not a claim of factual correctness."""
    if product not in ("english", "arabic"):
        raise ValueError("invalid_screen_language")
    if not isinstance(quote, str) or not isinstance(assessment, str):
        raise ValueError("invalid_screen_text")
    flags=[]
    if product=="arabic" and len(_ARABIC.findall(assessment))<max(5,len(_LATIN.findall(assessment))):
        flags.append("arabic_script_insufficient")
    if product=="english" and len(_LATIN.findall(assessment))<5:
        flags.append("english_script_insufficient")
    evidence_numbers=set(_NUMBERS.findall(quote))
    invented_numbers=set(_NUMBERS.findall(assessment))-evidence_numbers
    if invented_numbers:flags.append("numbers_not_in_excerpt")
    if bool(_NEGATIONS[product].search(quote)) != bool(_NEGATIONS[product].search(assessment)):
        flags.append("negation_mismatch_review")
    if _UNCERTAINTY[product].search(quote) and not _UNCERTAINTY[product].search(assessment):
        flags.append("uncertainty_missing_review")
    return {"status":"REVIEW_REQUIRED" if flags else "SCREEN_CLEAR_UNVERIFIED",
            "flags":flags,"independent_fact_verified":False}
