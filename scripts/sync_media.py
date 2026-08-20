from pathlib import Path
import os,sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from media_sync import sync_all,_ydl_extract,load,dump,OUT,now

TARGET_CATEGORIES=("video","lecture","podcast","research","documentary","audio")
EXPANSION_SOURCES=[
 {"id":"expand-video","kind":"youtube-search","query":"السيرة النبوية النبي محمد الشمائل فيديو","label":"Prophetic video repertory","category":"video","topics":["seerah","prophet","video"],"language":"ar"},
 {"id":"expand-lecture","kind":"youtube-search","query":"محاضرات السيرة النبوية الشمائل النبي محمد","label":"Prophetic lectures repertory","category":"lecture","topics":["seerah","lecture","shamail"],"language":"ar"},
 {"id":"expand-podcast","kind":"youtube-search","query":"بودكاست السيرة النبوية حياة النبي محمد الشمائل","label":"Prophetic podcasts repertory","category":"podcast","topics":["seerah","podcast","prophet"],"language":"ar"},
 {"id":"expand-research","kind":"youtube-search","query":"بحث أكاديمي السيرة النبوية الشمائل مؤتمر جامعة","label":"Prophetic research repertory","category":"research","topics":["seerah","research","academic"],"language":"ar"},
 {"id":"expand-documentary","kind":"youtube-search","query":"وثائقي السيرة النبوية حياة النبي محمد كامل","label":"Prophetic documentaries repertory","category":"documentary","topics":["seerah","documentary","prophet"],"language":"ar"},
 {"id":"expand-audio","kind":"youtube-search","query":"السيرة النبوية صوتي كاملة محاضرات مديح النبي","label":"Prophetic audio repertory","category":"audio","topics":["seerah","audio","prophet"],"language":"ar"},
]

def _medium(row):
    if row.get("medium") in TARGET_CATEGORIES:return row["medium"]
    if row.get("kind")=="audio":return "audio"
    c=str(row.get("category") or "").lower()
    if c in TARGET_CATEGORIES:return c
    if c in {"course","conference","seerah","hadith","quran","mawlid","madih","hadra","burda","dalail-khayrat","sufi-song","nasheed"}:return "lecture"
    return "video"

def run_expanded_sync(max_per_source=0):
    max_per_source=int(max_per_source or os.getenv("PM_MEDIA_MAX_PER_SOURCE","350") or 350)
    target=int(os.getenv("PM_MEDIA_TARGET_PER_CATEGORY","200") or 200)
    report=sync_all(min(max_per_source,80))
    current=load(OUT,{"version":"6.0.0","generated":now(),"taxonomy":[],"items":[]})
    by={x.get("id"):x for x in current.get("items",[]) if x.get("id")}
    counts={k:0 for k in TARGET_CATEGORIES}
    for x in by.values():
        x["medium"]=_medium(x)
        if x["medium"] in counts:counts[x["medium"]]+=1
    expansion=[]
    for src in EXPANSION_SOURCES:
        cat=src["category"]
        if counts.get(cat,0)>=target:continue
        need=max(1,min(max_per_source,target-counts.get(cat,0)+50))
        rows,err=_ydl_extract(f"ytsearch{need}:{src['query']}",src,need,False)
        if err:report.setdefault("errors",[]).append({"source":src["id"],"error":err})
        added=0
        for x in rows:
            x["medium"]=cat
            x["catalogTier"]="repertory-search"
            x["catalogSourceId"]=src["id"]
            if x.get("id") not in by:added+=1
            by[x.get("id")]=x
        expansion.append({"source":src["id"],"category":cat,"addedOrUpdated":len(rows),"new":added})
    items=list(by.values())
    for x in items:x["medium"]=_medium(x)
    items.sort(key=lambda x:(x.get("medium",""),str(x.get("published","")),int(x.get("viewCount") or 0),str(x.get("titleEn",""))),reverse=True)
    counts={k:0 for k in TARGET_CATEGORIES}
    for x in items:
        if x.get("medium") in counts:counts[x["medium"]]+=1
    current.update({"version":"7.0.0","generated":now(),"items":items,"mediaCategories":list(TARGET_CATEGORIES),"categoryCounts":counts,"targetPerCategory":target})
    dump(OUT,current)
    report.update({"total":len(items),"categories":counts,"targetPerCategory":target,"expansion":expansion,"ok":all(v>=min(target,1) for v in counts.values())})
    return report

if __name__=="__main__":
    print(json.dumps(run_expanded_sync(),ensure_ascii=False,indent=2))
