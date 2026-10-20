#!/usr/bin/env python3
"""Repair a SHA-pinned 0.2.1-rc.2 runtime overlay without an npm re-download.

The input was already extracted from the signed YMDSH APK. No unrelated runtime
file is modified: this streaming tar rewrite changes only audited module code
and adds the matching runtime-fs package. Source tar entries are not executed.
"""
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dsh_builder_021', ROOT / 'tools/build-dsh-runtime-next.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
from dsh_runtime_patch_021 import patch, SESSION, ATOMIC


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def repack(path):
    path = path.resolve(strict=True)
    metadata_path = path.with_suffix('.inputs.json')
    old = json.loads(metadata_path.read_text(encoding='utf-8'))
    if old.get('version') != '0.2.1-rc.2' or old.get('archive_sha256') != sha256(path):
        raise ValueError('Refusing unpinned or modified 0.2.1 runtime archive')
    stage = path.with_name(path.name + '.021-repair.tmp')
    fixed = {}
    found = set()
    try:
        with path.open('rb') as source:
            with tarfile.open(fileobj=source, mode='r|gz') as original:
                with stage.open('wb') as target:
                    with gzip.GzipFile(fileobj=target, mode='wb', filename='', mtime=0, compresslevel=9) as gz:
                        with tarfile.open(fileobj=gz, mode='w|', format=tarfile.PAX_FORMAT) as output:
                            for entry in original:
                                if entry.name in found:
                                    raise ValueError('Duplicate DSH archive entry: ' + entry.name)
                                found.add(entry.name)
                                if not entry.isfile():
                                    output.addfile(entry)
                                    continue
                                source_file = original.extractfile(entry)
                                if source_file is None:
                                    raise ValueError('Unreadable DSH archive member: ' + entry.name)
                                identity = builder.android_patch.module_identity(entry.name)
                                if identity == SESSION or identity in ATOMIC:
                                    content = patch(entry.name, source_file.read())
                                    entry.size = len(content)
                                    output.addfile(entry, io.BytesIO(content))
                                    fixed[identity] = fixed.get(identity, 0) + 1
                                else:
                                    output.addfile(entry, source_file)
                            expected = {SESSION: 2,
                                        '@deepseek-ai/dsh-fs-local/lib/index.js': 3,
                                        '@deepseek-ai/dsh-attachment-local/lib/index.js': 2}
                            if fixed != expected:
                                raise ValueError('Nested 0.2.1 module graph changed: ' + str(fixed))
                            for filename in ('package.json', 'index.js'):
                                name = builder.PREFIX + '/node_modules/dsha-runtime-fs/' + filename
                                if name in found:
                                    raise ValueError('Refusing to overwrite existing runtime-fs shim')
                                data = (builder.SHIM_DIR / filename).read_bytes()
                                member = tarfile.TarInfo(name)
                                member.size = len(data)
                                member.mode = 0o644
                                output.addfile(member, io.BytesIO(data))
        os.replace(stage, path)
    finally:
        stage.unlink(missing_ok=True)
    metadata_path.write_text(json.dumps({
        'version': '0.2.1-rc.2',
        'inputs': builder.recipe_inputs(),
        'archive_sha256': sha256(path),
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'sha256': sha256(path), 'bytes': path.stat().st_size,
            'verified_patches': fixed}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    print(json.dumps(repack(args.archive), ensure_ascii=False, indent=2))
