#!/usr/bin/env python3
# GOVERNED_BY: MASTER_OVERRIDING_INSTRUCTION.md
from __future__ import annotations
import argparse, importlib.util, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/'data/editorial_sections.json'
STATE=ROOT/'data/editorial/content_completion_state.json'
AUDIT=ROOT/'data/editorial/content_completion_slot_audit.json'
BUILDER=ROOT/'scripts/build_100_genuine_articles.py'
DRAFTS=ROOT/'data/editorial/drafts'

SECTION_TERMS={
 'light':('light','spiritual','mystic','mysticism','sufi','sufism','نور','روح'),
 'prophet':('prophet','mohammad','muhammad','birth','childhood','character','mecca','medina','النبي'),
 'messenger':('revelation','revealed','mission','preach','message','qur\'an','quran','koran','الوحي','الرسالة'),
 'human':('daily','home','food','dress','illness','smile','human','habit','marriage','personal'),
 'mercy':('mercy','merciful','compassion','kindness','forgave','forgive','pardon','charity'),
 'family':('khadija','aisha','wife','wives','daughter','son','uncle','father','mother','family','marriage'),
 'companions':('abu bakr','omar','umar','uthman','othman','ali','companion','companions','sahaba'),
 'media':('speech','lecture','sermon','audio','video','documentary','podcast','transcript','narration'),
 'forums':('community','society','advice','counsel','discussion','موعظة')
}
SUBSECTION_TERMS={
 'verses':('qur\'an','quran','koran','verse','verses','surah','sura','ayat','آية','قرآن'),
 'hadith':('hadith','tradition','reported','narrated','said','حديث','رواه'),
 'seerah':('life','journey','battle','hijra','migration','mecca','medina','birth','سيرة','هجرة','غزوة'),
 'righteous':('scholar','saint','mystic','sufi','spiritual','devotion','صالح','تصوف'),
 'research':(),
 'mercy-stories':('mercy','forgive','pardon','compassion','رحمة','عفو'),
 'love-stories':('love','marriage','wife','family','محبة','زواج'),
 'strength-stories':('battle','steadfast','courage','strength','أحد','ثبات','شجاعة'),
 'aspiration-stories':('brotherhood','community','hope','aspiration','هجرة','مؤاخاة'),
 'wives':('wife','wives','khadija','aisha','marriage','زوج'),
 'children':('daughter','son','children','child','بنت','ابن'),
 'grandchildren':('grandson','granddaughter','hasan','husayn','حسن','حسين'),
 'parents':('father','mother','amina','abdullah','والد','أم'),
 'paternal-uncles':('uncle','abu talib','hamza','abbas','عم'),
 'paternal-cousins':('cousin','ali','جعفر','علي'),
 'ancestors':('ancestor','lineage','genealogy','adnan',' نسب','عدنان'),
 'biographies':('companion','biography','life','صحابي','ترجمة'),
 'stories':('story','battle','event','incident','قصة','خبر'),
 'sayings':('said','saying','speech','quote','قال','قول'),
 'videos':('video','film','visual','youtube'),
 'lectures':('lecture','lesson','sermon','درس','محاضرة'),
 'podcasts':('podcast','episode','audio program'),
 'documentaries':('documentary','film'),
 'audio':('audio','recitation','recording','sound'),
 'community':('community','society','counsel','discussion')
}

def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return d

def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def module(path):
 spec=importlib.util.spec_from_file_location('builder',path);m=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(m);return m

def fingerprints():
 out=set()
 for p in DRAFTS.glob('**/*.json'):
  d=load(p,{})
  for x in d.get('drafts',[]) if isinstance(d,dict) else []:
   for s in x.get('sources') or []:
    fp=str(s.get('sourceFingerprint') or '').strip()
    if fp:out.add(fp)
 return out

def score(c,section,sub):
 text=' '.join([str(c.get('heading') or ''),str((c.get('source') or {}).get('titleOriginal') or ''),' '.join(c.get('paragraphs') or [])]).lower()
 s=sum(text.count(t.lower()) for t in SECTION_TERMS.get(section,()))
 if s<=0:return 0
 terms=SUBSECTION_TERMS.get(sub,())
 if not terms:return s
 ss=sum(text.count(t.lower()) for t in terms)
 return s+ss*3 if ss>0 else 0

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--slot');args=ap.parse_args()
 state=load(STATE,{})
 if state.get('ARTICLE_FILL_COMPLETE'):
  print('ARTICLE_FILL_COMPLETE');return 0
 slot=args.slot or state.get('nextTargetSlot')
 if not slot or '/' not in slot:
  print('NO_TARGET_SLOT');return 0
 section,sub=slot.split('/',1)
 reg=load(REG,{})
 valid={str(x.get('id')) for x in reg.get('sections',[]) if x.get('active') and x.get('editorial')}
 if slot not in valid:
  print('NEEDS_REVIEW',slot);return 0
 b=module(BUILDER);used=fingerprints();cand=[]
 for src in b.source_records():
  try:text=b.fetch_text(src)
  except Exception:continue
  if not text:continue
  try:rows=b.candidate_articles(src,text)
  except Exception:continue
  for c in rows:
   if c.get('fingerprint') in used:continue
   sc=score(c,section,sub)
   if sc>0:cand.append((sc,c))
 now=datetime.now(timezone.utc);audit=load(AUDIT,{});audit.setdefault('schema','content-completion-slot-audit-v1');audit.setdefault('slots',{})
 if not cand:
  audit['slots'][slot]={'status':'NEEDS_SOURCE','at':now.isoformat(),'reason':'No unused source-grounded candidate matched exact slot semantics; no filler fabricated.'};save(AUDIT,audit);print('NEEDS_SOURCE',slot);return 0
 cand.sort(key=lambda z:(-z[0],str((z[1].get('source') or {}).get('workId') or ''),str(z[1].get('fingerprint') or '')))
 chosen=cand[0][1];seq=int(now.timestamp());rec=b.build_record(chosen,seq,{(section,sub)})
 rec['id']=f'completion-{now.date().isoformat()}-{section}-{sub}-{seq}';rec['section']=section;rec['subsection']=sub;rec['publicationStatus']='READY';rec['publishedAt']=now.isoformat();rec['completionPrompt']={'targetSlot':slot,'targetMinimum':50,'governedBy':'MASTER_OVERRIDING_INSTRUCTION.md'}
 ref=rec['id']+'-source'
 for i,p in enumerate(rec.get('paragraphs') or [],1):p['id']=f"{rec['id']}-p{i:02d}";p['sourceRefs']=[ref]
 for s in rec.get('sources') or []:s['ref']=ref
 out=DRAFTS/now.date().isoformat()/f"completion-{section}-{sub}-{seq}.json";save(out,{'version':'completion-source-extract-v1','generatedAt':now.isoformat(),'count':1,'drafts':[rec]})
 audit['slots'][slot]={'status':'READY_TO_PUBLISH','at':now.isoformat(),'id':rec['id'],'path':str(out.relative_to(ROOT)),'sourceFingerprint':chosen.get('fingerprint')};save(AUDIT,audit);print('READY_TO_PUBLISH',slot,rec['id']);return 0
if __name__=='__main__':raise SystemExit(main())
