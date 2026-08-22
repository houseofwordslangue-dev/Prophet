#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
# FORCE_RESOLUTION_TRIGGER: 2026-08-22T06:30Z — exhaustive extraction/acquisition/generation gate execution NOW.
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AVAIL = ROOT / 'data/editorial/resource_extraction_availability.json'
OUT = ROOT / 'data/editorial/resource_extraction_force_report.json'
RESOLUTION = ROOT / 'private/source_first_resolution.json'
MAX_ROUNDS = 30
ACQUISITION_BATCH = '1000'
STABLE_ROUNDS_BEFORE_STOP = 6


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
        'stdoutTail': (p.stdout or '')[-6000:],
        'stderrTail': (p.stderr or '')[-6000:],
    }


def py(name, *args):
    path = ROOT / 'scripts' / name
    if not path.exists():
        return {'label': name, 'returnCode': 127, 'skipped': True, 'reason': 'script-missing'}
    return run(name, [sys.executable, str(path), *args])


def snapshot():
    a = load(AVAIL, {})
    return {
        'catalogResources': int(a.get('catalogResources') or a.get('cataloguedResources') or 0),
        'extractionReady': int(a.get('extractionReady') or 0),
        'acquisitionRequired': int(a.get('acquisitionRequired') or 0),
        'coveragePercent': float(a.get('coveragePercent') or 0),
    }


def main():
    rounds = []
    previous_ready = -1
    stable_rounds = 0

    exhaustive = py('force_resolve_unresolved_content.py')

    for n in range(1, MAX_ROUNDS + 1):
        steps = [
            py('source_first_fulltext_resolver.py'),
            py('live_native_catalog_resolver.py'),
            py('force_resolve_unresolved_content.py'),
            py('acquire_unrestricted_library.py', '--limit', ACQUISITION_BATCH),
            py('build_ingested_library.py'),
            py('source_first_fulltext_resolver.py'),
            py('force_resolve_unresolved_content.py'),
        ]
        s = snapshot()
        rounds.append({'round': n, 'steps': steps, 'snapshot': s})
        ready = s['extractionReady']
        if ready <= previous_ready:
            stable_rounds += 1
        else:
            stable_rounds = 0
        previous_ready = ready
        if s['acquisitionRequired'] == 0 or stable_rounds >= STABLE_ROUNDS_BEFORE_STOP:
            break

    # Final resolver + strict manifests before any downstream generation.
    final_resolver = py('source_first_fulltext_resolver.py')
    final = snapshot()
    resolution = load(RESOLUTION, {'items': []})
    unresolved = [x for x in resolution.get('items', []) if not x.get('extractionReady')]
    research_required = [{
        'id': x.get('id'),
        'title': x.get('title'),
        'author': x.get('author'),
        'state': 'RESEARCH_REQUIRED',
        'reason': 'No verified extraction path after maximum-priority exhaustive resolver/acquisition rounds.',
        'generationAllowed': False,
        'catalogueVisible': True,
        'retryOnNewSource': True,
    } for x in unresolved]

    gate = py('enforce_resource_extraction_readiness.py')
    manifest = py('build_extraction_ready_manifest.py')

    report = {
        'schema': 'resource-extraction-force-report-v6',
        'governedBy': 'MASTER-OVERRIDING-SITE-INSTRUCTION.md',
        'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'forceCompleteStateMachine': True,
        'priorityMode': 'MAXIMUM_ASAP',
        'maxRounds': MAX_ROUNDS,
        'acquisitionBatch': int(ACQUISITION_BATCH),
        'exhaustiveResolver': exhaustive,
        'finalResolver': final_resolver,
        'catalogResources': final['catalogResources'],
        'extractionReady': final['extractionReady'],
        'researchRequired': len(research_required),
        'hardBlocked': 0,
        'coveragePercent': final['coveragePercent'],
        'allResourcesExtractionReady': len(research_required) == 0,
        'generationPolicy': 'Only extractionReady resources in the generated allowlist/manifest may feed extraction or SOURCE_GROUNDED_SYNTHESIS. RESEARCH_REQUIRED resources remain catalogued and are retried; they are never silently substituted or used as evidence until verified.',
        'readinessGate': gate,
        'readyManifest': manifest,
        'rounds': rounds,
        'researchRequiredItems': research_required,
        'hardBlockedItems': [],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('catalogResources','extractionReady','researchRequired','hardBlocked','coveragePercent','allResourcesExtractionReady')}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
