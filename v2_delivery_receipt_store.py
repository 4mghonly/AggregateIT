"""B6 offline, single-host durable receipt-state lab. Absolutely NO sending.

The ambiguous-attempt marker is fsynced before callers could attempt a send;
post-crash reopen never treats that slot as eligible for blind retry. This is
not a Discord client, distributed coordination service or external receipt.
"""
from __future__ import annotations

import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import tempfile

from v2_delivery_gate import ReceiptGate


FORMAT = "aggregateit-v2-delivery-receipt-store/1"
STATE_NAME = "delivery.receipts.json"
LOCK_NAME = "delivery.receipts.lock"
ROW_KEYS = {"product", "slot_id", "destination_key", "edition_digest", "state",
            "message_id", "receipt_provenance"}
MAX_STATE_BYTES = 32_000_000


def _canonical(body: dict) -> bytes:
    return json.dumps(body, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _safe_open(path: Path, flags: int, mode: str):
    descriptor = os.open(path, flags | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("receipt_store_nonregular_file")
        return os.fdopen(descriptor, mode)
    except BaseException:
        os.close(descriptor)
        raise


class DurableReceiptStore:
    """Local test seam that persists reservations and ambiguous send markers.

    A real sender could only be built under separate authorization and must
    call mark_network_attempt and await success *before* its first network
    byte. The stored confirmation is still a caller assertion, not Discord
    proof. File deletion, coordinated file rollback and cross-host races are
    outside this local lab's security boundary.
    """

    def __init__(self, directory, *, max_slots: int = 1024):
        self.root = Path(directory)
        self.max_slots = max_slots
        self.gate: ReceiptGate | None = None
        self.lock = None
        self.poisoned = False

    @property
    def state_path(self) -> Path:
        return self.root / STATE_NAME

    def __enter__(self):
        if self.root.is_symlink() or not self.root.is_dir():
            raise ValueError("receipt_store_directory_missing_or_symlink")
        # The lock's existence is also a marker that a durable state should
        # already exist. Its accidental loss must not silently reset slots.
        lock_path = self.root / LOCK_NAME
        if self.state_path.is_symlink() or lock_path.is_symlink():
            raise ValueError("receipt_store_symlink_refused")
        old_lock, old_state = lock_path.exists(), self.state_path.exists()
        if old_lock != old_state:
            raise ValueError("receipt_state_missing_or_lock_missing")
        try:
            self.lock = _safe_open(lock_path, os.O_CREAT | os.O_RDWR, "r+b")
            try:
                fcntl.flock(self.lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError("receipt_writer_busy") from None
            self.gate = ReceiptGate(max_slots=self.max_slots)
            if old_state:
                self._read_state()
            else:
                self._write_state()
            return self
        except BaseException:
            self.close()
            raise

    def _read_state(self):
        with _safe_open(self.state_path, os.O_RDONLY, "rb") as stream:
            raw = stream.read(MAX_STATE_BYTES + 1)
        if len(raw) > MAX_STATE_BYTES:
            raise ValueError("receipt_state_oversize")
        try:
            envelope = json.loads(raw)
        except (UnicodeError, ValueError, TypeError) as exc:
            raise ValueError("invalid_receipt_state_json") from exc
        if not isinstance(envelope, dict) or set(envelope) != {"body", "checksum_sha256"}:
            raise ValueError("invalid_receipt_state_envelope")
        body = envelope["body"]
        if not isinstance(body, dict) or set(body) != {"format", "rows"} or body["format"] != FORMAT:
            raise ValueError("invalid_receipt_state_body")
        rows = body["rows"]
        if not isinstance(rows, list) or len(rows) > self.max_slots:
            raise ValueError("invalid_receipt_state_rows")
        checksum = sha256(_canonical(body)).hexdigest()
        if envelope["checksum_sha256"] != checksum:
            raise ValueError("receipt_state_checksum_mismatch")
        gate = ReceiptGate(max_slots=self.max_slots)
        for row in rows:
            if not isinstance(row, dict) or set(row) != ROW_KEYS:
                raise ValueError("invalid_receipt_state_row")
            try:
                created = gate.reserve(product=row["product"], slot_id=row["slot_id"],
                                       destination_key=row["destination_key"],
                                       edition_digest=row["edition_digest"])
                if not created:
                    raise ValueError("duplicate_receipt_state_slot")
                if row["state"] != "reserved":
                    gate.mark_network_attempt(product=row["product"], slot_id=row["slot_id"])
                if row["state"] == "confirmed_unverified":
                    gate.record_confirmed_receipt(product=row["product"],
                                                  slot_id=row["slot_id"],
                                                  destination_key=row["destination_key"],
                                                  message_id=row["message_id"])
                if gate.snapshot(product=row["product"], slot_id=row["slot_id"]) != row:
                    raise ValueError("invalid_receipt_state_transition")
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("invalid_receipt_state_row") from exc
        self.gate = gate

    def _write_state(self):
        assert self.gate is not None
        rows = sorted(self.gate._slots.values(), key=lambda r: (r["product"], r["slot_id"]))
        body = {"format": FORMAT, "rows": rows}
        envelope = {"body": body, "checksum_sha256": sha256(_canonical(body)).hexdigest()}
        raw = _canonical(envelope) + b"\n"
        if len(raw) > MAX_STATE_BYTES:
            raise ValueError("receipt_state_oversize")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", dir=self.root, prefix=".delivery-",
                                             delete=False) as stream:
                temporary = stream.name
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.state_path)
            temporary = None
            directory_fd = os.open(self.root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if temporary is not None:
                os.unlink(temporary)

    def _active(self) -> ReceiptGate:
        if self.poisoned or self.gate is None or self.lock is None:
            raise RuntimeError("receipt_store_requires_recovery")
        return self.gate

    def _persist_after_change(self):
        try:
            self._write_state()
        except BaseException:
            self.poisoned = True
            raise

    def reserve(self, **kwargs) -> bool:
        changed = self._active().reserve(**kwargs)
        if changed:
            self._persist_after_change()
        return changed

    def mark_network_attempt(self, **kwargs) -> None:
        self._active().mark_network_attempt(**kwargs)
        self._persist_after_change()

    def record_confirmed_receipt(self, **kwargs) -> None:
        self._active().record_confirmed_receipt(**kwargs)
        self._persist_after_change()

    def retry_allowed(self, **kwargs) -> bool:
        return self._active().retry_allowed(**kwargs)

    def snapshot(self, **kwargs) -> dict:
        return self._active().snapshot(**kwargs)

    def close(self):
        self.gate = None
        if self.lock is not None:
            fcntl.flock(self.lock.fileno(), fcntl.LOCK_UN)
            self.lock.close()
            self.lock = None

    def __exit__(self, _type, _value, _tb):
        self.close()
