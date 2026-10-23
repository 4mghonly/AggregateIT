"""B5 experimental *in-memory* raster preview, never an authorized publication image.

Uses Pillow with RAQM shaping for Arabic. No implicit font download, no file
write, no network and no Discord. A missing font or unfittable quote fails closed.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, features

from v2_layout import PAGE_COUNTS, STYLE

_MIN_BODY = {"arabic": 52, "english": 42}
_HEAD = {"arabic": 120, "english": 98}
_META = {"arabic": 56, "english": 50}
_SCREEN_WIDTH = {"arabic": 1600, "english": 1200}
_FONT_NAME = "DejaVuSans.ttf"  # Explicit experimental fallback; not Siraj Noir.


def _wrap(draw, text, font, width, *, direction):
    lines = []
    current = ""
    for word in text.split():
        tentative = (current + " " + word).strip()
        if draw.textlength(tentative, font=font, direction=direction) <= width:
            current = tentative
            continue
        if current:
            lines.append(current)
            current = ""
        if draw.textlength(word, font=font, direction=direction) > width:
            raise ValueError("unbreakable_word_overflow")
        current = word
    if current:
        lines.append(current)
    return lines


def _font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except OSError as exc:
        raise ValueError("approved_preview_font_missing") from exc


def render_preview(layout: dict, *, font_path: str = _FONT_NAME) -> dict:
    if not isinstance(layout, dict) or layout.get("schema") != "aggregateit-layout-contract/1":
        raise ValueError("untrusted_layout")
    product = layout.get("product")
    if product not in PAGE_COUNTS or layout.get("page_count") != PAGE_COUNTS[product]:
        raise ValueError("wrong_product_page_count")
    if layout.get("delivery_authorized") is not False or layout.get("scaled_image_qa") != "not_run":
        raise ValueError("cannot_render_publishable_payload")
    if layout.get("style") != STYLE[product] or not isinstance(layout.get("pages"), list) or len(layout["pages"]) != PAGE_COUNTS[product]:
        raise ValueError("untrusted_style_or_pages")
    if product == "arabic" and not features.check("raqm"):
        raise ValueError("accurate_arabic_shaping_unavailable")

    w, h = (int(i) for i in STYLE[product]["canvas"].split("x"))
    rtl = product == "arabic"
    direction = "rtl" if rtl else "ltr"
    bg = STYLE[product]["background"]
    card_color = STYLE[product]["card"]
    ink = STYLE[product]["ink"]
    accent = STYLE[product]["accent"]
    img_results = []
    for idx, page in enumerate(layout["pages"]):
        if not isinstance(page, dict) or page.get("page_number") != idx+1:
            raise ValueError("wrong_page_index")
        items = page.get("items")
        if not isinstance(items, list) or len(items) > page.get("cards_limit", -1):
            raise ValueError("unbounded_page_items")
        im = Image.new("RGB", (w, h), bg)
        draw = ImageDraw.Draw(im)
        title_font = _font(font_path, _HEAD[product])
        sub_font = _font(font_path, _META[product])
        body_floor = _MIN_BODY[product]
        xpad = 180 if rtl else 130
        title_y = 125 if rtl else 145
        draw.rounded_rectangle((xpad, 90, w-xpad, 98), radius=4, fill=accent)
        heading = str(page.get("heading") or "")
        if not heading or draw.textlength(heading, font=title_font, direction=direction) > w-2*xpad:
            raise ValueError("page_heading_overflow")
        heading_anchor = "ra" if rtl else "la"
        heading_x = w-xpad if rtl else xpad
        draw.text((heading_x, title_y), heading, font=title_font, fill=ink,
                  anchor=heading_anchor, direction=direction)
        draw.text((heading_x, title_y+145), "AGGREGATEIT  |  OFFLINE • SYNTHETIC",
                  font=sub_font, fill=accent, anchor=heading_anchor, direction=direction)

        grid_top, grid_bottom = (420, h-210) if rtl else (455, h-240)
        gap = 44 if rtl else 45
        available_w = w-2*xpad
        columns = 2
        rows = 3
        card_w = (available_w-gap)//columns
        card_h = (grid_bottom-grid_top-gap*(rows-1))//rows
        for i, item in enumerate(items):
            if not isinstance(item, dict) or not isinstance(item.get("quote"), str):
                raise ValueError("invalid_quote_card")
            row, col = divmod(i, columns)
            left = xpad+col*(card_w+gap)
            top = grid_top+row*(card_h+gap)
            right, bottom = left+card_w, top+card_h
            draw.rounded_rectangle((left,top,right,bottom),radius=22,fill=card_color)
            accent_width = 12
            if rtl:
                draw.rounded_rectangle((right-accent_width,top+30,right,top+145),radius=4,fill=accent)
            else:
                draw.rounded_rectangle((left,top+30,left+accent_width,top+145),radius=4,fill=accent)
            inset = 70
            content_left, content_right = left+inset, right-inset
            label = str(item.get("subject_country") or "—")+"  /  "+str(item.get("region") or "—")
            label_x = content_right if rtl else content_left
            draw.text((label_x,top+42),label,font=sub_font,fill=accent,
                      anchor=heading_anchor,direction=direction)
            quote = item["quote"]
            if not quote.strip() or len(quote)>240:
                raise ValueError("invalid_quote_budget")
            chosen = None
            for fsize in range(74 if rtl else 55,body_floor-1,-2):
                f=_font(font_path,fsize)
                lines=_wrap(draw,quote,f,content_right-content_left,direction=direction)
                line_h=int(fsize*1.45)
                quote_top=top+143
                footer_top=bottom-92
                if len(lines)*line_h <= footer_top-quote_top-14:
                    chosen=(f,lines,line_h,quote_top)
                    break
            if chosen is None:
                raise ValueError("card_text_cannot_fit:"+str(item.get("event_id")))
            font,lines,line_h,y=chosen
            for line in lines:
                draw.text((label_x,y),line,font=font,fill=ink,
                          anchor=heading_anchor,direction=direction)
                y+=line_h
            if y>=bottom-92:
                raise ValueError("card_text_clipping")
            src_label = str(item.get("source_id") or "unknown")+" • "+str(item.get("source_date") or "date unverified")
            draw.text((label_x,bottom-79),src_label,font=sub_font,fill=accent,
                      anchor=heading_anchor,direction=direction)
        footer = "NOT FOR DELIVERY  •  PUBLISHER RIGHTS UNVERIFIED"
        draw.text((xpad,h-118),footer,font=sub_font,fill=accent,anchor="la",direction="ltr")
        draw.text((w-xpad,h-118),f"{idx+1} / {len(layout['pages'])}",
                  font=sub_font,fill=accent,anchor="ra",direction="ltr")
        out=BytesIO()
        im.save(out,format="PNG",optimize=True)
        raw=out.getvalue()
        # Small-scale proof is an offline simulation, never a Discord image test.
        preview=im.resize((_SCREEN_WIDTH[product],round(h*_SCREEN_WIDTH[product]/w)),
                          Image.Resampling.LANCZOS)
        small=BytesIO()
        preview.save(small,format="PNG",optimize=True)
        img_results.append({
            "page_number":idx+1, "sha256":sha256(raw).hexdigest(),
            "png":raw, "scaled_png":small.getvalue(),
            "pixel_size":(w,h), "scaled_width":_SCREEN_WIDTH[product],
            "cards_rendered":len(items),"clipped_items":0,
        })
    return {
        "schema":"aggregateit-v2-raster-preview/1",
        "product":product,"synthetic_only":True,
        "font_used":font_path,"preferred_font_installed":None,
        "arabic_raqm_shaping":bool(features.check("raqm")) if rtl else None,
        "publisher_rights":"unverified",
        "discord_receipt":"not_attempted",
        "delivery_authorized":False,
        "pages":img_results,
        "review_status":"in_memory_scale_simulation_not_human_visual_QA",
    }
