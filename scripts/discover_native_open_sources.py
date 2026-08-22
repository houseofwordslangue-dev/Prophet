#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import argparse,json,re,time,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data'/'public_catalog_all.generated.json';QUEUE=ROOT/'private'/'acquisition_candidates.json';STATE=ROOT/'private'/'native_discovery_state.json'
UA='ProphetBiographyLibrary/7.1 native-source-discovery'
PRIORITY=['epub','txt','docx','doc','odt','rtf','html','htm','md','xml','pdf']
MAX=450*1024*1024

def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return d
def save(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def get_json(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'}),timeout=60) as r:return json.load(r)
def norm(s):
 s=str(s or '').lower();s=re.sub(r'[\u064b-\u065f\u0670]','',s);s=s.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ة','ه');return re.sub(r'[^\w\u0600-\u06ff]+',' ',s).strip()
def rights(meta):
 text=' '.join(str(meta.get(k) or '') for k in ('licenseurl','rights','possible-copyright-status','copyright-evidence-operator','copyright-evidence')).lower()
 ok=any(t in text for t in ('public domain','publicdomain','creativecommons.org/publicdomain','cc0','cc by','cc-by','cc_by'))
 return ok,text[:1000]
def kind(name):
 low=name.lower()
 for x in PRIORITY:
  if low.endswith('.'+x):return x
 return ''
def best_file(files):
 rows=[]
 for f in files:
  n=str(f.get('name') or '');k=kind(n)
  if not k:continue
  try:s=int(f.get('size') or 0)
  except Exception:s=0
  if s and (s<1024 or s>MAX):continue
  if k=='pdf' and ('_text.pdf' in n.lower() or 'searchable' in n.lower()):rank=9
  else:rank=PRIORITY.index(k)
  rows.append((rank,s or MAX,n,k))
 if not rows:return None
 _,_,n,k=sorted(rows)[0];return n,k
def search_archive(title,author=''):
 q='title:("'+str(title).replace('"','')+'")'
 if author:q+=' AND creator:("'+str(author).replace('"','')+'")'
 u='https://archive.org/advancedsearch.php?'+urllib.parse.urlencode({'q':q,'fl[]':['identifier','title','creator'],'rows':8,'page':1,'output':'json'},doseq=True)
 try:return get_json(u).get('response',{}).get('docs',[])
 except Exception:return []
def exactish(row,doc):
 a=norm(row.get('title'));b=norm(doc.get('title'));return bool(a and b and (a==b or (len(a)>8 and (a in b or b in a))))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=60);a=ap.parse_args();cat=load(CAT,{'items':[]});q=load(QUEUE,{'schema':'strict-unrestricted-candidates-v1','rotationEnabled':True,'items':[]});state=load(STATE,{'cursor':0,'checked':{}});items=[x for x in cat.get('items',[]) if x.get('access')!='PUBLIC_FULL_TEXT'];cursor=int(state.get('cursor',0))%max(1,len(items));seen={str(x.get('workId') or '') for x in q.get('items',[])};checked=added=0
 for off in range(len(items)):
  if checked>=a.limit:break
  row=items[(cursor+off)%len(items)];wid=str(row.get('id') or '')
  if not wid or wid in seen:continue
  checked+=1;found=None
  for doc in search_archive(row.get('title'),row.get('author')):
   if not exactish(row,doc):continue
   ident=str(doc.get('identifier') or '')
   if not ident:continue
   try:meta=get_json('https://archive.org/metadata/'+urllib.parse.quote(ident))
   except Exception:continue
   ok,evidence=rights(meta.get('metadata',{}) if isinstance(meta,dict) else {})
   if not ok:continue
   bf=best_file(meta.get('files',[]))
   if not bf:continue
   name,k=bf;found={'workId':wid,'catalogueId':wid,'titleOriginal':row.get('title'),'titleAr':row.get('title') if re.search(r'[\u0600-\u06ff]',str(row.get('title') or '')) else None,'author':row.get('author'),'language':'ar' if re.search(r'[\u0600-\u06ff]',str(row.get('title') or '')) else 'en','format':k,'sourceRepository':'Internet Archive','sourceIdentifier':ident,'sourceUrl':'https://archive.org/details/'+ident,'downloadUrl':'https://archive.org/download/'+urllib.parse.quote(ident)+'/'+urllib.parse.quote(name),'rightsEvidence':'Public/open rights metadata: '+evidence[:500],'rightsEvidenceUrl':'https://archive.org/metadata/'+ident,'subjects':[row.get('category') or 'المصادر'],'siteSections':['المصادر والدراسات'],'nativeSearchCompleted':True,'selectedByPriority':k};break
  state.setdefault('checked',{})[wid]={'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'found':bool(found)}
  if found:q.setdefault('items',[]).append(found);seen.add(wid);added+=1
 state['cursor']=(cursor+checked)%max(1,len(items));state['updatedAt']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());save(STATE,state);save(QUEUE,q);print(json.dumps({'checked':checked,'added':added,'queueTotal':len(q.get('items',[])),'cursor':state['cursor']},ensure_ascii=False))
if __name__=='__main__':main()
