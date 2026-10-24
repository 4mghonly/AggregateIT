"""B11 region/source readiness: feed connectivity never equals editorial coverage.

Consumes only bounded read-only observations. Native-Arabic counts are
*language candidates*, not verified analysis or permission to redistribute.
"""
from __future__ import annotations
from urllib.parse import urlsplit

TARGET_REGIONS = (
    'gcc','oman','iran','turkey','iraq','yemen','sudan','sahel',
    'north_africa','egypt','pakistan','afghanistan','somalia','horn',
    'palestine_israel','levant','jordan'
)
LANGUAGES = frozenset(('ar','en','fa','so','fr','tr','ps','prs','ur','he','ku'))
USABLE_STATUS = frozenset(('usable_dated_feed',))


def assess_source_regions(observations: list[dict]) -> dict:
    if not isinstance(observations, list) or len(observations)>350:
        raise ValueError('invalid_coverage_observations')
    rows={region: {'region':region,'tested_sources':0,'usable_feeds':0,
                   'native_arabic_feed_candidates':0,'host_candidates':0,
                   'languages_observed':set(),'_hosts':set(),
                   'status':'not_tested','independent_publisher_families_verified':False,
                   'editorial_coverage_verified':False,
                   'rights_verified':False,'publication_approved':False}
          for region in TARGET_REGIONS}
    seen=set()
    for value in observations:
        if not isinstance(value,dict) or value.get('region') not in rows:
            raise ValueError('unrecognized_region')
        sid=value.get('source_id')
        if not isinstance(sid,str) or not sid or len(sid)>100:
            raise ValueError('invalid_source_id')
        if sid in seen:continue
        seen.add(sid)
        language=value.get('language')
        if language not in LANGUAGES:
            raise ValueError('unsupported_declared_language')
        region=rows[value['region']]
        region['tested_sources']+=1
        region['status']='observed_unverified'
        if value.get('status') not in USABLE_STATUS:
            continue
        try:
            url=urlsplit(value['feed_url'])
            if url.scheme!='https' or not url.hostname or url.username or url.password:
                raise ValueError('unsafe_reported_feed_url')
        except (ValueError,TypeError,KeyError) as exc:
            raise ValueError('unsafe_reported_feed_url') from exc
        region['usable_feeds']+=1
        region['languages_observed'].add(language)
        region['_hosts'].add(url.hostname.removeprefix('www.'))
        if language=='ar' and value.get('arabic_original_language_candidate') is True:
            region['native_arabic_feed_candidates']+=1
    public={}
    for region,data in rows.items():
        data['host_candidates']=len(data.pop('_hosts'))
        data['languages_observed']=sorted(data['languages_observed'])
        public[region]=data
    return {
        'schema':'aggregateit-v2-b11-region-readiness/1',
        'regions':public,
        'tested_source_ids':len(seen),
        'regions_with_usable_feeds':sum(row['usable_feeds']>0 for row in public.values()),
        'regions_with_arabic_language_candidates':sum(row['native_arabic_feed_candidates']>0 for row in public.values()),
        'unproven_regions':list(TARGET_REGIONS),
        'editorial_completeness_verified':False,
        'publisher_independence_verified':False,
        'publication_rights_verified':False,
        'source_language_factuality_verified':False,
        'release_authorized':False,
    }
