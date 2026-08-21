"""storage.py — AggregateIT persistence layer.
v5: v4 + ddg_hits column (independent-domain corroboration count).
state.db is the single source of truth. Only filtered/analyzed/alerted are terminal;
deferred and failed stay retriable."""
import os, json, sqlite3, time

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
DB_PATH = os.path.join(DATA, "state.db")

TERMINAL = {"filtered", "analyzed", "alerted"}

EVENT_COLS = ["event_id", "entity", "tokens_json", "title", "event_type", "status", "severity",
              "confidence", "source_count", "assessment", "what_changed", "urls_json",
              "first_seen", "last_updated", "sentiment", "triggers_json", "sources_json", "score",
              "ddg_hits"]

class SQLiteStore:
    def __init__(self, path=DB_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        self.con = sqlite3.connect(path, timeout=30)
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.execute("PRAGMA busy_timeout=30000")
        self.con.executescript("""
        CREATE TABLE IF NOT EXISTS items(
            url TEXT PRIMARY KEY, title_hash TEXT, state TEXT,
            score REAL DEFAULT 0, analysis TEXT,
            discovered REAL, updated REAL);
        CREATE TABLE IF NOT EXISTS seen_titles(
            title_hash TEXT PRIMARY KEY, url TEXT, ts REAL);
        CREATE TABLE IF NOT EXISTS runs(
            ts REAL, fetched INT, new INT, matched INT, analyzed INT);
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS events(
            event_id TEXT PRIMARY KEY, entity TEXT, tokens_json TEXT,
            title TEXT, event_type TEXT, status TEXT, severity TEXT,
            confidence INTEGER, source_count INTEGER,
            assessment TEXT, what_changed TEXT, urls_json TEXT,
            first_seen REAL, last_updated REAL,
            sentiment TEXT, triggers_json TEXT, sources_json TEXT, score REAL DEFAULT 0,
            ddg_hits INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS claims(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT, claim TEXT, support_indices TEXT, status TEXT DEFAULT 'unverified');
        CREATE TABLE IF NOT EXISTS event_updates(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT, ts REAL, type TEXT, details_json TEXT);
        CREATE INDEX IF NOT EXISTS idx_updates_event ON event_updates(event_id, ts);
        """)
        # migration for DBs created before the extended event columns
        for col, ddl in (("sentiment", "TEXT"), ("triggers_json", "TEXT"),
                         ("sources_json", "TEXT"), ("score", "REAL DEFAULT 0"),
                         ("ddg_hits", "INTEGER DEFAULT 0")):
            try:
                self.con.execute(f"ALTER TABLE events ADD COLUMN {col} {ddl}")
            except Exception:
                pass
        self.con.commit()
        self.fresh = self._meta("created") is None
        if self.fresh:
            self._set_meta("created", str(time.time()))

    def _meta(self, k):
        r = self.con.execute("SELECT value FROM meta WHERE key=?", (k,)).fetchone()
        return r[0] if r else None

    def _set_meta(self, k, v):
        self.con.execute("INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)", (k, v))
        self.con.commit()

    # --- item state ---
    def url_active(self, url):
        r = self.con.execute("SELECT state FROM items WHERE url=?", (url,)).fetchone()
        return r is None or r[0] not in TERMINAL

    def title_active(self, thash):
        if not thash: return True
        return self.con.execute("SELECT 1 FROM seen_titles WHERE title_hash=?", (thash,)).fetchone() is None

    def register(self, url, thash, state, score=0):
        now = time.time()
        self.con.execute("INSERT OR REPLACE INTO items(url,title_hash,state,score,discovered,updated) VALUES (?,?,?,?,?,?)",
                         (url, thash, state, score, now, now))
        self.con.commit()

    def succeed(self, url, thash, state, analysis_json=None):
        now = time.time()
        self.con.execute("UPDATE items SET state=?, analysis=?, updated=? WHERE url=?",
                         (state, analysis_json, now, url))
        if thash:
            self.con.execute("INSERT OR IGNORE INTO seen_titles(title_hash,url,ts) VALUES (?,?,?)", (thash, url, now))
        self.con.commit()

    def fail(self, url):
        self.con.execute("UPDATE items SET state='failed', updated=? WHERE url=?", (time.time(), url))
        self.con.commit()

    # --- event store ---
    def _event_rows(self, where, params):
        rows = self.con.execute(f"SELECT {', '.join(EVENT_COLS)} FROM events {where}", params).fetchall()
        return [dict(zip(EVENT_COLS, r)) for r in rows]

    def recent_events(self, entity, hours=72, limit=25):
        return self._event_rows("WHERE entity=? AND last_updated > ? ORDER BY last_updated DESC LIMIT ?",
                                (entity, time.time() - hours * 3600, limit))

    def recent_all_events(self, hours=24, limit=100):
        return self._event_rows("WHERE last_updated > ? ORDER BY last_updated DESC LIMIT ?",
                                (time.time() - hours * 3600, limit))

    def upsert_event(self, e):
        self.con.execute(
            f"INSERT OR REPLACE INTO events({', '.join(EVENT_COLS)}) VALUES ({','.join('?' * len(EVENT_COLS))})",
            tuple(e.get(k) for k in EVENT_COLS))
        self.con.commit()

    def set_ddg_hits(self, event_id, n):
        """Store the number of independent domains corroborating this event."""
        self.con.execute("UPDATE events SET ddg_hits=? WHERE event_id=?", (n, event_id))
        self.con.commit()

    # --- event timeline ---
    def add_event_update(self, event_id, update_type, details=None):
        self.con.execute(
            "INSERT INTO event_updates(event_id, ts, type, details_json) VALUES (?,?,?,?)",
            (event_id, time.time(), update_type, json.dumps(details or {})))
        self.con.commit()

    def get_event_timeline(self, event_id):
        rows = self.con.execute(
            "SELECT ts, type, details_json FROM event_updates WHERE event_id=? ORDER BY ts ASC",
            (event_id,)).fetchall()
        out = []
        for ts, typ, det in rows:
            try:
                d = json.loads(det) if det else {}
            except Exception:
                d = {}
            out.append({"ts": ts, "type": typ, "details": d})
        return out

    # --- reporting ---
    def event_count(self):
        return self.con.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def record_run(self, fetched, new, matched, analyzed):
        self.con.execute("INSERT INTO runs(ts,fetched,new,matched,analyzed) VALUES (?,?,?,?,?)",
                         (time.time(), fetched, new, matched, analyzed))
        self.con.commit()

    def stats(self):
        rows = self.con.execute("SELECT state, COUNT(*) FROM items GROUP BY state").fetchall()
        titles = self.con.execute("SELECT COUNT(*) FROM seen_titles").fetchone()[0]
        return {"items_by_state": dict(rows), "titles": titles, "events": self.event_count(),
                "db_bytes": os.path.getsize(self.path) if os.path.exists(self.path) else 0,
                "fresh_init": self.fresh}
