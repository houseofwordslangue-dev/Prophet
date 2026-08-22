#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/'data/editorial/ocr_verification_ledger.json';OUT=ROOT/'data/editorial/ocr_verification_status.json'
def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return d
def main():
 d=load(LEDGER,{'records':[]});valid=[];invalid=[];seen=set()
 for i,r in enumerate(d.get('records') or []):
  if not isinstance(r,dict):invalid.append({'index':i,'reason':'not-object'});continue
  wid=str(r.get('resourceId') or '').strip();status=str(r.get('status') or '').upper();repaired=str(r.get('repairedArtifact') or '').strip();original=str(r.get('originalOcrArtifact') or '').strip();basis=r.get('verificationBasis') or []
  errs=[]
  if not wid:errs.append('resourceId-missing')
  if status!='VERIFIED':errs.append('status-not-VERIFIED')
  if not repaired:errs.append('repairedArtifact-missing')
  if not original:errs.append('originalOcrArtifact-missing')
  if not isinstance(basis,list) or not basis:errs.append('verificationBasis-missing')
  if wid in seen:errs.append('duplicate-resourceId')
  if errs:invalid.append({'index':i,'resourceId':wid,'errors':errs});continue
  seen.add(wid);valid.append({'resourceId':wid,'repairedArtifact':repaired,'originalOcrArtifact':original,'verificationBasis':basis,'verifiedAt':r.get('verifiedAt'),'verifiedBy':r.get('verifiedBy')})
 out={'schema':'ocr-verification-status-v1','governedBy':'MASTER-OVERRIDING-SITE-INSTRUCTION.md','generatedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'verifiedCount':len(valid),'invalidRecordCount':len(invalid),'verifiedResourceIds':[x['resourceId'] for x in valid],'verifiedRecords':valid,'invalidRecords':invalid,'complete':len(invalid)==0}
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'verifiedCount':len(valid),'invalidRecordCount':len(invalid)},ensure_ascii=False));return 1 if invalid else 0
if __name__=='__main__':raise SystemExit(main())
