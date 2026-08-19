#!/usr/bin/env python3
"""Fetch configured source pages and store exact short excerpts/metadata.

The importer never summarizes or rewrites fetched source wording. Public output omits source identity;
private provenance preserves verification data.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import quote_plus
from html import unescape
from html.parser import HTMLParser
import json,re,hashlib,datetime,argparse
ROOT=Path(__file__).resolve().parent
CONFIG=ROOT/'private'/'source_import_config.json';PUBLIC=ROOT/'data'/'imported_quotes.json';PRIVATE=ROOT/'private'/'import_cache.json';PROVENANCE=ROOT/'private'/'import_provenance.json';MEDIA=ROOT/'data'/'imported_media.json';TARGETS=ROOT/'private'/'media_targets.json';QURAN=ROOT/'data'/'quran_corpus.json';QURAN_OVERLAY=ROOT/'data'/'quran_interpretive_overlay.json';QURAN_PROV=ROOT/'private'/'quran_interpretive_provenance.json';UA='Mozilla/5.0 (compatible; PropheticBiographyResearchBot/1.0; editorial-fetch)'
def norm_ar(s):
 s=re.sub(r'[\u064b-\u065f\u0670\u06d6-\u06ed]','',str(s or ''));s=re.sub(r'[^\u0600-\u06ff]+',' ',s);return re.sub(r'\s+',' ',s).strip()
def sync_quran_context(text,src):
 if not QURAN.exists():return 0
 try:q=json.loads(QURAN.read_text(encoding='utf-8'))
 except Exception:return 0
 try:overlay=json.loads(QURAN_OVERLAY.read_text(encoding='utf-8')) if QURAN_OVERLAY.exists() else {'version':'5.2.0','refs':{}}
 except Exception:overlay={'version':'5.2.0','refs':{}}
 refs=overlay.setdefault('refs',{});nt=norm_ar(text);prophet_terms=('محمد','النبي','الرسول','المصطفى','الحبيب');changed=[]
 for v in q.get('verses',[]):
  words=norm_ar(v.get('ar','')).split()
  if len(words)<5:continue
  needles=[' '.join(words[:min(8,len(words))])]
  if len(words)>=14:needles.append(' '.join(words[len(words)//2:len(words)//2+7]))
  hit=-1;needle=''
  for candidate in needles:
   if len(candidate)<18:continue
   hit=nt.find(candidate)
   if hit>=0:needle=candidate;break
  if hit<0:continue
  ctx=nt[max(0,hit-550):hit+len(needle)+550]
  if not any(term in ctx for term in prophet_terms):continue
  ref=f"{v.get('surah')}:{v.get('ayah')}";entry=refs.setdefault(ref,{'interpretiveReference':True,'interpretiveTags':[]});tags=entry.setdefault('interpretiveTags',[])
  if 'verified-import' not in tags:tags.append('verified-import');changed.append(ref)
 if changed:
  overlay['updated']=datetime.datetime.now(datetime.timezone.utc).isoformat();QURAN_OVERLAY.parent.mkdir(parents=True,exist_ok=True);QURAN_OVERLAY.write_text(json.dumps(overlay,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  try:prov=json.loads(QURAN_PROV.read_text(encoding='utf-8'))
  except Exception:prov={'version':'5.2.0','verses':{}}
  for ref in changed:
   arr=prov.setdefault('verses',{}).setdefault(ref,[]);sid=src.get('id','')
   if sid and sid not in arr:arr.append(sid)
  prov['updated']=datetime.datetime.now(datetime.timezone.utc).isoformat();QURAN_PROV.parent.mkdir(parents=True,exist_ok=True);QURAN_PROV.write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return len(changed)
class TextExtractor(HTMLParser):
 def __init__(self):super().__init__();self.skip=0;self.parts=[]
 def handle_starttag(self,tag,attrs):
  if tag in {'script','style','noscript','svg'}:self.skip+=1
 def handle_endtag(self,tag):
  if tag in {'script','style','noscript','svg'} and self.skip:self.skip-=1
 def handle_data(self,data):
  if not self.skip and data.strip():self.parts.append(data.strip())
def fetch(url,timeout=12):
 req=Request(url,headers={'User-Agent':UA,'Accept-Language':'ar,en;q=0.8'})
 with urlopen(req,timeout=timeout) as r:raw=r.read(2_000_000);ctype=r.headers.get_content_charset() or 'utf-8'
 return raw.decode(ctype,errors='replace')
def sentences(text):
 text=unescape(text);text=re.sub(r'\s+',' ',text).strip();return [s.strip() for s in re.split(r'(?<=[.!؟])\s+|(?<=。)\s*',text) if s.strip()]
def pick_exact(text,keywords,max_words):
 if max_words<=0:return ''
 kws=[k.casefold() for k in keywords]
 for s in sentences(text):
  wc=len(s.split())
  if 3<=wc<=max_words and any(k in s.casefold() for k in kws):return s
 return ''
def youtube_meta(url):
 try:return json.loads(fetch('https://www.youtube.com/oembed?url='+quote_plus(url)+'&format=json'))
 except Exception:return {'title':'','thumbnail_url':'','author_name':''}
def run_import(live=True,limit=30):
 cfg=json.loads(CONFIG.read_text(encoding='utf-8'));pub=json.loads(PUBLIC.read_text(encoding='utf-8')) if PUBLIC.exists() else {'version':'5.2.0','items':[]};existing={x['id']:x for x in pub.get('items',[]) if x.get('id')};cache=json.loads(PRIVATE.read_text(encoding='utf-8')) if PRIVATE.exists() else {'version':'5.2.0','items':{}};medias=[];targets=json.loads(TARGETS.read_text(encoding='utf-8')) if TARGETS.exists() else {}
 if MEDIA.exists():
  try:medias=json.loads(MEDIA.read_text(encoding='utf-8')).get('items',[])
  except Exception:medias=[]
 media_by={x['id']:x for x in medias if x.get('id')};report={'checked':0,'imported':0,'media':0,'quran_refs':0,'skipped':0,'errors':[],'live':bool(live)}
 if not live:return report
 for src in cfg.get('sources',[])[:max(1,min(limit,60))]:
  report['checked']+=1;sid=src['id'];url=src.get('url','')
  if src.get('enabled',True) is False or not url:report['skipped']+=1;continue
  try:
   if src.get('kind')=='youtube':
    meta=youtube_meta(url);mid='media-'+hashlib.sha256(url.encode()).hexdigest()[:14];media_by[mid]={'id':mid,'kind':'video','titleEn':meta.get('title',''),'titleAr':meta.get('title',''),'titleFr':meta.get('title',''),'summaryEn':'','summaryAr':'','summaryFr':'','url':url,'embed':'','language':src.get('lang','ar'),'topics':src.get('categories',[]),'transcriptStatus':'external','duration':'external','chapters':[],'thumbnail':meta.get('thumbnail_url',''),'sourceOnly':True};targets[mid]=url;cache['items'][mid]={'source_id':sid,'url':url,'title':meta.get('title',''),'author':meta.get('author_name',''),'fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat()};report['media']+=1;continue
   html=fetch(url);x=TextExtractor();x.feed(html);txt=' '.join(x.parts);report['quran_refs']+=sync_quran_context(txt,src);tgs=src.get('targets') if isinstance(src.get('targets'),list) else []
   if not tgs and src.get('section') in {'light','prophet','messenger','human'}:report['skipped']+=1;continue
   if not tgs:tgs=[{'section':src.get('section',''),'conceptAr':'','keywords':src.get('keywords',[])}]
   imported_here=0
   try:prov=json.loads(PROVENANCE.read_text(encoding='utf-8')) if PROVENANCE.exists() else {'items':{}}
   except Exception:prov={'items':{}}
   for target in tgs:
    section=str(target.get('section','')).strip();concept=str(target.get('conceptAr','')).strip()
    if section in {'light','prophet','messenger','human'} and not concept:continue
    q=pick_exact(txt,target.get('keywords',[]),int(src.get('max_words',22)))
    if not q:continue
    qid='live-'+hashlib.sha256((sid+'|'+section+'|'+concept+'|'+q).encode()).hexdigest()[:16];existing[qid]={'id':qid,'section':section,'categories':src.get('categories',[]),'lang':src.get('lang','ar'),'kind':'verbatim','text':q,'topicEn':'','topicAr':concept,'strictConcept':concept,'sourceOnly':True,'exactExtract':True};stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();cache['items'][qid]={'source_id':sid,'url':url,'quote':q,'sha256':hashlib.sha256(q.encode()).hexdigest(),'fetched_at':stamp,'strict_verified':True};prov.setdefault('items',{})[qid]={'source_id':sid,'url':url,'fetched_at':stamp,'sha256':hashlib.sha256(q.encode()).hexdigest(),'strict_verified':True};imported_here+=1;report['imported']+=1
   if imported_here:PROVENANCE.parent.mkdir(parents=True,exist_ok=True);PROVENANCE.write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
   else:report['skipped']+=1
  except Exception as e:report['errors'].append({'source_id':sid,'error':str(e)[:180]})
 PUBLIC.parent.mkdir(parents=True,exist_ok=True);pub['items']=list(existing.values());pub['generated']=datetime.datetime.now(datetime.timezone.utc).isoformat();PUBLIC.write_text(json.dumps(pub,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');PRIVATE.parent.mkdir(parents=True,exist_ok=True);PRIVATE.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');MEDIA.parent.mkdir(parents=True,exist_ok=True);MEDIA.write_text(json.dumps({'version':'5.2.0','items':list(media_by.values())},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');TARGETS.parent.mkdir(parents=True,exist_ok=True);TARGETS.write_text(json.dumps(targets,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return report
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--offline',action='store_true');ap.add_argument('--limit',type=int,default=30);a=ap.parse_args();print(json.dumps(run_import(live=not a.offline,limit=a.limit),ensure_ascii=False,indent=2))
