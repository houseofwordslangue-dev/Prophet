#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import generate_animated_children_stories as base
import animated_children_expansion as expansion

METHODS=[
('يرسمون مخططًا زمنيًا على بطاقات منفصلة','they build a timeline on separate cards','ils construisent une chronologie sur des cartes séparées'),
('يقيسون المسافة بخيط معلّم ثم يعيدون القياس من الاتجاه المعاكس','they measure distance with a marked cord and repeat it from the opposite direction','ils mesurent la distance avec une corde graduée puis recommencent dans l’autre sens'),
('يصنعون نموذجًا ورقيًا قبل تحريك أي شيء حقيقي','they build a paper model before moving anything real','ils fabriquent une maquette en papier avant de déplacer quoi que ce soit'),
('يسجلون الأصوات في ثلاث نقاط ثم يقارنون أوقاتها','they record sounds at three points and compare their timing','ils enregistrent les sons en trois points puis comparent leur chronologie'),
('يرسمون مسارات الحركة بالطبشور القابل للمسح','they map movement paths with erasable chalk','ils tracent les déplacements avec une craie effaçable'),
('يفحصون عينتين تحت ضوءين مختلفين','they inspect two samples under two different lights','ils examinent deux échantillons sous deux éclairages différents'),
('يقسمون الموارد إلى حصص تجريبية صغيرة قبل التوزيع الكامل','they divide resources into small trial portions before full distribution','ils divisent les ressources en petites parts d’essai avant la répartition complète'),
('يطلبون من شخص لم يرَ الخطة أن يشرح التعليمات بكلماته','they ask someone who has not seen the plan to explain the instructions in their own words','ils demandent à une personne qui n’a pas vu le plan de reformuler les consignes'),
('يراقبون المكان عشر دقائق من دون التدخل ثم يقارنون الملاحظات','they observe the place for ten minutes without intervening and compare notes','ils observent le lieu pendant dix minutes sans intervenir puis comparent leurs notes'),
('يستخدمون جدولًا من ثلاثة أعمدة: حقيقة، احتمال، سؤال','they use a three-column table: fact, possibility, question','ils utilisent un tableau à trois colonnes : fait, hypothèse, question'),
('يختبرون الحل على مساحة صغيرة قابلة للرجوع عنها','they test the solution in a small reversible area','ils testent la solution sur une petite zone réversible'),
('يصورون ترتيب الأدوات قبل التجربة وبعدها للمقارنة','they photograph the tool layout before and after the trial for comparison','ils photographient la disposition du matériel avant et après l’essai'),
('يضعون مؤشرات ورقية على نقاط التغير بدل الاعتماد على الذاكرة','they place paper markers at change points instead of relying on memory','ils placent des repères en papier aux points de changement au lieu de se fier à la mémoire'),
('يطلبون رأيين مستقلين ثم يبحثون عن الجزء المتفق عليه','they seek two independent opinions and identify the part both support','ils demandent deux avis indépendants puis repèrent leur point commun'),
('يعيدون ترتيب الخطوات من الأقل خطورة إلى الأكثر تأثيرًا','they reorder the steps from lowest risk to highest impact','ils réordonnent les étapes du risque le plus faible à l’effet le plus important'),
('يحسبون ما سيستهلكه كل خيار قبل اختيار أي واحد','they calculate what each option will consume before choosing','ils calculent ce que chaque option consommera avant de choisir'),
('يرسمون خريطة وصول تراعي حركة الجميع لا أسرع شخص فقط','they draw an access map based on everyone’s movement, not only the fastest person','ils dessinent un plan d’accès adapté à tous, pas seulement à la personne la plus rapide'),
('يقارنون نتيجة اليوم بسجل يومين سابقين للبحث عن نمط','they compare today’s result with records from two earlier days to find a pattern','ils comparent le résultat du jour aux relevés de deux jours précédents pour trouver un motif'),
('ينشئون قائمة تحقق قصيرة يوقع عليها شخصان قبل الانتقال','they create a short checklist that two people confirm before moving on','ils créent une courte liste de contrôle validée par deux personnes avant de poursuivre'),
('يتركون دقيقة صمت بعد كل اقتراح حتى يكتب الجميع اعتراضًا أو دعمًا','they leave one quiet minute after each proposal so everyone can write an objection or support','ils gardent une minute de silence après chaque proposition afin que chacun note une objection ou un soutien'),
('يفصلون ما يمكن إصلاحه فورًا عما يحتاج إلى متابعة غدًا','they separate what can be repaired now from what needs follow-up tomorrow','ils distinguent ce qui peut être réparé immédiatement de ce qui demande un suivi le lendemain'),
('يجرون اختبارًا أعمى بحيث لا يعرف المقارن أي خيار صممه صديقه','they run a blind comparison so the reviewer does not know which option a friend designed','ils réalisent une comparaison à l’aveugle afin que l’évaluateur ignore quelle option a été conçue par son ami'),
('يضعون ميزانية زمنية لكل خطوة ويتركون هامشًا للطوارئ','they assign a time budget to each step and leave an emergency margin','ils attribuent un budget de temps à chaque étape et gardent une marge pour l’imprévu'),
('يختبرون وضوح اللافتات من مسافات وزوايا مختلفة','they test the clarity of signs from different distances and angles','ils testent la lisibilité des panneaux depuis plusieurs distances et angles'),
('يستخدمون وزنًا بسيطًا لمقارنة كمية المواد قبل وبعد العمل','they use a simple scale to compare material amounts before and after the work','ils utilisent une balance simple pour comparer les quantités de matériel avant et après le travail')
]

CONSTRAINTS=[
('من دون تعطيل مجموعة أصغر تعمل بجوارهم','without interrupting a younger group working nearby','sans interrompre un groupe plus jeune qui travaille à proximité'),
('مع إبقاء الممر الرئيسي مفتوحًا طوال الوقت','while keeping the main passage open at all times','tout en gardant le passage principal ouvert en permanence'),
('من دون استهلاك الماء الاحتياطي المخصص للنباتات','without using the reserve water set aside for plants','sans utiliser la réserve d’eau destinée aux plantes'),
('مع إعادة كل أداة مستعارة إلى مكانها قبل الإغلاق','while returning every borrowed tool before closing','en rendant chaque outil emprunté avant la fermeture'),
('من دون نشر اسم الشخص الذي ارتكب الخطأ قبل التحقق','without naming the person who made the mistake before verification','sans nommer la personne qui a commis l’erreur avant vérification'),
('مع إعطاء العضو الأبطأ وقتًا كافيًا للمشاركة','while giving the slowest team member enough time to participate','en laissant au membre le plus lent assez de temps pour participer'),
('من دون تجاوز المساحة المحددة للعمل','without crossing the boundary of the assigned work area','sans dépasser la zone de travail attribuée'),
('مع الحفاظ على هدوء ركن القراءة القريب','while preserving the quiet of the nearby reading corner','en préservant le calme du coin lecture voisin'),
('من دون إتلاف أي أثر يمكن أن يحتاجه فريق آخر للتحقق','without destroying any trace another team may need to verify','sans détruire aucun indice qu’une autre équipe pourrait devoir vérifier'),
('مع شرح كل تغيير لشخص لم يحضر بداية المشروع','while explaining each change to someone who missed the start of the project','en expliquant chaque changement à une personne absente au début du projet'),
('من دون جعل المنافسة سببًا لإخفاء معلومة مفيدة','without letting competition become a reason to hide useful information','sans laisser la compétition devenir une raison de cacher une information utile'),
('مع حماية طيور أو حشرات المكان من الإزعاج','while protecting the birds or insects in the area from disturbance','en protégeant les oiseaux ou les insectes du lieu contre les dérangements'),
('من دون الاعتماد على هاتف واحد قد تنفد بطاريته','without relying on a single phone whose battery could fail','sans dépendre d’un seul téléphone dont la batterie pourrait se vider'),
('مع إبقاء نسخة ورقية من التعليمات لأي شخص لا يستخدم الشاشة','while keeping a paper copy of instructions for anyone not using a screen','en gardant une copie papier des consignes pour toute personne n’utilisant pas d’écran'),
('من دون نقل المشكلة إلى فريق الوردية التالية','without pushing the problem onto the next team','sans reporter le problème sur l’équipe suivante'),
('مع إتاحة فرصة اعتراض قبل القرار النهائي','while allowing an opportunity to object before the final decision','en laissant la possibilité de contester avant la décision finale'),
('من دون استخدام مادة لا يعرفون طريقة التخلص منها بأمان','without using a material they cannot dispose of safely','sans utiliser un matériau dont ils ne savent pas assurer l’élimination'),
('مع توثيق سبب تغيير الخطة لا النتيجة فقط','while documenting why the plan changed, not only the result','en documentant la raison du changement de plan et pas seulement le résultat'),
('من دون إخفاء المحاولة الفاشلة من التقرير النهائي','without hiding the failed attempt from the final report','sans cacher la tentative échouée dans le rapport final'),
('مع مراعاة شخص يحتاج إلى تعليمات أبسط وأبطأ','while accommodating someone who needs simpler, slower instructions','en tenant compte d’une personne qui a besoin de consignes plus simples et plus lentes')
]

OUTCOMES=[
('فيكتشفون أن ترتيب الخطوات هو سبب التعطل لا نقص الأدوات','and discover that the order of steps, not missing tools, caused the delay','et découvrent que l’ordre des étapes, et non le manque d’outils, causait le retard'),
('فيظهر أن القياس الأول كان صحيحًا لكن تفسيره كان متسرعًا','and find that the first measurement was correct but its interpretation was rushed','et constatent que la première mesure était juste mais son interprétation trop hâtive'),
('فتكشف المقارنة أن حلًا أبطأ يحمي وقت الفريق على المدى الطويل','and the comparison shows that a slower option saves team time in the long run','et la comparaison montre qu’une option plus lente fait gagner du temps à long terme'),
('فيتضح أن سوء الفهم بدأ من كلمة واحدة غير واضحة في التعليمات','and learn that the misunderstanding began with one unclear word in the instructions','et découvrent que le malentendu venait d’un seul mot imprécis dans les consignes'),
('فيجدون أن المورد الذي ظنوه ناقصًا كان موزعًا في مكانين مختلفين','and find that the supposedly missing resource had been split between two locations','et découvrent que la ressource supposée manquante était répartie entre deux endroits'),
('فتقودهم الملاحظة إلى شخص يحتاج للمساعدة لا إلى شخص يستحق اللوم','and the clue leads them to someone who needs help rather than someone to blame','et l’indice les conduit vers une personne qui a besoin d’aide plutôt que vers un coupable'),
('فيتغير التصميم ليصبح أسهل استخدامًا لمن سيأتي بعدهم','and the design changes to become easier for the next group to use','et la conception évolue pour devenir plus facile à utiliser par le groupe suivant'),
('فيكتشفون أثرًا بيئيًا صغيرًا لم يكن ظاهرًا في الخطة الأولى','and discover a small environmental effect absent from the original plan','et découvrent un petit impact environnemental absent du plan initial'),
('فيتعلم الفريق أن الاعتذار المبكر وفر وقتًا أكثر من الدفاع عن الخطأ','and the team learns that an early apology saved more time than defending the mistake','et l’équipe apprend qu’une excuse rapide a fait gagner plus de temps que la défense de l’erreur'),
('فتصبح التعليمات الجديدة أقصر لكنها أدق وأكثر عدلًا','and the new instructions become shorter, more precise, and fairer','et les nouvelles consignes deviennent plus courtes, plus précises et plus équitables'),
('فيظهر أن الاختلاف بين شاهدين كان اختلاف زاوية لا اختلاف حقيقة','and they see that two witnesses differed in viewpoint, not in the underlying fact','et ils comprennent que deux témoins différaient par leur point de vue et non par les faits'),
('فتمنع خطوة تحقق واحدة إعادة العمل كله من البداية','and one verification step prevents the entire job from being repeated','et une seule étape de vérification évite de recommencer tout le travail'),
('فيجدون طريقة لمشاركة المورد بدل أن يفوز به فريق واحد','and they find a way to share the resource instead of letting one team take it all','et ils trouvent une manière de partager la ressource au lieu de la réserver à une seule équipe'),
('فيتحول الخلاف إلى اقتراح ثالث يجمع أفضل جزء من فكرتين','and the disagreement produces a third option combining the best parts of two ideas','et le désaccord produit une troisième option réunissant le meilleur de deux idées'),
('فيتبين أن حماية المكان الطبيعي لا تعطل المشروع بل تحسن نتيجته','and they learn that protecting the natural area improves rather than blocks the project','et ils constatent que protéger le milieu naturel améliore le projet au lieu de le ralentir'),
('فيعيدون توزيع المهام لأن الشخص الأكثر خبرة ليس دائمًا الأنسب لكل خطوة','and they redistribute tasks because the most experienced person is not always best for every step','et ils redistribuent les tâches car la personne la plus expérimentée n’est pas toujours la mieux placée pour chaque étape'),
('فيكتشفون أن ترك هامش للطوارئ هو ما أنقذ الموعد النهائي','and discover that the emergency margin is what protects the deadline','et découvrent que la marge prévue pour l’imprévu protège finalement le délai'),
('فيثبت الاختبار أن الحل البسيط أكثر ثباتًا من الحل المثير للإعجاب','and the test proves that the simpler solution is more reliable than the impressive one','et le test prouve que la solution la plus simple est plus fiable que la plus spectaculaire'),
('فيتغير معيار النجاح من السرعة إلى أن يستطيع الجميع استخدام النتيجة','and the definition of success changes from speed to whether everyone can use the result','et le critère de réussite passe de la vitesse à la possibilité pour tous d’utiliser le résultat'),
('فيتركون سجلًا يسمح للفريق التالي بفهم القرار من دون تخمين','and they leave a record that lets the next team understand the decision without guessing','et ils laissent un dossier permettant à l’équipe suivante de comprendre la décision sans deviner')
]

REFLECTIONS=[
('لم تكن القيمة درسًا منفصلًا عن المهمة؛ ظهرت حين اضطروا لاختيار ما يفيد الجميع لا ما يريحهم وحدهم.','The value was not a lesson separate from the mission; it appeared when they chose what served everyone rather than what was easiest for themselves.','La valeur n’était pas une leçon séparée de la mission; elle est apparue lorsqu’ils ont choisi ce qui servait tout le monde plutôt que ce qui les arrangeait eux seuls.'),
('تعلموا أن الدقة لا تعني البطء، بل تعني معرفة متى يجب التوقف قبل قرار لا يمكن الرجوع عنه.','They learned that accuracy does not mean slowness; it means knowing when to pause before a decision that cannot easily be reversed.','Ils ont appris que la précision ne signifie pas la lenteur, mais le fait de savoir quand s’arrêter avant une décision difficile à inverser.'),
('صار النجاح عندهم مرتبطًا بجودة التسليم لمن يأتي بعدهم، لا بصورة الفريق أمام الآخرين.','Success became tied to the quality of what they handed to the next group, not to how impressive they looked.','La réussite a fini par dépendre de la qualité de ce qu’ils transmettaient au groupe suivant, et non de l’image qu’ils donnaient.'),
('اكتشفوا أن الخلاف المفيد يكشف ما لم يره كل شخص بمفرده إذا بقي الاحترام حاضرًا.','They discovered that a respectful disagreement can reveal what no person notices alone.','Ils ont découvert qu’un désaccord respectueux peut révéler ce qu’aucune personne ne remarque seule.'),
('فهموا أن الاعتراف بالمعلومة المزعجة مبكرًا يحمي الثقة ويمنع المشكلة من التضخم.','They understood that admitting uncomfortable information early protects trust and keeps problems from growing.','Ils ont compris qu’admettre tôt une information gênante protège la confiance et empêche le problème de grandir.')
]


def identity_for(i:int):
    if i<=100:
        j=i-1
        return expansion.MISSIONS[j%25], expansion.STAKES[(j//25)%20]
    j=i-101
    return expansion.MISSIONS[j%25], expansion.STAKES[j//25]


def _names(i:int):
    p=(i-1)%25; f=i%25
    return (base.NAMES_AR[p],base.NAMES_EN[p],base.NAMES_FR[p]),(base.NAMES_AR[f],base.NAMES_EN[f],base.NAMES_FR[f])


def apply(story:dict,i:int)->dict:
    mission,stake=identity_for(i)
    protagonist,friend=_names(i)
    story['episodeIdentity']={'mission':{'ar':mission[0],'en':mission[1],'fr':mission[2]},'stake':{'ar':stake[0],'en':stake[1],'fr':stake[2]}}
    value=(story.get('categoryAr','القيمة'),story.get('categoryEn',story.get('category','value')),story.get('categoryFr',story.get('category','valeur')))
    for n in range(10):
        # The indices combine story and scene so adjacent stories do not walk the same sequence.
        method=METHODS[(i*7+n*11)%len(METHODS)]
        constraint=CONSTRAINTS[(i*13+n*7)%len(CONSTRAINTS)]
        outcome=OUTCOMES[(i*17+n*9)%len(OUTCOMES)]
        reflection=REFLECTIONS[(i+n*3)%len(REFLECTIONS)]
        ar=[
            f'في الحلقة الخاصة بـ{mission[0]} {stake[0]}، يحدد {protagonist[0]} و{friend[0]} سؤال المشهد رقم {n+1} قبل أي حركة.',
            f'بدل تكرار الخطة القديمة، {method[0]} {constraint[0]}.',
            f'يسجلان ما تغير وما بقي ثابتًا، ويضعان قيمة {value[0]} كشرط عملي يمكن ملاحظته في القرار.',
            f'عندما تعطي التجربة نتيجة غير متوقعة لا يخفونها؛ يعيدان قراءة الدليل ويغيران خطوة واحدة فقط.',
            f'ترتبط النتيجة مباشرة بمهمة {mission[0]} {outcome[0]}.',
            f'قبل الانتقال يسألان: من سيتأثر بهذا الاختيار إذا لم يكن حاضرًا في النقاش؟ ثم يعدلان الخطة وفق الإجابة.',
            f'{reflection[0]}',
            f'يختم المشهد بتوثيق قرار يمكن لفريق آخر مراجعته، بحيث تبقى مهمة {mission[0]} مفهومة حتى {stake[0]}.'
        ]
        en=[
            f'In this {mission[1]} episode {stake[1]}, {protagonist[1]} and {friend[1]} define the exact question for scene {n+1} before taking action.',
            f'Instead of repeating an earlier plan, {method[1]} {constraint[1]}.',
            f'They record what changed and what stayed stable, treating {value[1]} as a practical condition that must be visible in the decision.',
            f'When the trial produces an unexpected result, they do not hide it; they reread the evidence and alter only one step.',
            f'The result belongs specifically to the {mission[1]} task, {outcome[1]}.',
            f'Before moving on, they ask who could be affected by the choice without being present in the discussion, then adjust the plan to match the answer.',
            f'{reflection[1]}',
            f'The scene ends with a reviewable record so another team can understand the {mission[1]} decision {stake[1]} without guessing.'
        ]
        fr=[
            f'Dans cet épisode consacré à {mission[2]} {stake[2]}, {protagonist[2]} et {friend[2]} définissent la question précise de la scène {n+1} avant d’agir.',
            f'Au lieu de répéter un ancien plan, {method[2]} {constraint[2]}.',
            f'Ils consignent ce qui a changé et ce qui est resté stable, en faisant de {value[2]} une condition pratique visible dans la décision.',
            f'Lorsque l’essai donne un résultat inattendu, ils ne le cachent pas; ils relisent les indices et ne modifient qu’une seule étape.',
            f'Le résultat appartient précisément à la mission {mission[2]} : {outcome[2]}.',
            f'Avant de poursuivre, ils demandent qui pourrait subir ce choix sans participer à la discussion, puis adaptent le plan à la réponse.',
            f'{reflection[2]}',
            f'La scène se termine par un compte rendu vérifiable afin qu’une autre équipe puisse comprendre la décision concernant {mission[2]} {stake[2]} sans deviner.'
        ]
        # Put the story-specific layer first so the dramatic identity is present from the opening,
        # then retain the earlier resource-inspired material as depth rather than as the dominant scaffold.
        story['storyAr'][n]['text']=' '.join(ar)+' '+story['storyAr'][n]['text']
        story['storyEn'][n]['text']=' '.join(en)+' '+story['storyEn'][n]['text']
        story['storyFr'][n]['text']=' '.join(fr)+' '+story['storyFr'][n]['text']
        sc=story['scenes'][n]
        sc['narration']=story['storyAr'][n]['text']; sc['narrationEn']=story['storyEn'][n]['text']; sc['narrationFr']=story['storyFr'][n]['text']
        sc['specificMethod']={'ar':method[0],'en':method[1],'fr':method[2]}
        sc['specificConstraint']={'ar':constraint[0],'en':constraint[1],'fr':constraint[2]}
        sc['specificOutcome']={'ar':outcome[0],'en':outcome[1],'fr':outcome[2]}
    # Recalculate duration estimates from the final localized narrative instead of retaining old estimates.
    wc_en=sum(len(x['text'].split()) for x in story['storyEn'])
    story['estimatedReadingMinutes']=max(3,round(wc_en/180))
    story['estimatedAnimationMinutes']=max(4,round(wc_en/150,1))
    return story
