"""Pure native 4K B4-plan-to-PNG adapter, permanently unsendable.

Does not collect, call models, persist outside its explicit output directory,
or post. It may be called after a full-body ledger plan exists.
"""
from __future__ import annotations
from datetime import datetime,timezone
from math import isfinite
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


def _market_readout(observations:list[dict]|None)->str:
    """Literal cached V1 observations only, with attribution and no inferred currency."""
    if not observations:
        return 'No market evidence: absent, not zero.'
    if not isinstance(observations,list) or len(observations)>12:
        raise ValueError('invalid_market_readout')
    lines=[]
    for row in observations[:5]:
        if (not isinstance(row,dict)
            or row.get('source')!='tradingview_cached_snapshot'
            or row.get('unit')!='quoted_price_currency_unspecified'
            or not isinstance(row.get('symbol'),str)
            or not isinstance(row.get('value'),(float,int))
            or isinstance(row.get('value'),bool)):
            raise ValueError('untrusted_market_readout')
        lines.append(f"{row['symbol']} quoted {row['value']:.2f} (currency unspecified)")
    return 'V1 cached TradingView snapshot, not independently verified: '+ '; '.join(lines)+'.'


def _attach_market_charts(data:dict,pulse:dict|None,macro:dict|None,*,
                          as_of:str,has_admitted_market:bool)->dict:
    """Reuse actual V1 market arrays in its existing 4K chart renderer, gated by age.

    Caller has independently admitted at least one source-labelled market
    observation; this does not convert provider prices into verified facts.
    """
    out=dict(data)
    def fresh(value):
        if not isinstance(value,dict) or value.get('valid') is not True:
            return False
        raw=value.get('updated')
        if not isinstance(raw,(int,float)) or isinstance(raw,bool) or not isfinite(raw):
            return False
        stamp=datetime.fromisoformat(as_of.replace('Z','+00:00'))
        if stamp.utcoffset() is None:raise ValueError('market_slot_needs_timezone')
        return -300 <= stamp.timestamp()-raw <= 20*3600
    if has_admitted_market and fresh(pulse):
        out['pulse']=dict(pulse)
        if fresh(macro) and isinstance(macro.get('instruments'),list):
            from market import compute_regime
            out['macro']=dict(macro)
            out['regime']=compute_regime(macro)
    return out


def render_held_editions(english_plan:dict,arabic_plan:dict,*,slot_id:str,output_dir:Path,
                         market_observations:list[dict]|None=None,
                         pulse_snapshot:dict|None=None,macro_snapshot:dict|None=None)->dict:
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
    data=_attach_market_charts(_render_data(english_plan),pulse_snapshot,macro_snapshot,
                               as_of=slot_id,has_admitted_market=bool(market_observations))
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
    empty_analysis['market_read']=_market_readout(market_observations)
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
