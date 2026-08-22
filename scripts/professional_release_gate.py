#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CRITICAL_PAGES=[ROOT/x for x in ('library.html','library-all.html','reader.html','media.html','children.html','children-stories.html','children-very-short.html','children-animated.html','children-videos.html','people.html','person.html','family.html')]
REQUIRED_CHILDREN=[ROOT/'data/children/taxonomy.json',ROOT/'data/children/media-sources.json',ROOT/'data/children/stories/manifest.json',ROOT/'data/children/stories/index.json',ROOT/'data/children/animated/manifest.json',ROOT/'data/children/animated/index.json',ROOT/'data/children/animated/status.json',ROOT/'data/children/very-short/index.json',ROOT/'data/children/very-short/status.json']
REQUIRED_BOOKSTORE=[ROOT/'assets/bookstore-catalogue-bridge.js',ROOT/'assets/bookstore.js',ROOT/'assets/prophet-bookreader.js',ROOT/'assets/provider-access-ui.js',ROOT/'data/bookstore_publication_policy.json']
OCR_LEDGER=ROOT/'data/editorial/ocr_verification_ledger.json'
MAX_HTML_BYTES=180_000;MAX_STYLESHEETS=18;MAX_SCRIPTS=20
def load(p):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return None
def main():
 errors=[];warnings=[]
 for page in CRITICAL_PAGES:
  if not page.exists():errors.append(f'missing critical page: {page.name}');continue
  text=page.read_text(encoding='utf-8');size=page.stat().st_size
  if size>MAX_HTML_BYTES:warnings.append(f'{page.name}: HTML exceeds preferred {MAX_HTML_BYTES} bytes ({size})')
  styles=re.findall(r'<link\b[^>]*rel=["\']stylesheet["\'][^>]*>',text,re.I);scripts=re.findall(r'<script\b[^>]*src=["\'][^"\']+["\'][^>]*>',text,re.I)
  if len(styles)>MAX_STYLESHEETS:warnings.append(f'{page.name}: stylesheet count {len(styles)} > {MAX_STYLESHEETS}')
  if len(scripts)>MAX_SCRIPTS:warnings.append(f'{page.name}: script count {len(scripts)} > {MAX_SCRIPTS}')
  for tag in scripts:
   if not re.search(r'\b(?:defer|async|type=["\']module["\'])\b',tag,re.I):warnings.append(f'{page.name}: parser-blocking external script: {tag[:180]}')
  if re.search(r'\bjavascript\s*:',text,re.I):errors.append(f'{page.name}: javascript: URL detected')
  if re.findall(r'(?:src|href)=["\']http://[^"\']+',text,re.I):errors.append(f'{page.name}: insecure HTTP asset/link detected')
 for p in REQUIRED_CHILDREN:
  if not p.exists():errors.append(f'missing children backing data: {p.relative_to(ROOT)}')
  elif load(p) is None:errors.append(f'invalid children JSON: {p.relative_to(ROOT)}')
 illustrated=load(ROOT/'data/children/stories/manifest.json') or {};animated=load(ROOT/'data/children/animated/status.json') or {};veryshort=load(ROOT/'data/children/very-short/status.json') or {};sources=load(ROOT/'data/children/media-sources.json') or {};taxonomy=load(ROOT/'data/children/taxonomy.json') or {}
 if int(illustrated.get('count') or 0)<5000:errors.append(f"illustrated story corpus below published baseline: {illustrated.get('count',0)} < 5000")
 if int(animated.get('ready') or 0)<600 or int(animated.get('published') or 0)<600:errors.append(f"animated corpus below published baseline: ready={animated.get('ready',0)} published={animated.get('published',0)}")
 if int(veryshort.get('ready') or 0)<500 or int(veryshort.get('published') or 0)<500:errors.append(f"very-short corpus below published baseline: ready={veryshort.get('ready',0)} published={veryshort.get('published',0)}")
 channel_count=len(sources.get('sources') or [])
 if channel_count<100:warnings.append(f'children verified-channel backlog: {channel_count}/100')
 if len(taxonomy.get('subjects') or [])<12:warnings.append(f"children taxonomy subject coverage below baseline: {len(taxonomy.get('subjects') or [])}/12")
 if int(animated.get('audioReady') or 0)==0:warnings.append('animated stories use TTS/browser narration fallback; native prerecorded narration backlog remains')
 for p in REQUIRED_BOOKSTORE:
  if not p.exists():errors.append(f'missing bookstore runtime/policy: {p.relative_to(ROOT)}')
 chunks=sorted((ROOT/'data/catalogue').glob('chunk-*.json'))
 if len(chunks)<14:errors.append(f'bookstore catalogue chunk count below baseline: {len(chunks)} < 14')
 total=0
 for p in chunks:
  d=load(p)
  if d is None:errors.append(f'invalid catalogue JSON: {p.relative_to(ROOT)}')
  else:total+=len(d.get('items') or [])
 if total<650:errors.append(f'bookstore catalogue rows below published baseline: {total} < 650')
 audit_script=ROOT/'scripts/audit_bookstore_publication.py'
 if not audit_script.exists():errors.append('missing bookstore publication audit script')
 else:
  rc=subprocess.run([sys.executable,str(audit_script)],cwd=ROOT,check=False).returncode
  audit=load(ROOT/'data/audits/bookstore-publication-audit-current.json') or {}
  if rc!=0 or not audit.get('complete'):errors.append(f"published resources missing from bookstore: {audit.get('publishedMissingFromBookstoreCount','audit-failed')}")
 # OCR ledger may be empty, but every non-empty record must be structurally valid and explicitly VERIFIED.
 ledger=load(OCR_LEDGER)
 if ledger is None:errors.append('missing or invalid OCR verification ledger')
 else:
  seen=set()
  for i,r in enumerate(ledger.get('records') or []):
   if not isinstance(r,dict):errors.append(f'OCR verification record {i} is not an object');continue
   wid=str(r.get('resourceId') or '').strip();status=str(r.get('status') or '').upper();repaired=str(r.get('repairedArtifact') or '').strip();original=str(r.get('originalOcrArtifact') or '').strip();basis=r.get('verificationBasis') or []
   if not wid or status!='VERIFIED' or not repaired or not original or not isinstance(basis,list) or not basis:errors.append(f'OCR verification record {i} is incomplete or not VERIFIED')
   if wid and wid in seen:errors.append(f'duplicate OCR verification resourceId: {wid}')
   seen.add(wid)
 print('PROFESSIONAL RELEASE GATE:', 'FAIL' if errors else 'PASS')
 for x in errors:print('- HARD:',x)
 for x in warnings:print('- REVIEW:',x)
 return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
