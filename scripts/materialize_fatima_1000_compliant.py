#!/usr/bin/env python3
from __future__ import annotations
import base64, importlib.util, json, lzma
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'scripts'/'materialize_fatima_1000_compiled.py'
AUDIT=ROOT/'data'/'editorial'/'fatima_1000_audit.json'
SUPPLEMENT=ROOT/'data'/'editorial'/'publication_supplement.json'
OUT=ROOT/'data'/'editorial'/'drafts'/'2026-08-21'
PART_GLOB='fatima_source_fragments.part*.xz.b64'

spec=importlib.util.spec_from_file_location('fatima_base', BASE)
base=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(base)

# The original single gzip/base64 payload was truncated by the repository write
# boundary. Reconstruct the verified source payload from the chunked XZ/base64
# parts that were committed afterwards. The final XZ footer may be missing, so
# use the incremental decoder and accept the decompressed bytes if they contain
# a complete valid JSON corpus.
def load_fragments_from_parts():
    parts=sorted((ROOT/'data'/'editorial').glob(PART_GLOB))
    assert len(parts)>=3, f'Expected chunked Fatima payload parts, found {len(parts)}'
    encoded=''.join(p.read_text(encoding='ascii').strip() for p in parts)
    compressed=base64.b64decode(encoded)
    dec=lzma.LZMADecompressor()
    raw=dec.decompress(compressed)
    rows=json.loads(raw.decode('utf-8'))
    assert isinstance(rows,list) and len(rows)>=300, len(rows)
    assert all(int(x.get('wordCount',0))>=150 for x in rows)
    assert all('فاطم' in x.get('text','') for x in rows)
    return rows

base.load_fragments=load_fragments_from_parts

# Fatima al-Zahra is a direct daughter of the Prophet, so every article belongs
# under الأسرة النبوية → الأبناء. None may use Prophet-only sections.
base.THEMES=[
 ('birth-lineage','المولد والنسب','prophetic-household','children'),
 ('prophet-relationship','علاقتها برسول الله ﷺ','prophetic-household','children'),
 ('marriage-ali','زواجها من علي بن أبي طالب','prophetic-household','children'),
 ('household-life','حياتها في البيت','prophetic-household','children'),
 ('children','الأبناء والذرية','prophetic-household','children'),
 ('ahl-al-bayt','فاطمة وأهل البيت','prophetic-household','children'),
 ('virtues','الفضائل والمناقب','prophetic-household','children'),
 ('hadith-reports','الأخبار والآثار المروية','prophetic-household','children'),
 ('death-grief','الوفاة والحزن','prophetic-household','children'),
 ('legacy','الأثر والذكر والذرية','prophetic-household','children'),
]
base.main()

files=sorted(OUT.glob('fatima-long-batch-*.json'))
assert len(files)==20
rows=[]
for p in files:
    data=json.loads(p.read_text(encoding='utf-8'))
    rows.extend(data['drafts'])
assert len(rows)==1000
assert all(int(x['wordCount'])>500 for x in rows)
assert all(x['section']=='prophetic-household' and x['subsection']=='children' for x in rows)
assert not any(x['section'] in {'light','prophet','messenger','human','mercy'} for x in rows)

minimum=min(int(x['wordCount']) for x in rows)
maximum=max(int(x['wordCount']) for x in rows)
average=sum(int(x['wordCount']) for x in rows)/len(rows)

audit=json.loads(AUDIT.read_text(encoding='utf-8'))
audit['schema']='fatima-1000-compiled-source-audit-v2-master-compliant'
audit['minimumWordsExclusive']=500
audit['minimumRequiredWords']=501
audit['minimumObservedWords']=minimum
audit['maximumObservedWords']=maximum
audit['averageObservedWords']=average
audit['allOver500Words']=True
audit['articlesAtOrBelow500Words']=0
audit['prophetOnlySectionsUsed']=0
audit['destination']='prophetic-household/children'
audit['siteSections']={'prophetic-household/children':1000}
audit['payloadReconstruction']='PASS: chunked XZ/base64 source fragments reconstructed from committed parts using incremental XZ recovery'
AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

sup=json.loads(SUPPLEMENT.read_text(encoding='utf-8'))
sup['fatima1000'].update({
  'status':'PUBLISHED',
  'count':1000,
  'minimumWordsExclusive':500,
  'minimumRequiredWords':501,
  'minimumObservedWords':minimum,
  'maximumObservedWords':maximum,
  'averageObservedWords':average,
  'allOver500Words':True,
  'articlesAtOrBelow500Words':0,
  'prophetOnlySectionsUsed':0,
  'destination':'prophetic-household/children',
  'siteSections':{'prophetic-household/children':1000},
  'payloadReconstruction':'chunked-xz-base64-incremental',
})
SUPPLEMENT.write_text(json.dumps(sup,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'PASS: 1000 Fatima articles; min={minimum}; >500 words; Prophet-only=0; destination=prophetic-household/children')
