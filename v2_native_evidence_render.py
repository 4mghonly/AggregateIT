"""Pure native 4K B4-plan-to-PNG adapter, permanently unsendable.

Does not collect, call models, persist outside its explicit output directory,
or post. It may be called after a full-body ledger plan exists.
"""
from __future__ import annotations
from datetime import datetime
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageFont


def _stamp(raw:bytes)->bytes:
    with Image.open(BytesIO(raw)) as image:
        img=image.convert('RGB')
        if img.size!=(3840,2160):raise ValueError('invalid_native_page_dimensions')
        d=ImageDraw.Draw(img)
        d.rectangle((0,0,3840,120),fill=(100,22,22))
        font_file='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        font=ImageFont.truetype(font_file,48) if Path(font_file).is_file() else ImageFont.load_default()
        d.text((55,35),'ATTRIBUTED SOURCE TEST | UNVERIFIED | DO NOT PUBLISH',fill=(255,255,255),font=font)
        buffer=BytesIO();img.save(buffer,'PNG');return buffer.getvalue()


def render_held_editions(english_plan:dict,arabic_plan:dict,*,slot_id:str,output_dir:Path)->dict:
    if not isinstance(english_plan,dict) or not isinstance(arabic_plan,dict):raise ValueError('plans_required')
    for product,plan,lang in [('english',english_plan,'en'),('arabic',arabic_plan,'ar')]:
        if (plan.get('schema')!='aggregateit-editorial-plan/1'
                or plan.get('product')!=product or plan.get('language')!=lang
                or plan.get('delivery_authorized') is not False
                or not plan.get('items') or len(plan['items'])>15):
            raise ValueError('untrusted_edition_plan')
        for item in plan['items']:
            ev=item.get('evidence',{})
            if item.get('reporting_status')!='publisher_attributed_not_independently_verified' or not ev.get('excerpt_id') or not ev.get('source_id') or ev.get('original_language')!=lang:
                raise ValueError('missing_literal_original_language_evidence')
    try:dt=datetime.fromisoformat(slot_id.replace('Z','+00:00'))
    except (ValueError,AttributeError):raise ValueError('invalid_slot') from None
    if dt.utcoffset() is None:raise ValueError('invalid_slot')
    output=Path(output_dir)
    output.mkdir(parents=True,exist_ok=True)
    if output.is_symlink() or any(output.iterdir()):raise ValueError('nonempty_or_symlink_output')
    from v2_english_application_rehearsal import _render_data
    from v2_arabic_application_rehearsal import _render_brief
    from gazette_render import render_p1,render_p2
    from arabic_layout.render_pages import render as render_arabic
    data=_render_data(english_plan)
    empty_analysis={
      'headline':'UNVERIFIED ARTICLE EVIDENCE TEST',
      'lead':'Short attributed original-language source excerpts only. Publication and factual verification withheld.',
      'geopol_read':'No independently verified assessment has been supplied.',
      'market_read':'No market evidence: absent, not zero.',
      'social_read':'No measured social-platform signals.',
      'cross_asset':'Cross-market analysis withheld.',
      'outlook':'No source-backed outlook available.',
      'key_risk':'Publisher assertions are not independent confirmations.',
      'delta':'No authenticated previous edition for comparison.',
    }
    pages=[]
    for n,renderer in enumerate((render_p1,render_p2),1):
        io=BytesIO();renderer(data,empty_analysis,False,io);raw=_stamp(io.getvalue())
        target=output/f'english-no-post-{n}.png';target.write_bytes(raw)
        pages.append({'product':'english','page':n,'path':target.name,'sha256':sha256(raw).hexdigest()})
    brief=_render_brief(arabic_plan,{'synthetic':True,'slot_id':slot_id})
    for event in brief['events']:
        event['summary_ar']='نقل حرفي من تقرير صحفي؛ لم يتم التحقق المستقل من صحة المعلومات.'
        event['status_ar']='غير متحقق'
    with TemporaryDirectory(prefix='v2-held-arabic-') as temp:
        rendered,clipped=render_arabic(brief,temp)
        if clipped or len(rendered)!=3:raise ValueError('ar_native_layout_incomplete')
        for n,p in enumerate(rendered,1):
            raw=_stamp(p.read_bytes());target=output/f'arabic-no-post-{n}.png';target.write_bytes(raw)
            pages.append({'product':'arabic','page':n,'path':target.name,'sha256':sha256(raw).hexdigest()})
    return {'schema':'aggregateit-v2-native-no-post-pages/1','pages':pages,
            'source_facts_verified':False,'delivery_authorized':False,
            'llm_called':False,'discord_sent':False}
