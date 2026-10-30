"""V2 isolated preview publisher: fail closed on incomplete bilingual held evidence."""
import json, os, hashlib, urllib.request, urllib.error
from pathlib import Path
from PIL import Image
ROOT=Path("v2-preview-pages")
EXPECTED={"english":2,"arabic":3}
def prepare():
    receipt=json.loads(Path("v2-preview-receipt.json").read_text())
    if receipt.get("schema")!="aggregateit-v2-b46-live-chain/1": raise RuntimeError("wrong receipt schema")
    editorial=receipt.get("editorial",{})
    products=editorial.get("products",{})
    four=receipt.get("four_products",{})
    if four.get("schema")!="aggregateit-v2-b47-four-product-held/1": raise RuntimeError("four-product render incomplete")
    if not isinstance(products,dict) or set(products)!={"english","arabic"}: raise RuntimeError("missing bilingual editorial")
    result={}
    for language,n in EXPECTED.items():
        if products[language].get("story_count",0)<1: raise RuntimeError(language+" empty briefing")
        daily=four.get("daily",{}).get(language,{})
        if daily.get("page_count")!=n or daily.get("story_count",0)<1 or not daily.get("real_source_backed"): raise RuntimeError(language+" incomplete pages")
        hashes=daily.get("native_page_sha256")
        if not isinstance(hashes,list) or len(hashes)!=n: raise RuntimeError(language+" invalid image manifest")
        files=[]
        for i in range(1,n+1):
            p=ROOT/(language+"-no-post-"+str(i)+".png")
            if p.is_symlink() or not p.is_file(): raise RuntimeError("missing page "+str(p))
            b=p.read_bytes()
            if len(b)<20000 or hashlib.sha256(b).hexdigest()!=hashes[i-1]: raise RuntimeError("invalid page bytes "+str(p))
            with Image.open(p) as im:
                if im.format!="PNG" or im.size!=(3840,2160): raise RuntimeError("invalid page format")
                im.verify()
            files.append((p.name,b))
        result[language]=files
    return result
def send(language,files):
    key="V2_DISCORD_WEBHOOK_ENGLISH" if language=="english" else "V2_DISCORD_WEBHOOK_ARABIC"
    url=os.getenv(key,"").strip()
    if not url.startswith(("https://discord.com/api/webhooks/","https://discordapp.com/api/webhooks/")): raise RuntimeError(language+" invalid V2-only webhook")
    from urllib.parse import urlsplit
    if urlsplit(url).hostname not in ("discord.com","discordapp.com"): raise RuntimeError("webhook hostname invalid")
    boundary="aggregateitV2previewBoundary"
    caption=("[V2 PREVIEW — NOT PRODUCTION] Real-source English editorial test. Unverified excerpts; do not redistribute." if language=="english" else "[معاينة V2 — ليست نشرة إنتاجية] اختبار تحريري عربي بمصادر حقيقية؛ المحتوى غير مدقق للنشر.")
    payload=json.dumps({"content":caption,"allowed_mentions":{"parse":[]}},ensure_ascii=False).encode()
    parts=[]
    def field(name,data,filename=None,ctype=None):
        head=("--"+boundary+"\r\nContent-Disposition: form-data; name=\""+name+"\""+("; filename=\""+filename+"\"" if filename else "")+"\r\n"+("Content-Type: "+ctype+"\r\n" if ctype else "")+"\r\n").encode()
        parts.append(head+b"\r\n"+data+b"\r\n")
    field("payload_json",payload)
    for i,(name,body) in enumerate(files): field("files["+str(i)+"]",body,name,"image/png")
    data=b"".join(parts)+("--"+boundary+"--\r\n").encode()
    req=urllib.request.Request(url+("&" if "?" in url else "?")+"wait=true",data=data,headers={"Content-Type":"multipart/form-data; boundary="+boundary,"User-Agent":"AggregateIT-V2-preview/1"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=45) as res: response=json.load(res)
    except urllib.error.HTTPError as e: raise RuntimeError(language+" Discord HTTP "+str(e.code)) from None
    if not response.get("id") or len(response.get("attachments",[]))!=len(files): raise RuntimeError(language+" Discord receipt incomplete")
    print(language+" V2 preview accepted; attachments="+str(len(files)))
if __name__=="__main__":
    pages=prepare()  # validate BOTH languages before any posting
    for lang in EXPECTED: send(lang,pages[lang])
