#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AVAIL = ROOT / 'data/editorial/resource_extraction_availability.json'
OUT = ROOT / 'data/editorial/resource_extraction_force_report.json'
RESOLUTION = ROOT / 'private/source_first_resolution.json'
MAX_ROUNDS = 8


def load(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def run(label, args):
    p = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    return {
        'label': label,
        'returnCode': p.returncode,
        'stdoutTail': (p.stdout or '')[-4000:],
        'stderrTail': (p.stderr or '')[-4000:],
    }


def py(name, *args):
    path = ROOT / 'scripts' / name
    if not path.exists():
        return {'label': name, 'returnCode': 127, 'skipped': True, 'reason': 'script-missing'}
    return run(name, [sys.executable, str(path), *args])


def snapshot():
    a = load(AVAIL, {})
    return {
        'catalogResources': int(a.get('catalogResources') or 0),
        'extractionReady': int(a.get('extractionReady') or 0),
        'acquisitionRequired': int(a.get('acquisitionRequired') or 0),
        'coveragePercent': float(a.get('coveragePercent') or 0),
    }


def main():
    rounds = []
    previous_ready = -1
    stable_rounds = 0

    for n in range(1, MAX_ROUNDS + 1):
        steps = [
            py('source_first_fulltext_resolver.py'),
            py('live_native_catalog_resolver.py'),
            py('acquire_unrestricted_library.py', '--limit', '200'),
            py('build_ingested_library.py'),
            py('source_first_fulltext_resolver.py'),
        ]
        s = snapshot()
        rounds.append({'round': n, 'steps': steps, 'snapshot': s})
        ready = s['extractionReady']
        if ready <= previous_ready:
            stable_rounds += 1
        else:
            stable_rounds = 0
        previous_ready = ready
        if s['acquisitionRequired'] == 0 or stable_rounds >= 2:
            break
        time.sleep(1)

    final = snapshot()
    resolution = load(RESOLUTION, {'items': []})
    unresolved = [x for x in resolution.get('items', []) if not x.get('extractionReady')]
    hard_blocked = [{
        'id': x.get('id'),
        'title': x.get('title'),
        'author': x.get('author'),
        'state': 'HARD_BLOCKED',
        'reason': 'No verified extraction path after exhaustive current resolver/acquisition rounds.',
        'generationAllowed': False,
        'retryOnNewSource': True,
    } for x in unresolved]

    report = {
        'schema': 'resource-extraction-force-report-v2',
        'governedBy': 'MASTER-OVERRIDING-SITE-INSTRUCTION.md',
        'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'forceCompleteStateMachine': True,
        'catalogResources': final['catalogResources'],
        'extractionReady': final['extractionReady'],
        'hardBlocked': len(hard_blocked),
        'coveragePercent': final['coveragePercent'],
        'allResourcesExtractionReady': len(hard_blocked) == 0,
        'generationPolicy': 'Only extractionReady resources may feed extraction or SOURCE_GROUNDED_SYNTHESIS. HARD_BLOCKED resources are excluded, never silently substituted.',
        'rounds': rounds,
        'hardBlockedItems': hard_blocked,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    # Always materialize the authoritative downstream allowlist after the final pass.
    gate = py('enforce_resource_extraction_readiness.py')
    report['readinessGate'] = gate
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('catalogResources','extractionReady','hardBlocked','coveragePercent','allResourcesExtractionReady')}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
