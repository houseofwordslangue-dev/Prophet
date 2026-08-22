#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json, os, shutil, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data'/'ops'; OUT.mkdir(parents=True,exist_ok=True)
BACKUP=ROOT/'backups'/'platform'; BACKUP.mkdir(parents=True,exist_ok=True)

def run(name,cmd,timeout=7200):
 st=time.time()
 try:
  cp=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=timeout)
  return {'name':name,'ok':cp.returncode==0,'returncode':cp.returncode,'seconds':round(time.time()-st,2),'stdout':cp.stdout[-12000:],'stderr':cp.stderr[-12000:]}
 except Exception as e:return {'name':name,'ok':False,'seconds':round(time.time()-st,2),'error':str(e)}

def backup():
 stamp=time.strftime('%Y%m%d-%H%M%S'); d=BACKUP/stamp; d.mkdir(parents=True,exist_ok=True); copied=[]
 for rel in ['data/platform.sqlite3','data/runtime_telemetry.ndjson','data/mirror_manifest.json','data/replication_manifest.json','data/reader_player_platform_status.json']:
  src=ROOT/rel
  if src.exists():shutil.copy2(src,d/src.name);copied.append(rel)
 return {'name':'backup','ok':True,'files':copied,'path':str(d.relative_to(ROOT))}

def main():
 started=int(time.time()); steps=[]
 steps.append(run('search',[sys.executable,'-c','from platform_services import build_search_index; print(build_search_index(True))'],600))
 steps.append(run('mirrors',[sys.executable,'scripts/build_mirror_manifest.py'],1800))
 if os.getenv('PM_NIGHTLY_ASSET_PREP','0')=='1':steps.append(run('assets',[sys.executable,'scripts/prepare_reader_player_assets.py'],7200))
 else:steps.append({'name':'assets','ok':True,'skipped':True,'reason':'PM_NIGHTLY_ASSET_PREP not enabled'})
 steps.append(run('tests',[sys.executable,'-m','unittest','-v','tests/test_reader_player_runtime.py'],1200))
 steps.append(backup())
 ok=all(x.get('ok') for x in steps); result={'ok':ok,'startedAt':started,'finishedAt':int(time.time()),'steps':steps}
 (OUT/'nightly_status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 test=next((x for x in steps if x.get('name')=='tests'),{});(OUT/'regression_status.json').write_text(json.dumps({'ok':bool(test.get('ok')),'finishedAt':int(time.time()),'returncode':test.get('returncode'),'stdout':test.get('stdout',''),'stderr':test.get('stderr','')},ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'ok':ok,'steps':[{'name':x.get('name'),'ok':x.get('ok'),'skipped':x.get('skipped',False)} for x in steps]},ensure_ascii=False));raise SystemExit(0 if ok else 1)
if __name__=='__main__':main()
