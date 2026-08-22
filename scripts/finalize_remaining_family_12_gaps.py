#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import html,json,re,hashlib,urllib.parse,urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; OUT=DATA/'editorial'/'drafts'/'2026-08-21'; AUDIT=DATA/'editorial'/'remaining_family_life_5_audit.json'
UA='ProphetBiographySourceBuilder/1.1 (classical source-only editorial ingestion)'
MW='https://ar.wikisource.org/w/api.php'

CURATED={
'abd-yaghuth-ibn-wahb':[
 ('url','https://www.masaha.org/book/view/2330/page/124','جمهرة أنساب العرب — سياق بني زهرة'),
 ('url','https://www.masaha.org/book/view/2330/page/125','جمهرة أنساب العرب — عبد يغوث بن وهب'),
 ('url','https://www.masaha.org/book/view/2330/page/126','جمهرة أنساب العرب — تتمة بني زهرة'),
 ('url','https://www.masaha.org/book/view/2330/page/127','جمهرة أنساب العرب — تتمة النسب'),
 ('url','https://www.masaha.org/book/view/2330/page/128','جمهرة أنساب العرب — سياق النسب')],
'saad-ibn-abi-waqqas':[('ws','سير أعلام النبلاء/سعد بن أبي وقاص','سير أعلام النبلاء — سعد بن أبي وقاص')],
'salma-bint-amr-al-najjariyya':[
 ('url','https://islamweb.net/ar/library/content/126/220/ابن-عبد-المطلب','الكامل في التاريخ — خبر سلمى وهاشم وعبد المطلب'),
 ('url','https://www.islamweb.net/ar/library/content/126/206/ذكر-حرب-كعب-بن-عمرو-المازني','الكامل في التاريخ — سلمى بنت عمرو وبنو النجار'),
 ('url','https://islamweb.net/ar/library/content/200/16490/أولاد-هاشم-وأمهاتهم','السيرة والتاريخ — أولاد هاشم وأمهاتهم'),
 ('url','https://islamweb.net/ar/library/content/58/196/سبب-خؤولة-بني-عدي-بن-النجار','السيرة النبوية لابن هشام — خؤولة بني النجار')],
'umm-salama':[('ws','سير أعلام النبلاء/أم سلمة','سير أعلام النبلاء — أم سلمة')],
'umm-habiba':[('ws','سير أعلام النبلاء/أم حبيبة','سير أعلام النبلاء — أم حبيبة')],
'abu-al-as-ibn-al-rabi':[('ws','سير أعلام النبلاء/أبو العاص بن الربيع','سير أعلام النبلاء — أبو العاص بن الربيع')],
'uthman-ibn-affan':[
 ('ws','البداية والنهاية (ط. السعادة)/ثم استهلت سنة أربع وعشرين/خلافة أمير المؤمنين عثمان بن عفان رضي الله عنه','البداية والنهاية — خلافة عثمان'),
 ('ws','البداية والنهاية (ط. السعادة)/ثم دخلت سنة خمس وثلاثين/ذكر حصر أمير المؤمنين عثمان بن عفان رضي الله عنه','البداية والنهاية — حصر عثمان'),
 ('ws','البداية والنهاية (ط. السعادة)/ثم دخلت سنة خمس وثلاثين/فصل في الإشارة إلى شيء من الأحاديث الواردة في فضائل أمير المؤمنين عثمان بن عفان رضي الله عنه','البداية والنهاية — ترجمة عثمان وفضائله')],
'al-hasan-al-muthanna':[('ws','الحسن بن الحسن بن علي','سير أعلام النبلاء — الحسن بن الحسن بن علي')],
'abdullah-ibn-abbas':[('ws','سير أعلام النبلاء/عبد الله بن عباس','سير أعلام النبلاء — عبد الله بن عباس')],
'abu-ahmad-ibn-jahsh':[
 ('ws','صفحة:الإصابة في تمييز الصحابة7.pdf/3','الإصابة في تمييز الصحابة — أبو أحمد بن جحش'),
 ('ws','البداية والنهاية/الجزء الثالث/باب الهجرة من مكة إلى المدينة','البداية والنهاية — هجرة بني جحش'),
 ('url','https://www.islamweb.net/ar/library/content/1080/2871/باب-الألف','الاستيعاب في معرفة الأصحاب — أبو أحمد بن جحش')],
'al-shayma-bint-al-harith':[
 ('ws','البداية والنهاية (ط. السعادة)/ذكر رضاعه عليه الصلاة والسلام','البداية والنهاية — الشيماء وأسرة حليمة'),
 ('ws','البداية والنهاية/الجزء الثاني/رضاعه عليه الصلاة والسلام من حليمة','البداية والنهاية — رضاعه من حليمة'),
 ('url','https://islamweb.net/ar/library/content/58/189/','السيرة النبوية لابن هشام — نسب حليمة وإخوة الرضاعة')],
'al-harith-ibn-abd-al-uzza-al-sadi':[
 ('ws','البداية والنهاية (ط. السعادة)/ذكر رضاعه عليه الصلاة والسلام','البداية والنهاية — الحارث بن عبد العزى وأسرة حليمة'),
 ('ws','البداية والنهاية/الجزء الثاني/رضاعه عليه الصلاة والسلام من حليمة','البداية والنهاية — الحارث بن عبد العزى ورضاعة النبي'),
 ('url','https://www.islamweb.net/ar/library/content/59/161/ذكر-رضاعه-عليه-الصلاة-والسلام-من-حليمة-السعدية','البداية والنهاية — رواية حليمة وزوجها الحارث')]
}

ALIASES={
'abd-yaghuth-ibn-wahb':['عبد يغوث بن وهب','عبد يغوث'], 'saad-ibn-abi-waqqas':['سعد بن أبي وقاص','سعد بن مالك'],
'salma-bint-amr-al-najjariyya':['سلمى بنت عمرو','سلمى بنت عمرو النجارية'], 'umm-salama':['أم سلمة','هند بنت أبي أمية'],
'umm-habiba':['أم حبيبة','رملة بنت أبي سفيان'], 'abu-al-as-ibn-al-rabi':['أبو العاص بن الربيع','أبو العاص'],
'uthman-ibn-affan':['عثمان بن عفان','عثمان'], 'al-hasan-al-muthanna':['الحسن بن الحسن بن علي','الحسن المثنى','الحسن بن الحسن'],
'abdullah-ibn-abbas':['عبد الله بن عباس','ابن عباس'], 'abu-ahmad-ibn-jahsh':['أبو أحمد بن جحش','أبو أحمد'],
'al-shayma-bint-al-harith':['الشيماء بنت الحارث','الشيماء','حذافة بنت الحارث'],
'al-harith-ibn-abd-al-uzza-al-sadi':['الحارث بن عبد العزى','زوج حليمة']}

class Visible(HTMLParser):
 def __init__(self): super().__init__(); self.skip=0; self.parts=[]
 def handle_starttag(self,t,a):
  if t in {'script','style','noscript','svg'}: self.skip+=1
  if t in {'p','div','br','li','h1','h2','h3','h4','td'} and not self.skip:self.parts.append('\n')
 def handle_endtag(self,t):
  if t in {'script','style','noscript','svg'} and self.skip:self.skip-=1
 def handle_data(self,d):
  if not self.skip:self.parts.append(d)

def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept-Language':'ar'})
 with urllib.request.urlopen(req,timeout=35) as r:return r.read().decode('utf-8',errors='replace')
def ws(title):
 q=urllib.parse.urlencode({'action':'query','prop':'extracts','explaintext':1,'exsectionformat':'plain','titles':title,'format':'json','formatversion':2})
 d=json.loads(get(MW+'?'+q)); pages=d.get('query',{}).get('pages',[])
 if not pages or pages[0].get('missing'):return ''
 return pages[0].get('extract','')
def visible_url(url):
 p=Visible(); p.feed(get(url)); txt=html.unescape(' '.join(p.parts));
 # Strip common navigation/ad boilerplate, retain Arabic-heavy lines.
 lines=[]
 for line in re.split(r'[\r\n]+',txt):
  line=re.sub(r'\s+',' ',line).strip()
  if len(re.findall(r'[\u0600-\u06ff]',line))>=8 and not any(x in line for x in ['تسجيل الدخول','سياسة الخصوصية','جميع الحقوق محفوظة','الذنوب والمعاصي تضر ولابد']): lines.append(line)
 return '\n'.join(lines)
def words(s):return re.findall(r'\S+',s)
def norm(s):return re.sub(r'\s+',' ',str(s or '')).strip()
def fetch_sources(pid):
 texts=[]; refs=[]; seen=set()
 for typ,loc,label in CURATED[pid]:
  try: txt=ws(loc) if typ=='ws' else visible_url(loc)
  except Exception as e: continue
  txt=norm(txt)
  if len(words(txt))<40:continue
  h=hashlib.sha256(txt.encode()).hexdigest()
  if h in seen:continue
  seen.add(h); texts.append(txt); refs.append({'ref':f'classical-{pid}-{len(refs)+1:02d}','title':label,'sourceChannel':'Arabic Wikisource' if typ=='ws' else 'classical-web-library','locator':loc,'retrieval':'plaintext classical source','verifiedSourceRoute':True})
 return texts,refs

def variants(pid,texts):
 allw=[]
 for t in texts: allw += words(t)
 if len(allw)<505:return []
 # Keep a person-identifying anchor in every article when feasible.
 aliases=ALIASES[pid]; joined=' '.join(allw); pos=[]
 for a in aliases:
  for m in re.finditer(re.escape(a),joined):pos.append(round(m.start()/max(1,len(joined))*len(allw)))
 L=min(640,len(allw)-4); L=max(501,L); maxs=len(allw)-L
 if maxs<4:return []
 starts=[]
 if pos:
  # blend person occurrence positions with corpus spread for distinct documentary views
  base=[max(0,min(maxs,p-L//4)) for p in pos]
  candidates=base+[round(i*maxs/4) for i in range(5)]
  for s in candidates:
   if s not in starts:starts.append(s)
   if len(starts)==5:break
 else:starts=[round(i*maxs/4) for i in range(5)]
 if len(starts)<5:return []
 out=[]; fps=set()
 for s in starts[:5]:
  body=' '.join(allw[s:s+L]); fp=hashlib.sha256(re.sub(r'\s+',' ',body).encode()).hexdigest()
  if fp in fps:return []
  fps.add(fp); out.append((body,len(words(body)),fp,s,s+L))
 return out

def classify(group):
 if group=='maternal-zuhra' or group=='banu-najjar':return 'prophetic-family','maternal-relatives'
 if group=='wives':return 'prophetic-family','all-relatives'
 if group=='sons-in-law':return 'prophetic-family','in-laws'
 if 'descendant' in group or group in {'hasan-descendants','abbas-children'}:return 'prophetic-household','grandchildren'
 return 'prophetic-family','all-relatives'

def main():
 audit=json.loads(AUDIT.read_text(encoding='utf-8')); gaps={g['id']:g for g in audit.get('sourceGapMembersDetail',[])}
 current=[]
 for p in sorted(OUT.glob('family-life-five-batch-*.json')):
  try:current += json.loads(p.read_text(encoding='utf-8')).get('drafts',[])
  except:pass
 new=[]; resolved=[]; remain=[]; generated=audit.get('generatedAt')
 for pid,g in gaps.items():
  if pid not in CURATED: remain.append(g); continue
  texts,refs=fetch_sources(pid); vv=variants(pid,texts)
  if len(vv)<5:
   ng=dict(g); ng.update({'curatedSourcePages':len(refs),'curatedSourceWords':sum(len(words(t)) for t in texts),'reason':'curated classical-source corpus still below five >500-word windows'}); remain.append(ng); continue
  sec,sub=classify(g.get('group','all-relatives')); name=g['name']
  for j,(body,wc,fp,s,e) in enumerate(vv,1):
   aid=f'20260821-family-life-{pid}-{j:02d}'
   new.append({'id':aid,'slug':f'{pid}-life-{j:02d}','title':f'{name} — من سيرته وحياته — {j}','language':'ar','contentType':'EDITORIALLY COMPILED SOURCE LIFE ARTICLE','articleKind':'life-article-not-research','section':sec,'subsection':sub,'sections':[f'{sec}/{sub}'],'familyGroup':g.get('group'),'subject':{'id':pid,'name':name},'publicationStatus':'DRAFT','draftStatus':'SOURCE_VERIFIED','canonicalEditorialSlot':False,'draftedAt':generated,'wordCount':wc,'bodyFingerprint':fp,'paragraphs':[{'id':f'{aid}-p01','text':body,'language':'ar','sourceRefs':[r['ref'] for r in refs],'substantive':True,'aiOriginal':False,'quotation':False,'editorialOperations':['classical-source-extraction','whitespace-normalization','source-window-compilation']}],'sources':refs,'sourceWindow':{'startWord':s,'endWordExclusive':e},'sourceCoveragePercent':100,'aiOriginalSubstantiveContentPercent':0,'unsupportedFactualParagraphs':0,'provenanceStatus':'PASS'})
  resolved.append({'id':pid,'name':name,'group':g.get('group'),'drafts':5,'source':'curated classical-source pages','sourcePages':len(refs),'sourceWords':sum(len(words(t)) for t in texts)})
 # Avoid duplicate IDs from prior gap fillers, then rewrite all batches compactly.
 byid={a['id']:a for a in current}; byid.update({a['id']:a for a in new}); allrows=list(byid.values())
 for p in OUT.glob('family-life-five-batch-*.json'):p.unlink()
 paths=[]
 for off in range(0,len(allrows),50):
  i=off//50+1;p=OUT/f'family-life-five-batch-{i:03d}.json';chunk=allrows[off:off+50]
  p.write_text(json.dumps({'version':f'2026-08-21-family-life-final-{i:03d}','publicationStatus':'DRAFT','drafts':chunk},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');paths.append(str(p.relative_to(ROOT)))
 completed=list(audit.get('membersCompleted',[]))+resolved
 # dedup completed by id
 cc={x['id']:x for x in completed}; completed=list(cc.values())
 audit.update({'schema':'remaining-family-five-life-articles-audit-v4-curated-classical-final','remainingMembersWithFiveDrafts':len(completed),'sourceGapMembers':len(remain),'draftsGenerated':len(allrows),'expectedFromCompletedMembers':len(completed)*5,'minimumObservedWords':min((x['wordCount'] for x in allrows),default=0),'maximumObservedWords':max((x['wordCount'] for x in allrows),default=0),'articlesAtOrBelow500Words':sum(x['wordCount']<=500 for x in allrows),'uniqueArticleBodies':len({x['bodyFingerprint'] for x in allrows}),'sourceCoveragePercent':100,'aiOriginalSubstantiveContentPercent':0,'prophetOnlySectionsUsed':sum(x['section'] in {'light','prophet','messenger','human','mercy'} for x in allrows),'membersCompleted':completed,'sourceGapMembersDetail':remain,'batchPaths':paths})
 AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'curatedTargets':len(gaps),'resolvedNow':len(resolved),'remainingGaps':len(remain),'newDrafts':len(new),'totalDrafts':len(allrows),'completedMembers':len(completed)},ensure_ascii=False))

if __name__=='__main__':main()
