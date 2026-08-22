#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STEPS=[
 ('mirrors','build_mirror_manifest.py'),
 ('ocr','build_ocr_coordinates.py'),
 ('transcripts','build_timed_transcripts.py'),
 ('adaptive','build_adaptive_media.py'),
 ('replication','replicate_assets.py'),
]

def run(name,script):
 p=ROOT/'scripts'/script
 try:
  cp=subprocess.run([sys.executable,str(p)],cwd=ROOT,text=True,capture_output=True,timeout=86400)
  return {'name':name,'ok':cp.returncode==0,'code':cp.returncode,'stdout':cp.stdout[-4000:],'stderr':cp.stderr[-4000:]}
 except Exception as e:return {'name':name,'ok':False,'error':str(e)}

def main():
 results=[run(*s) for s in STEPS];out={'generatedAt':int(time.time()),'steps':results,'ok':all(x.get('ok') for x in results),'note':'A failed step usually means its real dependency or source asset is not present; no synthetic asset is substituted.'};(ROOT/'data'/'reader_player_asset_preparation_status.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
