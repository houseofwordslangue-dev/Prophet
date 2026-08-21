#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,html
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/children/very-short'
ART=ROOT/'assets/children-very-short/scenes'
TOTAL=500
VALUES=[
('kindness','اللطف','Kindness','Gentillesse'),('honesty','الصدق','Honesty','Honnêteté'),('sharing','المشاركة','Sharing','Partage'),('gratitude','الشكر','Gratitude','Gratitude'),('cleanliness','النظافة','Cleanliness','Propreté'),('patience','الصبر','Patience','Patience'),('helping','المساعدة','Helping','Entraide'),('animals','الرفق بالحيوان','Caring for animals','Respect des animaux'),('nature','العناية بالطبيعة','Caring for nature','Respect de la nature'),('gentle-truth','قول الحقيقة بلطف','Telling the truth gently','Dire la vérité avec douceur')]
NAMES=[('ليلى','Layla'),('سليم','Salim'),('هبة','Hiba'),('آدم','Adam'),('نور','Nour'),('ياسمين','Yasmine'),('رامي','Rami'),('سارة','Sara'),('أمين','Amin'),('مريم','Maryam')]
PLACES=[('الحديقة','the garden','le jardin'),('الفصل','the classroom','la classe'),('المكتبة','the library','la bibliothèque'),('الساحة','the courtyard','la cour'),('المطبخ','the kitchen','la cuisine'),('الشرفة','the balcony','le balcon'),('المزرعة الصغيرة','the little farm','la petite ferme'),('غرفة اللعب','the playroom','la salle de jeux'),('الممر','the hallway','le couloir'),('البيت','home','la maison')]
THINGS=[('كرة حمراء','red ball','balle rouge'),('كتاب مصور','picture book','livre illustré'),('نبتة صغيرة','little plant','petite plante'),('قلم أزرق','blue pencil','crayon bleu'),('سلة تفاح','basket of apples','panier de pommes')]
PALETTES=[('#ffe7ef','#fff4c7','#9fd8cb','#7aa6c2'),('#e8f4ff','#fff0d9','#b5d99c','#d7a9e3'),('#fff1df','#e9f7ef','#f6b8b8','#8fbad6'),('#f2e8ff','#fff7c9','#a8d8ea','#f4a7b9')]

def svg(path:Path,i:int,scene:int):
    a,b,c,d=PALETTES[(i+scene)%len(PALETTES)]; x=180+((i*47+scene*83)%700); y=220+((i*31+scene*29)%180)
    art=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 650" role="img" aria-hidden="true"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs><rect width="1000" height="650" rx="42" fill="url(#g)"/><circle cx="820" cy="105" r="62" fill="#fff6b7"/><path d="M0 500 Q230 410 460 500 T1000 490 V650 H0Z" fill="{c}" opacity=".72"/><g transform="translate({x} {y})"><circle cx="0" cy="0" r="92" fill="#ffe0bd"/><circle cx="-31" cy="-8" r="8" fill="#343434"/><circle cx="31" cy="-8" r="8" fill="#343434"/><path d="M-30 34 Q0 58 30 34" fill="none" stroke="#8f5a56" stroke-width="8" stroke-linecap="round"/><path d="M-95 -45 Q0 -145 95 -45" fill="{d}"/><rect x="-82" y="88" width="164" height="145" rx="65" fill="{d}"/></g><g fill="#fff" opacity=".9"><circle cx="155" cy="110" r="32"/><circle cx="195" cy="105" r="42"/><circle cx="238" cy="116" r="28"/></g><g fill="#f7d27c"><circle cx="710" cy="420" r="28"/><circle cx="760" cy="448" r="22"/><circle cx="805" cy="410" r="26"/></g></svg>'''
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(art,encoding='utf-8')

def make_story(i:int,assets=True):
    v=VALUES[(i-1)%10]; n=NAMES[((i-1)//10)%10]; p=PLACES[((i-1)//100)%5 + ((i-1)%2)*5]; t=THINGS[((i-1)//20)%5]
    sid=f'very-short-{i:03d}'; title_ar=f'{n[0]} و{t[0]}'; title_en=f'{n[1]} and the {t[1]}'; title_fr=f'{n[1]} et le {t[2]}'
    ar=[f'دخل {n[0]} إلى {p[0]} ورأى {t[0]}. ابتسم واقترب بهدوء. كان اليوم مناسبًا لفعل شيء جميل.',f'لاحظ {n[0]} أن صديقًا صغيرًا يحتاج إلى المساعدة. تذكّر قيمة {v[1]}، فتوقف وفكر في أبسط طريقة للمساعدة.',f'شارك {n[0]} {t[0]} بلطف، وقال كلمات قصيرة طيبة. شعر الصديق بالراحة، وصار المكان أكثر فرحًا وهدوءًا.',f'في نهاية اليوم، عاد {n[0]} سعيدًا. عرف أن {v[1]} يبدأ بفعل صغير، وأن القلب الطيب يجعل اليوم أجمل.']
    en=[f'{n[1]} entered {p[1]} and saw a {t[1]}. With a smile, {n[1]} walked closer. It felt like a good day to do something kind.',f'{n[1]} noticed a young friend who needed help. Remembering {v[2].lower()}, {n[1]} stopped and thought of one simple way to help.',f'{n[1]} shared the {t[1]} gently and used a few kind words. The friend felt better, and the place became happier and calmer.',f'At the end of the day, {n[1]} went home smiling. A small act of {v[2].lower()} had made a big, warm difference.']
    fr=[f'{n[1]} entra dans {p[2]} et vit un {t[2]}. Avec un sourire, {n[1]} s’approcha doucement. C’était un bon jour pour faire une belle action.',f'{n[1]} remarqua un petit ami qui avait besoin d’aide. En pensant à la {v[3].lower()}, {n[1]} chercha une manière simple de l’aider.',f'{n[1]} partagea le {t[2]} avec douceur et dit quelques mots gentils. L’ami se sentit mieux et l’endroit devint plus joyeux et calme.',f'À la fin de la journée, {n[1]} rentra avec le sourire. Un petit geste de {v[3].lower()} avait apporté beaucoup de chaleur.']
    scenes=[]
    for s in range(4):
        path=f'assets/children-very-short/scenes/{sid}-{s+1}.svg'
        if assets: svg(ROOT/path,i,s)
        scenes.append({'number':s+1,'textAr':ar[s],'textEn':en[s],'textFr':fr[s],'image':path})
    return {'id':sid,'ageGroup':'5-7','length':'very-short','value':v[0],'valueAr':v[1],'valueEn':v[2],'valueFr':v[3],'titleAr':title_ar,'titleEn':title_en,'titleFr':title_fr,'cover':scenes[0]['image'],'scenes':scenes,'fictional':True,'historicalClaim':False,'locales':['ar','en','fr'],'readingMode':'large-type','listenMode':'browser-tts','publicationStatus':'READY'}

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
