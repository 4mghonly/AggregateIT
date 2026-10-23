"""B6 no-network, in-memory delivery-idempotency state model.

This is a simulation contract only. It cannot send to Discord, resolve
ambiguous external sends, or certify an untrusted caller's receipt.
"""
from __future__ import annotations

from copy import deepcopy
from v2_evidence import _time

DESTINATION_KEYS = {
    "english": "discord_webhook",
    "arabic": "discord_webhook_arabic",
}


class ReceiptGate:
    def __init__(self, *, max_slots: int = 1024):
        if type(max_slots) is not int or not 1 <= max_slots <= 100_000:
            raise ValueError("invalid_slot_budget")
        self.max_slots = max_slots
        self._slots: dict[tuple[str, str], dict] = {}

    def _key(self, product: str, slot_id: str) -> tuple[str, str]:
        if product not in DESTINATION_KEYS:
            raise ValueError("unknown_product")
        return product, _time(slot_id)

    def reserve(self, *, product: str, slot_id: str, destination_key: str,
                edition_digest: str) -> bool:
        key = self._key(product, slot_id)
        if destination_key != DESTINATION_KEYS[product]:
            raise ValueError("product_destination_mismatch")
        if not isinstance(edition_digest, str) or len(edition_digest) != 64 or any(
                c not in "0123456789abcdef" for c in edition_digest):
            raise ValueError("invalid_edition_digest")
        if key in self._slots:
            item = self._slots[key]
            if item["edition_digest"] != edition_digest:
                raise ValueError("slot_already_reserved_different_content")
            return False
        if len(self._slots) >= self.max_slots:
            raise ValueError("slot_ceiling")
        self._slots[key] = {
            "product": product, "slot_id": key[1], "destination_key": destination_key,
            "edition_digest": edition_digest, "state": "reserved",
            "message_id": None, "receipt_provenance": "none",
        }
        return True

    def mark_network_attempt(self, *, product: str, slot_id: str) -> None:
        item = self._slots[self._key(product, slot_id)]
        if item["state"] != "reserved":
            raise ValueError("attempt_not_permitted")
        # A timeout after a send can mean it delivered. Fail closed on retry.
        item["state"] = "ambiguous_network_outcome"

    def record_confirmed_receipt(self, *, product: str, slot_id: str,
                                 destination_key: str, message_id: str) -> None:
        item = self._slots[self._key(product, slot_id)]
        if item["destination_key"] != destination_key:
            raise ValueError("receipt_wrong_destination")
        if item["state"] not in {"ambiguous_network_outcome", "confirmed_unverified"}:
            raise ValueError("receipt_without_network_attempt")
        if not isinstance(message_id, str) or not 3 <= len(message_id) <= 120 or not all(
                c.isalnum() or c in "-_" for c in message_id):
            raise ValueError("invalid_receipt_id")
        if item["state"] == "confirmed_unverified" and item["message_id"] != message_id:
            raise ValueError("conflicting_receipt_id")
        item["state"] = "confirmed_unverified"
        item["message_id"] = message_id
        item["receipt_provenance"] = "caller_assertion_requires_external_verification"

    def retry_allowed(self, *, product: str, slot_id: str) -> bool:
        return self._slots[self._key(product, slot_id)]["state"] == "reserved"

    def snapshot(self, *, product: str, slot_id: str) -> dict:
        return deepcopy(self._slots[self._key(product, slot_id)])
