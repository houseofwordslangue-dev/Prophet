from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from media_sync import sync_all
print(json.dumps(sync_all(),ensure_ascii=False,indent=2))
