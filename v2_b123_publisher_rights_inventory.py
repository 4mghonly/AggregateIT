"""B123 publisher-source rights and factuality checklist; never grants permission.

The source registry is an identity catalog, NOT a redistribution licence.
No external terms of service are inferred, scraped or accepted on faith.
"""
from __future__ import annotations
from v2_b46_live_editorial import SOURCE_CATALOG

def build_registry_rights_inventory():
    products={}
    seen=set()
    for product in ('english','arabic'):
        rows=[]
        for source in SOURCE_CATALOG[product]:
            sid=source['source_id']
            if sid in seen: continue
            seen.add(sid)
            rows.append({
                'source_id':sid,'publisher_id':source['publisher_id'],
                'stream':product,'language':source['language'],
                'feed_url':source['feed_url'],
                'rights_status':'UNVERIFIED',
                'licence_or_permission_document':None,
                'allowed_publisher_quote_length':None,
                'republication_permission_evidenced':False,
                'independent_fact_check_evidenced':False,
                'publisher_identity_independently_confirmed':False,
                'approval_required_for_public_distribution':True,
            })
        products[product]=rows
    return {'schema':'aggregateit-v2-b123-source-rights-register/1',
            'publisher_ids_total':len(seen),'products':products,
            'verified_republication_rights':0,
            'verified_independent_factuality':0,
            'can_release':False,
            'source_registry_is_not_a_licence':True}

if __name__=='__main__':
    import json
    from pathlib import Path
    result=build_registry_rights_inventory()
    Path('b123_publisher_rights_inventory.json').write_text(
        json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print(json.dumps({'publishers':result['publisher_ids_total'],
                      'rights_verified':0,'release_status':'HOLD'}))
