"""Isolated bounded SQLite store for V2 acceptance evidence. No network or secrets."""
import json,sqlite3
from datetime import datetime,timedelta,timezone
from pathlib import Path
MAX_DB_BYTES=20*1024*1024
MAX_PAYLOAD_BYTES=64*1024
RETENTION_DAYS={"articles":14,"source_health":30,"edition_evidence":30}
class Store:
 def __init__(self,path):
  self.path=Path(path)
  self.path.parent.mkdir(parents=True,exist_ok=True)
  if self.path.exists() and self.path.stat().st_size>MAX_DB_BYTES:raise ValueError("database_limit_exceeded")
  self.db=sqlite3.connect(self.path)
  self.db.execute("PRAGMA journal_mode=DELETE")
  self.db.execute("PRAGMA busy_timeout=2000")
  for table in RETENTION_DAYS:
   self.db.execute(f"""CREATE TABLE IF NOT EXISTS {table}(
    language TEXT NOT NULL, identity TEXT NOT NULL, observed_at TEXT NOT NULL,
    payload TEXT NOT NULL, PRIMARY KEY(language,identity))""")
   self.db.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_date ON {table}(observed_at)")
  self.db.commit()
 def __enter__(self):return self
 def __exit__(self,*args):self.db.close()
 def _table(self,table):
  if table not in RETENTION_DAYS:raise ValueError("invalid_table")
  return table
 def size_bytes(self):
  return self.path.stat().st_size if self.path.exists() else 0
 def put(self,table,language,identity,payload,observed_at=None):
  self._table(table)
  if language not in ("en","ar") or not isinstance(identity,str) or not 1<=len(identity)<=1000:raise ValueError("invalid_identity")
  raw=json.dumps(payload,ensure_ascii=False,separators=(",",":"))
  if len(raw.encode("utf-8"))>MAX_PAYLOAD_BYTES:raise ValueError("payload_limit_exceeded")
  observed_at=observed_at or datetime.now(timezone.utc).isoformat()
  dt=datetime.fromisoformat(observed_at)
  if dt.tzinfo is None:raise ValueError("timezone_required")
  if self.size_bytes()>MAX_DB_BYTES:raise ValueError("database_limit_exceeded")
  with self.db:
   self.db.execute(f"""INSERT INTO {table}(language,identity,observed_at,payload)
    VALUES(?,?,?,?) ON CONFLICT(language,identity) DO UPDATE SET
    observed_at=excluded.observed_at,payload=excluded.payload""",(language,identity,dt.astimezone(timezone.utc).isoformat(),raw))
  if self.size_bytes()>MAX_DB_BYTES:
   with self.db:self.db.execute(f"DELETE FROM {table} WHERE language=? AND identity=?",(language,identity))
   raise ValueError("database_limit_exceeded")
 def get(self,table,language,identity):
  self._table(table)
  row=self.db.execute(f"SELECT payload FROM {table} WHERE language=? AND identity=?",(language,identity)).fetchone()
  return json.loads(row[0]) if row else None
 def count(self,table):
  self._table(table)
  return self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
 def cleanup(self,now=None):
  now=datetime.fromisoformat(now) if now else datetime.now(timezone.utc)
  if now.tzinfo is None:raise ValueError("timezone_required")
  deleted=0
  with self.db:
   for table,days in RETENTION_DAYS.items():
    cutoff=(now-timedelta(days=days)).astimezone(timezone.utc).isoformat()
    deleted+=self.db.execute(f"DELETE FROM {table} WHERE observed_at < ?",(cutoff,)).rowcount
  self.db.execute("VACUUM")
  return deleted
