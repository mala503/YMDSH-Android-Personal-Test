#!/usr/bin/env python3
"""YMDSH Android / DSH 0.2.1-rc.2 静态回归门禁，不修改任何文件。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'app/src/main/java/com/deepseekharness/app'
ASSETS = ROOT / 'app/src/main/assets'

def text(path):
    return path.read_text(encoding='utf-8')

def check(condition, message):
    if not condition:
        raise SystemExit('YMDSH_CHECK_FAILED: ' + message)

manifest = json.loads(text(ASSETS / 'runtime-patches.json'))
check(manifest['dshVersion'] == '0.2.1-rc.2', 'patch registry pinned version')
check(not manifest['specialized'], 'obsolete specialized patches not retired')
check([item['asset'] for item in manifest['active']]
      == ['persona-compat-patch.json', 'scope-identity-patch.json',
          'guard-tools-patch.json', 'guard-bash-patch.json',
          'guard-fs-patch.json', 'guard-editor-patch.json'],
      '0.2.1 persona/scope/destructive guard compatibility patches missing')
persona = json.loads(text(ASSETS / 'persona-compat-patch.json'))
check(persona['dshVersion'] == manifest['dshVersion'] and
      any('YMDSH_PERSONA_SCOPED_021' in p['after'] for p in persona['patches']) and
      any('YMDSH_PERSONA_GLOBAL_OVERRIDE_021' in p['after'] for p in persona['patches']),
      'agent-scoped and legacy-global persona override contract')
scope = json.loads(text(ASSETS / 'scope-identity-patch.json'))
check(scope['dshVersion'] == manifest['dshVersion'] and
      'YMDSH_SCOPE_IDENTITY_021' in scope['markers'] and
      '@deepseek-ai/dsh-scope/lib/index.js' in scope['modules'] and
      any('/dsh-base/' in name for name in scope['modules']) and
      any('Symbol.for("dsh.scope")' in p['after'] for p in scope['patches']) and
      any('key.description !== "dsh.scope"' in p['after'] for p in scope['patches']),
      'cross-copy dsh-scope identity contract')
guards = {}
for name in ('guard-tools-patch.json', 'guard-bash-patch.json',
             'guard-fs-patch.json', 'guard-editor-patch.json'):
    guards[name] = json.loads(text(ASSETS / name))
    check(guards[name]['dshVersion'] == manifest['dshVersion'],
          'guard patch pinned version: ' + name)
check(guards['guard-tools-patch.json']['patches'][0]['before'].startswith(
          'import { Service, symbols } from "@deepseek-ai/cordis";'),
      '0.2.1 dsh-tools import anchor')
check(all(any('DSHA_REQUIRED_POLICY_V1' in patch['after'] for patch in guards[name]['patches'])
          for name in ('guard-bash-patch.json', 'guard-editor-patch.json', 'guard-fs-patch.json')),
      'mandatory policy dispatch markers')
policy = ASSETS / 'destructive-policy'
check((policy / 'index.js').is_file() and (policy / 'package.json').is_file(),
      'destructive policy package assets')
for name in ('destructive.js', 'workdir.js'):
    check((policy / name).read_bytes() ==
          (ASSETS / 'builtin-plugins/dsh-destructive-guard/lib' / name).read_bytes(),
          'policy classifier is byte-exact with its canonical source: ' + name)
registry = json.loads(text(ASSETS / 'builtin-plugins.json'))
guard = next((row for row in registry['plugins'] if row['name'] == 'dsh-destructive-guard'), None)
check(guard is not None and guard.get('internal') is True and
      guard.get('guestDirectory') == '/root/dsha-destructive-guard',
      'destructive guard is an internal APK-owned plugin')
java_registry = text(JAVA / 'util/BuiltinPluginRegistry.java')
check('"dsh-destructive-guard"' in java_registry and
      'INTERNAL = List.of("dsh-app-integration", "dsh-destructive-guard"' in java_registry,
      'generated registry owns the destructive guard')
runtime_tools = text(JAVA / 'runtime/RuntimeTools.java')
check('patchScopeIdentity(context, rootfs, spec)' in runtime_tools and
      'PATCH_SCOPE_ANCHOR' in runtime_tools,
      'multi-copy scope identity application')
check('out.add(BuiltinModuleBridge.DIRECTORY);' in text(JAVA / 'util/ManagedRuntimeLayout.java'),
      'transaction must include builtin module bridge')
tools = text(JAVA / 'runtime/RuntimeTools.java')
check('BuiltinModuleBridge.prepare(fs, root)' in tools, 'builtin bridge installation')
check('../../usr/local/share/dsha/builtin-node-modules' in tools,
      'builtin plugin imports must resolve through bridge')
bridge = text(JAVA / 'util/BuiltinModuleBridge.java')
check('BUNDLED_MODULE_MISSING' in bridge and 'BUNDLED_MODULE_CONFLICT' in bridge,
      'bundled dependency failure must be explicit')
for package in ('dsh-llm', 'dsh-mcp-client', 'cordis'):
    check('"' + package + '"' in bridge, 'required module ' + package)
for name in ('dsh-tool-vscreen', 'dsh-computer-use-android'):
    source = text(ASSETS / 'builtin-plugins' / name / 'lib/index.js')
    check('McpClient.Config(' not in source, '0.2.1 MCP config is an object: ' + name)
    check('ctx.plugin(McpClient,config)' in source, 'MCP plugin setup: ' + name)
expected_peers = {
    'dsh-device-shell-guide': {'@deepseek-ai/dsh-system-prompt', '@deepseek-ai/dsh-llm'},
    'dsh-tool-vscreen': {'@deepseek-ai/dsh-mcp-client'},
    'dsh-computer-use-android': {'@deepseek-ai/dsh-mcp-client'},
    'dsh-auto-review': {'@deepseek-ai/dsh-experimental-auto-review'},
}
for name, peers in expected_peers.items():
    package = json.loads(text(ASSETS / 'builtin-plugins' / name / 'package.json'))
    for peer in peers:
        check(package.get('peerDependencies', {}).get(peer) == '0.2.1-rc.2',
              'DSHA builtin peer must match locked runtime: ' + name + '/' + peer)
    check('@deepseek-ai/dsh-computer-use' not in package.get('peerDependencies', {}),
          'removed upstream dsh-computer-use is not an Android MCP runtime import')
    check('0.2.0-rc.2' not in json.dumps(package), 'stale 0.2.0 builtin dependency: ' + name)
mobile = ASSETS / 'builtin-plugins/dsh-web-mobile'
mobile_package = json.loads(text(mobile / 'package.json'))
check(mobile_package['dsh']['client']['inject'] == [], 'obsolete mobile UI peer injections')
client = text(mobile / 'lib/client.js')
check('ymdsh-mobile-021' in client and 'setInterval' not in client
      and 'MutationObserver' not in client, 'lightweight mobile UI')
gradle = text(ROOT / 'app/build.gradle')
check('applicationId "com.yunmeng.dsh"' in gradle and 'versionCode 18' in gradle,
      'package and upgrade code')
palette = text(ROOT / 'app/src/main/res/values/ymdsh_palettes.xml')
check('ym_claude_primary' in palette, 'third original palette')
check('CLAUDE' in text(JAVA / 'util/UiThemePreference.java'), 'third theme setting')
print('YMDSH compatibility checks passed: DSH 0.2.1, 2 MCP, 3 themes, low-overhead mobile UI')
