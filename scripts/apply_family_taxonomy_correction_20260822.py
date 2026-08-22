#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]

# One-time canonical correction requested 2026-08-22.
# 1) Correct the controlling master, including the canonical IA list and section 103.
p=ROOT/'MASTER-OVERRIDING-SITE-INSTRUCTION.md'
s=p.read_text(encoding='utf-8')
s=s.replace('- الأسرة النبوية\n- الصحابة','- الأسرة النبوية\n- العائلة النبوية\n- الصحابة',1)
new103='''==================================================
103. CANONICAL PROPHETIC HOUSEHOLD AND FAMILY NAVIGATION
==================================================

The public information architecture MUST maintain TWO distinct top-level family areas. They are complementary and MUST NOT be collapsed into one another.

A. `الأسرة النبوية`

This section is limited to the Prophet’s immediate household collections:

- `الزوجات / أمهات المؤمنين`;
- `الأبناء والبنات`;
- `الأحفاد والذرية`.

The spouse collection resolves through the family interface such as `family.html?group=wives` or an equivalent canonical collection route. Children and descendants resolve through their corresponding family collections.

B. `العائلة النبوية`

This is an independent top-level family section for the wider family and lineage structure. It contains:

- `الوالدان`;
- `الأجداد والنسب`;
- `الأعمام والعمات`;
- `الأخوال والخالات`;
- `أبناء العمومة`;
- `الأصهار`;
- `الرضاعة والكفالة`;
- `الشجرة العائلية`.

These two top-level sections are navigation and grouping systems only. They MUST NOT create duplicate biographies.

Every individual person represented in either `الأسرة النبوية` or `العائلة النبوية` remains ONE canonical person in `السير والتراجم` and resolves to that single canonical biography page.

Do not move the wider-family categories into `الأسرة النبوية`, and do not move the immediate-household categories into `العائلة النبوية`.

Historical classification remains source-sensitive. Do not place a person into `أمهات المؤمنين`, a lineage group, or another family relationship merely to satisfy a menu or quantity target when that classification is disputed or unsupported by the project's adopted sources. Use the most accurate supported relationship classification.

'''
pat=r'==================================================\n103\.[\s\S]*?(?==================================================\n104\.)'
s,n=re.subn(pat,new103,s,count=1)
if n!=1: raise SystemExit('could not replace master section 103')
p.write_text(s,encoding='utf-8')

# 2) Split the top-level menu exactly as instructed.
p=ROOT/'assets/site-menu.js';s=p.read_text(encoding='utf-8')
menu="const MENU=[['محمد ﷺ',null,[['النور','editorial.html?section=light'],['النبي','editorial.html?section=prophet'],['الرسول','editorial.html?section=messenger'],['الإنسان','editorial.html?section=human'],['الرحمة العظمى','editorial.html?section=mercy']],'reserved'],['الأسرة النبوية','family.html',[['الزوجات / أمهات المؤمنين','family.html?group=wives'],['الأبناء والبنات','family.html?group=children'],['الأحفاد والذرية','family.html?group=grandchildren']]],['العائلة النبوية','family.html',[['الوالدان','family.html?group=parents'],['الأجداد والنسب','family.html?group=ancestors'],['الأعمام والعمات','family.html?group=paternal-relatives'],['الأخوال والخالات','family.html?group=maternal-relatives'],['أبناء العمومة','family.html?group=cousins'],['الأصهار','family.html?group=in-laws'],['الرضاعة والكفالة','family.html?group=foster'],['الشجرة العائلية','family-tree.html']]],['الصحابة','editorial.html?section=companions',[['التراجم','people.html?group=companions&lang=ar'],['العلم والأقوال','editorial.html?section=companions&subsection=knowledge'],['المواقف والأحداث','editorial.html?section=companions&subsection=events']]],['السير والتراجم','people.html',[['التابعون','people.html?group=tabiin&lang=ar'],['تابعو التابعين','people.html?group=atba_tabiin&lang=ar'],['الرواة','people.html?group=rijal&lang=ar']]],['أحباب الله','children.html',[['بوابة أحباب الله','children.html'],['القراءات الموثقة','children.html#verified-readings'],['القصص المصوّرة','children-stories.html'],['القصص القصيرة جدًا','children-very-short.html'],['القصص المتحركة','children-animated.html'],['فيديو وصوت','children-videos.html']]],['المصادر والدراسات','library-all.html',[['الكتب','library.html?type=books'],['المخطوطات','library.html?type=manuscripts'],['الدراسات والبحوث','library.html?type=studies'],['التفسير وعلوم القرآن','library.html?type=quran'],['الحديث وشروحه','library.html?type=hadith'],['السيرة والشمائل','library.html?type=seerah'],['أهل البيت','library.html?type=ahl-al-bayt'],['PDF','library.html?format=pdf'],['EPUB','library.html?format=epub']]],['الوسائط','media.html',[['الفيديو','media.html?type=video'],['الصوتيات','media.html?type=audio'],['المحاضرات','media.html?type=lecture'],['البودكاست','media.html?type=podcast'],['الوثائقيات','media.html?type=documentary'],['الأبحاث المرئية والمسموعة','media.html?type=research']]],['المقالات والموضوعات','editorial.html',[]],['المنتدى','editorial.html?section=forums',[]]];"
s,n=re.subn(r'const MENU=.*?;\nconst esc',menu+'\nconst esc',s,count=1,flags=re.S)
if n!=1: raise SystemExit('could not replace site menu')
p.write_text(s,encoding='utf-8')

# 3) Split the canonical taxonomy registry while preserving one-person ownership.
p=ROOT/'data/content_taxonomy_policy.json';d=json.loads(p.read_text(encoding='utf-8'))
d['version']='2026-08-22.2'
cs=d.setdefault('canonicalSections',{})
cs['family']={'labelAr':'الأسرة النبوية','landing':'family.html','collectionOnly':True,'canonicalBiographyOwner':'people','groups':['wives','children','grandchildren'],'wivesLabelAr':'الزوجات / أمهات المؤمنين','onePersonOneCanonicalBiography':True,'scope':'Immediate Prophetic household only: spouses/Mothers of the Believers, children, grandchildren and descendants.'}
cs['extendedFamily']={'labelAr':'العائلة النبوية','landing':'family.html','collectionOnly':True,'canonicalBiographyOwner':'people','independentMenuSection':True,'groups':['parents','ancestors','paternal-relatives','maternal-relatives','cousins','in-laws','foster','family-tree'],'onePersonOneCanonicalBiography':True,'scope':'Wider Prophetic family, lineage, kinship, in-laws, foster/guardianship relations and family tree.'}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# 4) The audit file is maintained separately and must pass after this correction.
print('family taxonomy correction applied')
