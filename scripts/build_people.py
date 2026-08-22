#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
OUT=DATA/'people.json'

SEEDS=[
 ('prophet-muhammad','محمد ﷺ','Muhammad','Muhammad','prophet'),
 ('abdullah-ibn-abd-al-muttalib','عبد الله بن عبد المطلب','Abdullah ibn Abd al-Muttalib','Abdallah ibn Abd al-Muttalib','family'),
 ('amina-bint-wahb','آمنة بنت وهب','Amina bint Wahb','Amina bint Wahb','family'),
 ('abd-al-muttalib','عبد المطلب بن هاشم','Abd al-Muttalib ibn Hashim','Abd al-Muttalib ibn Hashim','ancestor'),
 ('hashim-ibn-abd-manaf','هاشم بن عبد مناف','Hashim ibn Abd Manaf','Hashim ibn Abd Manaf','ancestor'),
 ('abd-manaf-ibn-qusayy','عبد مناف بن قصي','Abd Manaf ibn Qusayy','Abd Manaf ibn Qusayy','ancestor'),
 ('qusayy-ibn-kilab','قصي بن كلاب','Qusayy ibn Kilab','Qusayy ibn Kilab','ancestor'),
 ('kilab-ibn-murra','كلاب بن مرة','Kilab ibn Murra','Kilab ibn Murra','ancestor'),
 ('murra-ibn-kab','مرة بن كعب','Murra ibn Kaab','Murra ibn Kaab','ancestor'),
 ('kab-ibn-luayy','كعب بن لؤي','Kaab ibn Luayy','Kaab ibn Luayy','ancestor'),
 ('luayy-ibn-ghalib','لؤي بن غالب','Luayy ibn Ghalib','Luayy ibn Ghalib','ancestor'),
 ('ghalib-ibn-fihr','غالب بن فهر','Ghalib ibn Fihr','Ghalib ibn Fihr','ancestor'),
 ('fihr-ibn-malik','فهر بن مالك','Fihr ibn Malik','Fihr ibn Malik','ancestor'),
 ('malik-ibn-al-nadr','مالك بن النضر','Malik ibn al-Nadr','Malik ibn al-Nadr','ancestor'),
 ('al-nadr-ibn-kinana','النضر بن كنانة','Al-Nadr ibn Kinana','Al-Nadr ibn Kinana','ancestor'),
 ('kinana-ibn-khuzayma','كنانة بن خزيمة','Kinana ibn Khuzayma','Kinana ibn Khuzayma','ancestor'),
 ('khuzayma-ibn-mudrika','خزيمة بن مدركة','Khuzayma ibn Mudrika','Khuzayma ibn Mudrika','ancestor'),
 ('mudrika-ibn-ilyas','مدركة بن إلياس','Mudrika ibn Ilyas','Mudrika ibn Ilyas','ancestor'),
 ('ilyas-ibn-mudar','إلياس بن مضر','Ilyas ibn Mudar','Ilyas ibn Mudar','ancestor'),
 ('mudar-ibn-nizar','مضر بن نزار','Mudar ibn Nizar','Mudar ibn Nizar','ancestor'),
 ('nizar-ibn-maadd','نزار بن معد','Nizar ibn Maadd','Nizar ibn Maadd','ancestor'),
 ('maadd-ibn-adnan','معد بن عدنان','Maadd ibn Adnan','Maadd ibn Adnan','ancestor'),
 ('adnan','عدنان','Adnan','Adnan','ancestor'),
 ('khadija-bint-khuwaylid','خديجة بنت خويلد','Khadija bint Khuwaylid','Khadija bint Khuwaylid','family'),
 ('sawda-bint-zama','سودة بنت زمعة','Sawda bint Zamaa','Sawda bint Zamaa','family'),
 ('aisha-bint-abi-bakr','عائشة بنت أبي بكر','Aisha bint Abi Bakr','Aicha bint Abi Bakr','family'),
 ('hafsa-bint-umar','حفصة بنت عمر','Hafsa bint Umar','Hafsa bint Umar','family'),
 ('zaynab-bint-khuzayma','زينب بنت خزيمة','Zaynab bint Khuzayma','Zaynab bint Khuzayma','family'),
 ('umm-salama','أم سلمة هند بنت أبي أمية','Umm Salama Hind bint Abi Umayya','Umm Salama Hind bint Abi Umayya','family'),
 ('zaynab-bint-jahsh','زينب بنت جحش','Zaynab bint Jahsh','Zaynab bint Jahsh','family'),
 ('juwayriya-bint-al-harith','جويرية بنت الحارث','Juwayriya bint al-Harith','Juwayriya bint al-Harith','family'),
 ('umm-habiba','أم حبيبة رملة بنت أبي سفيان','Umm Habiba Ramla bint Abi Sufyan','Umm Habiba Ramla bint Abi Sufyan','family'),
 ('safiyya-bint-huyayy','صفية بنت حيي','Safiyya bint Huyayy','Safiyya bint Huyayy','family'),
 ('maymuna-bint-al-harith','ميمونة بنت الحارث','Maymuna bint al-Harith','Maymuna bint al-Harith','family'),
 ('mariya-al-qibtiyya','مارية القبطية','Mariya al-Qibtiyya','Mariya al-Qibtiyya','family'),
 ('al-qasim-ibn-muhammad','القاسم بن محمد','Al-Qasim ibn Muhammad','Al-Qasim ibn Muhammad','family'),
 ('zaynab-bint-muhammad','زينب بنت محمد','Zaynab bint Muhammad','Zaynab bint Muhammad','family'),
 ('ruqayya-bint-muhammad','رقية بنت محمد','Ruqayya bint Muhammad','Ruqayya bint Muhammad','family'),
 ('umm-kulthum-bint-muhammad','أم كلثوم بنت محمد','Umm Kulthum bint Muhammad','Umm Kulthum bint Muhammad','family'),
 ('fatima-al-zahra','فاطمة الزهراء','Fatima al-Zahra','Fatima al-Zahra','family'),
 ('abdullah-ibn-muhammad','عبد الله بن محمد','Abdullah ibn Muhammad','Abdallah ibn Muhammad','family'),
 ('ibrahim-ibn-muhammad','إبراهيم بن محمد','Ibrahim ibn Muhammad','Ibrahim ibn Muhammad','family'),
 ('ali-ibn-abi-talib','علي بن أبي طالب','Ali ibn Abi Talib','Ali ibn Abi Talib','companion'),
 ('al-hasan-ibn-ali','الحسن بن علي','Al-Hasan ibn Ali','Al-Hasan ibn Ali','family'),
 ('al-husayn-ibn-ali','الحسين بن علي','Al-Husayn ibn Ali','Al-Husayn ibn Ali','family'),
 ('abu-bakr','أبو بكر الصديق','Abu Bakr al-Siddiq','Abu Bakr al-Siddiq','companion'),
 ('umar-ibn-al-khattab','عمر بن الخطاب','Umar ibn al-Khattab','Umar ibn al-Khattab','companion'),
 ('uthman-ibn-affan','عثمان بن عفان','Uthman ibn Affan','Uthman ibn Affan','companion'),
 ('hamza-ibn-abd-al-muttalib','حمزة بن عبد المطلب','Hamza ibn Abd al-Muttalib','Hamza ibn Abd al-Muttalib','companion'),
 ('al-abbas-ibn-abd-al-muttalib','العباس بن عبد المطلب','Al-Abbas ibn Abd al-Muttalib','Al-Abbas ibn Abd al-Muttalib','companion'),
 ('bilal-ibn-rabah','بلال بن رباح','Bilal ibn Rabah','Bilal ibn Rabah','companion'),
 ('salman-al-farisi','سلمان الفارسي','Salman al-Farisi','Salman al-Farisi','companion'),
 ('abu-hurayra','أبو هريرة','Abu Hurayra','Abu Hurayra','companion'),
 ('anas-ibn-malik','أنس بن مالك','Anas ibn Malik','Anas ibn Malik','companion'),
 ('abdullah-ibn-abbas','عبد الله بن عباس','Abdullah ibn Abbas','Abdallah ibn Abbas','companion'),
 ('abdullah-ibn-umar','عبد الله بن عمر','Abdullah ibn Umar','Abdallah ibn Umar','companion'),
 ('jabir-ibn-abdullah','جابر بن عبد الله','Jabir ibn Abdullah','Jabir ibn Abdallah','companion'),
 ('muadh-ibn-jabal','معاذ بن جبل','Muadh ibn Jabal','Muadh ibn Jabal','companion'),
 ('zaid-ibn-thabit','زيد بن ثابت','Zayd ibn Thabit','Zayd ibn Thabit','companion'),
 ('zaid-ibn-haritha','زيد بن حارثة','Zayd ibn Haritha','Zayd ibn Haritha','companion'),
 ('usama-ibn-zaid','أسامة بن زيد','Usama ibn Zayd','Usama ibn Zayd','companion'),
 ('khalid-ibn-al-walid','خالد بن الوليد','Khalid ibn al-Walid','Khalid ibn al-Walid','companion'),
 ('talha-ibn-ubaydullah','طلحة بن عبيد الله','Talha ibn Ubaydullah','Talha ibn Ubaydullah','companion'),
 ('al-zubayr-ibn-al-awwam','الزبير بن العوام','Al-Zubayr ibn al-Awwam','Al-Zubayr ibn al-Awwam','companion'),
 ('saad-ibn-abi-waqqas','سعد بن أبي وقاص','Saad ibn Abi Waqqas','Saad ibn Abi Waqqas','companion'),
 ('saeed-ibn-zayd','سعيد بن زيد','Saeed ibn Zayd','Saeed ibn Zayd','companion'),
 ('abu-ubayda-ibn-al-jarrah','أبو عبيدة بن الجراح','Abu Ubayda ibn al-Jarrah','Abu Ubayda ibn al-Jarrah','companion'),
]

def norm(s:str)->str:
    s=re.sub(r'[\u064b-\u065f\u0670ـ]','',s or '')
    return re.sub(r'\s+',' ',s).strip().lower()

def slugify(s:str)->str:
    h=hashlib.sha1(s.encode('utf-8')).hexdigest()[:12]
    return 'person-'+h

def load_json(p):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return None

def scan_values(obj,key=''):
    out=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            lk=k.lower()
            if lk in {'author','creator','narrator','person','personname','namear','nameen','namefr'} and isinstance(v,str) and 2<len(v)<120:
                out.append(v.strip())
            elif lk in {'children','spouses','parents','companions','narrators','people','persons'} and isinstance(v,list):
                for z in v:
                    if isinstance(z,str) and 2<len(z)<120: out.append(z.strip())
                    elif isinstance(z,dict): out.extend(scan_values(z,k))
            else: out.extend(scan_values(v,k))
    elif isinstance(obj,list):
        for v in obj: out.extend(scan_values(v,key))
    return out

def verified_passages():
    rows=[]
    for p in (DATA/'editorial'/'drafts').rglob('*.json') if (DATA/'editorial'/'drafts').exists() else []:
        j=load_json(p) or {}
        for d in j.get('drafts',[]):
            if int(d.get('sourceCoveragePercent') or 0)!=100 or int(d.get('aiOriginalSubstantiveContentPercent') or 0)!=0 or str(d.get('provenanceStatus','PASS')).upper()!='PASS': continue
            sources=d.get('sources') or []
            for para in d.get('paragraphs') or []:
                if para.get('aiOriginal') is True or para.get('quotationVerified') is False: continue
                text=str(para.get('text') or '').strip()
                if not text: continue
                rows.append({'text':text,'language':para.get('language') or 'ar','sources':sources,'articleId':d.get('id'),'title':d.get('title')})
    return rows

def build():
    people={}
    aliases={}
    for pid,ar,en,fr,cat in SEEDS:
        people[pid]={'id':pid,'slug':pid,'name':{'ar':ar,'en':en,'fr':fr},'category':cat,'biography':{'ar':[],'en':[],'fr':[]},'sayings':{'ar':[],'en':[],'fr':[]},'sourcePassages':[],'provenance':'source-only'}
        for x in (ar,en,fr): aliases[norm(x)]=pid
    # Discover explicitly named individuals/authors in repository JSON without inventing biographies.
    for p in DATA.rglob('*.json'):
        j=load_json(p)
        if j is None: continue
        for raw in scan_values(j):
            n=norm(raw)
            if not n or n in aliases: continue
            # Filter obvious non-person labels.
            if any(w in n for w in ('http','youtube','archive.org','هيئة تحرير الموقع','القرآن الكريم')): continue
            if len(n.split())>9: continue
            pid=slugify(raw)
            aliases[n]=pid
            people[pid]={'id':pid,'slug':pid,'name':{'ar':raw if re.search(r'[\u0600-\u06ff]',raw) else raw,'en':raw,'fr':raw},'category':'source-person','biography':{'ar':[],'en':[],'fr':[]},'sayings':{'ar':[],'en':[],'fr':[]},'sourcePassages':[],'provenance':'source-only'}
    passages=verified_passages()
    for row in passages:
        txtnorm=norm(row['text'])
        srcauthors=[str(s.get('author') or '').strip() for s in row['sources'] if isinstance(s,dict)]
        for n,pid in aliases.items():
            matched=n and len(n)>=4 and n in txtnorm
            authored=any(norm(a)==n for a in srcauthors if a)
            if not (matched or authored): continue
            rec=people[pid]
            entry={'text':row['text'],'language':row['language'],'articleId':row['articleId'],'articleTitle':row['title'],'sources':row['sources'],'relation':'authored-saying' if authored else 'documented-mention'}
            if entry not in rec['sourcePassages']: rec['sourcePassages'].append(entry)
            if authored:
                lang=row['language'] if row['language'] in ('ar','en','fr') else 'ar'
                rec['sayings'][lang].append(entry)
    payload={'version':'2026-08-20-source-only-people-v1','policy':{'aiSubstantiveContent':0,'aiComments':0,'biographyRule':'Only verified source passages or explicit source metadata may populate biography/sayings. No generated narrative.','locales':['ar','en','fr']},'count':len(people),'people':sorted(people.values(),key=lambda x:x['name']['ar'])}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'people':len(people),'withSourcePassages':sum(bool(x['sourcePassages']) for x in people.values()),'out':str(OUT)}

if __name__=='__main__': print(json.dumps(build(),ensure_ascii=False,indent=2))
