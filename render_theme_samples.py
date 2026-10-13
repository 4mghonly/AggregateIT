"""Offline samples. No collectors, inference, delivery or secrets."""
import argparse
import json
from pathlib import Path
from arabic_newsletter.sample import fixture as arabic_fixture
from test_gazette_layout import fixture as english_fixture
from newsletter_themes import sandstone,ink_copper

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,default=Path("reports/theme-preview"))
    p.add_argument("--arabic-json",type=Path)
    p.add_argument("--english-json",type=Path)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    arabic=json.loads(a.arabic_json.read_text(encoding="utf-8")) if a.arabic_json else arabic_fixture()
    if a.english_json:
        sample=json.loads(a.english_json.read_text(encoding="utf-8"))
        english,analysis=sample["data"],sample["analysis"]
    else: english,analysis=english_fixture()
    sandstone.render_p1(english,analysis,False,a.out/"english-1.png")
    sandstone.render_p2(english,analysis,False,a.out/"english-2.png")
    ink_copper.render(arabic,a.out/"arabic")
    (a.out/"manifest.json").write_text(json.dumps({
       "english":"sandstone_editorial","arabic":"ink_copper","offline":True,
       "arabic_input":"archived" if a.arabic_json else "synthetic",
       "english_input":"archived" if a.english_json else "synthetic"
    },ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":main()
