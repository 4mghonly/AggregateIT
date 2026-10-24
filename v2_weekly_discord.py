"""Pure boundary from a source-bound bilingual weekly report PDF to Discord.

No webhook URL, sender, queue, scheduler or live publication permission.
"""
from __future__ import annotations
from hashlib import sha256

from v2_discord_edition import prepare_discord_edition


def bundle_weekly_pdf(report: dict, pdf_bytes: bytes) -> dict:
    if (not isinstance(report, dict) or
            report.get('schema') != 'aggregateit-v2-weekly-rollup/1' or
            report.get('delivery_authorized') is not False or
            report.get('window_days') != 7):
        raise ValueError('weekly_rollup_contract_required')
    product = report.get('product')
    if product not in ('english', 'arabic'):
        raise ValueError('invalid_weekly_product')
    if product == 'arabic' and report.get('market_changes'):
        raise ValueError('arabic_financial_section_forbidden')
    if not isinstance(pdf_bytes, bytes):
        raise ValueError('invalid_weekly_pdf')
    filename = f'aggregateit-{product}-weekly.pdf'
    headline = ('Weekly geopolitical and financial intelligence (test)' if product == 'english'
                else 'تقرير أسبوعي جيوسياسي وأمني — اختبار')
    return prepare_discord_edition(
        product=product, cadence='weekly', slot_id=report.get('as_of'),
        pages=[{'filename':filename,'content':pdf_bytes,'sha256':sha256(pdf_bytes).hexdigest()}],
        headline=headline, summary=[],
        included_topics=['geopolitics'] if product == 'english' else ['security'],
        regions=report.get('regions_covered',[]),
        coverage_gaps=report.get('regions_uncovered',[]),
        critical_review='insufficient_evidence',synthetic=True,
    )
