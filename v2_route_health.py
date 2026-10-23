"""Bounded, secret-free route telemetry contract for AggregateIT V2.

B1 captures in-memory diagnostics only. No database, network transport,
credential, raw article, prompt, response or source URL is written.
"""
from collections import Counter

HTTP_AUTH = frozenset((401, 403))
HTTP_TRANSIENT = frozenset((408, 409, 425, 429, 500, 502, 503, 504))
STAGES = frozenset(("english_chat", "arabic_chat", "arabic_probe"))
ROUTES = frozenset(("primary", "fallback"))
OUTCOMES = frozenset((
    "success", "auth_rejected", "transient_http", "permanent_http",
    "transport_error", "invalid_content", "budget_exhausted",
))


def outcome_for_http(status):
    if status == 200:
        return "success"
    if status in HTTP_AUTH:
        return "auth_rejected"
    if status in HTTP_TRANSIENT:
        return "transient_http"
    return "permanent_http"


class RouteJournal:
    def __init__(self, max_entries=64):
        self.max_entries = max(1, min(128, int(max_entries)))
        self.events = []
        self.total = 0
        self.dropped = 0

    def record(self, stage, route, *, status=None, outcome=None):
        """Record only allowlisted fields and aggregate counters, never API text."""
        if stage not in STAGES or route not in ROUTES:
            raise ValueError("unsupported_route_telemetry")
        if outcome is None:
            if status is None:
                raise ValueError('missing_route_outcome')
            outcome = outcome_for_http(status)
        if outcome not in OUTCOMES:
            raise ValueError("unsupported_route_outcome")
        code = int(status) if isinstance(status, int) and 100 <= status <= 599 else None
        entry = {"stage": stage, "route": route, "outcome": outcome, "http": code}
        self.total += 1
        if len(self.events) == self.max_entries:
            self.events.pop(0)
            self.dropped += 1
        self.events.append(entry)
        return entry

    def snapshot(self):
        counts = Counter(event["outcome"] for event in self.events)
        return {
            "schema": "aggregateit-route-health/1",
            "total_attempts": self.total,
            "stored_attempts": len(self.events),
            "dropped_detail": self.dropped,
            "by_outcome": dict(sorted(counts.items())),
            "events": list(self.events),
        }
