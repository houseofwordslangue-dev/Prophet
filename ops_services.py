from __future__ import annotations
import json, os, shutil, subprocess, sys, time
from pathlib import Path
from urllib.parse import parse_qs

ROOT=Path(__file__).resolve().parent
ADMIN_TOKEN=os.getenv('PM_ADMIN_TOKEN','').strip()
STATUS_FILES={
 'platform':ROOT/'data'/'reader_player_platform_status.json',
 'mirrors':ROOT/'data'/'mirror_manifest.json',
 'replication':ROOT/'data'/'replication_manifest.json',
 'ocr':ROOT/'data'/'ocr'/'status.json',
 'transcripts':ROOT/'data'/'transcripts'/'status.json',
 'adaptive':ROOT/'media-adaptive'/'status.json',
 'nightly':ROOT/'data'/'ops'/'nightly_status.json',
 'regression':ROOT/'data'/'ops'/'regression_status.json'
}

def _read(p):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return None

def _authorized(h):
 host=(h.client_address[0] if h.client_address else '')
 if host in ('127.0.0.1','::1'):return True
 if not ADMIN_TOKEN:return False
 supplied=h.headers.get('X-Admin-Token','')
 if supplied==ADMIN_TOKEN:return True
 qs=parse_qs(h.path.split('?',1)[1] if '?' in h.path else '')
 return (qs.get('token') or [''])[0]==ADMIN_TOKEN

def _json(h,data,status=200):
 b=json.dumps(data,ensure_ascii=False).encode();h.send_response(status);h.send_header('Content-Type','application/json; charset=utf-8');h.send_header('Content-Length',str(len(b)));h.end_headers();h.wfile.write(b)

def _disk():
 u=shutil.disk_usage(ROOT);return {'total':u.total,'used':u.used,'free':u.free,'percent':round(u.used/u.total*100,1) if u.total else 0}

def summary():
 s={k:_read(v) for k,v in STATUS_FILES.items()}
 mirror=s.get('mirrors') or {}; shortage=mirror.get('shortage') or []
 ocr=s.get('ocr') or {}; tr=s.get('transcripts') or {}; ad=s.get('adaptive') or {}; reg=s.get('regression') or {}; nightly=s.get('nightly') or {}
 return {'ok':True,'generatedAt':int(time.time()),'disk':_disk(),'searchDb':{'exists':(ROOT/'data'/'platform.sqlite3').exists(),'bytes':(ROOT/'data'/'platform.sqlite3').stat().st_size if (ROOT/'data'/'platform.sqlite3').exists() else 0},'mirrors':{'meetingFiveOriginTarget':max(0,len(mirror.get('items') or [])-len(shortage)),'shortage':len(shortage),'target':5},'ocr':{'generated':ocr.get('generated',0),'needsOCR':len(ocr.get('needsOCR') or []),'missing':len(ocr.get('missingLocalPdf') or []),'failed':len(ocr.get('failed') or [])},'transcripts':{'generated':tr.get('generated',0),'missing':len(tr.get('missing') or tr.get('missingLocalMedia') or []),'failed':len(tr.get('failed') or [])},'adaptive':{'generated':ad.get('generated',0),'missing':len(ad.get('missing') or []),'failed':len(ad.get('failed') or [])},'regression':reg,'nightly':nightly,'raw':s}

def run_task(name):
 allowed={
  'search':[sys.executable,'-c','from platform_services import build_search_index; print(build_search_index(True))'],
  'mirrors':[sys.executable,'scripts/build_mirror_manifest.py'],
  'assets':[sys.executable,'scripts/prepare_reader_player_assets.py'],
  'tests':[sys.executable,'-m','unittest','-v','tests/test_reader_player_runtime.py'],
  'nightly':[sys.executable,'scripts/nightly_reader_player_ops.py']}
 if name not in allowed:raise ValueError('unknown task')
 cp=subprocess.run(allowed[name],cwd=ROOT,text=True,capture_output=True,timeout=7200)
 return {'ok':cp.returncode==0,'returncode':cp.returncode,'stdout':cp.stdout[-20000:],'stderr':cp.stderr[-20000:]}

def install(handler_cls):
 old_get=handler_cls.do_GET;old_post=handler_cls.do_POST
 def do_GET(self):
  p=self.path.split('?',1)[0]
  if p=='/api/ops/summary':
   if not _authorized(self):return _json(self,{'ok':False,'error':'admin authorization required'},403)
   return _json(self,summary())
  return old_get(self)
 def do_POST(self):
  p=self.path.split('?',1)[0]
  if p=='/api/ops/run':
   if not _authorized(self):return _json(self,{'ok':False,'error':'admin authorization required'},403)
   try:
    n=min(int(self.headers.get('Content-Length') or 0),4096);d=json.loads(self.rfile.read(n).decode() or '{}');return _json(self,run_task(str(d.get('task') or '')))
   except Exception as e:return _json(self,{'ok':False,'error':str(e)},400)
  return old_post(self)
 handler_cls.do_GET=do_GET;handler_cls.do_POST=do_POST
 try:
  from chat_services import install as _install_chat
  _install_chat(handler_cls)
 except Exception as exc:print('chat services warning:',exc)
