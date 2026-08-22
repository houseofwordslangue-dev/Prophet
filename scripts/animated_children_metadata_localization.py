#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

TAG_AR={
'friendship':'الصداقة','family':'الأسرة','school':'المدرسة','exploration':'الاستكشاف','science':'العلوم','technology':'التقنية','environment':'البيئة','creativity':'الإبداع','problem-solving':'حل المشكلات','leadership':'القيادة','teamwork':'العمل الجماعي','communication':'التواصل','self-confidence':'الثقة بالنفس','empathy':'التعاطف','resilience':'المرونة','adventure':'المغامرة','mystery':'الغموض','imagination':'الخيال','community':'المجتمع'
}
TAG_FR={
'friendship':'amitié','family':'famille','school':'école','exploration':'exploration','science':'sciences','technology':'technologie','environment':'environnement','creativity':'créativité','problem-solving':'résolution de problèmes','leadership':'leadership','teamwork':'travail d’équipe','communication':'communication','self-confidence':'confiance en soi','empathy':'empathie','resilience':'résilience','adventure':'aventure','mystery':'mystère','imagination':'imagination','community':'communauté'
}


def apply(story:dict)->dict:
    tags=story.get('secondaryTags') or []
    story['secondaryTagsEn']=list(tags)
    story['secondaryTagsAr']=[TAG_AR.get(x,x) for x in tags]
    story['secondaryTagsFr']=[TAG_FR.get(x,x) for x in tags]
    story['searchTextAr']=' '.join([story.get('titleAr',''),story.get('synopsisAr',''),story.get('categoryAr','')] + story['secondaryTagsAr'])
    story['searchTextEn']=' '.join([story.get('titleEn',''),story.get('synopsisEn',''),story.get('categoryEn','')] + story['secondaryTagsEn'])
    story['searchTextFr']=' '.join([story.get('titleFr',''),story.get('synopsisFr',''),story.get('categoryFr','')] + story['secondaryTagsFr'])
    insp=story.get('inspirationBasis') or {}
    if insp:
        insp['editorialRuleAr']='تحويل النمط القيمي والحدثي إلى موقف خيالي أصلي من غير الإيحاء بأن الحبكة الخيالية حدثت تاريخيًا.'
        insp['editorialRuleEn']='Transform the moral and event pattern into an original fictional situation without implying that the fictional plot happened historically.'
        insp['editorialRuleFr']='Transformer le motif moral et événementiel en une situation fictive originale sans laisser entendre que cette intrigue s’est produite historiquement.'
    return story
