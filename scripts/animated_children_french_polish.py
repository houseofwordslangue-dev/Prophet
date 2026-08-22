#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import generate_animated_children_stories as base

OBJ_ARTICLES=['la','la','le','la','le','le','la','la','le','la']
MASCULINE_CATEGORIES={'courage','nature','forgiveness'}

def apply(story:dict,i:int)->dict:
    name=base.NAMES_FR[(i-1)%25]
    set_idx=(i*3+i//7)%len(base.SETTINGS)
    obj_idx=(i*7)%len(base.OBJECTS)
    conf_idx=(i*9+i//5)%len(base.CONFLICTS)
    sfr=base.SETTINGS[set_idx][2]
    ofr=base.OBJECTS[obj_idx][2]
    cfr=base.CONFLICTS[conf_idx][2]
    article=OBJ_ARTICLES[obj_idx]
    object_phrase=f'{article} {ofr}'
    story['titleFr']=f'{name} et {object_phrase} à {sfr}'
    cat=story['category']
    cat_fr={
        'kindness':'la gentillesse','honesty':'l’honnêteté','courage':'le courage','patience':'la patience','curiosity':'la curiosité',
        'cooperation':'la coopération','responsibility':'la responsabilité','gratitude':'la gratitude','nature':'le soin de la nature','forgiveness':'le pardon'
    }[cat]
    action_fr={
        'kindness':'tenir compte du ressenti de l’autre avant de décider',
        'honesty':'dire la vérité même lorsqu’elle est gênante',
        'courage':'agir malgré la peur tout en mesurant les conséquences',
        'patience':'laisser au processus le temps nécessaire au lieu de forcer le résultat',
        'curiosity':'poser une nouvelle question puis vérifier la réponse',
        'cooperation':'répartir le travail afin que chacun complète les autres',
        'responsibility':'assumer les conséquences d’une décision et les réparer',
        'gratitude':'remarquer les efforts des autres et les remercier sincèrement',
        'nature':'protéger le milieu naturel avant de choisir la solution la plus facile',
        'forgiveness':'comprendre l’erreur et poser de meilleures limites au lieu de se venger'
    }[cat]
    adj='réel' if cat in MASCULINE_CATEGORIES else 'réelle'
    story['synopsisFr']=(f'{name} commence une journée ordinaire à {sfr} avec un objectif précis, mais le programme change lorsqu’{cfr}. '
                         f'{object_phrase.capitalize()} et une série de petits indices conduisent l’équipe à travers une enquête, un échec, '
                         f'un vrai désaccord puis un choix final qui transforme {cat_fr} en action concrète.')
    story['moralFr']=f'{cat_fr.capitalize()} devient {adj} lorsque nous choisissons de {action_fr} dans une décision concrète au lieu de nous contenter d’en parler.'
    # Normalize a few recurrent contractions in scene prose.
    for block in story.get('storyFr') or []:
        t=block.get('text','')
        t=t.replace('lorsque un ','lorsqu’un ').replace('lorsque une ','lorsqu’une ')
        t=t.replace('de le ','du ').replace('de les ','des ')
        block['text']=t
    for j,sc in enumerate(story.get('scenes') or []):
        if j < len(story.get('storyFr') or []): sc['narrationFr']=story['storyFr'][j]['text']
    return story
