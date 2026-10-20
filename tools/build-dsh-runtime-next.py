#!/usr/bin/env python3
"""Package locked DSH 0.2.1 ARM64, including reviewed Android filesystem fixes.

The rc.2 npm layout nests active session/attachment modules under package-local
node_modules. Only audited 0.2.1 transformations are applied to those exact
modules. All patch anchors are checked rather than silently skipped.
"""
from source_text import write_text as write_source_text
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import posixpath
import re
import tarfile

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'tools/dsh-runtime'
PACKAGE = '@deepseek-ai/dsh'
PREFIX = 'usr/local/lib/node_modules/@deepseek-ai/dsh'
ROOT_PACKAGES = PREFIX + '/node_modules/.ymdsh-root/node_modules'
import dsh_runtime_patch_021 as android_patch
SHIM_DIR = ROOT / 'app/src/main/assets/runtime-fs'


def overlay_path(relative):
    """Preserve distinct nested npm versions inside the DSH-owned tree.

    DSH's nested dependencies resolve from PREFIX/node_modules. Root npm
    packages retain their own independent node_modules beneath ROOT_PACKAGES;
    global aliases point to this private root so Node's normal realpath-based
    resolver can find root dependencies without owning user-installed modules.
    """
    name = relative.as_posix()
    if name == PACKAGE or name.startswith(PACKAGE + '/'):
        return PREFIX + name[len(PACKAGE):]
    return ROOT_PACKAGES + '/' + name


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for data in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(data)
    return digest.hexdigest()


def recipe_inputs():
    paths = [Path(__file__), LOCK / 'package.json', LOCK / 'package-lock.json']
    paths.append(Path(__file__).with_name('source_text.py'))
    paths.append(Path(__file__).with_name('dsh_runtime_patch_021.py'))
    paths.extend(SHIM_DIR / name for name in ('package.json', 'index.js'))
    return {path.relative_to(ROOT).as_posix(): sha256(path) for path in paths}


def legacy_helpers():
    """Reuse the audited platform filter and module-to-overlay path mapping."""
    spec = importlib.util.spec_from_file_location('dsh_overlay_paths',
                                                   Path(__file__).with_name('build-dsh-runtime.py'))
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    return helpers


def build(source, output, version):
    source = source.resolve(strict=True)
    package = json.loads((source / PACKAGE / 'package.json').read_text(encoding='utf-8'))
    if package.get('name') != PACKAGE or package.get('version') != version or version != '0.2.1-rc.2':
        raise ValueError('DSH offline overlay version must match the audited 0.2.1-rc.2 pin')
    if not (source / PACKAGE / 'lib/bin.js').is_file():
        raise ValueError('DSH CLI bin.js is absent')
    lock = json.loads((LOCK / 'package-lock.json').read_text(encoding='utf-8'))
    if lock.get('packages', {}).get('node_modules/@deepseek-ai/dsh', {}).get('version') != version:
        raise ValueError('npm lock and overlay DSH versions differ')
    helpers = legacy_helpers()
    foreign = helpers._foreign_packages(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix('.tmp')
    files = 0
    size = 0
    binaries = []
    omitted = {}
    links = {}
    patched_counts = {}
    try:
        with tmp.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0, compresslevel=9) as compressed:
            with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.PAX_FORMAT) as tar:
                emitted = set()

                def add(entry, stream=None):
                    if entry.name in emitted:
                        raise ValueError('Duplicate DSH archive path: ' + entry.name)
                    emitted.add(entry.name)
                    tar.addfile(entry, stream)

                for path in sorted(source.rglob('*')):
                    relative = path.relative_to(source)
                    reason = helpers.omitted(relative, foreign)
                    if relative.name.lower() in {'readme.md', 'changelog.md', 'history.md'}:
                        reason = 'nonruntime-documentation'
                    if ('musl_arm64' in relative.parts or 'linux-arm64-musl' in relative.parts) and not reason:
                        reason = 'foreign-libc'
                    if reason:
                        if path.is_file():
                            omitted[reason] = omitted.get(reason, 0) + path.stat().st_size
                        continue
                    name = overlay_path(relative)
                    if path.is_symlink():
                        resolved = path.resolve(strict=True)
                        resolved.relative_to(source)
                        entry = tarfile.TarInfo(name)
                        entry.type = tarfile.SYMTYPE
                        entry.linkname = posixpath.relpath(overlay_path(resolved.relative_to(source)), posixpath.dirname(name))
                        entry.mode = 0o777
                        add(entry)
                        continue
                    if path.is_dir():
                        continue
                    if not path.is_file():
                        raise ValueError('Unexpected npm filesystem item: ' + str(relative))
                    with path.open('rb') as stream:
                        header = stream.read(20)
                        stream.seek(0)
                        if header.startswith(b'\x7fELF'):
                            if int.from_bytes(header[18:20], 'little') != 183:
                                raise ValueError('Foreign architecture ELF in runtime: ' + str(relative))
                            binaries.append(relative.as_posix())
                        entry = tarfile.TarInfo(name)
                        identity = android_patch.module_identity(relative)
                        content = None
                        if identity == android_patch.SESSION or identity in android_patch.ATOMIC:
                            content = android_patch.patch(relative, stream.read())
                            stream = io.BytesIO(content)
                            patched_counts[identity] = patched_counts.get(identity, 0) + 1
                        entry.size = len(content) if content is not None else path.stat().st_size
                        entry.mode = 0o755 if header.startswith((b'#!', b'\x7fELF')) else 0o644
                        add(entry, stream)
                    files += 1
                    size += entry.size
                    if path.name != 'package.json':
                        continue
                    parent = path.parent.parent
                    if parent.name.startswith('@'):
                        parent = parent.parent
                    if parent != source:
                        continue
                    try:
                        metadata = json.loads(path.read_text(encoding='utf-8'))
                    except (ValueError, UnicodeError):
                        continue
                    package_name = metadata.get('name', '')
                    if package_name not in (PACKAGE, 'npm') and re.fullmatch(r'(?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*', package_name):
                        alias = 'usr/local/lib/node_modules/' + package_name
                        links[alias] = posixpath.relpath(overlay_path(path.parent.relative_to(source)), posixpath.dirname(alias))
                    entries = metadata.get('bin', {})
                    if isinstance(entries, str):
                        entries = {package_name.split('/')[-1]: entries}
                    if isinstance(entries, dict):
                        for command, target in entries.items():
                            if not command or '/' in command or '\\' in command or not isinstance(target, str):
                                continue
                            executable = (path.parent / target).resolve(strict=True)
                            executable.relative_to(source)
                            destination = PREFIX + '/node_modules/.bin/' + command
                            links.setdefault(destination, posixpath.relpath(overlay_path(executable.relative_to(source)), posixpath.dirname(destination)))
                if patched_counts.get(android_patch.SESSION, 0) < 2:
                    raise ValueError('0.2.1 both active nested JSONL session backends must be patched')
                if not any(patched_counts.get(module, 0) for module in android_patch.ATOMIC):
                    raise ValueError('0.2.1 filesystem publishing backend patch was not applied')
                for filename in ('package.json', 'index.js'):
                    content = (SHIM_DIR / filename).read_bytes()
                    entry = tarfile.TarInfo(PREFIX + '/node_modules/dsha-runtime-fs/' + filename)
                    entry.size, entry.mode = len(content), 0o644
                    add(entry, io.BytesIO(content))
                    files += 1
                    size += len(content)
                links['usr/local/bin/dsh'] = '../lib/node_modules/@deepseek-ai/dsh/lib/bin.js'
                for name, target in sorted(links.items()):
                    entry = tarfile.TarInfo(name)
                    entry.type = tarfile.SYMTYPE
                    entry.linkname = target
                    entry.mode = 0o777
                    add(entry)
                identity = (version + '\n').encode('ascii')
                entry = tarfile.TarInfo('usr/local/share/dsha/dsh-runtime.version')
                entry.size, entry.mode = len(identity), 0o644
                add(entry, io.BytesIO(identity))
        tmp.replace(output)
    finally:
        tmp.unlink(missing_ok=True)
    digest = sha256(output)
    write_source_text(output.with_suffix('.inputs.json'), json.dumps({
        'version': version, 'inputs': recipe_inputs(), 'archive_sha256': digest
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'version': version, 'files': files, 'unpacked_bytes': size,
            'archive_bytes': output.stat().st_size, 'sha256': digest,
            'arm64_binaries': binaries, 'omitted_unpacked_bytes': omitted,
            'omitted_foreign_packages': sorted(x.as_posix() for x in foreign),
            'patched_modules': patched_counts,
            'note': 'Exact npm lock and reviewed Android atomic publish; ARM64 real-device verification still required'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--version', default='0.2.1-rc.2')
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output, args.version), ensure_ascii=False, indent=2))
