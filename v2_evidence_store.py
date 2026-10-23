"""B3 isolated POSIX filesystem owner for the append-only evidence journal.

Coordinates cooperative local writers and persists an independently checksummed
head receipt. Not a signed publisher receipt or a production database adapter.
Never truncates or repairs a damaged/ambiguous journal automatically.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile

from v2_evidence_journal import EvidenceJournal, ZERO_HASH


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


class EvidenceStore:
    """Context-managed, single-host advisory-lock owner of one journal.

    Atomic receipt rename happens *after* journal fsync. A crash between the two
    makes the journal ahead of the receipt; opening then refuses until a human
    independently reconciles it. External rollback of BOTH files requires a
    trusted off-host receipt; neither hashes nor flock can prevent that attack.
    """

    def __init__(self, directory, *, max_observations=20_000):
        self.root = Path(directory)
        self.max_observations = max_observations
        self.lock_file = None
        self.sink = None
        self.journal = None
        self.poisoned = False

    @property
    def log_path(self):
        return self.root / "evidence.jsonl"

    @property
    def receipt_path(self):
        return self.root / "evidence.head.json"

    def __enter__(self):
        if not self.root.is_dir():
            raise ValueError("store_directory_missing")
        try:
            # A named persistent lock protects both log and receipt updates.
            self.lock_file = open(self.root / "evidence.lock", "a+b")
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError("evidence_writer_busy") from None

            existing_log = self.log_path.exists()
            existing_receipt = self.receipt_path.exists()
            if existing_log != existing_receipt:
                raise ValueError("journal_receipt_pair_missing")
            if not existing_log:
                with open(self.log_path, "x+b") as created:
                    created.flush()
                    os.fsync(created.fileno())
                self._fsync_directory()
                self.journal = EvidenceJournal(max_observations=self.max_observations)
                self._write_receipt(self.journal.receipt())
            else:
                payload = json.loads(self.receipt_path.read_text(encoding="utf-8"))
                receipt = payload.get("receipt") if isinstance(payload, dict) else None
                if not isinstance(receipt, dict) or set(payload) != {"receipt", "checksum_sha256"}:
                    raise ValueError("invalid_head_receipt")
                checksum = hashlib.sha256(_canonical(receipt).encode("utf-8")).hexdigest()
                if payload["checksum_sha256"] != checksum:
                    raise ValueError("head_receipt_checksum_mismatch")
                with open(self.log_path, "r", encoding="utf-8", newline="") as stream:
                    data = stream.read()
                self.journal = EvidenceJournal.replay(
                    data, expected_head=receipt.get("head_sha256"),
                    max_observations=self.max_observations,
                )
                if self.journal.receipt() != receipt:
                    raise ValueError("journal_receipt_metadata_mismatch")
            self.sink = open(self.log_path, "a", encoding="utf-8", newline="")
            if self.sink.tell() != self.journal.bytes_written:
                raise ValueError("journal_byte_size_mismatch")
            return self
        except BaseException:
            self.close()
            raise

    def _fsync_directory(self):
        descriptor = os.open(self.root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _write_receipt(self, receipt):
        payload = {"receipt": receipt,
                   "checksum_sha256": hashlib.sha256(_canonical(receipt).encode("utf-8")).hexdigest()}
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                             dir=self.root, prefix=".head-", delete=False) as stream:
                temporary = stream.name
                stream.write(_canonical(payload) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.receipt_path)
            temporary = None
            self._fsync_directory()
        finally:
            if temporary is not None:
                os.unlink(temporary)

    def append(self, kind, payload):
        if self.poisoned or self.journal is None or self.sink is None:
            raise RuntimeError("store_requires_recovery")
        before_seq = self.journal.seq
        try:
            result = self.journal.append(self.sink, kind, payload, durable=True)
            self._write_receipt(self.journal.receipt())
            return result
        except BaseException:
            # A deterministic rejection before I/O is safe to correct. Any
            # partial write or journal/receipt split requires manual recovery.
            if self.journal.poisoned or self.journal.seq != before_seq:
                self.poisoned = True
            raise

    def close(self):
        if self.sink is not None:
            self.sink.close()
            self.sink = None
        if self.lock_file is not None:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
            self.lock_file.close()
            self.lock_file = None
        self.journal = None

    def __exit__(self, _type, _value, _tb):
        self.close()

