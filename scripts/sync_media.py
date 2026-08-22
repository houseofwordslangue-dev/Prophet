# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from pathlib import Path
import os,sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from media_sync import sync_all,_ydl_extract,load,dump,OUT,now

TARGET_CATEGORIES=("video","lecture","podcast","research","documentary","audio")
TARGET_PER_CATEGORY=int(os.getenv("PM_MEDIA_TARGET_PER_CATEGORY","300") or 300)

EXPANSION_SOURCES=[
 {"id":"video-seerah","query":"السيرة النبوية النبي محمد فيديو","category":"video","topics":["seerah","prophet","video"]},
 {"id":"video-shamail","query":"الشمائل المحمدية النبي محمد فيديو","category":"video","topics":["shamail","prophet","video"]},
 {"id":"video-biography","query":"حياة النبي محمد السيرة فيديو","category":"video","topics":["biography","prophet","video"]},
 {"id":"lecture-seerah","query":"محاضرات السيرة النبوية النبي محمد","category":"lecture","topics":["seerah","lecture"]},
 {"id":"lecture-shamail","query":"محاضرات الشمائل المحمدية","category":"lecture","topics":["shamail","lecture"]},
 {"id":"lecture-mercy","query":"محاضرة رحمة النبي محمد أخلاقه","category":"lecture","topics":["mercy","ethics","lecture"]},
 {"id":"podcast-seerah","query":"بودكاست السيرة النبوية النبي محمد","category":"podcast","topics":["seerah","podcast"]},
 {"id":"podcast-shamail","query":"بودكاست الشمائل المحمدية","category":"podcast","topics":["shamail","podcast"]},
 {"id":"podcast-history","query":"بودكاست تاريخ السيرة النبوية","category":"podcast","topics":["history","podcast"]},
 {"id":"research-seerah","query":"بحث أكاديمي السيرة النبوية مؤتمر جامعة","category":"research","topics":["seerah","research","academic"]},
 {"id":"research-shamail","query":"دراسة أكاديمية الشمائل المحمدية مؤتمر","category":"research","topics":["shamail","research","academic"]},
 {"id":"research-prophetic","query":"ندوة علمية دراسات السيرة النبوية","category":"research","topics":["seerah","research","conference"]},
 {"id":"documentary-seerah","query":"وثائقي السيرة النبوية حياة النبي محمد كامل","category":"documentary","topics":["seerah","documentary"]},
 {"id":"documentary-makkah","query":"وثائقي مكة المدينة السيرة النبوية","category":"documentary","topics":["makkah","madinah","documentary"]},
 {"id":"documentary-history","query":"وثائقي تاريخ الإسلام السيرة النبوية النبي محمد","category":"documentary","topics":["history","documentary"]},
 {"id":"audio-seerah","query":"السيرة النبوية صوتي كاملة","category":"audio","topics":["seerah","audio"]},
 {"id":"audio-shamail","query":"الشمائل المحمدية صوتي","category":"audio","topics":["shamail","audio"]},
 {"id":"audio-praise","query":"مديح النبي محمد صوتي بردة دلائل الخيرات","category":"audio","topics":["praise","audio"]},
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
    target=int(os.getenv("PM_MEDIA_TARGET_PER_CATEGORY",str(TARGET_PER_CATEGORY)) or TARGET_PER_CATEGORY)
    report=sync_all(min(max_per_source,100))
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
        remaining=target-counts.get(cat,0)
        need=max(25,min(max_per_source,remaining+75))
        source={"id":src["id"],"kind":"youtube-search","query":src["query"],"label":src["id"],"category":cat,"topics":src["topics"],"language":"ar"}
        rows,err=_ydl_extract(f"ytsearch{need}:{src['query']}",source,need,False)
        if err:report.setdefault("errors",[]).append({"source":src["id"],"error":err})
        new=0
        for x in rows:
            x["medium"]=cat
            x["catalogTier"]="categorized-repertory"
            x["catalogSourceId"]=src["id"]
            if x.get("id") and x.get("id") not in by:new+=1
            if x.get("id"):by[x["id"]]=x
        counts={k:0 for k in TARGET_CATEGORIES}
        for x in by.values():
            x["medium"]=_medium(x)
            if x["medium"] in counts:counts[x["medium"]]+=1
        expansion.append({"source":src["id"],"category":cat,"retrieved":len(rows),"new":new,"categoryCount":counts.get(cat,0)})

    items=list(by.values())
    for x in items:x["medium"]=_medium(x)
    items.sort(key=lambda x:(x.get("medium",""),str(x.get("published","")),int(x.get("viewCount") or 0),str(x.get("titleAr") or x.get("titleEn") or "")),reverse=True)
    counts={k:0 for k in TARGET_CATEGORIES}
    for x in items:
        if x.get("medium") in counts:counts[x["medium"]]+=1
    missing={k:v for k,v in counts.items() if v<target}
    current.update({"version":"8.0.0","generated":now(),"items":items,"mediaCategories":list(TARGET_CATEGORIES),"categoryCounts":counts,"targetPerCategory":target,"minimumTotalTarget":target*len(TARGET_CATEGORIES),"complete":not missing})
    dump(OUT,current)
    report.update({"total":len(items),"categories":counts,"targetPerCategory":target,"minimumTotalTarget":target*len(TARGET_CATEGORIES),"missing":missing,"expansion":expansion,"ok":not missing})
    return report

if __name__=="__main__":
    result=run_expanded_sync()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result.get("missing"):
        raise SystemExit(2)
