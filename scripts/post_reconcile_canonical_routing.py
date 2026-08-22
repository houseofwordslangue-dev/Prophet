#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'assets/family.js'
s=p.read_text(encoding='utf-8')
old="const p=nameMap.get(norm(x.name));const label=p?n(p):x.name;return `<a class=\"family-person\" href=\"person.html?id=${encodeURIComponent(x.id)}&name=${encodeURIComponent(x.name)}&lang=${lang}\"><strong>${esc(label)}</strong><b>${esc(t.person)} ↗</b></a>`"
new="const p=nameMap.get(norm(x.name));const label=p?n(p):x.name,pid=p?.id||x.id;return `<a class=\"family-person\" href=\"person.html?id=${encodeURIComponent(pid)}&name=${encodeURIComponent(x.name)}&lang=${lang}\"><strong>${esc(label)}</strong><b>${esc(t.person)} ↗</b></a>`"
if old in s:
    s=s.replace(old,new,1)
elif 'pid=p?.id||x.id' not in s:
    raise SystemExit('canonical family link anchor not found')
p.write_text(s,encoding='utf-8')
print('canonical family routing confirmed')
