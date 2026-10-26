"""B22 bilingual private packet integrity rehearsal, without a sender."""
from __future__ import annotations


def rehearse_private_packets(english: dict, arabic: dict) -> dict:
    if not isinstance(english, dict) or not isinstance(arabic, dict):
        raise ValueError('missing_packets')
    for product, packet, destination in (
            ('english', english, 'discord_webhook'), ('arabic', arabic, 'discord_webhook_arabic')):
        if (packet.get('schema') != 'aggregateit-v2-discord-preview/1'
                or packet.get('product') != product or packet.get('destination_key') != destination
                or packet.get('message_count') != 1 or packet.get('can_send') is not False
                or packet.get('synthetic') is not True or packet.get('webhook_url') is not None):
            raise ValueError('unsafe_or_misrouted_packet')
        if not packet.get('attachments'):
            raise ValueError('missing_packet_attachments')
        if any(not row.get('sha256') or row.get('size_bytes', 0) < 1 for row in packet['attachments']):
            raise ValueError('invalid_packet_receipt')
    if english.get('slot_id') != arabic.get('slot_id'):
        raise ValueError('mismatched_packet_slots')
    return {'schema': 'aggregateit-v2-b22-packet-rehearsal/1',
            'slot_id': english['slot_id'], 'english_attachment_count': len(english['attachments']),
            'arabic_attachment_count': len(arabic['attachments']),
            'independent_destination_keys': True, 'single_message_per_product': True,
            'discord_sent': False, 'delivery_authorized': False}
