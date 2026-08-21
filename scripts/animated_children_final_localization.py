#!/usr/bin/env python3
from __future__ import annotations


def apply(story:dict,i:int)->dict:
    # For the 500 additions, mission + stake is a unique natural-language pair.
    # Include both in all three display titles so title uniqueness is guaranteed
    # without exposing internal IDs to children.
    if i>100 and story.get('mission') and story.get('stake'):
        m=story['mission']; s=story['stake']
        base_ar=story['titleAr'].split(' — مهمة ')[0]
        base_en=story['titleEn'].split(' — ')[0]
        base_fr=story['titleFr'].split(' — mission ')[0]
        story['titleAr']=f"{base_ar} — مهمة {m['ar']} {s['ar']}"
        story['titleEn']=f"{base_en} — {m['en'].title()} {s['en']}"
        story['titleFr']=f"{base_fr} — {m['fr']} {s['fr']}"
        story['cover']['altAr']=story['titleAr']
        story['cover']['altEn']=story['titleEn']
        story['cover']['altFr']=story['titleFr']

    # Localized labels used by the web UI; technical identifiers stay stable.
    story['readingLevelAr']={
        'beginner':'مبتدئ','developing':'نامٍ','intermediate':'متوسط','advanced':'متقدم'
    }.get(story.get('readingLevel'),story.get('readingLevel',''))
    story['readingLevelEn']={
        'beginner':'Beginner','developing':'Developing','intermediate':'Intermediate','advanced':'Advanced'
    }.get(story.get('readingLevel'),story.get('readingLevel',''))
    story['readingLevelFr']={
        'beginner':'Débutant','developing':'En progression','intermediate':'Intermédiaire','advanced':'Avancé'
    }.get(story.get('readingLevel'),story.get('readingLevel',''))
    return story
