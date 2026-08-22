#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

# Natural-language components are combined by mixed-radix indexing. The first
# 600 story IDs therefore receive a unique three-part episode fingerprint.
DESCRIPTORS=[
('الكهرماني','amber','ambré'),('اللازوردي','azure','azur'),('المرجاني','coral','corail'),('الفضي','silver','argenté'),('الزيتي','olive','olive'),('النحاسي','copper','cuivré'),('اللؤلؤي','pearl','nacré'),('الرملي','sand','sable'),('النعناعي','mint','menthe'),('البنفسجي','violet','violet'),('الذهبي','golden','doré'),('الفيروزي','turquoise','turquoise'),('القرمزي','crimson','cramoisi'),('العسلي','honey','miel'),('الرمادي','slate','ardoise'),('الخوخي','peach','pêche'),('النيلي','indigo','indigo')]
MARKERS=[
('المثلث الورقي','paper triangle','triangle de papier'),('الشريط المخطط','striped ribbon','ruban rayé'),('المشبك الخشبي','wooden clip','pince en bois'),('الحجر الأملس','smooth stone','galet lisse'),('القرص المثقب','perforated disc','disque perforé'),('البطاقة المطوية','folded card','carte pliée'),('الخيط المعقود','knotted cord','corde nouée'),('المكعب الصغير','small cube','petit cube'),('السهم القابل للمسح','erasable arrow','flèche effaçable'),('الحلقة القماشية','fabric loop','boucle de tissu'),('النجمة الورقية','paper star','étoile de papier'),('المسطرة القصيرة','short ruler','petite règle'),('الملصق الدائري','round sticker','pastille ronde'),('المغناطيس المسطح','flat magnet','aimant plat'),('الوتد الخفيف','light peg','petit piquet'),('العلامة الحلزونية','spiral marker','repère en spirale'),('القصاصة المسننة','notched tab','languette crantée'),('الزر الكبير','large button','gros bouton'),('الإطار المصغر','miniature frame','petit cadre')]
PLACES=[
('بجوار نافذة المكتبة الشرقية','beside the library east window','près de la fenêtre est de la bibliothèque'),('عند طرف الحديقة المظللة','at the shaded garden edge','au bord ombragé du jardin'),('قرب الرف السفلي في الورشة','near the workshop lower shelf','près de l’étagère basse de l’atelier'),('تحت لوحة المواعيد','under the schedule board','sous le tableau des horaires'),('إلى جانب مقعد الساحة الطويل','beside the long courtyard bench','près du long banc de la cour'),('عند مدخل الممر الهادئ','at the quiet corridor entrance','à l’entrée du couloir calme'),('قرب خزانة الأدوات الزرقاء','near the blue tool cabinet','près de l’armoire bleue à outils'),('بجوار الحوض الحجري الصغير','beside the small stone basin','près du petit bassin de pierre'),('عند زاوية منصة العرض','at the display platform corner','à l’angle de la plateforme d’exposition'),('قرب باب المخزن الداخلي','near the inner storeroom door','près de la porte intérieure du local'),('بجوار شجرة الظل الوسطى','beside the central shade tree','près de l’arbre d’ombre central'),('عند بداية المسار المرصوف','at the start of the paved path','au début du chemin pavé'),('قرب طاولة القياس المستديرة','near the round measuring table','près de la table ronde de mesure'),('بجوار رف الخرائط','beside the map shelf','près de l’étagère des cartes'),('عند نهاية الممر الخشبي','at the end of the wooden walkway','au bout de la passerelle en bois'),('قرب نافذة المختبر الصغيرة','near the small lab window','près de la petite fenêtre du laboratoire'),('بجوار صندوق البذور','beside the seed box','près de la boîte à graines'),('عند درج المسرح الأول','at the first theater step','sur la première marche du théâtre'),('قرب لوحة الطقس','near the weather board','près du panneau météo'),('بجوار محطة الماء','beside the water station','près du point d’eau'),('عند زاوية المكتبة المتنقلة','at the mobile library corner','à l’angle de la bibliothèque mobile'),('قرب بوابة الحديقة','near the garden gate','près de la grille du jardin'),('بجوار منضدة الإصلاح','beside the repair bench','près de l’établi de réparation')]

SCENE_ACTIONS=[
('يعدّان ثلاث خطوات من العلامة قبل أول قياس','they count three steps from the marker before the first measurement','ils comptent trois pas depuis le repère avant la première mesure'),
('يضعان ملاحظة مؤرخة تحت العلامة ثم يعودان إليها بعد التجربة','they place a dated note under the marker and return to it after the trial','ils placent une note datée sous le repère puis y reviennent après l’essai'),
('يقارنان ظل العلامة في لحظتين مختلفتين','they compare the marker shadow at two different moments','ils comparent l’ombre du repère à deux moments différents'),
('يطلبان من صديق تحديد العلامة من وصف شفهي فقط','they ask a friend to locate the marker from a spoken description alone','ils demandent à un ami de retrouver le repère à partir d’une description orale seulement'),
('يرسمان خطًا قصيرًا من العلامة إلى نقطة القرار','they draw a short line from the marker to the decision point','ils tracent une courte ligne du repère jusqu’au point de décision'),
('يختبران إن كانت العلامة مرئية لشخص أقصر قامة','they test whether the marker is visible to a shorter person','ils vérifient si le repère reste visible pour une personne plus petite'),
('ينقلان القياس إلى بطاقة ثانية ثم يتحققان من التطابق','they copy the measurement to a second card and verify the match','ils reportent la mesure sur une seconde carte puis vérifient la concordance'),
('يسجلان ما تغير حول العلامة وما بقي ثابتًا','they record what changed around the marker and what remained stable','ils notent ce qui a changé autour du repère et ce qui est resté stable'),
('يتركان العلامة في مكانها أثناء اختبار حل بديل','they leave the marker in place while testing an alternative solution','ils laissent le repère en place pendant l’essai d’une solution alternative'),
('يستخدمان العلامة كنقطة تسليم واضحة للفريق التالي','they use the marker as a clear handoff point for the next team','ils utilisent le repère comme point de transmission clair pour l’équipe suivante')]


def fingerprint(i:int):
    j=i-1
    a=j%len(DESCRIPTORS)
    b=(j//len(DESCRIPTORS))%len(MARKERS)
    c=(j//(len(DESCRIPTORS)*len(MARKERS)))%len(PLACES)
    return DESCRIPTORS[a],MARKERS[b],PLACES[c]


def apply(story:dict,i:int)->dict:
    d,m,p=fingerprint(i)
    story['episodeFingerprint']={'descriptor':{'ar':d[0],'en':d[1],'fr':d[2]},'marker':{'ar':m[0],'en':m[1],'fr':m[2]},'place':{'ar':p[0],'en':p[1],'fr':p[2]}}
    for n in range(10):
        a=SCENE_ACTIONS[(n+i)%len(SCENE_ACTIONS)]
        ar=(f'لهذه القصة علامة مرجعية خاصة: {m[0]} {d[0]} {p[0]}. '
            f'{a[0]}. يربطان النتيجة بهذه النقطة تحديدًا، ثم يكتبان ملاحظة تصف ما شاهداه من دون تعميم. '
            f'وعند المقارنة التالية يعودان إلى {m[0]} {d[0]} لا إلى الذاكرة، فيظهر الفرق بين الملاحظة الجديدة والسابقة بوضوح. '
            f'قبل ختام المشهد يتحققان من أن موضع {m[0]} {p[0]} ما زال مفهومًا لمن لم يشاهد بداية العمل.')
        en=(f'This episode has its own reference point: the {d[1]} {m[1]} {p[1]}. '
            f'{a[1].capitalize()}. They tie the result to that exact point and write an observation that says only what they actually saw. '
            f'For the next comparison they return to the {d[1]} {m[1]}, not to memory, making the difference between the new and earlier observation visible. '
            f'Before the scene closes, they verify that the position of the {d[1]} {m[1]} {p[1]} is understandable to someone who missed the beginning.')
        fr=(f'Cet épisode possède son propre point de référence : {m[2]} {d[2]} {p[2]}. '
            f'{a[2].capitalize()}. Ils rattachent le résultat à ce point précis et rédigent une observation limitée à ce qu’ils ont réellement constaté. '
            f'Pour la comparaison suivante, ils reviennent à {m[2]} {d[2]}, et non à leur mémoire, ce qui rend visible l’écart entre la nouvelle observation et la précédente. '
            f'Avant la fin de la scène, ils vérifient que la position de {m[2]} {d[2]} {p[2]} reste compréhensible pour une personne absente au début.')
        story['storyAr'][n]['text']=ar+' '+story['storyAr'][n]['text']
        story['storyEn'][n]['text']=en+' '+story['storyEn'][n]['text']
        story['storyFr'][n]['text']=fr+' '+story['storyFr'][n]['text']
        sc=story['scenes'][n]
        sc['narration']=story['storyAr'][n]['text']
        sc['narrationEn']=story['storyEn'][n]['text']
        sc['narrationFr']=story['storyFr'][n]['text']
        sc['episodeFingerprint']=story['episodeFingerprint']
    wc_en=sum(len(x['text'].split()) for x in story['storyEn'])
    story['estimatedReadingMinutes']=max(3,round(wc_en/180))
    story['estimatedAnimationMinutes']=max(4,round(wc_en/150,1))
    return story
