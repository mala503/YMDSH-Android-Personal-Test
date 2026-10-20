#!/usr/bin/env python3
"""Read-only check of shipped DSH 0.2.1 Android filesystem repairs."""
from pathlib import Path
import hashlib
import json
import sys
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import dsh_runtime_patch_021 as patcher

apk_path = Path(sys.argv[1])
source_path = ROOT / 'app/src/main/assets/dsh-runtime.bin'
with source_path.open('rb') as source:
    expected_hash = hashlib.file_digest(source, 'sha256').hexdigest()

count = {}
version = None
shim = set()
with zipfile.ZipFile(apk_path) as apk:
    with apk.open('assets/dsh-runtime.bin') as raw:
        with tarfile.open(fileobj=raw, mode='r|gz') as archive:
            for item in archive:
                identity = patcher.module_identity(item.name)
                if item.name == ('usr/local/lib/node_modules/@deepseek-ai/dsh/package.json'):
                    version = json.loads(archive.extractfile(item).read())['version']
                if identity in (patcher.SESSION, *patcher.ATOMIC):
                    text = archive.extractfile(item).read()
                    marker = (b'YMDSH_021_SESSION_DIRECT_HINTS_V1' if identity == patcher.SESSION
                              else b'YMDSH_021_ATOMIC_PUBLISH_V1')
                    if marker not in text or b'from "dsha-runtime-fs"' not in text:
                        raise ValueError('DSH_021_APK_PATCH_MISSING: ' + item.name)
                    count[identity] = count.get(identity, 0) + 1
                if item.name.endswith('/dsha-runtime-fs/index.js'):
                    shim.add('index.js')
                if item.name.endswith('/dsha-runtime-fs/package.json'):
                    shim.add('package.json')
    with apk.open('assets/dsh-runtime.bin') as raw:
        actual_hash = hashlib.file_digest(raw, 'sha256').hexdigest()

if version != '0.2.1-rc.2':
    raise ValueError('DSH_021_APK_VERSION: ' + str(version))
if actual_hash != expected_hash:
    raise ValueError('DSH_021_APK_RUNTIME_HASH: ' + actual_hash + ' != ' + expected_hash)
expected_count = {patcher.SESSION: 2, '@deepseek-ai/dsh-fs-local/lib/index.js': 3,
                  '@deepseek-ai/dsh-attachment-local/lib/index.js': 2}
if count != expected_count:
    raise ValueError('DSH_021_APK_PATCH_COUNT: ' + repr(count))
if shim != {'index.js', 'package.json'}:
    raise ValueError('DSH_021_APK_SHIM: ' + repr(shim))
print('PASS: DSH version', version)
print('PASS: seven Android filesystem patches', count)
print('PASS: bundled publishing shim', ', '.join(sorted(shim)))
print('PASS: embedded runtime SHA-256', actual_hash)
