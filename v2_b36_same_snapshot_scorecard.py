"""B36: compare offline V1/V2 metrics only when source bytes, window and schema match.

All run metrics are caller supplied. No publisher authenticity, LLM quality,
Discord delivery, or real-world model execution is established by this tool.
"""
from __future__ import annotations

from v2_b16_replay_contract import build_replay_manifest
from v2_shadow_scorecard import compare_runs, validate_run


def compare_same_snapshot_metrics(v1_run: dict, v2_run: dict,
                                  v1_sources: list[dict], v2_sources: list[dict]) -> dict:
    """Require full source-roster and source-byte digest equality before any delta."""
    old, new = validate_run(v1_run), validate_run(v2_run)
    v1_manifest = build_replay_manifest(v1_sources)
    v2_manifest = build_replay_manifest(v2_sources)
    base = {'schema': 'aggregateit-v2-b36-snapshot-scorecard/1',
            'status': 'HOLD', 'exact_input_bytes_compared': False,
            'metric_values_authenticated': False,
            'full_edition_delivery_comparable': False,
            'delivery_authorized': False, 'discord_sent': False}
    if v1_manifest != v2_manifest:
        return {**base, 'reason': 'different_source_bytes_or_roster'}
    if (old['product'], old['window_start'], old['window_end']) != (
            new['product'], new['window_start'], new['window_end']):
        return {**base, 'reason': 'different_product_or_window'}
    if old['code_revision'] == new['code_revision']:
        return {**base, 'reason': 'same_code_revision'}
    scorecard = compare_runs(old, new)
    if scorecard.get('comparable') is not True:
        return {**base, 'reason': scorecard.get('reason', 'invalid_scorecard')}
    return {**base, 'status': 'OFFLINE_SAME_INPUT_METRIC_COMPARISON',
            'exact_input_bytes_compared': True,
            'source_count': len(v1_manifest['records']),
            'input_manifest_sha256': v1_manifest['manifest_sha256'],
            'reason': 'matching_source_bytes_and_metric_contract_only',
            'scorecard': scorecard}
