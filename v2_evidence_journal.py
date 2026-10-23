"""B3 experimental append-only, tamper-evident evidence journal.

The caller owns the file/stream and exclusive-writer lock. No production storage,
network, automatic truncation, deletion, or retention is performed here.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os

from v2_evidence_ledger import EvidenceLedger

MAX_FRAME_BYTES = 1_200_000
MAX_LOG_BYTES = 64_000_000
MAX_RECORDS = 50_000
ZERO_HASH = "0" * 64
COMMANDS = frozenset({"observe", "excerpt", "claim", "event", "relation"})


def _canonical(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _apply(ledger: EvidenceLedger, kind: str, payload: dict):
    if not isinstance(payload, dict):
        raise ValueError("invalid_payload")
    if kind == "observe":
        return ledger.observe(payload)
    if kind == "excerpt":
        return ledger.attach_excerpt(payload)
    if kind == "claim":
        return ledger.attach_claim(payload)
    if kind == "event":
        return ledger.upsert_event(payload)
    if kind == "relation":
        try:
            if set(payload) != {"event_id", "kind", "first_claim_id", "second_claim_id", "rationale"}:
                raise ValueError("invalid_relation_payload")
            return ledger.relate(**payload)
        except TypeError:
            raise ValueError("invalid_relation_payload") from None
    raise ValueError("unsupported_journal_command")


class EvidenceJournal:
    """Append validated commands to caller's exclusive stream, then update memory.

    A write/flush/fsync failure poisons this instance; recover from the persisted
    bytes before attempting another append. The stream must be opened for append
    and positioned at the end of the verified journal by its owning caller.
    """

    def __init__(self, *, ledger: EvidenceLedger | None = None, seq: int = 0,
                 head: str = ZERO_HASH, max_observations: int = 20_000, bytes_written: int = 0):
        self.ledger = ledger if ledger is not None else EvidenceLedger(max_observations=max_observations)
        self.seq = seq
        self.head = head
        self.bytes_written = bytes_written
        self.poisoned = False

    def append(self, sink, kind: str, payload: dict, *, durable: bool = True):
        if self.poisoned:
            raise RuntimeError("journal_requires_recovery")
        if kind not in COMMANDS:
            raise ValueError("unsupported_journal_command")
        if self.seq >= MAX_RECORDS:
            raise ValueError("journal_record_limit")
        # Validate the full mutation before any I/O. Preserve the live graph if
        # a broken source, reference or event version is supplied.
        candidate = deepcopy(self.ledger)
        value = _apply(candidate, kind, payload)
        body = {"v": 1, "seq": self.seq + 1, "prev": self.head,
                "kind": kind, "payload": deepcopy(payload)}
        body_text = _canonical(body)
        digest = hashlib.sha256(body_text.encode("utf-8")).hexdigest()
        line = _canonical({**body, "hash": digest}) + "\n"
        line_size = len(line.encode("utf-8"))
        if line_size > MAX_FRAME_BYTES:
            raise ValueError("journal_frame_limit")
        if self.bytes_written + line_size > MAX_LOG_BYTES:
            raise ValueError("journal_size_limit")
        try:
            count = sink.write(line)
            if count != len(line):
                raise OSError("journal_short_write")
            sink.flush()
            if durable:
                os.fsync(sink.fileno())
        except Exception:
            self.poisoned = True
            raise
        self.ledger = candidate
        self.seq += 1
        self.head = digest
        self.bytes_written += line_size
        return value

    @classmethod
    def replay(cls, data: str, *, expected_head: str | None = None,
               max_observations: int = 20_000):
        """Replay exact complete canonical frames; reject corruption and truncation.

        expected_head should be a separately stored receipt if loss of entire
        trailing records must be detected. Hashes alone are not signatures.
        """
        if not isinstance(data, str) or len(data.encode("utf-8")) > MAX_LOG_BYTES:
            raise ValueError("invalid_journal_size")
        if data and not data.endswith("\n"):
            raise ValueError("journal_truncated_tail")
        journal = cls(max_observations=max_observations)
        for raw in data.splitlines(keepends=True):
            if journal.seq >= MAX_RECORDS or len(raw.encode("utf-8")) > MAX_FRAME_BYTES:
                raise ValueError("journal_record_limit")
            try:
                frame = json.loads(raw)
                if not isinstance(frame, dict) or set(frame) != {"v", "seq", "prev", "kind", "payload", "hash"}:
                    raise ValueError("invalid_frame")
                if type(frame["v"]) is not int or frame["v"] != 1 or type(frame["seq"]) is not int or frame["seq"] != journal.seq + 1:
                    raise ValueError("journal_sequence")
                if frame["prev"] != journal.head or frame["kind"] not in COMMANDS:
                    raise ValueError("journal_chain")
                body = {k: frame[k] for k in ("v", "seq", "prev", "kind", "payload")}
                expected = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
                if frame["hash"] != expected or raw != _canonical(frame) + "\n":
                    raise ValueError("journal_hash_or_canonical_mismatch")
                _apply(journal.ledger, frame["kind"], frame["payload"])
            except (TypeError, KeyError, UnicodeError, json.JSONDecodeError, OverflowError) as exc:
                raise ValueError("invalid_journal_frame") from exc
            journal.seq += 1
            journal.head = frame["hash"]
            journal.bytes_written += len(raw.encode("utf-8"))
        if expected_head is not None and journal.head != expected_head:
            raise ValueError("journal_head_receipt_mismatch")
        return journal

    def receipt(self) -> dict:
        return {"format": "v2-evidence-jsonl/1", "seq": self.seq,
                "head_sha256": self.head, "journal_bytes": self.bytes_written,
                "counters": self.ledger.counters()}
