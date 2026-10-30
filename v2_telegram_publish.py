"""AggregateIT V2 Telegram delivery. Preview-only; never changes V1."""
from __future__ import annotations
import io, json, os, time, urllib.request, urllib.error
from pathlib import Path
from PIL import Image, ImageStat
from v2_preview_publish import prepare

MAX_PHOTO_BYTES=9_500_000
def api(method, fields, *, files=()):
    token=os.environ.get("V2_TELEGRAM_BOT_TOKEN","").strip()
    if not token or any(x in token for x in "\r\n /"): raise RuntimeError("missing_or_invalid_bot_token")
    url="https://api.telegram.org/bot"+token+"/"+method
    if not fields and not files:
        req=urllib.request.Request(url,method="GET")
        try:
            with urllib.request.urlopen(req,timeout=45) as resp: answer=json.load(resp)
        except urllib.error.HTTPError as exc:
            raise RuntimeError("telegram_http_"+str(exc.code)+"_"+method) from None
        if not answer.get("ok"): raise RuntimeError("telegram_api_rejected_"+method)
        return answer["result"]
    boundary="V2TelegramPreviewBoundary"
    parts=[]
    for k,v in fields.items():
        parts.append(("--"+boundary+"\r\nContent-Disposition: form-data; name=\""+k+"\"\r\n\r\n"+str(v)+"\r\n").encode())
    for name,filename,body in files:
        parts.append(("--"+boundary+"\r\nContent-Disposition: form-data; name=\""+name+"\"; filename=\""+filename+"\"\r\nContent-Type: image/jpeg\r\n\r\n").encode()+body+b"\r\n")
    data=b"".join(parts)+("--"+boundary+"--\r\n").encode()
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,data=data,headers={"Content-Type":"multipart/form-data; boundary="+boundary},method="POST")
            with urllib.request.urlopen(req,timeout=45) as resp: answer=json.load(resp)
            if not answer.get("ok"): raise RuntimeError("telegram_api_rejected_"+method)
            return answer["result"]
        except urllib.error.HTTPError as exc:
            if exc.code==429 and attempt<2:
                delay=min(10,int(json.loads(exc.read()).get("parameters",{}).get("retry_after",2)))
                time.sleep(delay)
                continue
            if exc.code>=500 and attempt<2:
                time.sleep(2**attempt)
                continue
            raise RuntimeError("telegram_http_"+str(exc.code)) from None
    raise RuntimeError("telegram_retry_exhausted")

def optimized(png):
    with Image.open(io.BytesIO(png)) as im:
        if im.format!="PNG" or im.size!=(3840,2160): raise RuntimeError("unexpected_native_image")
        im=im.convert("RGB")
        im.thumbnail((1920,1080),Image.Resampling.LANCZOS)
        if max(ImageStat.Stat(im.resize((48,27))).stddev)<3: raise RuntimeError("visually_blank_slide")
        for quality in (88,80,72):
            buf=io.BytesIO()
            im.save(buf,format="JPEG",quality=quality,optimize=True,subsampling=0)
            if len(buf.getvalue())<=MAX_PHOTO_BYTES: return buf.getvalue()
    raise RuntimeError("oversize_telegram_slide")

def publish(language,files):
    chat=os.environ.get("V2_TELEGRAM_CHAT_ID_"+language.upper(),"").strip()
    if not chat.startswith("-100") or not chat[1:].isdigit(): raise RuntimeError("invalid_private_channel_id_"+language)
    media=[];uploads=[]
    for i,(_,png) in enumerate(files):
        name=language+"-"+str(i+1)+".jpg"
        uploads.append(("photo"+str(i),name,optimized(png)))
        item={"type":"photo","media":"attach://photo"+str(i)}
        if i==0:
            item["caption"]=("[V2 PREVIEW — NOT PRODUCTION] Source-backed English editorial preview. Unverified for publication." if language=="english" else "[معاينة V2 — ليست نشرة إنتاجية] عرض تحريري عربي مستند إلى مصادر، لم يعتمد للنشر.")
        media.append(item)
    response=api("sendMediaGroup",{"chat_id":chat,"media":json.dumps(media,ensure_ascii=False),"disable_notification":"true"},files=uploads)
    if not isinstance(response,list) or len(response)!=len(files) or any(not msg.get("message_id") or str(msg.get("chat",{}).get("id"))!=chat for msg in response):
        raise RuntimeError("telegram_delivery_receipt_invalid_"+language)
    print(json.dumps({"language":language,"status":"accepted","message_count":len(response),"image_bytes":[len(x[2]) for x in uploads],"message_ids":[x["message_id"] for x in response]}))

def main():
    pages=prepare() # validate both products before any sends
    # Verify bot identity and both target channels before any sends.
    bot=api("getMe",{})
    if not bot.get("is_bot"): raise RuntimeError("invalid_telegram_bot")
    for language in ("english","arabic"):
        chat=os.environ.get("V2_TELEGRAM_CHAT_ID_"+language.upper(),"").strip()
        if not chat.startswith("-100") or not chat[1:].isdigit(): raise RuntimeError("invalid_channel_id_"+language)
        info=api("getChat",{"chat_id":chat})
        if info.get("type")!="channel" or str(info.get("id"))!=chat: raise RuntimeError("wrong_telegram_destination_"+language)
    for language in ("english","arabic"): publish(language,pages[language])
if __name__=="__main__": main()
