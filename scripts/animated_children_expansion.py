#!/usr/bin/env python3
from __future__ import annotations

import generate_animated_children_stories as base

TOTAL_STORIES=600
ORIGINAL_STORIES=100
ADDITIONAL_STORIES=500

CATEGORY_EN={
    'kindness':'Kindness','honesty':'Honesty','courage':'Courage','patience':'Patience','curiosity':'Curiosity',
    'cooperation':'Cooperation','responsibility':'Responsibility','gratitude':'Gratitude','nature':'Care for nature','forgiveness':'Forgiveness'
}
CATEGORY_FR={
    'kindness':'Gentillesse','honesty':'Honnêteté','courage':'Courage','patience':'Patience','curiosity':'Curiosité',
    'cooperation':'Coopération','responsibility':'Responsabilité','gratitude':'Gratitude','nature':'Soin de la nature','forgiveness':'Pardon'
}

# 25 missions × 20 stakes = 500 distinct, naturally readable story identities.
MISSIONS=[
('محطة الطقس الصغيرة','community weather station','petite station météo'),('ممر الطيور','bird migration corridor','couloir des oiseaux'),('حديقة السطح','rooftop garden','jardin sur le toit'),('مكتبة الحي المتنقلة','mobile neighborhood library','bibliothèque mobile du quartier'),('مرصد النجوم المدرسي','school stargazing station','poste d’observation des étoiles'),('قارب تنظيف البحيرة','lake cleanup boat','bateau de nettoyage du lac'),('مختبر الماء','water-testing lab','laboratoire de l’eau'),('خريطة الظلال','shadow map','carte des ombres'),('ورشة إصلاح الدراجات','bicycle repair workshop','atelier de réparation des vélos'),('بيت الحشرات النافعة','beneficial-insect shelter','abri pour insectes utiles'),('مسرح الدمى','puppet theater','théâtre de marionnettes'),('مخزن البذور','seed library','grainothèque'),('مسار الوصول السهل','accessible route','parcours accessible'),('نظام ري الحديقة','garden irrigation system','système d’irrigation du jardin'),('ركن التجارب الصوتية','sound experiment corner','coin d’expériences sonores'),('جسر المشاة الصغير','small pedestrian bridge','petit pont piéton'),('لوحة أخبار المدرسة','school news board','panneau d’information scolaire'),('مركز تبادل الأدوات','tool-sharing station','point de partage d’outils'),('حائط النباتات','living plant wall','mur végétal'),('مسار قياس الرياح','wind-measurement trail','parcours de mesure du vent'),('صندوق المفقودات الذكي','smart lost-and-found box','boîte intelligente des objets trouvés'),('معرض الصور القديمة','old-photo exhibition','exposition de photos anciennes'),('منصة مراقبة السحب','cloud observation deck','plateforme d’observation des nuages'),('مزرعة المدرسة الصغيرة','small school farm','petite ferme scolaire'),('محطة تدوير الورق','paper recycling station','station de recyclage du papier')
]
STAKES=[
('قبل يوم المدرسة المفتوح','before the school open day','avant la journée portes ouvertes'),('بينما تقل كمية الماء المتاحة','while the available water supply is limited','alors que la réserve d’eau est limitée'),('قبل وصول مجموعة أصغر سنًا','before a younger group arrives','avant l’arrivée d’un groupe plus jeune'),('أثناء موجة حر قصيرة','during a short heat wave','pendant une courte vague de chaleur'),('بعد ليلة عاصفة','after a stormy night','après une nuit d’orage'),('بينما يستخدم المكان فريقان مختلفان','while two teams share the same space','alors que deux équipes partagent le même espace'),('قبل عرض النتائج أمام العائلات','before presenting results to families','avant de présenter les résultats aux familles'),('مع وجود وقت محدود قبل الإغلاق','with little time before closing','avec peu de temps avant la fermeture'),('حين تتعارض سرعتان مختلفتان للعمل','when two working rhythms conflict','lorsque deux rythmes de travail s’opposent'),('بعد اكتشاف خطأ في السجل القديم','after an error is found in an old record','après la découverte d’une erreur dans un ancien registre'),('بينما يحتاج أحد الأصدقاء إلى مسار أسهل','while a friend needs an easier route','alors qu’un ami a besoin d’un parcours plus accessible'),('قبل رحلة قصيرة إلى خارج الحي','before a short trip outside the neighborhood','avant une courte sortie hors du quartier'),('حين يختلف الفريق حول توزيع الموارد','when the team disagrees about sharing resources','lorsque l’équipe n’est pas d’accord sur le partage des ressources'),('أثناء مسابقة لا ينبغي أن تفسد الصداقة','during a competition that should not damage friendship','pendant un concours qui ne doit pas abîmer l’amitié'),('بعد وعد بإعادة الأدوات في موعدها','after promising to return borrowed tools on time','après avoir promis de rendre le matériel emprunté à temps'),('حين تظهر معلومة محرجة في القياسات','when an uncomfortable measurement appears','lorsqu’une mesure gênante apparaît'),('بينما يهدد حل سريع مكانًا طبيعيًا قريبًا','while a quick fix could harm a nearby natural place','alors qu’une solution rapide pourrait nuire à un espace naturel voisin'),('بعد سوء فهم سببه شرح غير واضح','after a misunderstanding caused by unclear instructions','après un malentendu causé par des consignes imprécises'),('حين يضطر الفريق إلى الاعتذار عن قرار متسرع','when the team must apologize for a rushed decision','lorsque l’équipe doit s’excuser d’une décision précipitée'),('قبل تسليم المشروع لفريق جديد','before handing the project to a new team','avant de transmettre le projet à une nouvelle équipe')
]

PHASE_AR=[
'يعرّف الفريق المهمة ويكتب ما سيعدّه نجاحًا قبل لمس أي أداة.',
'تظهر عقبة أولى تجبرهم على التمييز بين المعلومة والتخمين.',
'يجمعون شاهدين مستقلين ويقارنون القياسات بدل الاعتماد على الذاكرة.',
'تفشل تجربة محدودة، فيوثقون سبب الفشل من غير لوم أحد.',
'يكشف تفصيل صغير أن المشكلة أوسع من الشيء الذي لفت الانتباه أولًا.',
'يختلف صديقان حول الأولوية، فيعيد كل واحد كلام الآخر قبل الرد عليه.',
'يختار الفريق حلاً يحمي حق شخص أو مكان لا يشارك في النقاش.',
'ينفذون الخطة خطوة خطوة مع نقطة توقف للمراجعة قبل القرار الحاسم.',
'بعد النجاح يصلحون أثر المحاولات السابقة ويتركون تعليمات أوضح لمن يأتي بعدهم.',
'يعود الأبطال إلى يومهم العادي وهم يعرفون كيف سيستخدمون الدرس في موقف آخر.'
]
PHASE_EN=[
'The team defines the mission and writes down what success will mean before touching any tool.',
'The first obstacle forces them to separate evidence from assumption.',
'They gather two independent observations and compare measurements instead of relying on memory.',
'A limited trial fails, so they record the reason without blaming anyone.',
'A small clue reveals that the problem is wider than the object that first caught their attention.',
'Two friends disagree about priorities and each restates the other’s view before replying.',
'The team chooses an option that protects a person or place not represented in the discussion.',
'They carry out the plan step by step and pause for review before the decisive action.',
'After success, they repair the effects of earlier attempts and leave clearer instructions for the next group.',
'The characters return to ordinary life knowing how they will use the lesson in a different situation.'
]
PHASE_FR=[
'L’équipe définit la mission et écrit ce que signifiera la réussite avant de toucher au matériel.',
'Le premier obstacle les oblige à distinguer les faits des suppositions.',
'Ils recueillent deux observations indépendantes et comparent les mesures au lieu de se fier à la mémoire.',
'Un essai limité échoue; ils en consignent la cause sans accuser personne.',
'Un petit indice révèle que le problème dépasse l’objet qui avait d’abord attiré leur attention.',
'Deux amis ne sont pas d’accord sur les priorités et chacun reformule l’avis de l’autre avant de répondre.',
'L’équipe choisit une solution qui protège aussi une personne ou un lieu absent de la discussion.',
'Ils appliquent le plan étape par étape et s’arrêtent pour vérifier avant l’action décisive.',
'Après la réussite, ils réparent les effets des essais précédents et laissent des consignes plus claires au groupe suivant.',
'Les personnages reprennent leur quotidien en sachant comment réutiliser cette leçon dans une autre situation.'
]

PERSONALITY={
'ar':'ملاحظ، فضولي، يتعلم من الخطأ ويصغي قبل أن يحكم',
'en':'observant, curious, learns from mistakes, and listens before judging',
'fr':'observateur, curieux, apprend de ses erreurs et écoute avant de juger'
}
WEAKNESS={'ar':'يتعجل أحيانًا عندما يشعر بالمسؤولية','en':'sometimes rushes when feeling responsible','fr':'se précipite parfois lorsqu’il se sent responsable'}
APPEARANCE={'ar':'شخصية خيالية أصلية بملامح واضحة وتسريحة ثابتة وتعبير مناسب للعمر','en':'an original fictional character with a clear silhouette, consistent hairstyle, and age-appropriate expression','fr':'un personnage fictif original à la silhouette claire, à la coiffure cohérente et à l’expression adaptée à son âge'}
CLOTHING={'ar':'ملابس يومية عملية بألوان هادئة من دون شعارات أو علامات تجارية','en':'practical everyday clothing in calm colors with no logos or brands','fr':'des vêtements quotidiens pratiques aux couleurs douces, sans logo ni marque'}
TONE={
'curious':('فضولي','curious','curieux'),'hopeful':('متفائل','hopeful','optimiste'),'focused':('مركّز','focused','concentré'),'warm':('دافئ','warm','chaleureux')
}


def age_for(i:int)->str:
    if i<=100:
        return base.AGE_GROUPS[(i-1)//25]
    j=i-101
    return base.AGE_GROUPS[min(3,j//125)]


def _localized_names(i:int):
    p=(i-1)%25; f=i%25
    return {
        'protagonist':(base.NAMES_AR[p],base.NAMES_EN[p],base.NAMES_FR[p]),
        'friend':(base.NAMES_AR[f],base.NAMES_EN[f],base.NAMES_FR[f])
    }


def _dialogue(i:int,scene_no:int):
    names=_localized_names(i); pa,pe,pf=names['protagonist']; fa,fe,ff=names['friend']
    ar=[
        (pa,'لنكتب ما نعرفه أولًا، ثم نختبر خطوة واحدة.'),(fa,'وسأدوّن ما يتغير حتى نستطيع المقارنة.')
    ]
    en=[
        (pe,'Let us write down what we know first, then test one step.'),(fe,'I will record what changes so we can compare it.')
    ]
    fr=[
        (pf,'Écrivons d’abord ce que nous savons, puis testons une seule étape.'),(ff,'Je noterai ce qui change afin que nous puissions comparer.')
    ]
    if scene_no>=6:
        ar=[(pa,'أريد أن أفهم اعتراضك قبل أن أدافع عن فكرتي.'),(fa,'إذن نبحث عن حل يحمي الهدف والآخرين معًا.')]
        en=[(pe,'I want to understand your objection before defending my idea.'),(fe,'Then we should find a solution that protects both the goal and other people.')]
        fr=[(pf,'Je veux comprendre ton objection avant de défendre mon idée.'),(ff,'Cherchons alors une solution qui protège à la fois l’objectif et les autres.')]
    def pack(rows): return [{'speaker':a,'text':b} for a,b in rows]
    return pack(ar),pack(en),pack(fr)


def apply(story:dict,i:int)->dict:
    base.age_for=age_for
    names=_localized_names(i)
    cat=story['category']
    story['categoryEn']=CATEGORY_EN[cat]
    story['categoryFr']=CATEGORY_FR[cat]
    story['locales']=['ar','en','fr']
    story['localizationStatus']={'ar':'complete','en':'complete','fr':'complete'}

    # New stories receive one of 500 unique mission/stake identities.
    if i>100:
        j=i-101; mission=MISSIONS[j%25]; stake=STAKES[j//25]
        story['expansionKey']=f'addition-500-{j+1:03d}'
        story['mission']={'ar':mission[0],'en':mission[1],'fr':mission[2]}
        story['stake']={'ar':stake[0],'en':stake[1],'fr':stake[2]}
        story['titleAr']=f"{story['titleAr']} — مهمة {mission[0]}"
        story['titleEn']=f"{story['titleEn']} — {mission[1].title()} Mission"
        story['titleFr']=f"{story['titleFr']} — mission {mission[2]}"
        story['slug']=f"{story['id']}-{j+1:03d}-{base.slugify(mission[1])}"
        story['synopsisAr'] += f" وتتخذ الحكاية مسارًا خاصًا حول {mission[0]} {stake[0]}."
        story['synopsisEn'] += f" This episode develops a distinct mission around the {mission[1]} {stake[1]}."
        story['synopsisFr'] += f" Cet épisode développe une mission particulière autour de {mission[2]} {stake[2]}."
        for n in range(10):
            ar=f"في مسار {mission[0]} {stake[0]}، {PHASE_AR[n]}"
            en=f"For the {mission[1]} {stake[1]}, {PHASE_EN[n]}"
            fr=f"Pour {mission[2]} {stake[2]}, {PHASE_FR[n]}"
            story['storyAr'][n]['text'] += ' '+ar
            story['storyEn'][n]['text'] += ' '+en
            story['storyFr'][n]['text'] += ' '+fr
            story['scenes'][n]['narration']=story['storyAr'][n]['text']
            story['scenes'][n]['narrationEn']=story['storyEn'][n]['text']
            story['scenes'][n]['narrationFr']=story['storyFr'][n]['text']
            story['scenes'][n]['expansionBeat']={'ar':ar,'en':en,'fr':fr}

    # Fully localize character metadata.
    for idx,ch in enumerate(story.get('characters') or []):
        triple=names['protagonist' if idx==0 else 'friend']
        ch['nameAr'],ch['nameEn'],ch['nameFr']=triple
        ch['personalityAr'],ch['personalityEn'],ch['personalityFr']=PERSONALITY['ar'],PERSONALITY['en'],PERSONALITY['fr']
        ch['weaknessAr'],ch['weaknessEn'],ch['weaknessFr']=WEAKNESS['ar'],WEAKNESS['en'],WEAKNESS['fr']
        ch['appearanceDescriptionAr'],ch['appearanceDescriptionEn'],ch['appearanceDescriptionFr']=APPEARANCE['ar'],APPEARANCE['en'],APPEARANCE['fr']
        ch['clothingDescriptionAr'],ch['clothingDescriptionEn'],ch['clothingDescriptionFr']=CLOTHING['ar'],CLOTHING['en'],CLOTHING['fr']

    # Fully localize visible scene metadata and dialogue.
    setting=base.SETTINGS[(i*3+i//7)%len(base.SETTINGS)]
    obj=base.OBJECTS[(i*7)%len(base.OBJECTS)]
    for n,sc in enumerate(story.get('scenes') or [],1):
        dar,den,dfr=_dialogue(i,n)
        sc['settingAr'],sc['settingEn'],sc['settingFr']=setting
        sc['visualDescriptionAr']=f'مشهد أصلي في {setting[0]} يبرز {obj[0]} وتفاعل الشخصيات الخيالية مع تطور الحدث.'
        sc['visualDescriptionEn']=f'An original scene in {setting[1]} featuring the {obj[1]} and fictional characters responding to the developing event.'
        sc['visualDescriptionFr']=f'Une scène originale à {setting[2]} mettant en valeur {obj[2]} et des personnages fictifs qui réagissent à l’évolution de l’événement.'
        sc['dialogueAr'],sc['dialogueEn'],sc['dialogueFr']=dar,den,dfr
        tone=TONE.get(sc.get('emotionalTone'),TONE['focused'])
        sc['emotionalToneAr'],sc['emotionalToneEn'],sc['emotionalToneFr']=tone
        sc['animationInstructionsAr']='حركة كاميرا هادئة وعمق بسيط وانتقال لطيف مع احترام إعداد تقليل الحركة.'
        sc['animationInstructionsEn']='Gentle camera movement, light depth, and soft transitions with reduced-motion preferences respected.'
        sc['animationInstructionsFr']='Mouvement de caméra doux, légère profondeur et transitions souples en respectant la préférence de réduction des animations.'
        sc['illustrationPromptAr']=f'مشهد قصصي أصلي للفئة {story["ageGroup"]} في {setting[0]} حول {obj[0]}، شخصيات خيالية أصلية، بلا شعارات ولا شخصيات تاريخية أو مقدسة.'
        sc['illustrationPromptEn']=sc.get('illustrationPrompt','')
        sc['illustrationPromptFr']=f'Scène narrative originale pour les {story["ageGroup"]} ans à {setting[2]} autour de {obj[2]}, personnages fictifs originaux, sans logo ni personnage historique ou sacré.'

    story['searchTextAr']=' '.join([story['titleAr'],story['synopsisAr'],story['categoryAr']] + story.get('secondaryTags',[]))
    story['searchTextEn']=' '.join([story['titleEn'],story['synopsisEn'],story['categoryEn']] + story.get('secondaryTags',[]))
    story['searchTextFr']=' '.join([story['titleFr'],story['synopsisFr'],story['categoryFr']] + story.get('secondaryTags',[]))
    return story
