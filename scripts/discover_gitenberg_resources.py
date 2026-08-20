#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request,urlopen
import argparse,json,os,re,time
ROOT=Path(__file__).resolve().parents[1]; QUEUE=ROOT/'private'/'acquisition_candidates.json'
UA='ProphetBiographyLibrary/6.9 GITenbergDiscovery'; QUERIES=('Muhammad','Mohammed','Mahomet','Islam','Koran','Quran','Ghazzali')
def headers():
 h={'User-Agent':UA,'Accept':'application/vnd.github+json'}; t=os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
 if t:h['Authorization']='Bearer '+t
 return h
def fetch(u):
 with urlopen(Request(u,headers=headers()),timeout=45) as r:return r.read()
def jget(u):return json.loads(fetch(u).decode('utf-8','replace'))
def readj(p,d):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return d
def meta(text,name):
 def one(p):
  m=re.search(p,text,re.M|re.I);return m.group(1).strip(" '\"") if m else ''
 rights=one(r'^rights:\s*(.+)$');title=one(r'^title:\s*(.+)$');lang=one(r'^language:\s*([^\s#]+)') or 'en';gid=one(r'^\s*gutenberg:\s*[\'\"]?(\d+)')
 if not gid:
  m=re.search(r'_(\d+)$',name);gid=m.group(1) if m else ''
 subs=[m.group(1).strip() for m in re.finditer(r'^\s*-\s*!?lcsh\s*[\'\"]?(.+?)[\'\"]?\s*$',text,re.M|re.I)];hay=' '.join([title,*subs]).lower()
 if 'public domain' not in rights.lower() or not gid or 'fiction' in hay:return None
 if not any(k in hay for k in ('muhammad','mohammed','mahomet','islam','qur','koran','ghazzali','ghazali')):return None
 return gid,title or name.rsplit('_',1)[0].replace('-',' '),lang,rights,subs
def txt(full,branch,gid):
 a=jget(f'https://api.github.com/repos/{full}/contents/?ref={branch}');f=[x for x in a if x.get('type')=='file' and str(x.get('name') or '').lower().endswith('.txt') and x.get('download_url')] if isinstance(a,list) else []
 f.sort(key=lambda x:(0 if str(x.get('name')).lower()==gid+'.txt' else 1 if gid in str(x.get('name')).lower() else 2,str(x.get('name'))));return str(f[0].get('download_url') or '') if f else ''
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=12);a=ap.parse_args();q=readj(QUEUE,{'schema':'strict-unrestricted-candidates-v1','rotationEnabled':True,'items':[]});items=q.setdefault('items',[]);seen={str(x.get('sourceIdentifier') or '') for x in items};added=[];repos=set()
 for term in QUERIES:
  if len(added)>=a.limit:break
  try:r=jget('https://api.github.com/search/repositories?q='+quote_plus('org:GITenberg '+term)+'&per_page=20')
  except Exception:continue
  for repo in r.get('items',[]) if isinstance(r,dict) else []:
   if len(added)>=a.limit:break
   full=str(repo.get('full_name') or '');name=str(repo.get('name') or '');branch=str(repo.get('default_branch') or 'master')
   if not full.startswith('GITenberg/') or full in repos:continue
   repos.add(full)
   try:
    raw=f'https://raw.githubusercontent.com/{full}/{branch}/metadata.yaml';m=meta(fetch(raw).decode('utf-8','replace'),name)
    if not m or m[0] in seen:continue
    mirror=txt(full,branch,m[0]);
    if not mirror:continue
   except Exception:continue
   gid,title,lang,rights,subs=m;hay=' '.join([title,*subs]).lower();subjects=['الدراسات الإسلامية','المصادر والدراسات']
   if any(k in hay for k in ('muhammad','mohammed','mahomet')):subjects.insert(0,'السيرة النبوية')
   if any(k in hay for k in ('qur','koran')):subjects.insert(0,'القرآن وعلومه')
   items.append({'workId':'gutenberg-'+gid,'titleOriginal':title,'author':'','language':lang,'format':'txt','sourceRepository':'Project Gutenberg','sourceIdentifier':gid,'sourceUrl':f'https://www.gutenberg.org/ebooks/{gid}','downloadUrl':mirror,'rightsEvidence':rights,'rightsEvidenceUrl':raw,'subjects':subjects,'siteSections':['المصادر والدراسات'],'transportMirror':'GITenberg','mirrorRepository':full,'discoveredBy':'gitenberg-github-public-domain-metadata'});seen.add(gid);added.append(gid)
 if added:q['lastGITenbergDiscoveryAt']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());QUEUE.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'added':len(added),'addedIds':added,'queueTotal':len(items)},ensure_ascii=False))
if __name__=='__main__':main()
