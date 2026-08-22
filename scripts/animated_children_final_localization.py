#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import animated_children_unique_rewrite as unique_rewrite
import animated_children_story_fingerprint as story_fingerprint


def apply(story:dict,i:int)->dict:
    # Apply the story-specific narrative layers before the final UI-facing
    # localization fields are frozen. The second layer assigns one of 600
    # unique natural-language episode fingerprints so corpus similarity is
    # reduced through actual story content rather than a weaker validator.
    story=unique_rewrite.apply(story,i)
    story=story_fingerprint.apply(story,i)

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
