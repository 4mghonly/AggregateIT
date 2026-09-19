"""Editorial filtering, fixed UAE edition windows, isolated transactional state."""
import hashlib
import json
import re
import sqlite3
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = Path(__file__).parent
UAE = timezone(timedelta(hours=4))
REGIONS = {
    'gcc': 'الخليج', 'iran': 'إيران', 'turkey': 'تركيا', 'iraq': 'العراق',
    'yemen': 'اليمن', 'sudan': 'السودان', 'sahel': 'الساحل الأفريقي',
    'north_africa': 'شمال أفريقيا', 'pakistan': 'باكستان',
    'afghanistan': 'أفغانستان', 'horn': 'القرن الأفريقي', 'levant': 'لبنان وسوريا',
    'palestine_israel': 'فلسطين / إسرائيل', 'jordan': 'الأردن',
}
SECURITY = ('war','military','missile','drone','attack','defen','diploma','sanction','embargo','border',
 'ceasefire','terror','insurgen','coup','security','troop','naval','nuclear','election','negotiat','foreign minister',
 'حرب','عسكري','عسکر','جيش','جیش','أمن','امن','صاروخ','هجوم','هجمات','دبلوما','حدود','نزاع','قتال',
 'هدنة','إرهاب','ارهاب','انقلاب','عقوبات','انتخاب','مفاوض','خارجية','احتلال','غارة','غارات','اشتباك',
 'guerre','militaire','attaque','sécurité','securite','diplom','armée','armee','conflit','cessez',
 'savaş','asker','saldırı','güvenlik','ateşkes','terör','تحریم','حمله','نظامی','جنگ','فوج','طالبان')
FINANCE = ('stock market','earnings','dividend','forex','crypto','bitcoin','nasdaq','s&p 500','bond yield',
 'share price','wall street','market rally','interest rate','inflation data','أسهم','بورصة','عملات مشفرة',
 'بيتكوين','أرباح الشركات','سعر الذهب','أسعار النفط','سعر النفط','سعر الصرف','سوق المال','الفائدة',
 'بورس','رمزارز','bourse','boursier')
UAE_SECONDARY = ('uae','emirates','abu dhabi','dubai','sharjah','ajman','fujairah','ras al khaimah',
 'umm al quwain','president','crown prince','cabinet','government','ministry','police','civil defence',
 'emergency','airport','aviation','airspace','port','border','critical infrastructure','public safety',
 'الإمارات','الامارات','أبوظبي','ابوظبي','دبي','الشارقة','عجمان','الفجيرة','رأس الخيمة','راس الخيمة',
 'أم القيوين','ام القيوين','الرئيس','ولي العهد','مجلس الوزراء','الحكومة','وزارة','شرطة','الدفاع المدني',
 'طوارئ','مطار','طيران','مجال جوي','ميناء','حدود','بنية تحتية','سلامة عامة')

def clean(value):
    value = unicodedata.normalize('NFKC', str(value or ''))
    return re.sub(r'\s+', ' ', re.sub(r'[\u200b-\u200f\u202a-\u202e\u2066-\u2069]', '', value)).strip()

def canonical(url):
    p = urlsplit(url)
    query = [(k,v) for k,v in parse_qsl(p.query) if not k.lower().startswith(('utm_', 'fbclid','gclid'))]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip('/'), urlencode(query), ''))

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def preliminary_relevant(text, language='en'):
    text = clean(text).casefold()
    security = any(k in text for k in SECURITY)
    if any(k in text for k in FINANCE) and not security:
        return False
    # Unknown-language items reach the multilingual classifier, never silently disappear.
    return security or language not in ('en', 'ar', 'fr', 'tr', 'fa', 'ur')

def uae_secondary_relevant(text):
    """Controlled lower threshold for the dedicated UAE command-news panel."""
    text=clean(text).casefold()
    if any(k in text for k in FINANCE): return False
    return any(k in text for k in UAE_SECONDARY)

def edition_window(now=None):
    """03:30, 09:30, 15:30, 21:30 UAE; most recent due six-hour edition."""
    now = (now or datetime.now(timezone.utc)).astimezone(UAE)
    anchor = now.replace(hour=3, minute=30, second=0, microsecond=0)
    end = anchor + timedelta(hours=6 * int((now-anchor).total_seconds() // 21600))
    return end-timedelta(hours=6), end

def live_window(now=None):
    # Scheduled app wakeups can arrive slightly early. Wait for the imminent
    # boundary instead of accidentally publishing the preceding edition.
    now=now or datetime.now(timezone.utc)
    start,end=edition_window(now+timedelta(minutes=2))
    remaining=(end-now).total_seconds()
    while remaining>0:
        pause=min(remaining,30)
        time.sleep(pause)
        remaining-=pause
    return start,end

def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)

class State:
    def __init__(self, directory):
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory/'arabic.sqlite', timeout=30)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS cache(key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS deliveries(edition TEXT PRIMARY KEY, status TEXT NOT NULL, message_id TEXT);
        ''')
    def get(self, key):
        row = self.db.execute('SELECT value FROM cache WHERE key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else None
    def put(self, key, value):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO cache VALUES (?,?)',(key,json.dumps(value,ensure_ascii=False)))
    def delivery(self, edition):
        return self.db.execute('SELECT status,message_id FROM deliveries WHERE edition=?',(edition,)).fetchone()
    def reserve(self, edition):
        with self.db:
            self.db.execute('INSERT INTO deliveries VALUES (?, ?, NULL)',(edition,'sending'))
    def mark(self, edition, status, message_id=None):
        with self.db:
            self.db.execute('UPDATE deliveries SET status=?,message_id=? WHERE edition=?',(status,message_id,edition))
    def close(self):
        self.db.close()
