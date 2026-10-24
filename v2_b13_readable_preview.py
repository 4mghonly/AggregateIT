"""B13 readable native 4K design candidate (2 EN / 3 AR), NEVER SEND.

Real articles are masked unless a separate audited rights gate explicitly
permits republication. This preview accepts *only* synthetic or masked copy.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image, ImageDraw, ImageFont

SIZE=(3840,2160)
AR_LABELS={'gcc':'الخليج','oman':'عمان','iran':'إيران','turkey':'تركيا',
           'iraq':'العراق','yemen':'اليمن','sudan':'السودان','sahel':'الساحل',
           'north_africa':'شمال أفريقيا','egypt':'مصر','pakistan':'باكستان',
           'afghanistan':'أفغانستان','somalia':'الصومال','horn':'القرن الأفريقي',
           'palestine_israel':'فلسطين وإسرائيل','levant':'بلاد الشام','jordan':'الأردن'}
WITHHELD={'english':'SOURCE TEXT WITHHELD — RIGHTS NOT CLEARED',
          'arabic':'حقوق إعادة النشر غير مؤكدة'}
PALETTES={'english':('#F7F3EA','#1B3038','#556C72','#A45A42','#FFFFFF','#C9BDB0'),
          'arabic':('#101E2B','#F2F5F4','#B3C3CA','#DDB57B','#1C3443','#496271')}

def _font(size,*,ar=False,bold=False):
    names=('/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf',
           '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf') if ar else (
           '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
           '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    path=names[0 if bold else 1]
    if not Path(path).is_file():path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    return ImageFont.truetype(path,size)

def _wrap(d,content,font,width,direction,limit):
    words=content.split();lines=[];line=''
    for word in words:
        candidate=(line+' '+word).strip()
        if d.textbbox((0,0),candidate,font=font,direction=direction)[2]<=width:
            line=candidate
        else:
            if line:lines.append(line)
            line=word
    if line:lines.append(line)
    return lines if len(lines)<=limit else None

def _headline(d,text,width,ar):
    for size in (75,70,64,58,54,50,46):
        font=_font(size,ar=ar,bold=True)
        lines=_wrap(d,text,font,width,'rtl' if ar else 'ltr',3 if ar else 2)
        if lines and all(d.textbbox((0,0),z,font=font,direction='rtl' if ar else 'ltr')[2]<=width for z in lines):
            return lines,font
    raise ValueError('unreadable_title')

def _validate(plan,product):
    if (not isinstance(plan,dict) or plan.get('schema')!='aggregateit-v2-b13-balanced-held-preview/1'
            or plan.get('product')!=product or plan.get('language')!=('ar' if product=='arabic' else 'en')
            or plan.get('delivery_authorized') is not False or plan.get('rights_cleared') is not False):
        raise ValueError('invalid_held_preview')
    tiles=plan.get('tiles')
    if not isinstance(tiles,list) or not 1<=len(tiles)<=12:
        raise ValueError('invalid_tiles')
    ids=set()
    for item in tiles:
        if not isinstance(item,dict) or not isinstance(item.get('event_id'),str) or item['event_id'] in ids:
            raise ValueError('duplicate_or_invalid_event')
        ids.add(item['event_id'])
        if item.get('original_language')!=('ar' if product=='arabic' else 'en'):
            raise ValueError('non_native_tile')
        if not isinstance(item.get('source_id'),str) or not isinstance(item.get('region'),str):
            raise ValueError('invalid_source')
        if item.get('synthetic') is True:
            if item.get('rights_status')!='synthetic_only':raise ValueError('unsafe_preview_rights')
        elif item.get('synthetic') is False:
            if item.get('rights_status')!='rights_hold' or item.get('display_headline')!=WITHHELD[product]:
                raise ValueError('unlicensed_text_refused')
        else:raise ValueError('unknown_content_provenance')
    return tiles

def _page(tiles,product,n,total):
    ar=product=='arabic';bg,ink,muted,accent,panel,border=PALETTES[product]
    image=Image.new('RGB',SIZE,bg);d=ImageDraw.Draw(image)
    direction='rtl' if ar else 'ltr'
    d.rectangle((0,0,3840,20),fill=accent)
    d.line((95,302,3745,302),fill=accent,width=5)
    title='نشرة الرصد الاستراتيجي' if ar else 'THE STRATEGIC NEWS DESK'
    sub='توزيع التغطية · عرض تجريبي محجوب الحقوق' if ar else 'REGIONAL COVERAGE • RIGHTS-HELD PREVIEW'
    if ar:
        d.text((3700,70),title,font=_font(106,ar=True,bold=True),fill=ink,anchor='ra',direction=direction)
        d.text((3700,220),sub,font=_font(43,ar=True),fill=muted,anchor='ra',direction=direction)
        d.text((100,75),f'{n:02d} / {total:02d}',font=_font(43,bold=True),fill=accent)
    else:
        d.text((100,60),title,font=_font(99,bold=True),fill=ink)
        d.text((100,220),sub,font=_font(43),fill=muted)
        d.text((3490,75),f'{n:02d}/{total:02d}',font=_font(43,bold=True),fill=accent)
    d.rounded_rectangle((95,332,3745,444),radius=15,fill=panel,outline=border,width=2)
    report=('مناطق متنوعة • تقارير مرخصة للنشر: صفر • دون تحليلات مولّدة' if ar
            else 'DIVERSE REGIONS • 0 RIGHTS-CLEARED ARTICLES • NO MODEL ANALYSIS')
    if ar:d.text((3700,352),report,font=_font(38,ar=True,bold=True),fill=ink,anchor='ra',direction=direction)
    else:d.text((130,359),report,font=_font(36,bold=True),fill=ink)
    height=650 if ar else 442;gap=30 if ar else 24
    for i,item in enumerate(tiles):
        if i>=4 if ar else i>=6:break
        x=95+(i%2)*1840;y=473+(i//2)*(height+gap)
        w=1810
        d.rounded_rectangle((x,y,x+w,y+height),radius=24,fill=panel,outline=border,width=3)
        d.rounded_rectangle((x+28,y+27,x+w-28,y+107),radius=14,outline=border,width=2)
        region=AR_LABELS.get(item['region'],item['region']) if ar else item['region'].replace('_',' ').upper()
        if ar:
            d.text((x+w-60,y+38),region,font=_font(40,ar=True,bold=True),fill=accent,anchor='ra',direction=direction)
        else:d.text((x+60,y+39),region,font=_font(38,bold=True),fill=accent)
        lines,font=_headline(d,item['display_headline'],w-112,ar)
        for j,line in enumerate(lines):
            top=y+145+j*int(font.size*1.4)
            if ar:d.text((x+w-55,top),line,font=font,fill=ink,anchor='ra',direction=direction)
            else:d.text((x+55,top),line,font=font,fill=ink)
        fy=y+height-118
        d.line((x+50,fy-22,x+w-50,fy-22),fill=border,width=2)
        source=('المصدر' if ar else 'SOURCE')+': '+item['source_id']
        if ar:d.text((x+w-52,fy),source,font=_font(34,ar=True,bold=True),fill=muted,anchor='ra',direction=direction)
        else:d.text((x+52,fy),source,font=_font(34,bold=True),fill=muted)
    d.line((95,2030,3745,2030),fill=border,width=3)
    note=('عرض تجريبي فقط • لا إعادة نشر للنصوص بلا تصريح • تغطية غير مكتملة' if ar else
          'DESIGN REVIEW ONLY • NO UNLICENSED REPRINTS • COVERAGE INCOMPLETE')
    if ar:d.text((3690,2066),note,font=_font(35,ar=True,bold=True),fill=accent,anchor='ra',direction=direction)
    else:d.text((100,2067),note,font=_font(35,bold=True),fill=accent)
    return image

def render_balanced_preview(english:dict,arabic:dict,*,output_dir:Path)->dict:
    en=_validate(english,'english');ar=_validate(arabic,'arabic')
    dest=Path(output_dir)
    if dest.exists() or dest.is_symlink() or not dest.parent.is_dir():
        raise ValueError('unsafe_output_directory')
    rows=[('english',1,2,en[:5]),('english',2,2,en[5:10]),('arabic',1,3,ar[:4]),
          ('arabic',2,3,ar[4:8]),('arabic',3,3,ar[8:12])]
    pages=[]
    with TemporaryDirectory(prefix='b13-readability-',dir=dest.parent) as tmp:
        stage=Path(tmp)/'pages';stage.mkdir()
        for product,n,count,tiles in rows:
            if not tiles:
                heading=('لا توجد أدلة مرخصة لهذه الصفحة' if product=='arabic' else 'NO RIGHTS-CLEARED ARTICLES')
                tiles=[{'event_id':'gap','region':'gcc','source_id':'NO-SOURCE',
                        'display_headline':heading,'synthetic':True}]
            im=_page(tiles,product,n,count)
            name=f'{product}-balanced-preview-{n}.png'
            p=stage/name;im.save(p,'PNG',optimize=True)
            pages.append({'product':product,'page':n,'filename':name,'dimensions':[3840,2160],
                          'sha256':sha256(p.read_bytes()).hexdigest(),'tiles':len(tiles)})
        result={'schema':'aggregateit-v2-b13-visual-design/1','pages':pages,
                'rights_cleared':False,'delivery_authorized':False,
                'source_content_republished':False,'llm_called':False,
                'discord_sent':False,'synthetic_or_masked_only':True}
        (stage/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        os.rename(stage,dest)
    return result
