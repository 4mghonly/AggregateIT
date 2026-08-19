"""storage.py — AggregateIT persistence layer (F-15/F-16).
SQLite is the single source of truth during execution. Cross-run durability
on GitHub Actions = rolling cache (primary) + artifact backup (recovery).
Swap SQLiteStore for PostgresStore later without touching main.py."""
import os, sqlite3, time

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
DB_PATH = os.path.join(DATA, "state.db")

# Item lifecycle (F-06). Only TERMINAL states count as "done".
# "failed" and "discovered" remain retriable on the next run.
TERMINAL = {"filtered", "analyzed", "alerted", "capped"}

class SQLiteStore:
    def __init__(self, path=DB_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        self.con = sqlite3.connect(path, timeout=30)
        self.con.execute("PRAGMA journal_mode=WAL")    # safer concurrent writes
        self.con.execute("PRAGMA busy_timeout=30000")  # wait on lock, don't fail
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
        """)
        self.con.commit()
        self.fresh = self._meta("created") is None
        if self.fresh:
            self._set_meta("created", str(time.time()))

    def _meta(self, k):
        r = self.con.execute("SELECT value FROM meta WHERE key=?", (k,)).fetchone()
        return r[0] if r else None
    def _set_meta(self, k, v):
        self.con.execute("INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)", (k, v)); self.con.commit()

    # --- seen checks: retriable states pass through (F-06) ---
    def url_active(self, url):
        r = self.con.execute("SELECT state FROM items WHERE url=?", (url,)).fetchone()
        return r is None or r[0] not in TERMINAL
    def title_active(self, thash):
        if not thash: return True
        return self.con.execute("SELECT 1 FROM seen_titles WHERE title_hash=?", (thash,)).fetchone() is None

    # --- state transitions ---
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

    # --- reporting ---
    def record_run(self, fetched, new, matched, analyzed):
        self.con.execute("INSERT INTO runs(ts,fetched,new,matched,analyzed) VALUES (?,?,?,?,?)",
                         (time.time(), fetched, new, matched, analyzed))
        self.con.commit()
    def stats(self):
        rows = self.con.execute("SELECT state, COUNT(*) FROM items GROUP BY state").fetchall()
        titles = self.con.execute("SELECT COUNT(*) FROM seen_titles").fetchone()[0]
        return {"items_by_state": dict(rows), "titles": titles,
                "db_bytes": os.path.getsize(self.path) if os.path.exists(self.path) else 0,
                "fresh_init": self.fresh}
