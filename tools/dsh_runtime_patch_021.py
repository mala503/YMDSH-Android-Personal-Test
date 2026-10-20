"""Locked, fail-closed Android filesystem compatibility for DSH 0.2.1-rc.2.

0.2.1 introduced nested npm installations. A patch applied solely to the
top-level package names silently leaves the modules actually used by DSH
unpatched, so normalize the resolved package identity before patching.
"""
import re
from pathlib import PurePosixPath

SESSION = '@deepseek-ai/dsh-session-persistence-jsonl/lib/index.js'
ATOMIC = {
    '@deepseek-ai/dsh-fs-local/lib/index.js': 'publishExclusive',
    '@deepseek-ai/dsh-attachment-local/lib/index.js': 'publishAttachmentExclusive',
}
MARKER = '/* YMDSH_021_SESSION_DIRECT_HINTS_V1 */'


def module_identity(relative):
    """Find the innermost package under any node_modules nesting."""
    name = PurePosixPath(relative).as_posix()
    if '/node_modules/' in name:
        return name.rsplit('/node_modules/', 1)[1]
    return name


def one(text, before, after, label):
    if text.count(before) != 1 or after in text:
        raise ValueError('DSH 0.2.1 incompatible ' + label + ' source anchor')
    return text.replace(before, after, 1)


def atomic(text, function):
    expression = re.compile(r'^import \{([^}]+)\} from "node:fs/promises";', re.M)
    found = expression.search(text)
    if not found:
        raise ValueError('0.2.1 atomic filesystem import is absent')
    imports = [name.strip() for name in found.group(1).split(',') if name.strip()]
    if 'link' not in imports:
        raise ValueError('0.2.1 atomic link() caller was not found')
    imports.remove('link')
    replacement = ('/* YMDSH_021_ATOMIC_PUBLISH_V1 */\n'
                   + f'import {{ {function} as link }} from "dsha-runtime-fs";\n'
                   + 'import { ' + ', '.join(imports) + ' } from "node:fs/promises";')
    return text[:found.start()] + replacement + text[found.end():]


def session(text):
    text = atomic(text, 'publishSessionExclusive')
    text = one(text,
               '\t\tthis.tracker.registerCreated(snapshot, inheritedEventCount);\n'
               '\t\treturn this.tracker.adopt(',
               '\t\tthis.tracker.registerCreated(snapshot, inheritedEventCount);\n'
               '\t\tthis.dshaSessionHints.remember(snapshot);\n'
               '\t\treturn this.tracker.adopt(', 'session create')
    text = one(text, '\ttracker;\n\t/** Backend label',
               '\ttracker;\n\tdshaSessionHints = new YmdshSessionHints();\n\t/** Backend label',
               'session class field')
    text = one(text, '\tasync findLog(id, signal) {\n\t\tconst matches = [];',
               '\tasync findLog(id, signal) {\n'
               '\t\tconst hinted = this.dshaSessionHints.get(id);\n'
               '\t\tif (hinted !== void 0) {\n'
               '\t\t\tconst found = await this.resolveHintedGeneration(hinted, id, signal);\n'
               '\t\t\tif (found !== void 0) return found;\n'
               '\t\t\tthis.dshaSessionHints.forget(id);\n'
               '\t\t}\n\t\tconst matches = [];', 'session lookup')
    text = one(text, '\t/** Find the unique authoritative generation for an id across project directories. */\n'
               '\tasync findLog(id, signal) {',
               '\t/** Resolve a known physical session without relying on delayed parent getdents. */\n'
               '\tasync resolveHintedGeneration(header, id, signal) {\n'
               '\t\tsignal?.throwIfAborted();\n'
               '\t\tconst currentPath = generationLogPath(this.root, header.cwd, id, '
               'sessionFormatCatalog.currentVersion, this.compression);\n'
               '\t\tif (await this.exists(currentPath)) return { sourcePath: currentPath, '
               'sourceVersion: sessionFormatCatalog.currentVersion, currentPath };\n'
               '\t\tconst oppositePath = generationLogPath(this.root, header.cwd, id, '
               'sessionFormatCatalog.currentVersion, this.oppositeCompression());\n'
               '\t\tif (await this.exists(oppositePath)) throw this.encodingMismatch(oppositePath);\n'
               '\t\treturn void 0;\n'
               '\t}\n'
               '\t/** Find the unique authoritative generation for an id across project directories. */\n'
               '\tasync findLog(id, signal) {', 'session direct generation')
    text = one(text,
               '\treleaseHandle(handle, materialized) {\n'
               '\t\tthis.tracker.release(handle, materialized);\n\t}',
               '\treleaseHandle(handle, materialized) {\n'
               '\t\tif (!materialized) this.dshaSessionHints.forget(handle.id);\n'
               '\t\tthis.tracker.release(handle, materialized);\n\t}', 'session cleanup')
    helper = (MARKER + '\n'
              'class YmdshSessionHints {\n'
              '\tentries = new Map();\n'
              '\tremember(header) {\n'
              '\t\tif (!header || typeof header.id !== "string") return;\n'
              '\t\tthis.entries.delete(header.id);\n'
              '\t\tif (this.entries.size >= 512) this.entries.delete(this.entries.keys().next().value);\n'
              '\t\tthis.entries.set(header.id, { cwd: header.cwd });\n'
              '\t}\n'
              '\tget(id) { return this.entries.get(id); }\n'
              '\tforget(id) { this.entries.delete(id); }\n'
              '}\n')
    text = one(text, 'var JsonlSessionPersistence = class extends SessionPersistence {',
               helper + 'var JsonlSessionPersistence = class extends SessionPersistence {',
               'session hints helper')
    if 'await link(tmp, finalPath)' not in text:
        raise ValueError('0.2.1 session publish site changed')
    return text


def patch(relative, content):
    identity = module_identity(relative)
    if identity != SESSION and identity not in ATOMIC:
        return None
    text = content.decode('utf-8')
    patched = session(text) if identity == SESSION else atomic(text, ATOMIC[identity])
    return patched.encode('utf-8')
