# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from content_importer import run_import
import argparse,json
ap=argparse.ArgumentParser();ap.add_argument('--offline',action='store_true');ap.add_argument('--limit',type=int,default=30);a=ap.parse_args();print(json.dumps(run_import(not a.offline,a.limit),ensure_ascii=False,indent=2))
