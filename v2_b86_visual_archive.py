"""Validate a five-page 4K native held archive before retaining it for visual review."""
from pathlib import Path
from hashlib import sha256
from PIL import Image
EXPECTED=[f"{language}-no-post-{n}.png" for language,count in (("english",2),("arabic",3)) for n in range(1,count+1)]
def validate_page_archive(directory):
 directory=Path(directory)
 if directory.is_symlink() or not directory.is_dir():raise ValueError("missing_visual_archive")
 if sorted(p.name for p in directory.iterdir())!=sorted(EXPECTED):raise ValueError("incomplete_visual_archive")
 pages=[]
 for name in EXPECTED:
  p=directory/name
  if p.is_symlink() or not p.is_file():raise ValueError("unsafe_visual_page")
  with Image.open(p) as image:
   if image.format!="PNG" or image.size!=(3840,2160):raise ValueError("invalid_visual_page")
   image.verify()
  pages.append({"filename":name,"sha256":sha256(p.read_bytes()).hexdigest(),"dimensions":[3840,2160]})
 return {"schema":"aggregateit-v2-b86-visual-review/1","pages":pages,"independent_pixel_review_complete":False,"can_release":False}
