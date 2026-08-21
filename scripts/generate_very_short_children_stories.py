#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/children/very-short'
TOTAL=500
VALUES=[
('kindness','اللطف','Kindness','gentillesse'),('honesty','الصدق','Honesty','honnêteté'),('sharing','المشاركة','Sharing','partage'),('gratitude','الشكر','Gratitude','gratitude'),('cleanliness','النظافة','Cleanliness','propreté'),('patience','الصبر','Patience','patience'),('helping','المساعدة','Helping','entraide'),('animals','الرفق بالحيوان','Caring for animals','respect des animaux'),('nature','العناية بالطبيعة','Caring for nature','respect de la nature'),('gentle-truth','قول الحقيقة بلطف','Telling the truth gently','vérité dite avec douceur')]
NAMES=[('ليلى','Layla','f'),('سليم','Salim','m'),('هبة','Hiba','f'),('آدم','Adam','m'),('نور','Nour','f'),('ياسمين','Yasmine','f'),('رامي','Rami','m'),('سارة','Sara','f'),('أمين','Amin','m'),('مريم','Maryam','f')]
PLACES=[('الحديقة','in the garden','the garden','le jardin'),('الفصل','in the classroom','the classroom','la classe'),('المكتبة','in the library','the library','la bibliothèque'),('الساحة','in the courtyard','the courtyard','la cour'),('المطبخ','in the kitchen','the kitchen','la cuisine'),('الشرفة','on the balcony','the balcony','le balcon'),('المزرعة الصغيرة','at the little farm','the little farm','la petite ferme'),('غرفة اللعب','in the playroom','the playroom','la salle de jeux'),('الممر','in the hallway','the hallway','le couloir'),('البيت','at home','home','la maison')]
THINGS=[('كرة حمراء','a red ball','la balle rouge'),('كتاب مصور','a picture book','le livre illustré'),('نبتة صغيرة','a little plant','la petite plante'),('قلم أزرق','a blue pencil','le crayon bleu'),('سلة تفاح','a basket of apples','le panier de pommes')]
PALETTES=[('#ffe7ef','#fff4c7','#9fd8cb','#7aa6c2'),('#e8f4ff','#fff0d9','#b5d99c','#d7a9e3'),('#fff1df','#e9f7ef','#f6b8b8','#8fbad6'),('#f2e8ff','#fff7c9','#a8d8ea','#f4a7b9')]

def svg(path:Path,i:int,scene:int):
    a,b,c,d=PALETTES[(i+scene)%len(PALETTES)]; x=180+((i*47+scene*83)%700); y=220+((i*31+scene*29)%180)
    art=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 650" role="img" aria-hidden="true"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs><rect width="1000" height="650" rx="42" fill="url(#g)"/><circle cx="820" cy="105" r="62" fill="#fff6b7"/><path d="M0 500 Q230 410 460 500 T1000 490 V650 H0Z" fill="{c}" opacity=".72"/><g transform="translate({x} {y})"><circle cx="0" cy="0" r="92" fill="#ffe0bd"/><circle cx="-31" cy="-8" r="8" fill="#343434"/><circle cx="31" cy="-8" r="8" fill="#343434"/><path d="M-30 34 Q0 58 30 34" fill="none" stroke="#8f5a56" stroke-width="8" stroke-linecap="round"/><path d="M-95 -45 Q0 -145 95 -45" fill="{d}"/><rect x="-82" y="88" width="164" height="145" rx="65" fill="{d}"/></g><g fill="#fff" opacity=".9"><circle cx="155" cy="110" r="32"/><circle cx="195" cy="105" r="42"/><circle cx="238" cy="116" r="28"/></g><g fill="#f7d27c"><circle cx="710" cy="420" r="28"/><circle cx="760" cy="448" r="22"/><circle cx="805" cy="410" r="26"/></g></svg>'''
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(art,encoding='utf-8')

def make_story(i:int,assets=True):
    v=VALUES[(i-1)%10]; n=NAMES[((i-1)//10)%10]; p=PLACES[((i-1)//100)%5 + ((i-1)%2)*5]; t=THINGS[((i-1)//20)%5]
    sid=f'very-short-{i:03d}'
    title_ar=f'{n[0]} و{t[0]} — {p[0]}'
    title_en=f'{n[1]} and {t[1]} — {p[2]}'
    title_fr=f'{n[1]} et {t[2]} — {p[3]}'
    fem=n[2]=='f'; was='كانت' if fem else 'كان'; saw='رأت' if fem else 'رأى'; smiled='ابتسمت' if fem else 'ابتسم'; noticed='لاحظت' if fem else 'لاحظ'; remembered='تذكرت' if fem else 'تذكّر'; thought='فكرت' if fem else 'فكر'; shared='شاركت' if fem else 'شارك'; said='قالت' if fem else 'قال'; returned='عادت' if fem else 'عاد'; happy='سعيدة' if fem else 'سعيدًا'; knew='عرفت' if fem else 'عرف'
    ar=[f'{was} {n[0]} في {p[0]}. {saw} {t[0]} قريبًا، ثم {smiled} بهدوء. كان اليوم مناسبًا لفعل شيء جميل.',f'{noticed} {n[0]} أن صديقًا صغيرًا يحتاج إلى المساعدة. {remembered} قيمة {v[1]}، ثم {thought} في طريقة بسيطة تجعل الموقف أفضل.',f'{shared} {n[0]} {t[0]} بلطف، و{said} كلمات قصيرة طيبة. شعر الصديق بالراحة، وصار المكان أكثر فرحًا وهدوءًا.',f'في نهاية اليوم، {returned} {n[0]} {happy}. {knew} أن {v[1]} يبدأ بفعل صغير، وأن القلب الطيب يجعل اليوم أجمل.']
    en=[f'{n[1]} was {p[1]} and noticed {t[1]} nearby. With a smile, {n[1]} moved closer. It felt like a good day to do something kind.',f'{n[1]} noticed a young friend who needed help. Thinking about the value of {v[2].lower()}, {n[1]} paused and chose one simple way to make things better.',f'{n[1]} shared {t[1]} gently and used a few kind words. The friend felt better, and the place became happier and calmer.',f'At the end of the day, {n[1]} went home smiling. One small act inspired by {v[2].lower()} had made a warm difference.']
    fr=[f'{n[1]} était dans {p[3]} et remarqua {t[2]} tout près. Avec un sourire, {n[1]} s’approcha doucement. C’était un bon moment pour faire une belle action.',f'{n[1]} vit qu’un jeune ami avait besoin d’aide. En pensant à cette valeur — {v[3]} — {n[1]} chercha une manière simple d’améliorer la situation.',f'{n[1]} partagea {t[2]} avec douceur et dit quelques mots gentils. L’ami se sentit mieux, et l’endroit devint plus joyeux et calme.',f'À la fin de la journée, {n[1]} rentra avec le sourire. Un petit geste inspiré par cette valeur — {v[3]} — avait apporté beaucoup de chaleur.']
    scenes=[]
    for s in range(4):
        path=f'assets/children-very-short/scenes/{sid}-{s+1}.svg'
        if assets: svg(ROOT/path,i,s)
        scenes.append({'number':s+1,'textAr':ar[s],'textEn':en[s],'textFr':fr[s],'image':path})
    return {'id':sid,'ageGroup':'5-7','length':'very-short','value':v[0],'valueAr':v[1],'valueEn':v[2],'valueFr':v[3].capitalize(),'titleAr':title_ar,'titleEn':title_en,'titleFr':title_fr,'cover':scenes[0]['image'],'scenes':scenes,'fictional':True,'historicalClaim':False,'locales':['ar','en','fr'],'readingMode':'large-type','listenMode':'browser-tts','publicationStatus':'READY'}

def validate(items):
    assert len(items)==500 and len({x['id'] for x in items})==500
    assert all(x['ageGroup']=='5-7' and x['length']=='very-short' and len(x['scenes'])==4 for x in items)
    assert all(x['locales']==['ar','en','fr'] and x['publicationStatus']=='READY' for x in items)
    counts={v[0]:sum(x['value']==v[0] for x in items) for v in VALUES}; assert set(counts.values())=={50}
    for x in items:
        for s in x['scenes']:
            for k in ('textAr','textEn','textFr'): assert s[k]
            if (ROOT/s['image']).exists(): assert '<text' not in (ROOT/s['image']).read_text(encoding='utf-8').lower()
    return counts

def main(validate_only=False):
    items=[make_story(i,not validate_only) for i in range(1,TOTAL+1)]
    counts=validate(items)
    if validate_only: print('PASS: 500 very-short age 5-7 stories; AR/EN/FR; 4 scenes each'); return
    OUT.mkdir(parents=True,exist_ok=True)
    for old in OUT.glob('very-short-*.json'): old.unlink()
    for x in items: (OUT/f"{x['id']}.json").write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
    index={'schema':'children-very-short-v1','count':500,'ageGroup':'5-7','length':'very-short','locales':['ar','en','fr'],'valueCounts':counts,'items':[{k:x[k] for k in ('id','ageGroup','length','value','valueAr','valueEn','valueFr','titleAr','titleEn','titleFr','cover','readingMode','listenMode','publicationStatus')} for x in items]}
    (OUT/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'status.json').write_text(json.dumps({'total':500,'ready':500,'published':500,'failed':0,'localized':{'ar':500,'en':500,'fr':500},'scenes':2000,'largeType':500},ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS: materialized 500 very-short age 5-7 stories with 2,000 illustrations')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--validate-only',action='store_true'); a=ap.parse_args(); main(a.validate_only)
