#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ED=ROOT/'data/editorial';OUT=ED/'biography_coverage_status.json'
def load(name):
    try:return json.loads((ED/name).read_text(encoding='utf-8'))
    except Exception:return {}
def main():
    req=load('required_biographies_audit.json');ext=load('all_biographies_extension_audit.json');gap=load('biography_gap_repair_audit.json')
    required=int(req.get('requiredPersonCount') or 0);missing=int(req.get('missingCanonicalBiographyCount') or 0);scanned=int(ext.get('peopleScanned') or 0);covered=int(ext.get('peopleWithExtendedSourceContent') or 0);unresolved=int(ext.get('unresolvedCount') or max(0,scanned-covered));latin=int(gap.get('remainingLatinOnlyNameCount') or 0)
    state={'schema':'biography-coverage-status-v1','generatedAt':datetime.now(timezone.utc).isoformat(),'governedBy':'MASTER-OVERRIDING-SITE-INSTRUCTION.md','requiredCanonicalPeople':required,'missingCanonicalBiographies':missing,'CANONICAL_BIOGRAPHY_COMPLETE':missing==0,'peopleScannedForExtendedSourceContent':scanned,'peopleWithExtendedSourceContent':covered,'unresolvedExtendedSourcePeople':unresolved,'extendedSourceCoveragePercent':round(100*covered/scanned,2) if scanned else 100,'ENRICHMENT_COVERAGE_COMPLETE':unresolved==0,'remainingLatinOnlyArabicNames':latin,'ARABIC_NAME_LOCALIZATION_COMPLETE':latin==0,'BIOGRAPHY_SYSTEM_COMPLETE':bool(missing==0 and unresolved==0 and latin==0),'note':'Historical audit fields named complete may mean pass execution completed. This canonical ledger distinguishes run completion from actual content/localization coverage.'}
    OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(state,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
