"""B27 multi-gate private review; separates technical tests from live proof."""
from __future__ import annotations


def evaluate_private_acceptance(*, admission: dict, source_watch: dict,
                                parser_shadow: dict, english_mobile: dict,
                                arabic_mobile: dict, packet_rehearsal: dict,
                                rollback: dict) -> dict:
    expected = {
        'admission': (admission, 'aggregateit-v2-b14-admission/1'),
        'source_watch': (source_watch, 'aggregateit-v2-b15-watch/1'),
        'parser_shadow': (parser_shadow, 'aggregateit-v2-b26-parser-shadow/1'),
        'english_mobile': (english_mobile, 'aggregateit-v2-b23-markup-audit/1'),
        'arabic_mobile': (arabic_mobile, 'aggregateit-v2-b23-markup-audit/1'),
        'packet': (packet_rehearsal, 'aggregateit-v2-b22-packet-rehearsal/1'),
        'rollback': (rollback, 'aggregateit-v2-b28-canary-rollback/1')}
    if any(not isinstance(value, dict) or value.get('schema') != schema
           for value, schema in expected.values()):
        raise ValueError('untrusted_private_acceptance_input')
    checks = {
        'article_admitted': bool(admission.get('admitted')),
        'source_probed': source_watch.get('healthy_count', 0) > 0,
        'same_input_parser_parity': parser_shadow.get('parity_passed') is True,
        'english_private_markup': english_mobile.get('static_checks_passed') is True,
        'arabic_private_markup': arabic_mobile.get('static_checks_passed') is True,
        'packet_destinations_isolated': packet_rehearsal.get('independent_destination_keys') is True,
        'rollback_tabletop': rollback.get('rollback_acceptance') == 'TABLETOP_ONLY',
    }
    live = (parser_shadow.get('live_parser_parity_proven') is True
            and english_mobile.get('real_device_verified') is True
            and arabic_mobile.get('real_device_verified') is True)
    if all(checks.values()) and live:
        state = 'PRIVATE_ACCEPTANCE_MEASURED'
    elif all(checks.values()):
        state = 'PARTIAL_OFFLINE'
    else:
        state = 'HOLD'
    return {'schema': 'aggregateit-v2-b27-private-acceptance/1',
            'status': state, 'checks': checks, 'unmet': [k for k, ok in checks.items() if not ok],
            'live_comparison_verified': live, 'delivery_authorized': False,
            'production_cutover': False, 'discord_sent': False}
