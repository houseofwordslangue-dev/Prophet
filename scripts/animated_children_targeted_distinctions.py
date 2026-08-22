#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

AR=[
'إلى جانب المهمة الأساسية، قرر الفريق إعداد بطاقات مصورة لفريق جديد سيستخدم المكان غدا من دون أن يعرف ترتيبه.',
'عندما ظهرت المشكلة لاحظوا أن التعليمات القديمة تفترض معرفة مسبقة بالمكان، فصار وضوحها جزءا من الحل لا عملا إضافيا.',
'اختبروا أول بطاقة مع شخص لم يزر الموقع من قبل، فاكتشفوا أن سهما واحدا كان يشير إلى الاتجاه الخطأ.',
'بعد المحاولة الفاشلة لم يمزقوا البطاقات؛ وضعوا علامة على موضع الالتباس وكتبوا سببه بجانب الرسم.',
'أعادوا تصوير المسار من مستوى عين طفل أصغر، فظهرت حواجز لم ينتبه إليها الكبار أثناء سيرهم المعتاد.',
'خلال الخلاف دافع أحدهم عن اختصار التعليمات، لكن الفريق قرر أن السرعة لا تبرر ترك القادم الجديد في حيرة.',
'اختاروا رموزا بسيطة يمكن فهمها حتى قبل قراءة الكلمات، ثم طلبوا من شخصين تفسيرها من دون شرح مسبق.',
'أثناء التنفيذ ثبتوا البطاقات مؤقتا وجربوا السير وفقها فقط، من غير الاعتماد على الذاكرة أو مساعدة أعضاء الفريق.',
'في مرحلة الإصلاح صححوا موضعين وأضافوا تنبيها يحمي الأدوات الهشة من الاستخدام الخاطئ.',
'قبل المغادرة تركوا نسخة مرتبة من البطاقات وسجلوا ما تعلموه عن كتابة تعليمات عادلة لمن يأتي بعدهم.'
]
EN=[
'Alongside the main task, the team decided to prepare illustrated guide cards for a new group that would use the place the next day without knowing its layout.',
'When the problem appeared, they noticed that the old instructions assumed prior knowledge, so clarity became part of the solution rather than an optional extra.',
'They tested the first card with someone who had never visited the site and discovered that one arrow pointed in the wrong direction.',
'After the failed attempt, they did not discard the cards; they marked the exact point of confusion and wrote the reason beside the drawing.',
'They photographed the route again from the eye level of a younger child and found obstacles adults had stopped noticing.',
'During the disagreement, someone argued for shorter instructions, but the team decided that speed did not justify leaving a newcomer confused.',
'They chose simple symbols that could be understood before the words were read and asked two people to interpret them without hints.',
'During implementation, the cards were mounted temporarily and the route was tested using only the guides, with no memory cues from the original team.',
'While repairing the final details, they corrected two positions and added a warning that protected fragile equipment from misuse.',
'Before leaving, they placed the cards in order and recorded what they had learned about writing fair instructions for the people who would come after them.'
]
FR=[
'En plus de la mission principale, l’équipe décida de préparer des cartes illustrées pour un nouveau groupe qui utiliserait le lieu le lendemain sans en connaître l’organisation.',
'Lorsque le problème apparut, ils constatèrent que les anciennes consignes supposaient une connaissance préalable du lieu; la clarté devint donc une partie du véritable problème.',
'Ils testèrent la première carte avec une personne qui n’était jamais venue et découvrirent qu’une flèche indiquait la mauvaise direction.',
'Après l’échec, ils ne jetèrent pas les cartes : ils marquèrent précisément le point de confusion et écrivirent sa cause près du dessin.',
'Ils reprirent des photos du trajet à la hauteur des yeux d’un enfant plus jeune et virent des obstacles que les adultes ne remarquaient plus.',
'Pendant le désaccord, quelqu’un proposa de raccourcir fortement les consignes, mais l’équipe refusa de gagner du temps en laissant un nouvel arrivant dans l’incertitude.',
'Ils choisirent des symboles simples compréhensibles avant même la lecture des mots et demandèrent à deux personnes de les interpréter sans explication préalable.',
'Pendant la mise en œuvre, ils fixèrent les cartes provisoirement et parcoururent le trajet en utilisant uniquement ces indications, sans aide de la mémoire de l’équipe initiale.',
'Au moment des corrections finales, ils déplacèrent deux cartes et ajoutèrent un avertissement protégeant le matériel fragile contre une mauvaise manipulation.',
'Avant de partir, ils laissèrent les cartes dans l’ordre et notèrent ce qu’ils avaient appris sur la manière d’écrire des consignes équitables pour ceux qui viendraient ensuite.'
]

def apply(story:dict,i:int)->dict:
    if i!=72:
        return story
    story['distinctiveSecondaryArc']='accessible-guidance-for-next-team'
    for j in range(10):
        story['storyAr'][j]['text'] += ' '+AR[j]
        story['storyEn'][j]['text'] += ' '+EN[j]
        story['storyFr'][j]['text'] += ' '+FR[j]
        story['scenes'][j]['narration']=story['storyAr'][j]['text']
        story['scenes'][j]['narrationEn']=story['storyEn'][j]['text']
        story['scenes'][j]['narrationFr']=story['storyFr'][j]['text']
        story['scenes'][j]['distinctiveArcBeat']={'ar':AR[j],'en':EN[j],'fr':FR[j]}
    return story
