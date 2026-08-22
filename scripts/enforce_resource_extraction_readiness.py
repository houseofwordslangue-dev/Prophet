#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CAT=ROOT/'data/public_catalog_all.generated.json';RES=ROOT/'private/source_first_resolution.json';OUT=ROOT/'data/editorial/resource_extraction_readiness_gate.json';ALLOW=ROOT/'data/editorial/generation_resource_allowlist.json'
DIRECT_GENERATION_ORIGINS={'NATIVE','VERIFIED_TEXT','GENERATED_TEXT'}
def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return d
def verified_after_ocr(r):
 p=r.get('preferred') or {};mode=str(p.get('extractionMode') or '').upper()
 return bool(p.get('ocrVerified') is True or p.get('proofread') is True or p.get('verifiedAfterOcr') is True or mode in {'OCR_REPAIRED_VERIFIED','PROOFREAD_OCR','VERIFIED_PDF_TEXT'})
def main():
 cat=[x for x in load(CAT,{'items':[]}).get('items',[]) if isinstance(x,dict)];rows=[x for x in load(RES,{'items':[]}).get('items',[]) if isinstance(x,dict)];by={str(x.get('id') or ''):x for x in rows};eligible=[];eligible_rows=[];preprocess=[];missing=[]
 for item in cat:
  wid=str(item.get('id') or '');r=by.get(wid);origin=(r or {}).get('textOrigin') or ((r or {}).get('preferred') or {}).get('textOrigin')
  if not r or r.get('extractionReady') is not True or not r.get('preferred'):
   missing.append({'id':wid,'title':item.get('title'),'author':item.get('author'),'state':'HARD_BLOCKED','resolverState':(r or {}).get('state') or 'MISSING_FROM_RESOLUTION','reason':'No verified extraction path is currently materialized.','generationAllowed':False,'retryOnNewSource':True});continue
  if origin in DIRECT_GENERATION_ORIGINS or verified_after_ocr(r):
   eligible.append(wid);eligible_rows.append({'id':wid,'title':item.get('title'),'author':item.get('author'),'state':r.get('state'),'preferred':r.get('preferred'),'textOrigin':origin,'generationAllowed':True});continue
  preprocess.append({'id':wid,'title':item.get('title'),'author':item.get('author'),'state':'PREPROCESSING_REQUIRED','resolverState':r.get('state'),'textOrigin':origin,'preferred':r.get('preferred'),'reason':'OCR/PDF witness is extraction-capable but must pass OCR repair/proofreading verification before source-grounded generation.','generationAllowed':False,'nextStage':'OCR_REPAIR_PROOFREAD_VERIFY'})
 total=len(cat);blocked=len(missing)+len(preprocess);now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());out={'schema':'resource-extraction-readiness-gate-v3','governedBy':'MASTER-OVERRIDING-SITE-INSTRUCTION.md','generatedAt':now,'catalogResources':total,'extractionPathReady':total-len(missing),'generationReady':len(eligible),'missingExtractionPath':len(missing),'preprocessingRequired':len(preprocess),'blockedForGeneration':blocked,'generationCoveragePercent':round(100*len(eligible)/total,2) if total else 100.0,'allResourcesGenerationReady':blocked==0,'generationEligibleIds':eligible,'preprocessingRequiredIds':[x['id'] for x in preprocess],'hardBlockedIds':[x['id'] for x in missing],'preprocessing':preprocess,'blockers':missing,'policy':'Raw OCR derivatives and unverified PDF/scan text may enter OCR repair/proofreading but may not feed SOURCE_GROUNDED_SYNTHESIS until verified. Native, verified text, and source-derived generated text remain directly eligible.'};allow={'schema':'generation-resource-allowlist-v2','governedBy':'MASTER-OVERRIDING-SITE-INSTRUCTION.md','generatedAt':now,'eligibleCount':len(eligible),'preprocessingRequiredCount':len(preprocess),'hardBlockedCount':len(missing),'generationEligibleIds':eligible,'preprocessingRequiredIds':[x['id'] for x in preprocess],'hardBlockedIds':[x['id'] for x in missing],'eligibleResources':eligible_rows,'rule':'Downstream SOURCE_GROUNDED_SYNTHESIS must use generationEligibleIds only. OCR/PDF witnesses first pass OCR_REPAIR_PROOFREAD_VERIFY.'};OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');ALLOW.write_text(json.dumps(allow,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:out[k] for k in ('catalogResources','extractionPathReady','generationReady','missingExtractionPath','preprocessingRequired','generationCoveragePercent','allResourcesGenerationReady')},ensure_ascii=False));return 0 if out['allResourcesGenerationReady'] else 2
if __name__=='__main__':sys.exit(main())
