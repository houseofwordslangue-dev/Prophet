#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'children'/'stories'
COUNT=5000
SHARD_SIZE=100

NAMES=[('سليم','m'),('ليلى','f'),('ياسر','m'),('مريم','f'),('آدم','m'),('سارة','f'),('حمزة','m'),('نور','f'),('أيوب','m'),('هبة','f'),('إلياس','m'),('ريم','f'),('أنس','m'),('صفاء','f'),('زياد','m'),('لينا','f'),('سامر','m'),('هدى','f'),('بلال','m'),('جنى','f')]
PLACES=[
('الحديقة','حديقة هادئة تملؤها الأشجار والزهور'),('المكتبة','مكتبة صغيرة ذات نوافذ واسعة'),('القرية','قرية بين التلال'),('الشاطئ','شاطئ رملي هادئ'),('المزرعة','مزرعة مليئة بالأشجار والطيور'),('المدرسة','مدرسة مضيئة بفناء واسع'),('الجبل','طريق جبلي تحيط به الصخور والأعشاب'),('الواحة','واحة خضراء وسط الرمل'),('السوق','سوق صباحي مليء بالألوان'),('المرصد','مرصد صغير لمراقبة النجوم'),('الميناء','ميناء صغير وقوارب ملونة'),('البستان','بستان من أشجار الفاكهة'),('الورشة','ورشة صغيرة للأعمال اليدوية'),('المتحف','متحف هادئ للمعرفة والاكتشاف'),('المخيم','مخيم بين الأشجار'),('الحي','حي هادئ يعرف فيه الجيران بعضهم'),('النهر','ضفة نهر تتلألأ فوقها الشمس'),('القطار','رحلة قصيرة في قطار بين المدن'),('المرج','مرج أخضر واسع'),('المنارة','منارة قديمة قرب البحر'),('حديقة الطيور','حديقة صغيرة للطيور'),('مركز العلوم','مركز تجارب علمية للصغار'),('مخبز الحي','مخبز دافئ برائحة الخبز'),('مشتل النباتات','مشتل مليء بالنباتات الصغيرة'),('ساحة الألعاب','ساحة ألعاب بألوان لطيفة')]
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

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def g(gender,m,f): return f if gender=='f' else m

def story_for(idx:int)->dict:
    name,gender=NAMES[idx % len(NAMES)]
    place,place_desc=PLACES[(idx//len(NAMES)) % len(PLACES)]
    key,theme,lesson,action_m,discovery_m=THEMES[(idx//(len(NAMES)*len(PLACES))) % len(THEMES)]
    age,level=AGE_GROUPS[idx % len(AGE_GROUPS)]
    action=action_m
    discovery=discovery_m
    if gender=='f':
        replacements={'ساعد ':'ساعدت ','قال ':'قالت ','واجه ':'واجهت ','انتظر ':'انتظرت ','تبع ':'تبعت ','قسم ':'قسمت ','تذكر ':'تذكرت ','توقف ':'توقفت ','اعتنى ':'اعتنت ','حل ':'حلت ','اكتشف ':'اكتشفت ','فهم ':'فهمت ','تعلم ':'تعلمت ','رأى ':'رأت ','أدرك ':'أدركت ','عرف ':'عرفت ','شعر ':'شعرت '}
        for a,b in replacements.items():
            if action.startswith(a): action=b+action[len(a):]
            if discovery.startswith(a): discovery=b+discovery[len(a):]
    openings=[
        f'في صباح هادئ، {g(gender,"وصل","وصلت")} {name} إلى {place_desc} و{g(gender,"هو يفكر","هي تفكر")} في شيء جديد تريد تجربته.' if gender=='f' else f'في صباح هادئ، وصل {name} إلى {place_desc} وهو يفكر في شيء جديد يريد أن يجربه.',
        f'بعد يوم طويل قليلًا، {g(gender,"وجد","وجدت")} {name} {g(gender,"نفسه","نفسها")} في {place_desc}، وهناك بدأت حكاية صغيرة لم تكن في الحسبان.',
        f'كان الهواء لطيفًا عندما {g(gender,"دخل","دخلت")} {name} {place}، و{g(gender,"لاحظ","لاحظت")} تفصيلًا صغيرًا لم {g(gender,"ينتبه","تنتبه")} إليه من قبل.',
        f'في أحد الأيام، {g(gender,"اختار","اختارت")} {name} أن {g(gender,"يقضي","تقضي")} بعض الوقت في {place_desc}، فظهرت {g(gender,"أمامه","أمامها")} فرصة للتعلم.',
        f'مع أول ضوء في ذلك اليوم، {g(gender,"كان","كانت")} {name} في {place_desc} {g(gender,"مستعدًا","مستعدة")} لمغامرة هادئة وبسيطة.'
    ]
    middles=[
        f'لم يكن الحل واضحًا من البداية، لذلك {g(gender,"توقف","توقفت")} قليلًا و{g(gender,"فكر","فكرت")} في أكثر من طريقة قبل أن {g(gender,"يتصرف","تتصرف")}.',
        f'تغير الموقف عندما {g(gender,"قرر","قررت")} أن {g(gender,"يستمع","تستمع")} جيدًا إلى من حوله بدل أن {g(gender,"يتعجل","تتعجل")} الإجابة.',
        f'{g(gender,"جرب","جربت")} فكرة أولى فلم تنجح تمامًا، {g(gender,"لكنه","لكنها")} {g(gender,"عدلها","عدلتها")} بدل أن {g(gender,"يتوقف","تتوقف")}.',
        f'{g(gender,"لاحظ","لاحظت")} أن التفاصيل الصغيرة كانت أهم مما توقع، ف{g(gender,"بدأ","بدأت")} {g(gender,"يرتبها","ترتبها")} واحدة بعد أخرى.',
        f'{g(gender,"تذكر","تذكرت")} نصيحة بسيطة {g(gender,"تعلمها","تعلمتها")} من قبل، و{g(gender,"حاول","حاولت")} أن {g(gender,"يطبقها","تطبقها")} بهدوء في هذا الموقف.'
    ]
    closings=[
        f'{g(gender,"عاد","عادت")} {name} و{g(gender,"هو يشعر","هي تشعر")} أن يومه أصبح أوسع قليلًا، لأن درسًا صغيرًا تحول إلى عادة يمكن تكرارها.' if gender=='m' else f'عادت {name} وهي تشعر أن يومها أصبح أوسع قليلًا، لأن درسًا صغيرًا تحول إلى عادة يمكن تكرارها.',
        f'قبل أن ينتهي اليوم، {g(gender,"ابتسم","ابتسمت")} {name} {g(gender,"لأنه عرف","لأنها عرفت")} أن أفضل القصص قد تبدأ من موقف عادي جدًا.',
        f'ومنذ ذلك اليوم، {g(gender,"صار","صارت")} {name} {g(gender,"يتذكر","تتذكر")} أن التغيير الجيد غالبًا يبدأ بخطوة هادئة.',
        f'{g(gender,"احتفظ","احتفظت")} {name} بالدرس في ذهنه، و{g(gender,"وعد نفسه","وعدت نفسها")} أن {g(gender,"يجربه","تجربه")} مرة أخرى عندما تأتي فرصة جديدة.' if gender=='m' else f'احتفظت {name} بالدرس في ذهنها، ووعدت نفسها أن تجربه مرة أخرى عندما تأتي فرصة جديدة.',
        f'وهكذا انتهت المغامرة دون ضجيج، لكنها تركت فكرة جميلة ترافق {name} في الأيام التالية.'
    ]
    body=[
        openings[idx % len(openings)],
        f'{g(gender,"وجد","وجدت")} {name} {g(gender,"نفسه","نفسها")} أمام موقف بسيط: {action}. لم يكن الأمر كبيرًا، لكنه احتاج إلى انتباه وقرار هادئ.',
        middles[(idx//5) % len(middles)],
        f'ومع مرور الوقت، {discovery}. عندها {g(gender,"فهم","فهمت")} معنى {theme} بطريقة عملية لا تحتاج إلى كلام كثير.',
        f'{g(gender,"نظر","نظرت")} {name} حوله إلى {place} و{g(gender,"لاحظ","لاحظت")} أن كل شيء بدا أكثر هدوءًا. {g(gender,"قال","قالت")} في {g(gender,"نفسه","نفسها")}: «{lesson}.»' if gender=='m' else f'نظرت {name} حولها إلى {place} ولاحظت أن كل شيء بدا أكثر هدوءًا. قالت في نفسها: «{lesson}.»',
        closings[(idx//25) % len(closings)]
    ]
    sid=f'child-story-{idx+1:04d}'
    return {'id':sid,'number':idx+1,'titleAr':f'{name} ودرس {theme} في {place}','language':'ar','fictional':True,'historicalClaim':False,'category':key,'categoryAr':theme,'age':age,'readingLevel':level,'setting':place,'character':name,'characterGender':gender,'lesson':lesson,'body':body,'illustration':{'type':'pastel-svg','palette':PALETTES[idx % len(PALETTES)],'seed':idx+1,'scene':place},'estimatedMinutes':2+(idx%3),'disclaimer':'قصة خيالية تربوية؛ ليست رواية تاريخية ولا نقلًا عن مصدر.'}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    stories=[story_for(i) for i in range(COUNT)]
    assert len(stories)==COUNT and len({s['id'] for s in stories})==COUNT
    index=[]
    for shard_no,start in enumerate(range(0,COUNT,SHARD_SIZE),1):
        chunk=stories[start:start+SHARD_SIZE]
        (OUT/f'shard-{shard_no:03d}.json').write_text(json.dumps({'schema':'children-stories-shard-v1','shard':shard_no,'count':len(chunk),'items':chunk},ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
        for s in chunk:index.append({k:s[k] for k in ('id','number','titleAr','category','categoryAr','age','readingLevel','setting','character','lesson','estimatedMinutes')}|{'shard':shard_no})
    counts={k:0 for k,_,_,_,_ in THEMES}; ages={a:0 for a,_ in AGE_GROUPS}
    for s in stories: counts[s['category']]+=1; ages[s['age']]+=1
    manifest={'schema':'children-stories-manifest-v1','generatedAt':now(),'count':COUNT,'shardSize':SHARD_SIZE,'shards':COUNT//SHARD_SIZE,'fictional':True,'historicalClaims':False,'illustrationMode':'procedural-pastel-svg','categories':[{'id':k,'labelAr':ar,'count':counts[k]} for k,ar,_,_,_ in THEMES],'ageGroups':[{'id':a,'labelAr':a,'count':ages[a]} for a,_ in AGE_GROUPS],'disclaimer':'هذه القصص خيالية تربوية، منفصلة عن المواد التاريخية والمصدرية في الموقع.','index':'index.json','shardPattern':'shard-{n:03d}.json'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'index.json').write_text(json.dumps({'schema':'children-stories-index-v1','count':COUNT,'items':index},ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps({'count':COUNT,'shards':COUNT//SHARD_SIZE,'output':str(OUT.relative_to(ROOT))},ensure_ascii=False))

if __name__=='__main__': main()
