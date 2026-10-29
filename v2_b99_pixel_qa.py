"""B99 objective 4K visual QA metrics; cannot replace independent reading."""
from __future__ import annotations
from pathlib import Path
from PIL import Image
from v2_b86_visual_archive import validate_page_archive

def inspect(directory):
 receipt=validate_page_archive(directory)
 findings=[]
 for item in receipt["pages"]:
  path=Path(directory)/item["filename"]
  with Image.open(path) as image:
   im=image.convert("RGB")
   # Detect accidental entirely blank output and absence of held watermark.
   colors=im.resize((192,108)).getcolors(192*108+1) or []
   diverse=len(colors)>=20
   # The red no-publish banner must occupy a visible portion of top 120px.
   samples=[im.getpixel((x,60)) for x in (60,960,1920,2880,3780)]
   banner=sum(r>g*1.3 and r>b*1.3 for r,g,b in samples)>=4
   findings.append({"page":item["filename"],"nonblank_color_diversity":diverse,"held_warning_banner_present":banner})
 return {"schema":"aggregateit-v2-b99-pixel-qa/1","pages":findings,"all_objective_checks_pass":all(x["nonblank_color_diversity"] and x["held_warning_banner_present"] for x in findings),"arabic_rtl_semantics_verified":False,"readability_verified":False,"text_clipping_verified":False,"can_release":False}

if __name__=="__main__":
 import json
 report=inspect(Path("b86-visual-review"))
 Path("b99_pixel_qa.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps(report))
 if not report["all_objective_checks_pass"]:raise SystemExit("B99 objective image quality failure")
