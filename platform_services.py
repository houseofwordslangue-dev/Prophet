from __future__ import annotations

import hashlib, hmac, json, os, re, secrets, sqlite3, time, unicodedata
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data' / 'platform.sqlite3'
TELEMETRY = ROOT / 'data' / 'runtime_telemetry.ndjson'
SEARCH_SOURCES = [
    ROOT/'data'/'ingested_library.json', ROOT/'data'/'published_user_books.json', ROOT/'data'/'generated_epubs.json',
    ROOT/'data'/'people.json', ROOT/'data'/'expanded_people_135.json', ROOT/'data'/'expanded_biographies_135_full.json',
    ROOT/'data'/'family_people.json', ROOT/'data'/'family_biographies.json', ROOT/'data'/'imported_media.json',
    ROOT/'data'/'editorial'/'publication_manifest.json', ROOT/'data'/'editorial'/'publication_supplement.json'
]

AR_DIACRITICS = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
NON_WORD = re.compile(r'[^0-9A-Za-z\u0600-\u06FF\s]+')

def normalize_ar(text: str) -> str:
    s = unicodedata.normalize('NFKC', str(text or '')).lower().replace('ـ','')
    s = AR_DIACRITICS.sub('', s)
    table = str.maketrans({'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ي','ؤ':'و','ئ':'ي','ة':'ه'})
    s = s.translate(table)
    return re.sub(r'\s+', ' ', NON_WORD.sub(' ', s)).strip()

def _conn():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=20)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    return c

def init_db():
    with _conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS search_docs(id TEXT PRIMARY KEY, kind TEXT, title TEXT, author TEXT, url TEXT, body TEXT, norm_title TEXT, norm_body TEXT, updated INTEGER);
        CREATE INDEX IF NOT EXISTS idx_search_kind ON search_docs(kind);
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE COLLATE NOCASE, salt BLOB, password_hash BLOB, created INTEGER);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id INTEGER, expires INTEGER, FOREIGN KEY(user_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS sync_state(user_id INTEGER, scope TEXT, item_key TEXT, payload TEXT, updated INTEGER, PRIMARY KEY(user_id,scope,item_key));
        ''')

def _iter_records(obj):
    if isinstance(obj, list):
        for x in obj: yield from _iter_records(x)
    elif isinstance(obj, dict):
        if any(k in obj for k in ('id','workId','title','titleAr','name','canonicalNameAr')):
            yield obj
        for k,v in obj.items():
            if k not in ('paragraphs','body','content','text','summary','biography') and isinstance(v,(list,dict)):
                yield from _iter_records(v)

def _pick(d, *keys):
    for k in keys:
        v=d.get(k)
        if isinstance(v,str) and v.strip(): return v.strip()
    return ''

def _body(d):
    out=[]
    for k in ('body','content','text','summary','summaryAr','summaryEn','summaryFr','biography','bio','description','abstract'):
        v=d.get(k)
        if isinstance(v,str): out.append(v)
        elif isinstance(v,list): out.extend(str(x) for x in v if isinstance(x,(str,int,float)))
    p=d.get('paragraphs')
    if isinstance(p,list): out.extend(str(x) for x in p if isinstance(x,str))
    return '\n'.join(out)[:250000]

def _url_for(d, kind):
    if d.get('url') and str(d.get('url')).startswith(('/', 'http')): return str(d['url'])
    rid=str(d.get('id') or d.get('workId') or '')
    if kind=='person': return f'person.html?id={rid}'
    if kind=='media': return f'media.html?v={rid}'
    if kind=='book': return f'reader.html?id={rid}'
    return str(d.get('publicUrl') or d.get('href') or '')

def build_search_index(force=False):
    init_db(); stamp=int(time.time()); rows={}
    for path in SEARCH_SOURCES:
        if not path.exists(): continue
        try: data=json.loads(path.read_text(encoding='utf-8'))
        except Exception: continue
        for d in _iter_records(data):
            rid=str(d.get('id') or d.get('workId') or d.get('slug') or '')
            title=_pick(d,'titleAr','title','canonicalNameAr','nameAr','name','titleEn','titleFr','titleOriginal')
            if not rid or not title: continue
            pstr=str(path).lower(); kind='article'
            if 'media' in pstr: kind='media'
            elif 'people' in pstr or 'biograph' in pstr or 'family' in pstr: kind='person'
            elif 'library' in pstr or 'books' in pstr or 'epub' in pstr: kind='book'
            author=_pick(d,'author','authorAr','creator','byline')
            body=_body(d)
            key=f'{kind}:{rid}'
            prev=rows.get(key)
            if prev and len(prev[5])>=len(body): continue
            rows[key]=(key,kind,title,author,_url_for(d,kind),body,normalize_ar(title+' '+author),normalize_ar(body),stamp)
    # Include editorial draft batches without assuming a fixed batch count.
    drafts=ROOT/'data'/'editorial'/'drafts'
    if drafts.exists():
        for path in drafts.rglob('batch-*.json'):
            try:data=json.loads(path.read_text(encoding='utf-8'))
            except Exception:continue
            for d in data.get('drafts',[]):
                rid=str(d.get('id') or ''); title=_pick(d,'titleAr','title','titleEn','titleFr')
                if not rid or not title:continue
                body=_body(d); author=_pick(d,'author','byline')
                key='article:'+rid
                rows[key]=(key,'article',title,author,f'feature.html?id={rid}',body,normalize_ar(title+' '+author),normalize_ar(body),stamp)
    with _conn() as c:
        if force or not c.execute('SELECT 1 FROM search_docs LIMIT 1').fetchone(): c.execute('DELETE FROM search_docs')
        c.executemany('INSERT OR REPLACE INTO search_docs VALUES(?,?,?,?,?,?,?,?,?)', rows.values())
    return len(rows)

def search(query, limit=30, kind=''):
    q=normalize_ar(query); terms=[x for x in q.split() if len(x)>1][:12]
    if not terms:return []
    init_db()
    where=[]; args=[]
    for t in terms:
        where.append('(norm_title LIKE ? OR norm_body LIKE ?)'); args.extend([f'%{t}%',f'%{t}%'])
    sql='SELECT * FROM search_docs WHERE '+' AND '.join(where)
    if kind: sql+=' AND kind=?'; args.append(kind)
    sql+=' LIMIT 600'
    with _conn() as c: rows=c.execute(sql,args).fetchall()
    phrase=q
    scored=[]
    for r in rows:
        nt,nb=r['norm_title'],r['norm_body']; score=0.0
        if phrase and phrase in nt:score+=70
        elif phrase and phrase in nb:score+=16
        for t in terms:
            if t in nt:score+=12
            score+=min(8, nb.count(t))*1.2
        score+=max(0,10-len(nt)/30)
        snippet=r['body'][:260].replace('\n',' ') if r['body'] else ''
        scored.append((score,dict(id=r['id'],kind=r['kind'],title=r['title'],author=r['author'],url=r['url'],snippet=snippet,score=round(score,2))))
    scored.sort(key=lambda x:(-x[0],x[1]['title']))
    return [x[1] for x in scored[:max(1,min(limit,100))]]

def _password_hash(password:str,salt:bytes)->bytes:
    return hashlib.pbkdf2_hmac('sha256',password.encode(),salt,260000)

def register(email,password):
    email=str(email or '').strip().lower(); password=str(password or '')
    if '@' not in email or len(password)<10: raise ValueError('valid email and password of at least 10 characters required')
    salt=secrets.token_bytes(16); ph=_password_hash(password,salt)
    with _conn() as c:
        c.execute('INSERT INTO users(email,salt,password_hash,created) VALUES(?,?,?,?)',(email,salt,ph,int(time.time())))
    return login(email,password)

def login(email,password):
    with _conn() as c:r=c.execute('SELECT * FROM users WHERE email=?',(str(email).lower(),)).fetchone()
    if not r or not hmac.compare_digest(r['password_hash'],_password_hash(password,r['salt'])):raise ValueError('invalid credentials')
    token=secrets.token_urlsafe(32); th=hashlib.sha256(token.encode()).hexdigest(); exp=int(time.time())+60*60*24*30
    with _conn() as c:c.execute('INSERT OR REPLACE INTO sessions VALUES(?,?,?)',(th,r['id'],exp))
    return {'token':token,'expires':exp,'email':r['email']}

def _user(handler):
    a=handler.headers.get('Authorization','')
    if not a.startswith('Bearer '):return None
    th=hashlib.sha256(a[7:].encode()).hexdigest()
    with _conn() as c:r=c.execute('SELECT user_id FROM sessions WHERE token_hash=? AND expires>?',(th,int(time.time()))).fetchone()
    return int(r['user_id']) if r else None

def telemetry_summary():
    rows=[]
    if TELEMETRY.exists():
        for line in TELEMETRY.read_text(encoding='utf-8',errors='ignore').splitlines()[-10000:]:
            try:rows.append(json.loads(line))
            except:pass
    def nums(key):return [float(x[key]) for x in rows if isinstance(x.get(key),(int,float))]
    def avg(a):return round(sum(a)/len(a),2) if a else 0
    events={}
    for r in rows:events[r.get('event','unknown')]=events.get(r.get('event','unknown'),0)+1
    return {'ok':True,'events':len(rows),'byEvent':events,'avgStartupMs':avg(nums('startupMs')),'avgBufferMs':avg(nums('bufferMs')),'avgRenderMs':avg(nums('renderMs')),'avgSearchMs':avg(nums('searchMs')),'last':rows[-50:]}

def _json(handler,data,status=200):
    payload=json.dumps(data,ensure_ascii=False).encode('utf-8'); handler.send_response(status); handler.send_header('Content-Type','application/json; charset=utf-8'); handler.send_header('Content-Length',str(len(payload))); handler.end_headers(); handler.wfile.write(payload)

def _read_json(handler,max_bytes=2_000_000):
    n=min(int(handler.headers.get('Content-Length') or 0),max_bytes); return json.loads(handler.rfile.read(n).decode('utf-8','replace') or '{}')

def install(handler_cls, root=None):
    init_db()
    try: build_search_index(False)
    except Exception as e: print('search index warning:',e)
    old_get=handler_cls.do_GET; old_post=handler_cls.do_POST
    def do_GET(self):
        p=self.path.split('?',1)[0]; qs=parse_qs(self.path.split('?',1)[1] if '?' in self.path else '')
        if p=='/api/search':
            started=time.perf_counter(); out=search((qs.get('q') or [''])[0],int((qs.get('limit') or ['30'])[0]),(qs.get('kind') or [''])[0]); _json(self,{'ok':True,'results':out,'elapsedMs':round((time.perf_counter()-started)*1000,2)}); return
        if p=='/api/search/rebuild':
            _json(self,{'ok':True,'indexed':build_search_index(True)}); return
        if p=='/api/telemetry/summary':
            _json(self,telemetry_summary()); return
        if p=='/api/sync':
            uid=_user(self)
            if not uid:_json(self,{'ok':False,'error':'authentication required'},401); return
            scope=(qs.get('scope') or [''])[0]
            with _conn() as c:
                rr=c.execute('SELECT scope,item_key,payload,updated FROM sync_state WHERE user_id=?'+(' AND scope=?' if scope else ''),(uid,scope) if scope else (uid,)).fetchall()
            _json(self,{'ok':True,'items':[{'scope':r['scope'],'key':r['item_key'],'payload':json.loads(r['payload']),'updated':r['updated']} for r in rr]}); return
        return old_get(self)
    def do_POST(self):
        p=self.path.split('?',1)[0]
        if p in ('/api/account/register','/api/account/login'):
            try:
                d=_read_json(self); out=register(d.get('email'),d.get('password')) if p.endswith('register') else login(d.get('email'),d.get('password')); _json(self,{'ok':True,**out})
            except Exception as e:_json(self,{'ok':False,'error':str(e)},400)
            return
        if p=='/api/sync':
            uid=_user(self)
            if not uid:_json(self,{'ok':False,'error':'authentication required'},401); return
            try:
                d=_read_json(self); items=d.get('items') or []; now=int(time.time()*1000)
                with _conn() as c:
                    for x in items:
                        scope=str(x.get('scope') or 'general')[:80]; key=str(x.get('key') or '')[:240]
                        if key:c.execute('INSERT OR REPLACE INTO sync_state VALUES(?,?,?,?,?)',(uid,scope,key,json.dumps(x.get('payload'),ensure_ascii=False),int(x.get('updated') or now)))
                _json(self,{'ok':True,'saved':len(items)})
            except Exception as e:_json(self,{'ok':False,'error':str(e)},400)
            return
        return old_post(self)
    handler_cls.do_GET=do_GET; handler_cls.do_POST=do_POST
