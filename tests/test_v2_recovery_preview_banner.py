import io,unittest
from PIL import Image
from v2_native_evidence_render import _stamp

class PreviewBannerTests(unittest.TestCase):
 def test_preview_banner_is_neutral_and_bounded(self):
  img=Image.new("RGB",(3840,2160),(12,40,50))
  raw=io.BytesIO();img.save(raw,format="PNG")
  out=_stamp(raw.getvalue())
  with Image.open(io.BytesIO(out)) as rendered:
   self.assertEqual(rendered.size,(3840,2160))
   r,g,b=rendered.getpixel((10,10))
   self.assertLess(abs(r-g),30)
   self.assertGreater(g,20)
   self.assertEqual(rendered.getpixel((200,200)),(12,40,50))
if __name__=="__main__":unittest.main()
