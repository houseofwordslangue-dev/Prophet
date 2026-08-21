#!/usr/bin/env python3
from __future__ import annotations

# Internal editorial motifs distilled from the site's seerah/resource corpus.
# They guide fictional story architecture only. They are not presented as
# historical retellings, quotations, hadith, or claims about named figures.
MOTIFS={
    'kindness': {
        'ar':'الرفق بالضعيف وخدمة المحتاج قبل طلب المقابل',
        'en':'gentleness toward the vulnerable and helping before asking for reward',
        'fr':'la douceur envers les plus vulnérables et l’aide avant toute récompense',
        'resourceEvent':'care-and-service'
    },
    'honesty': {
        'ar':'الأمانة والصدق حين تكون المصلحة الشخصية في الاتجاه الآخر',
        'en':'trustworthiness and truthfulness when personal convenience points the other way',
        'fr':'la confiance et la vérité lorsque l’intérêt personnel pousse dans l’autre direction',
        'resourceEvent':'trustworthiness'
    },
    'courage': {
        'ar':'الشجاعة المقترنة بالتخطيط والحذر لا بالاندفاع',
        'en':'courage joined to planning and caution rather than impulsiveness',
        'fr':'le courage uni à la préparation et à la prudence plutôt qu’à l’impulsivité',
        'resourceEvent':'careful-journey-planning'
    },
    'patience': {
        'ar':'الصبر أمام الأذى والضغط مع الحفاظ على مقصد رحيم',
        'en':'patience under pressure while preserving a merciful purpose',
        'fr':'la patience sous la pression tout en préservant une intention bienveillante',
        'resourceEvent':'patience-under-harm'
    },
    'curiosity': {
        'ar':'السؤال والملاحظة والتثبت قبل الحكم',
        'en':'asking, observing, and verifying before judging',
        'fr':'questionner, observer et vérifier avant de juger',
        'resourceEvent':'verification-before-judgment'
    },
    'cooperation': {
        'ar':'المؤازرة وتقاسم الموارد والعمل حتى يشعر كل عضو أنه جزء من جماعة واحدة',
        'en':'mutual support, sharing resources, and working as one community',
        'fr':'l’entraide, le partage des ressources et le travail comme une seule communauté',
        'resourceEvent':'mutual-support'
    },
    'responsibility': {
        'ar':'الوفاء بالعهد واحترام الاتفاق حتى عندما يصبح الالتزام صعبًا',
        'en':'keeping agreements even when honoring them becomes difficult',
        'fr':'respecter les engagements même lorsqu’ils deviennent difficiles à tenir',
        'resourceEvent':'keeping-agreements'
    },
    'gratitude': {
        'ar':'حفظ الجميل وذكر فضل من قدّم المساندة بعد مرور الزمن',
        'en':'remembering kindness and acknowledging those who offered support long afterward',
        'fr':'garder la mémoire du bien reçu et reconnaître longtemps après ceux qui ont aidé',
        'resourceEvent':'remembering-support'
    },
    'nature': {
        'ar':'الرحمة بالحيوان والمكان والموارد وعدم الإفساد من أجل راحة عابرة',
        'en':'care for animals, places, and resources instead of damaging them for quick convenience',
        'fr':'prendre soin des animaux, des lieux et des ressources plutôt que les abîmer pour une facilité passagère',
        'resourceEvent':'care-for-living-world'
    },
    'forgiveness': {
        'ar':'العفو عند القدرة مع وضع حدود تمنع تكرار الضرر',
        'en':'forgiving when one has the power to retaliate while setting boundaries against renewed harm',
        'fr':'pardonner lorsqu’on pourrait se venger tout en posant des limites contre un nouveau tort',
        'resourceEvent':'forgiveness-with-strength'
    }
}


def apply(story:dict)->dict:
    motif=MOTIFS[story['category']]
    story['inspirationBasis']={
        'type':'resource-derived-motif',
        'historicalRetelling':False,
        'quotation':False,
        'namedHistoricalFigures':False,
        'motifAr':motif['ar'],
        'motifEn':motif['en'],
        'motifFr':motif['fr'],
        'eventPattern':motif['resourceEvent'],
        'editorialRule':'Transform the moral/event pattern into an original fictional situation; never imply the fictional plot happened historically.'
    }
    # Let the final scene explicitly connect the fictional decision to the moral
    # pattern without importing names, dates, quotations, or sacred narration.
    story['scenes'][-1]['resourceInspiredMotif']=motif['resourceEvent']
    return story
