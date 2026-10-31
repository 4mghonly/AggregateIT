"""Extractive, attributed edition digest; no unsupported analytical conclusions."""
def grounded_digest(items, *, language="en", max_quotes=3):
    if language not in ("en","ar") or not isinstance(items,list):
        raise ValueError("invalid_digest_input")
    evidence=[];seen=set()
    for item in items:
        if not isinstance(item,dict):
            continue
        ev=item.get("evidence",{})
        quote=ev.get("quote","")
        source=ev.get("source_id","")
        if isinstance(quote,str) and quote.strip() and isinstance(source,str) and source:
            identity=(source,quote.strip())
            if identity not in seen:
                evidence.append((quote.strip(),source))
                seen.add(identity)
        if len(evidence)>=max_quotes:break
    if not evidence:
        return {"status":"insufficient_evidence","lead":"","sources":[],"verified":False}
    separator=" ؛ " if language=="ar" else " | "
    lead=separator.join(quote for quote,_ in evidence)
    return {"status":"publisher_attributed_only","lead":lead,
            "sources":list(dict.fromkeys(source for _,source in evidence)),
            "verified":False}
