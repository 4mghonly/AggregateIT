"""Build the original SIRAJ NOIR Arabic/Latin prototype with FontForge.

All source SVG outlines under glyphs/ must be original artwork. The builder refuses
to emit a font when required outlines are missing so production cannot silently
ship blank glyphs.
"""
import fontforge
import psMat
import os
from pathlib import Path

FONT_NAME="SirajNoir"
FAMILY_NAME="Siraj Noir"
FULL_NAME="Siraj Noir Display"
VERSION="1.000"

ROOT=Path(__file__).resolve().parent
GLYPH_ROOT=ROOT/"glyphs"
BUILD_DIR=ROOT/"build"
BUILD_DIR.mkdir(parents=True,exist_ok=True)

font=fontforge.font()
font.encoding="UnicodeFull"
font.fontname=FONT_NAME
font.familyname=FAMILY_NAME
font.fullname=FULL_NAME
font.version=VERSION
font.em=1000
font.ascent=790
font.descent=210
font.os2_typoascent=790
font.os2_typodescent=-210
font.os2_typolinegap=40
font.hhea_ascent=790
font.hhea_descent=-210
font.hhea_linegap=40
font.os2_weight=800
font.os2_width=4
font.os2_vendor="SIRJ"

LATIN_WIDTH=560
LATIN_NARROW=470
LATIN_WIDE=680
ARABIC_WIDTH=610
ARABIC_WIDE=740
SPACE_WIDTH=260
HORIZONTAL_SCALE=.955
MISSING=[]

def svg_path(*parts):
    return GLYPH_ROOT.joinpath(*parts)

def import_svg_glyph(name, codepoint, filename, width, scale_x=HORIZONTAL_SCALE):
    g=font.createChar(codepoint,name)
    filename=Path(filename)
    if filename.exists():
        g.importOutlines(str(filename))
        g.transform(psMat.scale(scale_x,1.0))
        g.removeOverlap(); g.correctDirection(); g.round(); g.simplify()
    else:
        MISSING.append(str(filename.relative_to(ROOT)))
    g.width=width
    return g

space=font.createChar(0x20,"space"); space.width=SPACE_WIDTH
nbsp=font.createChar(0x00A0,"nbspace"); nbsp.width=SPACE_WIDTH

latin_caps={chr(c):c for c in range(ord("A"),ord("Z")+1)}
narrow={"I","J","L","T"}; wide={"M","W"}
for ch,cp in latin_caps.items():
    width=LATIN_NARROW if ch in narrow else (LATIN_WIDE if ch in wide else LATIN_WIDTH)
    import_svg_glyph(ch,cp,svg_path("latin",f"{ch}.svg"),width)

for cp in range(ord("a"),ord("z")+1):
    ch=chr(cp)
    import_svg_glyph(ch,cp,svg_path("latin",f"{ch}.svg"),LATIN_WIDTH)

numbers=["zero","one","two","three","four","five","six","seven","eight","nine"]
for i,name in enumerate(numbers):
    import_svg_glyph(name,0x30+i,svg_path("numbers",f"{name}.svg"),580,1.0)
for i,name in enumerate([f"{n}.arabic" for n in numbers]):
    import_svg_glyph(name,0x0660+i,svg_path("numbers",f"{name}.svg"),580,1.0)

arabic_letters={
    "alef":0x0627,"beh":0x0628,"tehmarbuta":0x0629,"teh":0x062A,"theh":0x062B,
    "jeem":0x062C,"hah":0x062D,"khah":0x062E,"dal":0x062F,"thal":0x0630,
    "reh":0x0631,"zain":0x0632,"seen":0x0633,"sheen":0x0634,"sad":0x0635,
    "dad":0x0636,"tah":0x0637,"zah":0x0638,"ain":0x0639,"ghain":0x063A,
    "feh":0x0641,"qaf":0x0642,"kaf":0x0643,"lam":0x0644,"meem":0x0645,
    "noon":0x0646,"heh":0x0647,"waw":0x0648,"alefmaksura":0x0649,"yeh":0x064A,
}
# Unicode joining behaviour: ة and ى are right-joining too.
RIGHT_JOINING={"alef","tehmarbuta","dal","thal","reh","zain","waw","alefmaksura"}
DUAL_JOINING=set(arabic_letters)-RIGHT_JOINING

for name,cp in arabic_letters.items():
    import_svg_glyph(name,cp,svg_path("arabic",f"{name}.isol.svg"),ARABIC_WIDTH,1.0)
    import_svg_glyph(f"{name}.fina",-1,svg_path("arabic",f"{name}.fina.svg"),ARABIC_WIDTH,1.0)
    if name in DUAL_JOINING:
        import_svg_glyph(f"{name}.init",-1,svg_path("arabic",f"{name}.init.svg"),ARABIC_WIDTH,1.0)
        import_svg_glyph(f"{name}.medi",-1,svg_path("arabic",f"{name}.medi.svg"),ARABIC_WIDTH,1.0)

marks={"fathatan":0x064B,"dammatan":0x064C,"kasratan":0x064D,"fatha":0x064E,
       "damma":0x064F,"kasra":0x0650,"shadda":0x0651,"sukun":0x0652}
for name,cp in marks.items():
    g=import_svg_glyph(name,cp,svg_path("arabic",f"{name}.svg"),0,1.0); g.width=0

for feature in ("init","medi","fina"):
    font.addLookup(feature,"gsub_single",(),((feature,(("arab",("dflt",)),)),))
    font.addLookupSubtable(feature,f"{feature}-1")

for name in DUAL_JOINING:
    font[name].addPosSub("init-1",f"{name}.init")
    font[name].addPosSub("medi-1",f"{name}.medi")
    font[name].addPosSub("fina-1",f"{name}.fina")
for name in RIGHT_JOINING:
    font[name].addPosSub("fina-1",f"{name}.fina")

lam_alef=import_svg_glyph("lam_alef",-1,svg_path("arabic","lam_alef.svg"),ARABIC_WIDE,1.0)
font.addLookup("rlig","gsub_ligature",(),(("rlig",(("arab",("dflt",)),)),))
font.addLookupSubtable("rlig","rlig-lamalef")
lam_alef.addPosSub("rlig-lamalef",("lam","alef"))

font.addLookup("kern","gpos_pair",(),(("kern",(("latn",("dflt",)),)),))
font.addLookupSubtable("kern","kern-1")
pairs={("A","V"):-65,("A","W"):-55,("A","Y"):-70,("F","A"):-45,("L","T"):-40,
       ("L","V"):-60,("L","Y"):-65,("P","A"):-45,("T","A"):-55,("T","O"):-35,
       ("T","a"):-45,("T","e"):-45,("T","o"):-45,("V","A"):-65,("W","A"):-55,
       ("Y","A"):-70,("Y","O"):-40}
for (left,right),value in pairs.items():
    if left in font and right in font:
        font[left].addPosSub("kern-1",right,value,0,value,0)

punct={"period":(0x2E,280),"comma":(0x2C,280),"colon":(0x3A,300),
       "semicolon":(0x3B,300),"hyphen":(0x2D,360),"endash":(0x2013,580),
       "emdash":(0x2014,760),"parenleft":(0x28,340),"parenright":(0x29,340),
       "percent":(0x25,700),"commaarabic":(0x060C,320),
       "semicolonarabic":(0x061B,340),"questionarabic":(0x061F,450)}
for name,(cp,width) in punct.items():
    import_svg_glyph(name,cp,svg_path("punctuation",f"{name}.svg"),width,1.0)

if MISSING:
    print("SIRAJ NOIR build stopped: required original SVG outlines are missing:")
    for p in sorted(set(MISSING)): print("  ",p)
    font.close()
    raise SystemExit(2)

font.appendSFNTName("English (US)","Copyright","Copyright © 2026. Original SIRAJ NOIR typeface.")
font.appendSFNTName("English (US)","Designer","SIRAJ NOIR Design")
font.appendSFNTName("English (US)","Description",
    "Original bilingual Arabic-Latin typeface for high-density briefings, intelligence dashboards and dark-interface typography.")

for g in font.glyphs():
    if g.isWorthOutputting():
        try:
            g.removeOverlap(); g.correctDirection(); g.round()
        except Exception:
            pass

validation=font.validate()
if validation: print("FontForge validation returned:",validation)
else: print("Validation OK")

sfd=BUILD_DIR/"SirajNoir-Display.sfd"
ttf=BUILD_DIR/"SirajNoir-Display.ttf"
otf=BUILD_DIR/"SirajNoir-Display.otf"
font.save(str(sfd))
font.generate(str(ttf),flags=("opentype",))
font.generate(str(otf),flags=("opentype",))
print("SIRAJ NOIR generated:",ttf,otf)
font.close()
