#!/usr/bin/env python3
"""Smoke-check the audited session patch against both shipped 0.2.1 copies."""
import importlib.util
from pathlib import Path
import sys
import tarfile
import zipfile
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
spec = importlib.util.spec_from_file_location('dsh_patcher_021', ROOT / 'tools/dsh_runtime_patch_021.py')
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)
apk = Path(sys.argv[1])
tested = []
atomic = {}
with zipfile.ZipFile(apk) as z, z.open('assets/dsh-runtime.bin') as data:
    with tarfile.open(fileobj=data, mode='r|gz') as archive:
        for member in archive:
            identity = patcher.module_identity(member.name)
            if identity != patcher.SESSION and identity not in patcher.ATOMIC:
                continue
            original = archive.extractfile(member).read()
            updated = patcher.patch(member.name, original)
            with tempfile.TemporaryDirectory() as work:
                file = Path(work) / 'module.mjs'
                file.write_bytes(updated)
                subprocess.run(['node', '--check', str(file)], check=True, capture_output=True)
            if identity == patcher.SESSION:
                assert b'YMDSH_021_SESSION_DIRECT_HINTS_V1' in updated
                assert b'publishSessionExclusive as link' in updated
                assert b'await link(tmp, finalPath)' in updated
                tested.append(member.name)
            else:
                assert b'YMDSH_021_ATOMIC_PUBLISH_V1' in updated
                atomic[identity] = atomic.get(identity, 0) + 1
assert len(tested) == 2, tested
assert atomic == {
    '@deepseek-ai/dsh-fs-local/lib/index.js': 3,
    '@deepseek-ai/dsh-attachment-local/lib/index.js': 2,
}, atomic
print('Patched 0.2.1 JSONL session modules:', *tested, sep='\n - ')
print('Verified atomic filesystem modules:', atomic)
