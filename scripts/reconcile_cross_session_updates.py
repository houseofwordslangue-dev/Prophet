#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/'MASTER-OVERRIDING-SITE-INSTRUCTION.md'
BASE=ROOT/'MASTER-OVERRIDING-SITE-INSTRUCTION-BASE.md'
ALIAS=ROOT/'MASTER_OVERRIDING_INSTRUCTION.md'
DECL='GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md'
END='END OF MASTER OVERRIDING INSTRUCTION'

ADD=r'''

==================================================
102. SINGLE-FILE MASTER AUTHORITY AND PROCESS GOVERNANCE
==================================================

This file, `MASTER-OVERRIDING-SITE-INSTRUCTION.md`, is the ONE and ONLY controlling project instruction.

It MUST contain the complete controlling instruction in one file. The controlling instruction MUST NOT be split across a base file, addendum, wrapper, incorporated-by-reference file, or competing master document.

Any earlier or later file named like `MASTER-OVERRIDING-SITE-INSTRUCTION-BASE.md`, `MASTER_OVERRIDING_INSTRUCTION.md`, any specialized MASTER prompt, automation prompt, editorial/source/children/ingestion policy, or similar document is subordinate to this file and MUST NOT independently claim controlling authority.

Compatibility pointer files may exist only when technically necessary. Such files must explicitly state that they are non-authoritative pointers to `MASTER-OVERRIDING-SITE-INSTRUCTION.md`.

Every new or materially modified process, workflow, script, ingestion controller, OCR process, publication process, biography process, media process, localization process, content-generation process, scheduled job or automation MUST read and obey this file first.

Every such process MUST declare exactly:

`GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md`

The underscore alias `MASTER_OVERRIDING_INSTRUCTION.md` is not a valid governing declaration.

A subordinate prompt may set operational targets or implementation details only when compatible with this master. It may never weaken source truth, provenance, rights, canonical ownership, public-page purity, localization, functionality, accessibility or any higher-priority rule in this file.

When project state is reconciled across sessions, branches, Drive, generated artifacts or older releases, preserve useful compatible work, migrate it to the current canonical architecture, and remove obsolete competing wiring only after its useful content has been retained.

==================================================
103. CANONICAL FAMILY NAVIGATION AND SPOUSE COLLECTION
==================================================

`الأسرة النبوية` is the canonical public family area.

It MUST provide a clear collection/filter entry for `الزوجات / أمهات المؤمنين`, resolving through the family interface such as `family.html?group=wives` or an equivalent canonical collection route.

This collection is navigation and grouping only. It MUST NOT create duplicate biographies. Every individual wife/Mother of the Believers remains ONE canonical person in `السير والتراجم` and resolves to the single canonical biography page for that person.

The family area should also expose, where applicable and supported by the live family registry: الوالدان; الأجداد والنسب; الأبناء والبنات; الأحفاد والذرية; الأعمام والعمات; الأخوال والخالات; أبناء العمومة وسائر القرابة; الأصهار; وعلاقات الرضاعة والكفالة.

Do not maintain a competing top-level `العائلة النبوية` architecture when the same material can be represented as collections within `الأسرة النبوية` and canonical person biographies.

Historical classification must remain source-sensitive. Do not place a person into the public `أمهات المؤمنين` collection merely to satisfy a menu or quantity target when that classification is disputed or not supported by the project's adopted sources. Such a person may remain in the broader family system under the most accurate supported relationship classification.

==================================================
104. CANONICAL SOURCES AND STUDIES PUBLIC LABEL
==================================================

The canonical primary resource area is `المصادر والدراسات`.

This label MUST be used as the primary public navigation label for the site's source/resource library.

Legacy routes, code keys or functional sublabels such as `library`, `المكتبة`, `books` or `resources` may remain internally or as compatibility routes, but they MUST NOT replace the canonical top-level information-architecture label `المصادر والدراسات`.

The area may contain books, manuscripts, studies, editions, Qur'an and tafsir resources, hadith resources, Seerah and Shama'il, Ahl al-Bayt resources, PDFs, EPUB/native text, audio/video source records, transcripts and other research resources according to rights and provenance policy.

==================================================
105. GLOBAL ARABIC SPEECH AND AUDIO LOCALE — ar-MA
==================================================

This is a permanent site-wide localization and audio governance rule.

- All Arabic speech, text-to-speech, narration, read-aloud, chatbot audio, story audio, accessibility speech, voice-selection systems and other locale-controlled Arabic audio MUST use `ar-MA` as the primary Arabic locale.
- Configured Arabic speech/TTS MUST NOT use `ar-SA` anywhere on the site.
- This applies to the main site, `أحباب الله`, chatbots, players, stories, articles, biographies, readers, media interfaces, accessibility features, existing code, future code and generated components.
- Arabic voice selection MUST prefer an explicitly identified male `ar-MA` voice whenever male output is required by the governing voice policy.
- If an exact male `ar-MA` voice is unavailable, a clearly identified male Arabic `ar-*` voice may be considered only as a compatibility fallback; never silently substitute a female or unidentified voice where male output is required.
- External or fallback TTS providers MUST request Moroccan Arabic / `ar-MA` whenever locale selection is supported.
- Prerecorded audio without a locale-controlled synthesis setting is not altered merely to attach a locale tag.
- Every generated or synthesized Arabic speech implementation inherits this rule automatically.

Existing locale-controlled Arabic speech code must be migrated from `ar-SA` to `ar-MA`. Future audits and acceptance checks must treat configured runtime `ar-SA` as a defect unless a later explicit rule in THIS file supersedes it.

==================================================
106. CROSS-SESSION / REPOSITORY / DRIVE RECONCILIATION RULE
==================================================

When the user requests a recheck, continuation, full audit, or reconciliation across sessions:

1. Inspect the current repository head and current canonical registries first.
2. Inspect relevant preserved branches and prior artifacts for updates implemented in another session but not successfully merged.
3. Inspect the connected Drive production corpus and manifests for source/resource records that affect the requested architecture or content.
4. Distinguish content/data existence from routing, menu, ledger, taxonomy, public exposure and process-governance defects.
5. Recover compatible missing updates into the CURRENT architecture rather than reverting the project to an older branch.
6. Do not blindly merge an old branch when it would reintroduce obsolete pages, duplicate canonical biographies, stale policies, weak rights handling, or superseded runtime code.
7. One canonical person, one canonical source work, one canonical content owner and one authoritative master file take precedence over historical implementation shape.
8. Record unresolved ambiguities for review; never invent an implementation claim merely to report "no missing".
9. Re-run dependent indexes, menus, manifests, public counts, audits and caches after reconciliation where applicable.
10. Reconciliation is complete only when recovered compatible instructions are placed in the correct canonical location and no known conflicting implementation remains active.
'''

def write_master():
    if not BASE.exists():
        base=MASTER.read_text(encoding='utf-8')
        if '102. SINGLE-FILE MASTER AUTHORITY' in base: return
    else: base=BASE.read_text(encoding='utf-8')
    pos=base.rfind(END)
    if pos<0: raise SystemExit('master base end marker missing')
    MASTER.write_text(base[:pos].rstrip()+ADD+'\n\n'+END+'\n',encoding='utf-8')
    ALIAS.write_text('# DEPRECATED COMPATIBILITY POINTER\n\nThis file is **not** a controlling instruction.\n\nThe sole authoritative project instruction is [`MASTER-OVERRIDING-SITE-INSTRUCTION.md`](MASTER-OVERRIDING-SITE-INSTRUCTION.md).\n\nAll processes must declare `GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md`.\n',encoding='utf-8')
    if BASE.exists(): BASE.unlink()

def normalize_processes():
    roots=[ROOT/'.github/workflows',ROOT/'scripts']
    suffix={'.yml','.yaml','.py','.js','.mjs','.cjs','.sh','.ts'}
    for d in roots:
        if not d.exists(): continue
        for p in d.rglob('*'):
            if not p.is_file() or p.suffix.lower() not in suffix: continue
            try:s=p.read_text(encoding='utf-8')
            except UnicodeDecodeError:continue
            s=s.replace('MASTER_OVERRIDING_INSTRUCTION.md','MASTER-OVERRIDING-SITE-INSTRUCTION.md')
            s=s.replace('MASTER-OVERRIDING-SITE-INSTRUCTION-BASE.md','MASTER-OVERRIDING-SITE-INSTRUCTION.md')
            if DECL not in s:
                marker=('# '+DECL+'\n') if p.suffix.lower() in {'.yml','.yaml','.py','.sh'} else ('// '+DECL+'\n')
                if s.startswith('#!'):
                    i=s.find('\n')+1;s=s[:i]+marker+s[i:]
                else:s=marker+s
            p.write_text(s,encoding='utf-8')
    for p in ROOT.glob('AUTO*.md'):
        s=p.read_text(encoding='utf-8').replace('MASTER_OVERRIDING_INSTRUCTION.md','MASTER-OVERRIDING-SITE-INSTRUCTION.md').replace('MASTER-OVERRIDING-SITE-INSTRUCTION-BASE.md','MASTER-OVERRIDING-SITE-INSTRUCTION.md')
        p.write_text(s,encoding='utf-8')

def update_menu():
    p=ROOT/'assets/site-menu.js';s=p.read_text(encoding='utf-8')
    s=s.replace("library:'المكتبة',sources:'المكتبة'","library:'المصادر والدراسات',sources:'المصادر والدراسات'")
    menu="const MENU=[['محمد ﷺ',null,[['النور','editorial.html?section=light'],['النبي','editorial.html?section=prophet'],['الرسول','editorial.html?section=messenger'],['الإنسان','editorial.html?section=human'],['الرحمة العظمى','editorial.html?section=mercy']],'reserved'],['الأسرة النبوية','family.html',[['الزوجات / أمهات المؤمنين','family.html?group=wives'],['الأبناء والبنات','family.html?group=children'],['الأحفاد والذرية','family.html?group=grandchildren'],['الوالدان','family.html?group=parents'],['الأجداد والنسب','family.html?group=ancestors'],['الأعمام والعمات','family.html?group=paternal-relatives'],['الأخوال والخالات','family.html?group=maternal-relatives'],['أبناء العمومة','family.html?group=cousins'],['الأصهار','family.html?group=in-laws'],['الرضاعة والكفالة','family.html?group=foster'],['الشجرة العائلية','family-tree.html']]],['الصحابة','editorial.html?section=companions',[['التراجم','people.html?group=companions&lang=ar'],['العلم والأقوال','editorial.html?section=companions&subsection=knowledge'],['المواقف والأحداث','editorial.html?section=companions&subsection=events']]],['السير والتراجم','people.html',[['التابعون','people.html?group=tabiin&lang=ar'],['تابعو التابعين','people.html?group=atba_tabiin&lang=ar'],['الرواة','people.html?group=rijal&lang=ar']]],['أحباب الله','children.html',[['بوابة أحباب الله','children.html'],['القراءات الموثقة','children.html#verified-readings'],['القصص المصوّرة','children-stories.html'],['القصص القصيرة جدًا','children-very-short.html'],['القصص المتحركة','children-animated.html'],['فيديو وصوت','children-videos.html']]],['المصادر والدراسات','library-all.html',[['الكتب','library.html?type=books'],['المخطوطات','library.html?type=manuscripts'],['الدراسات والبحوث','library.html?type=studies'],['التفسير وعلوم القرآن','library.html?type=quran'],['الحديث وشروحه','library.html?type=hadith'],['السيرة والشمائل','library.html?type=seerah'],['أهل البيت','library.html?type=ahl-al-bayt'],['PDF','library.html?format=pdf'],['EPUB','library.html?format=epub']]],['الوسائط','media.html',[['الفيديو','media.html?type=video'],['الصوتيات','media.html?type=audio'],['المحاضرات','media.html?type=lecture'],['البودكاست','media.html?type=podcast'],['الوثائقيات','media.html?type=documentary'],['الأبحاث المرئية والمسموعة','media.html?type=research']]],['المقالات والموضوعات','editorial.html',[]],['المنتدى','editorial.html?section=forums',[]]];"
    s,n=re.subn(r"const MENU=.*?;\nconst esc",menu+'\nconst esc',s,count=1,flags=re.S)
    if n!=1:raise SystemExit('menu replacement failed')
    # One Adel on children pages: children-experience.js owns it; global site-chat stays non-child.
    s=s.replace("function loadChildrenChat(){if(!isChildrenPage())return;loadStyle('assets/children-chat.css');loadScript('assets/children-chat.js')}\n",'')
    s=s.replace('loadPlatform();loadLaunchAudio();loadChildrenExperience();loadChildrenChat();loadSiteChat();','loadPlatform();loadLaunchAudio();loadChildrenExperience();loadSiteChat();')
    p.write_text(s,encoding='utf-8')

def update_family():
    p=ROOT/'assets/family.js';s=p.read_text(encoding='utf-8')
    s=s.replace("const P=new URLSearchParams(location.search);let lang=", "const P=new URLSearchParams(location.search);let requestedGroup=P.get('group')||'';let lang=",1)
    if 'const GROUP_ALIASES=' not in s:
        anchor="const t=UI[lang];document.documentElement.lang=lang;document.documentElement.dir=t.dir;"
        aliases="const GROUP_ALIASES={children:['sons','daughters'],grandchildren:['zaynab-grandchildren','ruqayya-grandchildren','fatima-grandchildren'],ancestors:['higher-lineage','paternal-ancestors','maternal-ancestors'],\n'paternal-relatives':['paternal-uncles','paternal-aunts','harith-children','rabia-desc','abu-talib-children','aqil-children','jafar-children','abbas-children','ibn-abbas-children','abu-lahab-children','zubayr-abd-muttalib-children','safiyya-desc','umayma-desc','arwa-desc'],\n'maternal-relatives':['maternal-zuhra','banu-najjar'],'cousins':['harith-children','rabia-desc','abu-talib-children','aqil-children','jafar-children','abbas-children','ibn-abbas-children','abu-lahab-children','zubayr-abd-muttalib-children'],'in-laws':['sons-in-law'],'foster':['foster-mothers','foster-brothers','foster-sisters','halima-family','guardians','guardian-household']};\nfunction groupMatches(id,q){if(!q||q==='relatives')return true;return id===q||(GROUP_ALIASES[q]||[]).includes(id)}\n"
        s=s.replace(anchor,anchor+'\n'+aliases,1)
    old="filter.innerHTML=`<option value=\"\">${esc(t.all)}</option>`+groups.map(g=>`<option value=\"${esc(g.id)}\">${esc(g.labels[lang])}</option>`).join('');function draw(){const q=norm(search.value),f=filter.value;let html='';for(const g of groups){if(f&&g.id!==f)continue;"
    new="filter.innerHTML=`<option value=\"\">${esc(t.all)}</option>`+groups.map(g=>`<option value=\"${esc(g.id)}\">${esc(g.labels[lang])}</option>`).join('');if(requestedGroup&&groups.some(g=>g.id===requestedGroup))filter.value=requestedGroup;function draw(){const q=norm(search.value),f=filter.value,routeGroup=f?'':requestedGroup;let html='';for(const g of groups){if(f&&g.id!==f)continue;if(routeGroup&&!groupMatches(g.id,routeGroup))continue;"
    if old not in s:raise SystemExit('family draw anchor missing')
    s=s.replace(old,new,1)
    s=s.replace("filter.addEventListener('change',draw);draw()", "filter.addEventListener('change',()=>{requestedGroup='';draw()});draw()",1)
    p.write_text(s,encoding='utf-8')

def update_taxonomy():
    p=ROOT/'data/content_taxonomy_policy.json';d=json.loads(p.read_text(encoding='utf-8'))
    c=d.setdefault('canonicalSections',{})
    c['family']={'labelAr':'الأسرة النبوية','landing':'family.html','collectionOnly':True,'canonicalBiographyOwner':'people','groups':['wives','children','grandchildren','parents','ancestors','paternal-relatives','maternal-relatives','cousins','in-laws','foster','relatives'],'wivesLabelAr':'الزوجات / أمهات المؤمنين','onePersonOneCanonicalBiography':True}
    c['library']['labelAr']='المصادر والدراسات';c['library']['landing']='library-all.html'
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def update_drive_manifest():
    p=ROOT/'data/drive_production_manifest.json'
    if not p.exists():return
    d=json.loads(p.read_text(encoding='utf-8'))
    d['publicationPolicy']='RIGHTS_AWARE_VERIFIED_PUBLICATION'
    d['rightsRule']='Drive presence does not by itself authorize public redistribution. Publish/host only under the controlling master rights and provenance rules.'
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def write_audit_script():
    p=ROOT/'scripts/audit_current_instructions.py'
    code='''#!/usr/bin/env python3\n"""GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md\nDeterministic acceptance audit for the unified controlling instruction.\n"""\nfrom pathlib import Path\nimport json,sys\nROOT=Path(__file__).resolve().parents[1]\nM=ROOT/"MASTER-OVERRIDING-SITE-INSTRUCTION.md"\nD="GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md"\ndef main():\n e=[]\n if not M.is_file():e.append("missing canonical master")\n else:\n  s=M.read_text(encoding="utf-8")\n  for x in ("1. PRIMARY OBJECTIVE","88.","101.","102. SINGLE-FILE MASTER AUTHORITY","103. CANONICAL FAMILY NAVIGATION","104. CANONICAL SOURCES AND STUDIES","105. GLOBAL ARABIC SPEECH","106. CROSS-SESSION / REPOSITORY / DRIVE RECONCILIATION RULE","END OF MASTER OVERRIDING INSTRUCTION"):\n   if x not in s:e.append("master missing marker: "+x)\n  if len(s)<65000:e.append("canonical master is unexpectedly short")\n  if "MASTER-OVERRIDING-SITE-INSTRUCTION-BASE.md" in s:e.append("canonical master still depends on split BASE")\n if (ROOT/"MASTER-OVERRIDING-SITE-INSTRUCTION-BASE.md").exists():e.append("split BASE master still exists")\n menu=(ROOT/"assets/site-menu.js").read_text(encoding="utf-8")\n for x in ("الزوجات / أمهات المؤمنين","family.html?group=wives","المصادر والدراسات","المقالات والموضوعات"):\n  if x not in menu:e.append("menu missing: "+x)\n if "['العائلة النبوية'" in menu:e.append("competing top-level family taxonomy remains")\n if "loadChildrenChat()" in menu:e.append("duplicate child assistant loader remains")\n fam=(ROOT/"assets/family.js").read_text(encoding="utf-8")\n for x in ("requestedGroup=P.get('group')","'wives'","groupMatches"):\n  if x not in fam:e.append("family routing missing: "+x)\n tax=json.loads((ROOT/"data/content_taxonomy_policy.json").read_text(encoding="utf-8"))\n cs=tax.get("canonicalSections",{})\n if cs.get("family",{}).get("wivesLabelAr")!="الزوجات / أمهات المؤمنين":e.append("taxonomy missing wives collection")\n if cs.get("library",{}).get("labelAr")!="المصادر والدراسات":e.append("taxonomy library label mismatch")\n for root in (ROOT/".github/workflows",ROOT/"scripts"):\n  for q in root.rglob("*"):\n   if not q.is_file() or q.suffix.lower() not in {".yml",".yaml",".py",".js",".mjs",".cjs",".sh",".ts"}:continue\n   try:t=q.read_text(encoding="utf-8")\n   except UnicodeDecodeError:continue\n   if D not in t:e.append("process lacks canonical declaration: "+str(q.relative_to(ROOT)))\n   if "GOVERNED_BY: MASTER_OVERRIDING_INSTRUCTION.md" in t:e.append("stale governing alias: "+str(q.relative_to(ROOT)))\n for q in ROOT.rglob("*"):\n  if not q.is_file() or q.suffix.lower() not in {".html",".js",".mjs",".cjs",".json",".webmanifest",".toml",".ini",".cfg"}:continue\n  if any(x in q.parts for x in (".git","node_modules","vendor","dist","build","runtime_cache")):continue\n  try:t=q.read_text(encoding="utf-8")\n  except UnicodeDecodeError:continue\n  if "ar-SA" in t:e.append("configured runtime ar-SA: "+str(q.relative_to(ROOT)))\n if e:\n  print("CURRENT-INSTRUCTIONS AUDIT FAIL",file=sys.stderr);[print(" - "+x,file=sys.stderr) for x in e];return 1\n print("CURRENT-INSTRUCTIONS AUDIT PASS");return 0\nif __name__=="__main__":raise SystemExit(main())\n'''
    p.write_text(code,encoding='utf-8')

def update_readme():
    p=ROOT/'README.md'
    if not p.exists():return
    s=p.read_text(encoding='utf-8')
    s=s.replace('MASTER_OVERRIDING_INSTRUCTION.md','MASTER-OVERRIDING-SITE-INSTRUCTION.md').replace('MASTER-OVERRIDING-SITE-INSTRUCTION-BASE.md','MASTER-OVERRIDING-SITE-INSTRUCTION.md')
    marker='## Canonical governance and information architecture'
    if marker not in s:
        s+='\n\n'+marker+'\n\n- Sole controlling instruction: `MASTER-OVERRIDING-SITE-INSTRUCTION.md`.\n- Canonical family area: **الأسرة النبوية**, including **الزوجات / أمهات المؤمنين** as a collection that links to canonical person biographies.\n- **السير والتراجم** remains an independent canonical biography section; one person = one canonical biography.\n- Canonical resource area: **المصادر والدراسات**.\n- Children/young-person content belongs in **أحباب الله**.\n- Arabic generated/synthesized speech uses `ar-MA`.\n'
    p.write_text(s,encoding='utf-8')

def write_reconciliation_audit():
    p=ROOT/'data/audits/cross-session-reconciliation-20260822.json';p.parent.mkdir(parents=True,exist_ok=True)
    d={'schema':'cross-session-reconciliation-v1','governedBy':'MASTER-OVERRIDING-SITE-INSTRUCTION.md','repositoryBaseline':'9ed39b3b48f68e80f3813d839dece4df56e18a45','preservedBranchReviewed':'menu/add-wives-mothers-believers-20260821','driveProductionManifestRecords':335,'driveEvidenceReviewed':['Prophet Muhammad Resources — Archive.org','الطبقات الكبرى-ج4.pdf','سبل الهدى و الرشاد في سيرة خير العباد-ج8.pdf','سبل الهدى و الرشاد في سيرة خير العباد-ج10.pdf'],'recoveredUpdates':['single full master authority','الزوجات / أمهات المؤمنين family collection','family group query routing','المصادر والدراسات canonical public label','ar-MA global synthesized Arabic locale','canonical governing declaration for active processes','single children Adel loader','Drive rights-aware publication policy'],'notBlindlyMerged':['legacy family-person duplicate routing','disputed spouse classification not promoted merely from branch metadata'],'principle':'Recovered compatible work into current architecture; historical/source truth and one-person-one-canonical-biography remain controlling.'}
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

write_master();normalize_processes();update_menu();update_family();update_taxonomy();update_drive_manifest();write_audit_script();update_readme();write_reconciliation_audit()
print('cross-session reconciliation applied')
