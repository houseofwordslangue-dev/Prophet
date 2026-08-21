#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'children'/'stories'
COUNT=5000
SHARD_SIZE=100

NAMES=['سليم','ليلى','ياسر','مريم','آدم','سارة','حمزة','نور','أيوب','هبة','إلياس','ريم','أنس','صفاء','زياد','لينا','سامر','هدى','بلال','جنى']
PLACES=[
('الحديقة','حديقة هادئة تملؤها الأشجار والزهور'),('المكتبة','مكتبة صغيرة ذات نوافذ واسعة'),('القرية','قرية بين التلال'),('الشاطئ','شاطئ رملي هادئ'),('المزرعة','مزرعة مليئة بالأشجار والطيور'),
('المدرسة','مدرسة مضيئة بفناء واسع'),('الجبل','طريق جبلي تحيط به الصخور والأعشاب'),('الواحة','واحة خضراء وسط الرمل'),('السوق','سوق صباحي مليء بالألوان'),('المرصد','مرصد صغير لمراقبة النجوم'),
('الميناء','ميناء صغير وقوارب ملونة'),('البستان','بستان من أشجار الفاكهة'),('الورشة','ورشة صغيرة للأعمال اليدوية'),('المتحف','متحف هادئ للمعرفة والاكتشاف'),('المخيم','مخيم بين الأشجار'),
('الحي','حي هادئ يعرف فيه الجيران بعضهم'),('النهر','ضفة نهر تتلألأ فوقها الشمس'),('القطار','رحلة قصيرة في قطار بين المدن'),('المرج','مرج أخضر واسع'),('المنارة','منارة قديمة قرب البحر'),
('حديقة الطيور','حديقة صغيرة للطيور'),('مركز العلوم','مركز تجارب علمية للصغار'),('مخبز الحي','مخبز دافئ برائحة الخبز'),('مشتل النباتات','مشتل مليء بالنباتات الصغيرة'),('ساحة الألعاب','ساحة ألعاب بألوان لطيفة')]

THEMES=[
('kindness','اللطف','اللطف يجعل اليوم أخف على الجميع','ساعد صديقًا صغيرًا كان يحتاج إلى يد هادئة','اكتشف أن الكلمة الطيبة والفعل الصغير يمكن أن يغيّرا مزاج يوم كامل'),
('honesty','الصدق','الصدق يمنح القلب راحة وثقة','قال الحقيقة عندما كان من السهل أن يخفي خطأً بسيطًا','فهم أن الاعتراف بالحقيقة يساعد على إصلاح الخطأ وبناء الثقة'),
('courage','الشجاعة','الشجاعة تبدأ بخطوة صغيرة','واجه موقفًا جديدًا كان يثير القلق وتقدم خطوة خطوة','تعلم أن الشجاعة ليست غياب الخوف بل التصرف بحكمة رغم وجوده'),
('patience','الصبر','الأشياء الجميلة تحتاج وقتًا','انتظر بهدوء نتيجة عمل بدأه ولم تظهر ثماره بسرعة','رأى أن الصبر مع الاستمرار يصنع فرقًا حقيقيًا'),
('curiosity','حب المعرفة','السؤال الجيد يفتح بابًا جديدًا','تبع سؤالًا صغيرًا حتى قاده إلى اكتشاف ممتع','أدرك أن الفضول المنظم يجعل التعلم مغامرة لطيفة'),
('cooperation','التعاون','حين نتعاون يصبح الصعب أسهل','قسم مهمة كبيرة إلى أجزاء وتعاون مع الآخرين لإنجازها','عرف أن كل شخص يستطيع أن يضيف شيئًا مفيدًا للفريق'),
('responsibility','المسؤولية','الاهتمام بما نبدأه جزء من النجاح','تذكر مهمة وعد بها وأتمها حتى النهاية','شعر أن الاعتماد على النفس يبدأ من الوفاء بالمهام الصغيرة'),
('gratitude','الشكر','ملاحظة النعم الصغيرة تجعل القلب أكثر هدوءًا','توقف ليرى الأشياء الجميلة التي اعتاد المرور بجانبها','تعلم أن الشكر لا يحتاج إلى أشياء كبيرة بل إلى انتباه صادق'),
('nature','العناية بالطبيعة','الطبيعة تزدهر حين نعاملها برفق','اعتنى بمكان صغير ونظفه وسقى ما فيه من نباتات','رأى أن حماية البيئة تبدأ من عادة بسيطة تتكرر كل يوم'),
('forgiveness','التسامح','التسامح يفتح بابًا لبداية أفضل','حل خلافًا صغيرًا بالكلام الهادئ والاعتذار المتبادل','فهم أن التسامح لا يمحو الدرس لكنه يمنع الخطأ من إفساد الصداقة')]

AGE_GROUPS=[('4-6','مبتدئ'),('7-9','متوسط'),('10-12','متقدم')]
PALETTES=[['#f8e8ec','#e7f3ef','#fff4d6','#cfe4f5'],['#f6eadf','#e8eef8','#e9f5e5','#f9e8f1'],['#fff1df','#e7f1ff','#eef6e8','#f3e9fb'],['#eaf6f2','#fff2e7','#e9effb','#faeaf0'],['#f5eee6','#e7f4f1','#f7efd2','#e8ecf8']]

OPENINGS=[
'في صباح هادئ، وصل {name} إلى {place_desc} وهو يفكر في شيء جديد يريد أن يجربه.',
'بعد يوم طويل قليلًا، وجد {name} نفسه في {place_desc}، وهناك بدأت حكاية صغيرة لم تكن في الحسبان.',
'كان الهواء لطيفًا عندما دخل {name} {place}، ولاحظ تفصيلًا صغيرًا لم ينتبه إليه من قبل.',
'في أحد الأيام، اختار {name} أن يقضي بعض الوقت في {place_desc}، فظهرت أمامه فرصة للتعلم.',
'مع أول ضوء في ذلك اليوم، كان {name} في {place_desc} مستعدًا لمغامرة هادئة وبسيطة.'
]
MIDDLES=[
'لم يكن الحل واضحًا من البداية، لذلك توقف قليلًا وفكر في أكثر من طريقة قبل أن يتصرف.',
'تغير الموقف عندما قرر أن يستمع جيدًا إلى من حوله بدل أن يتعجل الإجابة.',
'جرب فكرة أولى فلم تنجح تمامًا، لكنه عدلها بدل أن يتوقف.',
'لاحظ أن التفاصيل الصغيرة كانت أهم مما توقع، فبدأ يرتبها واحدة بعد أخرى.',
'تذكر نصيحة بسيطة تعلمها من قبل، وحاول أن يطبقها بهدوء في هذا الموقف.'
]
CLOSINGS=[
'عاد {name} وهو يشعر أن يومه أصبح أوسع قليلًا، لأن درسًا صغيرًا تحول إلى عادة يمكن تكرارها.',
'قبل أن ينتهي اليوم، ابتسم {name} لأنه عرف أن أفضل القصص قد تبدأ من موقف عادي جدًا.',
'ومنذ ذلك اليوم، صار {name} يتذكر أن التغيير الجيد غالبًا يبدأ بخطوة هادئة.',
'احتفظ {name} بالدرس في ذهنه، ووعد نفسه أن يجربه مرة أخرى عندما تأتي فرصة جديدة.',
'وهكذا انتهت المغامرة دون ضجيج، لكنها تركت فكرة جميلة ترافق {name} في الأيام التالية.'
]

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def story_for(idx:int)->dict:
    n_idx=idx % len(NAMES)
    p_idx=(idx//len(NAMES)) % len(PLACES)
    t_idx=(idx//(len(NAMES)*len(PLACES))) % len(THEMES)
    name=NAMES[n_idx]; place,place_desc=PLACES[p_idx]
    key,theme,lesson,action,discovery=THEMES[t_idx]
    age,level=AGE_GROUPS[idx % len(AGE_GROUPS)]
    opening=OPENINGS[idx % len(OPENINGS)].format(name=name,place=place,place_desc=place_desc)
    middle=MIDDLES[(idx//5) % len(MIDDLES)]
    closing=CLOSINGS[(idx//25) % len(CLOSINGS)].format(name=name)
    body=[
        opening,
        f'وجد {name} نفسه أمام موقف بسيط: {action}. لم يكن الأمر كبيرًا، لكنه احتاج إلى انتباه وقرار هادئ.',
        middle,
        f'ومع مرور الوقت، {discovery}. عندها فهم معنى {theme} بطريقة عملية لا تحتاج إلى كلام كثير.',
        f'نظر {name} حوله إلى {place} ولاحظ أن كل شيء بدا أكثر هدوءًا. قال في نفسه: «{lesson}.»',
        closing
    ]
    sid=f'child-story-{idx+1:04d}'
    palette=PALETTES[idx % len(PALETTES)]
    title=f'{name} ودرس {theme} في {place}'
    return {
        'id':sid,'number':idx+1,'titleAr':title,'language':'ar','fictional':True,
        'historicalClaim':False,'category':key,'categoryAr':theme,'age':age,'readingLevel':level,
        'setting':place,'character':name,'lesson':lesson,'body':body,
        'illustration':{'type':'pastel-svg','palette':palette,'seed':idx+1,'scene':place},
        'estimatedMinutes':2 + (idx % 3),
        'disclaimer':'قصة خيالية تربوية؛ ليست رواية تاريخية ولا نقلًا عن مصدر.'
    }

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    stories=[story_for(i) for i in range(COUNT)]
    assert len(stories)==COUNT
    assert len({s['id'] for s in stories})==COUNT
    index=[]
    for shard_no,start in enumerate(range(0,COUNT,SHARD_SIZE),1):
        chunk=stories[start:start+SHARD_SIZE]
        filename=f'shard-{shard_no:03d}.json'
        payload={'schema':'children-stories-shard-v1','shard':shard_no,'count':len(chunk),'items':chunk}
        text=json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n'
        (OUT/filename).write_text(text,encoding='utf-8')
        digest=hashlib.sha256(text.encode()).hexdigest()
        for s in chunk:
            index.append({k:s[k] for k in ('id','number','titleAr','category','categoryAr','age','readingLevel','setting','character','lesson','estimatedMinutes')}|{'shard':shard_no})
    counts={k:0 for k,_,_,_,_ in THEMES}
    ages={a:0 for a,_ in AGE_GROUPS}
    for s in stories:
        counts[s['category']]+=1; ages[s['age']]+=1
    manifest={
        'schema':'children-stories-manifest-v1','generatedAt':now(),'count':COUNT,'shardSize':SHARD_SIZE,'shards':COUNT//SHARD_SIZE,
        'fictional':True,'historicalClaims':False,'illustrationMode':'procedural-pastel-svg',
        'categories':[{'id':k,'labelAr':ar,'count':counts[k]} for k,ar,_,_,_ in THEMES],
        'ageGroups':[{'id':a,'labelAr':a,'count':ages[a]} for a,_ in AGE_GROUPS],
        'disclaimer':'هذه القصص خيالية تربوية، منفصلة عن المواد التاريخية والمصدرية في الموقع.',
        'index':'index.json','shardPattern':'shard-{n:03d}.json'
    }
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'index.json').write_text(json.dumps({'schema':'children-stories-index-v1','count':COUNT,'items':index},ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps({'count':COUNT,'shards':COUNT//SHARD_SIZE,'output':str(OUT.relative_to(ROOT))},ensure_ascii=False))

if __name__=='__main__': main()
