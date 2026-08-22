#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/'scripts/content_completion_status.py'
FILL=ROOT/'scripts/completion_slot_fill.py'
STATE=ROOT/'data/editorial/content_completion_state.json'
MAX_ATTEMPTS=39

def run(*args):
    p=subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,text=True,capture_output=True)
    if p.stdout.strip():print(p.stdout.strip())
    if p.stderr.strip():print(p.stderr.strip(),file=sys.stderr)
    return p.returncode

def load_state():
    try:return json.loads(STATE.read_text(encoding='utf-8'))
    except Exception:return {}

def main():
    attempted=set();made=0;blocked=0
    for _ in range(MAX_ATTEMPTS):
        run(STATUS);s=load_state()
        if s.get('ARTICLE_FILL_COMPLETE'):
            print('ARTICLE_FILL_COMPLETE');break
        slot=s.get('nextTargetSlot')
        if not slot or slot in attempted:
            print('NO_NEW_ELIGIBLE_SLOT');break
        attempted.add(slot)
        p=subprocess.run([sys.executable,str(FILL),'--slot',slot],cwd=ROOT,text=True,capture_output=True)
        text=(p.stdout or '')+'\n'+(p.stderr or '')
        print(text.strip())
        if 'READY_TO_PUBLISH' in text:made+=1
        elif 'NEEDS_SOURCE' in text or 'NEEDS_REVIEW' in text:blocked+=1
        # Refresh status so recently blocked slots are bypassed and the next
        # lowest-count eligible slot is selected. Never repeat/fabricate to hit a quota.
        run(STATUS)
    print(json.dumps({'attemptedSlots':len(attempted),'newSourceGroundedDrafts':made,'sourceBlockedSlots':blocked,'attempted':sorted(attempted)},ensure_ascii=False))
    return 0
if __name__=='__main__':raise SystemExit(main())
