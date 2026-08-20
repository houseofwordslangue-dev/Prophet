(() => {
  'use strict';

  const SOURCE_BASE = 'https://raw.githubusercontent.com/R3GENESI5/Itqan/master/app/data/rijal';
  const FAMILY_MODES = new Set(['mothers_of_believers','distinct_household_status','children','grandchildren','parents','direct_grandparents','ancestor_to_adnan']);
  const MODE_LABELS = {
    all_family:'الأسرة والنسب', mothers_of_believers:'أمهات المؤمنين', distinct_household_status:'نساء البيت — تصنيف تاريخي متميز',
    children:'أولاد النبي ﷺ', grandchildren:'أحفاد النبي ﷺ', parents:'والدا النبي ﷺ', direct_grandparents:'الأجداد المباشرون', ancestor_to_adnan:'النسب إلى عدنان',
    companions:'الصحابة', tabiin:'التابعون', atba_al_tabiin:'أتباع التابعين', all_rijal:'الرواة والأعلام'
  };
  const state = { manifest:null, family:null, audit:null, index:null, mode:'all_family', query:'', limit:180, chunkCache:new Map() };
  const $ = s => document.querySelector(s);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const fmt = n => Number(n).toLocaleString('en-US');

  async function getJSON(url, optional=false) {
    try {
      const r = await fetch(url, {cache:'no-cache'});
      if (!r.ok) throw new Error(`${r.status} ${url}`);
      return await r.json();
    } catch (err) {
      if (optional) return null;
      throw err;
    }
  }

  function buildCategories() {
    const bar = $('#categoryBar');
    const modes = [
      ['all_family','الأسرة والنسب'],['mothers_of_believers','أمهات المؤمنين'],['distinct_household_status','نساء البيت'],['children','الأولاد'],['grandchildren','الأحفاد'],['parents','الوالدان'],['direct_grandparents','الأجداد'],['ancestor_to_adnan','النسب إلى عدنان'],
      ['companions','الصحابة'],['tabiin','التابعون'],['atba_al_tabiin','أتباع التابعين'],['all_rijal','الرواة والأعلام']
    ];
    bar.innerHTML = modes.map(([id,label]) => `<button type="button" data-mode="${id}" class="${state.mode===id?'active':''}">${label}</button>`).join('');
    bar.addEventListener('click', e => {
      const b = e.target.closest('[data-mode]'); if (!b) return;
      state.mode = b.dataset.mode; state.limit = 180;
      bar.querySelectorAll('button').forEach(x => x.classList.toggle('active', x===b));
      render().catch(showError);
    });
  }

  function applyAudit() {
    if (!state.audit) {
      const panel = $('#statusPanel');
      panel.hidden = false;
      panel.textContent = 'مسح الطبقات الآلي لم يُنشر بعد؛ لذلك تبقى أعداد التابعين وأتباع التابعين غير معلنة بدلاً من استخدام أرقام تقديرية.';
      return;
    }
    const c = state.audit.counts || {};
    if (Number.isFinite(c.tabiin)) $('#tabiinCount').textContent = fmt(c.tabiin);
    if (Number.isFinite(c.atba_al_tabiin)) $('#atbaCount').textContent = fmt(c.atba_al_tabiin);
    const panel = $('#statusPanel');
    if (!state.audit.complete || c.generation_conflicts) {
      panel.hidden = false;
      panel.textContent = `حالة تدقيق الطبقات: ${state.audit.complete?'مكتمل بنيوياً':'يحتاج مراجعة'}؛ تعارضات الدليل الصريح: ${fmt(c.generation_conflicts || 0)}؛ سجلات بلا طبقة صريحة: ${fmt(c.without_explicit_layer || 0)}.`;
    }
  }

  async function ensureIndex() {
    if (state.index) return state.index;
    $('#loading').hidden = false;
    state.index = await getJSON('data/people/rijal-index.json');
    $('#loading').hidden = true;
    return state.index;
  }

  function normalize(s) { return String(s || '').toLocaleLowerCase('ar').replace(/[ًٌٍَُِّْـ]/g,'').trim(); }
  function matchQuery(record, query) {
    if (!query) return true;
    const hay = normalize([record.name,record.name_ar,record.kunya,record.city,record.death,record.relationship,record.tabaqa].filter(Boolean).join(' '));
    return hay.includes(normalize(query));
  }

  function familyResults() {
    const records = state.family.records || [];
    return records.filter(r => (state.mode==='all_family' || r.category===state.mode) && matchQuery(r,state.query));
  }

  function rijalModeMatch(r) {
    if (state.mode==='all_rijal') return true;
    if (state.mode==='companions') return r.grade==='companion' || r.generation_class==='companions_explicit_layer';
    if (state.mode==='tabiin') return r.generation_class==='tabiin';
    if (state.mode==='atba_al_tabiin') return r.generation_class==='atba_al_tabiin';
    return false;
  }

  async function rijalResults() {
    const index = await ensureIndex();
    return (index.records || []).filter(r => rijalModeMatch(r) && matchQuery(r,state.query));
  }

  function familyCard(r) {
    const cat = MODE_LABELS[r.category] || r.category;
    return `<article class="person-card" tabindex="0" data-family="${esc(r.id)}"><h3>${esc(r.name_ar)}</h3><p>${esc(r.relationship || '')}</p><div class="badges"><span class="badge">${esc(cat)}</span>${r.historical_note?'<span class="badge warn">تصنيف تاريخي يحتاج قراءة المصدر</span>':''}</div></article>`;
  }

  function rijalCard(r) {
    return `<article class="person-card" tabindex="0" data-rijal="${esc(r.id)}"><h3>${esc(r.name)}</h3><p>${esc([r.kunya,r.city,r.death].filter(Boolean).join(' · '))}</p><div class="badges">${r.grade?`<span class="badge">${esc(r.grade)}</span>`:''}${r.tabaqa?`<span class="badge">${esc(r.tabaqa)}</span>`:''}</div></article>`;
  }

  async function render() {
    $('#empty').hidden = true;
    $('#resultTitle').textContent = MODE_LABELS[state.mode] || 'الدليل';
    const isFamily = state.mode==='all_family' || FAMILY_MODES.has(state.mode);
    const rows = isFamily ? familyResults() : await rijalResults();
    const shown = rows.slice(0,state.limit);
    $('#peopleGrid').innerHTML = shown.map(isFamily?familyCard:rijalCard).join('');
    $('#resultCount').textContent = shown.length < rows.length ? `عرض ${fmt(shown.length)} من ${fmt(rows.length)}` : `${fmt(rows.length)} سجل`;
    $('#empty').hidden = rows.length !== 0;
  }

  function sourceList(record) {
    const ids = record.source_ids || [];
    if (!ids.length) return '';
    const items = ids.map(id => state.family.source_registry?.[id]).filter(Boolean);
    return items.length ? section('المصادر والببليوغرافيا', `<ul class="source-list">${items.map(s=>`<li>${esc(s.work)} — ${esc(s.scope)}</li>`).join('')}</ul>`) : '';
  }

  function section(title, html, cls='') { return html ? `<section class="profile-section ${cls}"><h3>${esc(title)}</h3>${html}</section>` : ''; }
  function textSection(title, value, cls='') { return value ? section(title, `<p>${esc(value)}</p>`, cls) : ''; }
  function listSection(title, value) {
    if (!value) return '';
    const arr = Array.isArray(value) ? value : (typeof value==='object' ? Object.entries(value).map(([k,v])=>`${k}: ${typeof v==='string'?v:JSON.stringify(v)}`) : [value]);
    const clean = arr.filter(v => v !== null && v !== '' && v !== undefined);
    return clean.length ? section(title, `<ul>${clean.map(v=>`<li>${esc(typeof v==='string'?v:JSON.stringify(v))}</li>`).join('')}</ul>`) : '';
  }

  function openFamily(id, push=true) {
    const r = state.family.records.find(x => x.id===id); if (!r) return;
    const body = `<div class="profile"><header class="profile-head"><h2>${esc(r.name_ar)}</h2><p>${esc(r.relationship || '')}</p></header>
      ${listSection('الهوية وصيغ الاسم', r.name_variants)}
      ${textSection('النسب والقرابة', r.genealogy || r.relationship)}
      ${textSection('الوضع أو التصنيف التاريخي', r.historical_note, 'source-warning')}
      ${textSection('التسلسل الزمني', r.chronology)}
      ${textSection('نص السيرة المصدرية', r.biography_source_text)}
      ${listSection('الشيوخ', r.teachers)}${listSection('التلاميذ', r.students)}${listSection('النقول والتقييمات', r.evaluations)}
      ${sourceList(r)}<p class="empty-field-note">لا تُعرض الأقسام التي لا تتضمنها المادة المصدرية؛ عدم ظهور قسم لا يعني إنشاء معلومات بديلة.</p></div>`;
    $('#personBody').innerHTML = body; $('#personDialog').showModal();
    if (push) history.replaceState(null,'',`?person=${encodeURIComponent(id)}`);
  }

  async function loadSourceProfile(meta) {
    const file = meta.source_file; if (!file) return null;
    if (!state.chunkCache.has(file)) state.chunkCache.set(file, getJSON(`${SOURCE_BASE}/${encodeURIComponent(file)}`));
    const payload = await state.chunkCache.get(file);
    if (Array.isArray(payload)) return payload.find((p,i)=>String(p.id ?? i)===String(meta.source_key)) || null;
    if (payload && typeof payload==='object') {
      if (payload.profiles && Array.isArray(payload.profiles)) return payload.profiles.find((p,i)=>String(p.id ?? i)===String(meta.source_key)) || null;
      return payload[meta.source_key] || null;
    }
    return null;
  }

  async function openRijal(id, push=true) {
    const index = await ensureIndex();
    const meta = index.records.find(x => x.id===id); if (!meta) return;
    $('#personBody').innerHTML = `<div class="profile"><header class="profile-head"><h2>${esc(meta.name)}</h2><p>جارٍ تحميل السجل المصدر عند الطلب…</p></header></div>`;
    $('#personDialog').showModal();
    if (push) history.replaceState(null,'',`?rijal=${encodeURIComponent(id)}`);
    let p = null;
    try { p = await loadSourceProfile(meta); } catch (_) {}
    if (!p) {
      $('#personBody').innerHTML = `<div class="profile"><header class="profile-head"><h2>${esc(meta.name)}</h2></header>${textSection('الطبقة',meta.tabaqa)}${textSection('المدينة',meta.city)}${textSection('الوفاة',meta.death)}${textSection('الحكم المختصر',meta.grade)}${section('المصدر',`<p class="source-list">${esc(meta.source_file)} · ${esc(meta.source_key)}</p>`,'source-warning')}<p class="empty-field-note">تعذر تحميل نص السجل المصدر الكامل في هذه الجلسة؛ لم تُنشأ بدائل.</p></div>`;
      return;
    }
    const variants = p.namings || p.name_variants || p.variants;
    const genealogy = p.nasab || p.nisba || p.lineage || p.genealogy;
    const chronology = [p.birth?`الميلاد: ${p.birth}`:'',p.death?`الوفاة: ${p.death}`:'',p.city?`البلد/المدينة: ${p.city}`:''].filter(Boolean).join(' · ');
    const biography = p.biography || p.bio || p.biography_text || p.dhahabi;
    const assessments = p.jarh_wa_tadil || p.assessments || p.evaluations;
    const sources = p.sources || p.references || p.source_refs;
    $('#personBody').innerHTML = `<div class="profile"><header class="profile-head"><h2>${esc(p.full_name || p.name || meta.name)}</h2><p>${esc(p.kunya || '')}</p></header>
      ${listSection('الهوية وصيغ الاسم',variants)}${textSection('النسب والنسبة',genealogy)}${textSection('الجيل / الطبقة',p.tabaqat || p.generation || (meta.tabaqa_order?`الطبقة ${meta.tabaqa_order}`:''))}
      ${textSection('التسلسل الزمني',chronology)}${textSection('نص السيرة المصدرية',biography)}${listSection('الشيوخ',p.teachers)}${listSection('التلاميذ',p.students)}${listSection('النقول والتقييمات',assessments)}${listSection('العلاقات',p.relationships)}${listSection('المصادر والببليوغرافيا',sources)}
      ${section('مرجع السجل المصدر',`<p class="source-list">${esc(meta.source_file)} · ${esc(meta.source_key)}</p>`)}<p class="empty-field-note">أي حقل غير موجود في المصدر يظل غائباً عن الصفحة.</p></div>`;
  }

  function showError(err) {
    console.error(err); $('#loading').hidden = true; const panel=$('#statusPanel'); panel.hidden=false; panel.textContent='تعذر تحميل جزء من corpus. لم يستبدل النظام البيانات بمحتوى مُنشأ.';
  }

  async function init() {
    [state.manifest,state.family,state.audit] = await Promise.all([getJSON('data/people/manifest.json'),getJSON('data/people/family-core.json'),getJSON('data/people/rijal-audit.json',true)]);
    buildCategories(); applyAudit();
    $('#peopleSearch').addEventListener('submit', e=>{e.preventDefault();state.query=$('#q').value;state.limit=180;render().catch(showError)});
    $('#q').addEventListener('input', ()=>{state.query=$('#q').value;if(state.mode==='all_family'||FAMILY_MODES.has(state.mode))render().catch(showError)});
    $('#peopleGrid').addEventListener('click', e=>{const c=e.target.closest('.person-card');if(!c)return;if(c.dataset.family)openFamily(c.dataset.family);if(c.dataset.rijal)openRijal(c.dataset.rijal).catch(showError)});
    $('#peopleGrid').addEventListener('keydown', e=>{if((e.key==='Enter'||e.key===' ')&&e.target.classList.contains('person-card'))e.target.click()});
    $('.dialog-close').addEventListener('click',()=>$('#personDialog').close());
    $('#personDialog').addEventListener('close',()=>history.replaceState(null,'','people.html'));
    await render();
    const params = new URLSearchParams(location.search);
    if (params.get('person')) openFamily(params.get('person'),false);
    if (params.get('rijal')) await openRijal(params.get('rijal'),false);
  }
  init().catch(showError);
})();
