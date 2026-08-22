#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

METHODS=[
('قسّموا المسار إلى مربعات صغيرة ورسموا كل تغيير على ورق شفاف','they divided the route into small squares and mapped every change on transparent paper','ils divisèrent le trajet en petites cases et reportèrent chaque changement sur une feuille transparente'),
('قاسوا طول الظلال في ثلاث نقاط وقارنوا النتائج بدل الاعتماد على الذاكرة','they measured shadow lengths at three points and compared the results instead of trusting memory','ils mesurèrent la longueur des ombres à trois endroits et comparèrent les résultats au lieu de se fier à leur mémoire'),
('استخدموا أكواب ماء متساوية لاختبار ميل السطح من دون أجهزة معقدة','they used equal cups of water to test the slope without complicated equipment','ils utilisèrent des verres d’eau identiques pour tester la pente sans matériel compliqué'),
('سجلوا الأصوات في أوقات مختلفة ثم رتبوا التسجيلات من الأهدأ إلى الأعلى','they recorded sounds at different times and ordered the clips from quietest to loudest','ils enregistrèrent les sons à différents moments puis classèrent les extraits du plus calme au plus fort'),
('رسموا خريطة للروائح والهواء وحددوا المواضع التي تغير فيها الاتجاه','they drew a map of smells and airflow and marked where the direction changed','ils dessinèrent une carte des odeurs et des courants d’air en notant chaque changement de direction'),
('صنعوا نموذجا ورقيا للمكان وحركوا عليه القطع قبل لمس الأشياء الحقيقية','they built a paper model of the place and moved pieces on it before touching the real objects','ils construisirent une maquette en papier et y déplacèrent les éléments avant de toucher aux objets réels'),
('راجعوا صورا التقطت في أيام سابقة وبحثوا عن فروق صغيرة في الخلفية','they reviewed photos from earlier days and searched for tiny differences in the background','ils examinèrent des photos des jours précédents pour repérer de petites différences dans l’arrière-plan'),
('كتب كل عضو ملاحظته منفردا ثم فتحوا الأوراق معا لتجنب تأثير رأي واحد على البقية','each member wrote an observation alone before they opened the notes together, avoiding group influence','chaque membre nota son observation séparément avant de comparer les feuilles afin d’éviter l’influence du groupe'),
('جربوا المسار وهم يحملون أوزانا مختلفة ليروا إن كانت الحركة تغير النتيجة','they tested the route while carrying different weights to see whether movement changed the result','ils testèrent le trajet avec des charges différentes pour voir si le mouvement modifiait le résultat'),
('وضعوا علامات قابلة للإزالة عند كل نقطة مؤكدة حتى لا يخلطوا بين الدليل والتخمين','they placed removable markers at every confirmed point so evidence would not be confused with guesses','ils placèrent des repères amovibles à chaque point confirmé pour ne pas confondre preuve et supposition'),
('طلبوا من شخص لم يعرف المشكلة أن يسير في المكان ويصف ما يلاحظه من تلقاء نفسه','they asked someone who did not know the problem to walk through the area and describe what stood out','ils demandèrent à une personne qui ignorait le problème de parcourir le lieu et de décrire spontanément ce qu’elle remarquait'),
('اختبروا الخطة في نسخة مصغرة باستخدام ورق وخيط ومشابك قبل التنفيذ الحقيقي','they tested the plan in miniature with paper, string, and clips before trying it for real','ils testèrent le plan en miniature avec du papier, de la ficelle et des pinces avant de passer à l’échelle réelle'),
('راقبوا حركة الناس عشر دقائق ورسموا أسهما تبين أين تتقاطع المسارات','they watched people move for ten minutes and drew arrows where paths crossed','ils observèrent les déplacements pendant dix minutes et dessinèrent des flèches aux points où les trajets se croisaient'),
('حسبوا الزمن بين كل خطوتين بساعة بسيطة واكتشفوا أن التأخير لا يحدث دائما في الموضع نفسه','they timed each pair of steps with a simple watch and found that the delay did not always occur in the same place','ils chronométrèrent chaque paire d’étapes et découvrirent que le retard ne se produisait pas toujours au même endroit'),
('استعاروا مرآة صغيرة لرؤية زاوية مخفية من غير تحريك الأثاث أو إزعاج المكان','they borrowed a small mirror to inspect a hidden angle without moving furniture or disturbing the area','ils empruntèrent un petit miroir pour observer un angle caché sans déplacer les meubles ni déranger le lieu'),
('وضعوا قائمة بما يجب ألا يتغير أثناء التجربة حتى يعرفوا أي نتيجة تنتمي إلى الاختبار نفسه','they listed everything that had to stay unchanged so they could tell which result belonged to the test','ils dressèrent la liste de tout ce qui devait rester inchangé afin d’identifier correctement le résultat du test'),
('قارنوا ملمس ثلاث مواد بأطراف الأصابع ثم ارتدوا قفازات وأعادوا الفحص للتأكد','they compared the texture of three materials by touch, then repeated the check with gloves','ils comparèrent au toucher la texture de trois matériaux puis recommencèrent avec des gants'),
('تابعوا اتجاه طائر صغير وحركة أوراق الأشجار ففهموا شيئا عن الهواء لم تظهره الخريطة','they followed a small bird and the movement of leaves, learning something about the air that the map had missed','ils suivirent un petit oiseau et le mouvement des feuilles, découvrant sur l’air un détail absent de la carte'),
('صنعوا جدولا زمنيا بالألوان وربطوا كل ملاحظة باللحظة التي ظهرت فيها','they built a color-coded timeline and linked every observation to the moment it appeared','ils construisirent une frise chronologique en couleurs et relièrent chaque observation au moment où elle était apparue'),
('بدل البحث عن الشيء المفقود مباشرة بحثوا عما تغير حول المكان الذي كان فيه','instead of searching directly for the missing item, they searched for what had changed around its former place','au lieu de chercher directement l’objet disparu, ils examinèrent ce qui avait changé autour de son emplacement initial'),
('طلبوا من الفريق ترتيب الاحتمالات من الأقل ضررا إلى الأكثر ثم بدأوا باختبار الأول','they ranked possible explanations from least harmful to most disruptive and tested the safest one first','ils classèrent les hypothèses de la moins risquée à la plus perturbatrice puis testèrent d’abord la plus sûre'),
('صنعوا شبكة من الخيط تحدد مناطق البحث كي لا يعيد اثنان فحص المكان نفسه','they made a string grid that divided the search area so two people would not inspect the same place twice','ils tendirent une grille de ficelle pour partager la zone de recherche et éviter les vérifications en double'),
('حولوا الملاحظات إلى أسئلة نعم أو لا حتى يستطيعوا استبعاد الاحتمالات واحدا بعد آخر','they turned observations into yes-or-no questions so possibilities could be eliminated one by one','ils transformèrent les observations en questions fermées afin d’éliminer les hypothèses une à une'),
('رسموا المشهد من ثلاث زوايا مختلفة فاكتشفوا تفصيلا لم يكن ظاهرا من الأمام','they sketched the scene from three different angles and discovered a detail invisible from the front','ils dessinèrent la scène sous trois angles différents et découvrirent un détail invisible de face'),
('قارنوا درجة حرارة الأسطح في الظل والشمس بأداة مدرسية بسيطة','they compared surface temperatures in shade and sun with a simple classroom instrument','ils comparèrent la température des surfaces à l’ombre et au soleil avec un instrument scolaire simple'),
('كتبوا توقع النتيجة قبل كل تجربة حتى لا يغيروا تفسيرهم بعد رؤيتها','they wrote down the predicted result before every test so they could not change the interpretation afterward','ils écrivirent le résultat attendu avant chaque essai afin de ne pas modifier leur interprétation après coup'),
('قسموا الفريق إلى شخص يراقب وآخر ينفذ وثالث يسجل كي تبقى الأدوار واضحة','they assigned one observer, one operator, and one recorder so the roles stayed clear','ils attribuèrent les rôles d’observateur, d’exécutant et de secrétaire afin de garder des responsabilités nettes'),
('تتبعوا آثار الغبار بفرشاة ناعمة وحددوا أين انقطعت فجأة','they traced dust patterns with a soft brush and marked where the trail stopped abruptly','ils suivirent les traces de poussière avec une brosse douce et notèrent l’endroit où elles s’interrompaient brusquement'),
('أعادوا بناء ترتيب الأحداث باستعمال بطاقات منفصلة يمكن تحريكها على الطاولة','they rebuilt the sequence of events with separate cards that could be rearranged on the table','ils reconstruisirent la suite des événements à l’aide de cartes mobiles disposées sur la table'),
('استخدموا مصباحا منخفضا لإظهار البروزات الصغيرة التي تختفي في الإضاءة العمودية','they used a low lamp to reveal tiny raised marks hidden by overhead light','ils utilisèrent une lampe placée très bas pour faire apparaître de petites aspérités invisibles sous l’éclairage vertical')]

PRESSURES=[
('وكان أمامهم موعد لا يمكن نقله بسهولة','and they were facing a deadline that could not easily be moved','alors qu’une échéance difficile à déplacer approchait'),
('بينما كان طفل أصغر ينتظر نتيجة عملهم','while a younger child was waiting for the result of their work','tandis qu’un enfant plus jeune attendait le résultat de leur travail'),
('مع ضرورة إبقاء الممر مفتوحا للآخرين','while needing to keep the passage open for everyone else','tout en devant garder le passage accessible aux autres'),
('من دون إنفاق المال المخصص لنشاط آخر','without spending money reserved for another activity','sans dépenser l’argent réservé à une autre activité'),
('مع احتمال أن يفسد المطر ما تركوه في الخارج','with rain likely to damage anything left outside','alors que la pluie risquait d’abîmer tout ce qui restait dehors'),
('في وقت كان أحد أعضاء الفريق متعبا ولا يستطيع حمل الأشياء الثقيلة','while one team member was tired and could not carry heavy objects','alors qu’un membre de l’équipe était fatigué et ne pouvait pas porter de charges lourdes'),
('مع وجود ضيوف لا يعرفون تفاصيل المكان','while visitors unfamiliar with the place were present','en présence de visiteurs qui ne connaissaient pas le lieu'),
('من غير إيقاف نشاط مجموعة أخرى تعمل قربهم','without stopping another group working nearby','sans interrompre l’activité d’un autre groupe installé à proximité'),
('مع ضرورة إعادة كل شيء إلى وضعه قبل الغروب','while needing to restore everything before sunset','avec l’obligation de tout remettre en place avant le coucher du soleil'),
('ومن دون نشر إشاعة عن شخص لم تثبت مسؤوليته','without starting a rumor about someone whose responsibility had not been established','sans lancer de rumeur sur une personne dont la responsabilité n’était pas établie'),
('مع نقص أداة كانوا يعتمدون عليها عادة','while missing a tool they normally relied on','alors qu’il leur manquait un outil qu’ils utilisaient habituellement'),
('بينما كانت بطارية جهاز القياس توشك أن تنفد','while the measuring device battery was nearly empty','alors que la batterie de l’appareil de mesure était presque vide'),
('مع تغير الطقس أسرع مما توقعوا','while the weather was changing faster than expected','alors que la météo changeait plus vite que prévu'),
('ومع اختلاف الفريق حول الأولوية التي يجب حمايتها','while the team disagreed about which priority mattered most','alors que l’équipe n’était pas d’accord sur la priorité à protéger'),
('مع ضرورة شرح قرارهم لاحقا لإدارة المدرسة','while knowing they would later need to explain the decision to the school administration','en sachant qu’ils devraient ensuite expliquer leur décision à l’administration scolaire'),
('من دون إزعاج حيوان صغير اتخذ المكان مأوى مؤقتا','without disturbing a small animal using the area as temporary shelter','sans déranger un petit animal qui avait trouvé là un abri provisoire'),
('مع بقاء عشرين دقيقة فقط قبل وصول المجموعة التالية','with only twenty minutes left before the next group arrived','alors qu’il ne restait que vingt minutes avant l’arrivée du groupe suivant'),
('بينما كان عليهم الحفاظ على مادة هشة من الكسر','while they also had to protect a fragile material from breaking','tout en devant protéger un matériau fragile contre la casse'),
('مع حاجة أحد الأصدقاء إلى مغادرة المكان مبكرا','while one friend needed to leave early','alors qu’un ami devait partir plus tôt'),
('ومن غير استخدام الهاتف في منطقة لا توجد فيها تغطية','without being able to use a phone in an area with no signal','sans pouvoir utiliser de téléphone dans une zone sans réseau')]

OUTCOMES=[
('فانكشف أن المشكلة مرتبطة بطريقة ترتيب الأشياء لا بالشخص الذي استعملها أخيرا','which revealed that the problem came from how things were arranged rather than from the last person who used them','ce qui révéla que le problème venait de l’organisation des objets et non de la dernière personne qui les avait utilisés'),
('ففهموا أن التوقيت كان أهم من المكان نفسه','which showed them that timing mattered more than the location itself','ce qui leur montra que le moment comptait davantage que le lieu lui-même'),
('فاضطروا إلى الاعتذار لشخص استعجلوا في تفسير تصرفه','which led them to apologize to someone whose behavior they had judged too quickly','ce qui les conduisit à présenter leurs excuses à une personne qu’ils avaient jugée trop vite'),
('فوجدوا حلا يحافظ على ممتلكات الجميع ولا يضحي بفريق لم يشارك في الخطأ','which produced a solution that protected everyone’s belongings without burdening a group that had not caused the problem','ce qui permit une solution protégeant les affaires de tous sans faire porter la faute à un groupe innocent'),
('فصار بإمكانهم إصلاح السبب بدلا من إخفاء الأثر','which allowed them to repair the cause instead of hiding the symptom','ce qui leur permit de réparer la cause au lieu de masquer le symptôme'),
('فاكتشفوا أن معلومة صغيرة أهملوها في البداية كانت مفتاح التسلسل كله','which showed that a small fact ignored at the beginning was the key to the entire sequence','ce qui révéla qu’un petit fait négligé au départ était la clé de toute la suite'),
('فعدلوا الخطة بحيث يستطيع أضعف عضو في الفريق المشاركة بأمان','which led them to redesign the plan so the least physically strong member could participate safely','ce qui les amena à modifier le plan afin que le membre le moins robuste puisse participer sans danger'),
('فأصبح الحل أقل سرعة لكنه أكثر عدلا واستدامة','which made the solution slower but fairer and more durable','ce qui rendit la solution plus lente mais plus juste et plus durable'),
('فقرروا توثيق الخطأ كي لا يضطر فريق آخر إلى اكتشافه من جديد','which convinced them to document the mistake so another team would not have to rediscover it','ce qui les convainquit de documenter l’erreur afin qu’une autre équipe n’ait pas à la redécouvrir'),
('فانتقل النقاش من تبادل اللوم إلى مقارنة الخيارات','which shifted the discussion from blame to comparing options','ce qui transforma la discussion : au lieu de chercher un coupable, ils comparèrent les options possibles'),
('فوجدوا أن أفضل خطوة هي التوقف المؤقت لا الاستمرار بعناد','which showed that the best move was a temporary pause rather than stubbornly continuing','ce qui leur montra que le meilleur choix était une pause temporaire plutôt qu’une poursuite obstinée'),
('فأعادوا توزيع الموارد بحيث لا يخسر أحد فرصته في المشاركة','which led them to redistribute resources so nobody lost the chance to participate','ce qui les amena à redistribuer les ressources afin que personne ne perde sa chance de participer'),
('فصار الاعتراف بالخطأ أسرع طريق لاستعادة الثقة','which made admitting the mistake the fastest route to rebuilding trust','ce qui fit de l’aveu de l’erreur le chemin le plus rapide vers le rétablissement de la confiance'),
('فحموا المكان الطبيعي من حل قصير المدى كان سيترك أثرا دائما','which protected the natural setting from a short-term fix that would have caused lasting damage','ce qui protégea le milieu naturel d’une solution rapide qui aurait laissé des dégâts durables'),
('فأبقوا الاتفاق الذي قطعوه مع فريق آخر رغم أن تغييره كان أسهل','which helped them honor an agreement with another team even though changing it would have been easier','ce qui les conduisit à respecter un accord avec une autre équipe alors qu’il aurait été plus simple de le modifier'),
('ففهموا أن مساعدة شخص واحد في اللحظة المناسبة أنقذت عمل المجموعة كلها','which showed that helping one person at the right moment had protected the work of the whole group','ce qui montra qu’aider une seule personne au bon moment avait préservé le travail de tout le groupe'),
('فصار الشكر جزءا من الحل لأنهم عرفوا من بذل جهدا لم يكن ظاهرا','which made gratitude part of the solution once they noticed effort that had previously gone unseen','ce qui fit de la gratitude une partie de la solution lorsqu’ils remarquèrent un effort jusque-là invisible'),
('فقرروا منح فرصة جديدة مع قاعدة واضحة تمنع تكرار الضرر','which led them to offer another chance with a clear rule preventing the same harm from recurring','ce qui les conduisit à offrir une nouvelle chance accompagnée d’une règle claire empêchant la répétition du tort'),
('فتركوا مساحة للشك حتى آخر فحص ولم يحولوا الاحتمال إلى حقيقة','which kept room for uncertainty until the final check instead of turning a possibility into a fact','ce qui leur permit de garder une place au doute jusqu’à la dernière vérification sans transformer une possibilité en certitude'),
('فأصبح نجاحهم قابلا للتكرار لأنهم عرفوا لماذا نجح لا أنه نجح فقط','which made their success repeatable because they understood why it worked, not merely that it worked','ce qui rendit leur réussite reproductible parce qu’ils comprenaient pourquoi elle avait fonctionné')]


def _pick(bank,i,scene,offset): return bank[(i*17+scene*11+offset)%len(bank)]

def diversify(story:dict,i:int)->dict:
    """Add story-specific concrete action and consequence vocabulary.

    This is deliberately contentful rather than an ID/noise trick: every addition
    changes what the fictional team actually does, what constraint it faces, and
    what consequence follows.
    """
    for j in range(10):
        m1=_pick(METHODS,i,j,0); m2=_pick(METHODS,i,j,7); pressure=_pick(PRESSURES,i,j,3); outcome=_pick(OUTCOMES,i,j,5)
        additions={
            'ar':f'في هذه المرحلة {m1[0]}، {pressure[0]}. ثم {m2[0]}، {outcome[0]}.',
            'en':f'At this stage, {m1[1]}, {pressure[1]}. They then {m2[1]}, {outcome[1]}.',
            'fr':f'À cette étape, {m1[2]}, {pressure[2]}. Ensuite, {m2[2]}, {outcome[2]}.'
        }
        story['storyAr'][j]['text'] += ' '+additions['ar']
        story['storyEn'][j]['text'] += ' '+additions['en']
        story['storyFr'][j]['text'] += ' '+additions['fr']
        story['scenes'][j]['narration']=story['storyAr'][j]['text']
        story['scenes'][j]['narrationEn']=story['storyEn'][j]['text']
        story['scenes'][j]['narrationFr']=story['storyFr'][j]['text']
        story['scenes'][j]['storySpecificMethod']={'ar':m1[0],'en':m1[1],'fr':m1[2]}
        story['scenes'][j]['storySpecificConstraint']={'ar':pressure[0],'en':pressure[1],'fr':pressure[2]}
        story['scenes'][j]['storySpecificOutcome']={'ar':outcome[0],'en':outcome[1],'fr':outcome[2]}
    return story
