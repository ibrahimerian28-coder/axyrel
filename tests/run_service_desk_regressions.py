"""Full process-isolated backend regressions, retaining generated PostgreSQL DBs."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import os
import re
from uuid import uuid4
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
# Playwright clears frontend/test-results when foundation starts. Keep backend
# evidence outside that tree so browser validation cannot erase completed runs.
OUTPUT=ROOT/'test-results/service-desk-backend'

def run(name):
    env={**os.environ,'AXYREL_RETAIN_TEST_DATABASES':'1','AXYREL_ENV':'test','AXYREL_PHASE3_TEST_PORT':str(20000+int(uuid4().hex[:4],16)%40000)}
    result=subprocess.run([sys.executable,'-B',str(ROOT/'tests/isolated_backend_suite.py'),name],cwd=ROOT,env=env,capture_output=True,text=True)
    output=result.stdout+result.stderr
    (OUTPUT/(name+'.log')).write_text(output,encoding='utf-8')
    count=re.search(r'Ran (\d+) tests?',output)
    return dict(module=name,exit_code=result.returncode,tests=int(count[1]) if count else 0)

if __name__=='__main__':
    OUTPUT.mkdir(parents=True,exist_ok=True)
    modules=sorted(p.stem for p in (ROOT/'tests').glob('test_*.py'))
    if len(sys.argv)>1:modules=sys.argv[1:]
    results=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(run,name) for name in modules]):
            row=future.result();results.append(row);print(json.dumps(row),flush=True)
    (OUTPUT/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(f"Total: {sum(r['tests'] for r in results)} tests across {len(results)} isolated modules; failures: {sum(r['exit_code']!=0 for r in results)}",flush=True)
    raise SystemExit(int(any(r['exit_code'] for r in results)))
