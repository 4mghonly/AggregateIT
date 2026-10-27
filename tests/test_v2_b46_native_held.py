"""B46 stage 5: actual native page receipts are never publishable."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from hashlib import sha256
from v2_b46_native_held import render_genuine_held
from v2_b46_live_editorial import compile_captured_articles

NOW="2026-10-27T08:00:00+00:00"
SLOT="2026-10-27T12:00:00+04:00"
E=("Officials in Somalia said their security representatives met with regional "
   "officials to discuss security changes and public reports regarding the situation.")
A="أكد مسؤولون في الصومال عقد مباحثات دبلوماسية مع ممثلين إقليميين لبحث التطورات السياسية ومناقشة بيانات الاجتماع المتعلق بالعلاقات الإقليمية."
def evidence():
    en={"product":"english","source_id":"en-001",
        "article_url":"https://www.bbc.com/news/articles/c123-example",
        "title":"Somalia security officials outline latest measures",
        "published_at":"2026-10-27T07:00:00+00:00",
        "html_bytes":("<article><p>"+E+"</p><p>"+E+"</p></article>").encode("utf8")}
    ar={"product":"arabic","source_id":"ar-s003",
        "article_url":"https://www.aljazeera.net/news/2026/10/27/example",
        "title":"مباحثات دبلوماسية في الصومال بشأن العلاقات الإقليمية",
        "published_at":"2026-10-27T07:00:00+00:00",
        "html_bytes":('<div class="wysiwyg--all-content"><p>'+A+'</p><p>'+A+'</p></div>').encode('utf8')}
    return compile_captured_articles([en,ar],as_of=NOW,slot_id=SLOT)

class NativeHeldTests(unittest.TestCase):
    def test_without_arabic_article_no_fake_pages(self):
        bad=evidence()
        bad["products"]["arabic"]["story_count"]=0
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"bilingual_evidence_required"):
                render_genuine_held(bad,output_dir=Path(td)/"pages")
    def test_unverified_edition_delivery_authority_refused(self):
        bad=evidence();bad["products"]["english"]["newsroom"]["delivery_authorized"]=True
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                render_genuine_held(bad,output_dir=Path(td)/"pages")
    def test_five_real_png_files_are_hash_checked_and_nonpublishable(self):
        def renderer(en,ar,*,slot_id,output_dir):
            output_dir.mkdir(parents=True)
            pages=[]
            for product,limit in (("english",2),("arabic",3)):
                for page in range(1,limit+1):
                    name=product+"-"+str(page)+".png"
                    path=output_dir/name
                    Image.new("RGB",(3840,2160)).save(path,format="PNG")
                    pages.append({"product":product,"page":page,"path":name,
                                  "sha256":sha256(path.read_bytes()).hexdigest()})
            return {"schema":"aggregateit-v2-native-no-post-pages/1",
                    "delivery_authorized":False,"pages":pages}
        with tempfile.TemporaryDirectory() as td,patch("v2_b46_native_held.render_held_editions",side_effect=renderer):
            out=render_genuine_held(evidence(),output_dir=Path(td)/"pages")
        self.assertEqual(len(out["native_pages"]),5)
        self.assertEqual(out["status"],"HELD_VALID_NATIVE_PAGES")
        self.assertFalse(out["publisher_facts_verified"])
        self.assertFalse(out["can_release"])
    def test_renderer_wrong_digest_fails(self):
        def renderer(en,ar,*,slot_id,output_dir):
            output_dir.mkdir(parents=True)
            from PIL import Image
            result=[]
            for product,count in (("english",2),("arabic",3)):
                for i in range(1,count+1):
                    path=output_dir/(product+str(i)+".png")
                    Image.new("RGB",(3840,2160)).save(path,format="PNG")
                    result.append({"product":product,"page":i,"path":path.name,
                                   "sha256":"0"*64})
            return {"schema":"aggregateit-v2-native-no-post-pages/1",
                    "delivery_authorized":False,"pages":result}
        with tempfile.TemporaryDirectory() as td,patch("v2_b46_native_held.render_held_editions",side_effect=renderer):
            with self.assertRaisesRegex(ValueError,"native_image_digest_mismatch"):
                render_genuine_held(evidence(),output_dir=Path(td)/"pages")
if __name__=="__main__":unittest.main()
