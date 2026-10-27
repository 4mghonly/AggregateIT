"""B47 weekly PDF *held preview* from source-bound existing weekly rollup.

Uses true source excerpts and bounded PDF layout. May have only 1/7 observed
days. Missing history, model analysis or verified rights never gets invented.
"""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

import arabic_reshaper
from bidi.algorithm import get_display
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import simpleSplit

_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def _font():
    if not Path(_FONT).is_file() or not Path(_FONT_BOLD).is_file():
        raise ValueError('arabic_capable_pdf_font_missing')
    if 'B47DejaVu' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('B47DejaVu',_FONT))
        pdfmetrics.registerFont(TTFont('B47DejaVuBold',_FONT_BOLD))
    return 'B47DejaVu','B47DejaVuBold'

def _display(text, rtl):
    if not isinstance(text,str) or not text.strip() or len(text)>2000:
        raise ValueError('invalid_weekly_pdf_text')
    text=' '.join(text.split())
    if rtl:
        return get_display(arabic_reshaper.reshape(text),base_dir='R')
    return text

def generate_held_weekly_pdf(report:dict)->dict:
    if (not isinstance(report,dict) or report.get('schema')!='aggregateit-v2-weekly-rollup/1'
        or report.get('delivery_authorized') is not False or report.get('window_days')!=7
        or report.get('product') not in ('english','arabic')):
        raise ValueError('untrusted_weekly_pdf_source')
    days=report.get('days_with_snapshots')
    if type(days) is not int or not 0<=days<=7:
        raise ValueError('invalid_weekly_observed_days')
    stories=report.get('stories')
    if not isinstance(stories,list) or len(stories)>40:
        raise ValueError('invalid_weekly_story_roster')
    rtl=report['product']=='arabic'
    font,bold=_font()
    out=BytesIO()
    c=Canvas(out,pagesize=A4,pageCompression=1)
    W,H=A4;left,right=46,W-46
    y=H-62
    pages=1
    def line(text,size=10,bold_text=False,shade='#263D4A',space=16):
        nonlocal y,pages
        visual=_display(text,rtl)
        use_font=bold if bold_text else font
        lines=simpleSplit(visual,use_font,size,right-left)
        if not lines:lines=[visual]
        for row in lines:
            if y<65:
                c.showPage();pages+=1;y=H-52
            c.setFont(use_font,size)
            c.setFillColor(HexColor(shade))
            if rtl:
                c.drawRightString(right,y,row)
            else:
                c.drawString(left,y,row)
            y-=space
    heading='تقرير أسبوعي موثق المصادر - معاينة' if rtl else 'SOURCE-LINKED WEEKLY REPORT - PREVIEW'
    c.setTitle('AggregateIT Arabic Weekly Held' if rtl else 'AggregateIT English Weekly Held')
    line(heading,size=15,bold_text=True,shade='#153E56',space=25)
    warning=('الأدلة غير مكتملة؛ غير مصرح بالنشر'
             if rtl else 'INCOMPLETE EVIDENCE - NOT FOR DELIVERY')
    line(warning,size=12,bold_text=True,shade='#A03633',space=23)
    line((f'أيام الرصد الفعلية: {days} من 7' if rtl else f'Observed real days: {days} of 7'),
         size=12,space=23)
    status=('تحليل الأخبار والتحقق المستقل غير مكتمل'
            if rtl else 'Model analysis and independent factual verification withheld')
    line(status,size=9,space=22)
    for index,story in enumerate(stories,1):
        if not isinstance(story,dict) or not isinstance(story.get('evidence'),dict):
            raise ValueError('unbound_weekly_story')
        evidence=story['evidence']
        url=evidence.get('source_url')
        if not isinstance(url,str) or len(url)>2048:
            raise ValueError('invalid_source_url')
        p=urlsplit(url)
        if p.scheme!='https' or not p.hostname or p.username or p.password:
            raise ValueError('untrusted_weekly_source_url')
        quote=evidence.get('quote')
        if not isinstance(quote,str) or not quote.strip() or len(quote)>1500:
            raise ValueError('missing_original_language_quote')
        line((f'المادة {index} | {story["region"]}' if rtl else
              f'Article {index} | {story["region"]}'),size=11,bold_text=True,space=20)
        line(quote,size=10,space=16)
        line((f'معرّف الدليل: {evidence["excerpt_id"]}' if rtl
              else f'Evidence: {evidence["excerpt_id"]}'),size=8,space=15)
        line(('المصدر: '+url if rtl else 'Source: '+url),size=7,space=22)
    if not stories:
        line('لا توجد بيانات مقبولة' if rtl else 'No accepted source evidence.',size=11)
    line('لا تترتب صلاحية نشر على هذا الاختبار' if rtl else
         'Preview is nonpublishable; publisher rights and quality remain unverified.',
         size=8,shade='#A03633',space=14)
    c.save()
    data=out.getvalue()
    if not data.startswith(b'%PDF-') or len(data)>8*1024*1024:
        raise ValueError('invalid_pdf_output')
    reader=PdfReader(BytesIO(data))
    if len(reader.pages)!=pages or not 1<=pages<=12:
        raise ValueError('unexpected_pdf_page_count')
    for page in reader.pages:
        if round(float(page.mediabox.width))!=595 or round(float(page.mediabox.height))!=842:
            raise ValueError('invalid_pdf_page_size')
    return {'bytes':data,'pages':pages,
        'observed_days':days,'required_days':7,
        'complete_week':days==7,'source_bound_story_count':len(stories),
        'rights_verified':False,'model_analysis_verified':False,
        'can_send':False}
