#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
"""Run the cross-session reconciler without bulk workflow-file rewrites.
Workflow declarations are reconciled separately through the GitHub connector.
"""
from pathlib import Path
src=Path(__file__).with_name('reconcile_cross_session_updates.py').read_text(encoding='utf-8')
src=src.replace("roots=[ROOT/'.github/workflows',ROOT/'scripts']","roots=[ROOT/'scripts']")
src=src.replace('for root in (ROOT/".github/workflows",ROOT/"scripts"):', 'for root in (ROOT/"scripts",):')
exec(compile(src,'reconcile_cross_session_updates.py','exec'),{'__name__':'__main__','__file__':str(Path(__file__).with_name('reconcile_cross_session_updates.py'))})
