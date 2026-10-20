/**
 * Regression for the Android "new session" agent-preset/invalid failure.
 * Reads the exact bundled rc2 npm source, not a rewritten fixture. The scope
 * fake models ScopedLayers.effect(ctx), a second dsh-scope copy (a different
 * `Symbol('dsh.scope')`), global shadowing and disposal.
 */
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const archive = path.join(root, 'app/src/main/assets/dsh-runtime.bin');
const moduleName = 'usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/dsh-persona/lib/index.js';
function extract(member) {
  const result = spawnSync('tar', ['-xOzf', archive, member], {
    encoding: 'utf8', maxBuffer: 4 * 1024 * 1024, timeout: 30_000
  });
  assert.equal(result.status, 0, result.stderr);
  return result.stdout;
}
const upstream = extract(moduleName);
const registry = JSON.parse(readFileSync(path.join(root, 'app/src/main/assets/runtime-patches.json'), 'utf8'));
assert.equal(registry.dshVersion, '0.2.1-rc.2');
assert.deepEqual(registry.active.map(row => row.asset).slice(0, 2), ['persona-compat-patch.json', 'scope-identity-patch.json']);
const recipe = JSON.parse(readFileSync(path.join(root, 'app/src/main/assets/persona-compat-patch.json'), 'utf8'));
assert.equal(recipe.dshVersion, registry.dshVersion);
assert.equal(recipe.module, '@deepseek-ai/dsh-persona/lib/index.js');
let patched = upstream;
for (const { before, after } of recipe.patches) {
  assert.equal(patched.split(before).length, 2, 'rc2 upstream anchor must occur exactly once');
  patched = patched.replace(before, after);
}
for (const marker of registry.active[0].markers) assert(patched.includes(marker));
assert(!patched.includes('ctx.systemPrompt.section({'));

// Import the original rc2 schemastery and cosmokit as well, so legacy schema
// validation uses the real npm APIs rather than a hand-written mock.
const makeUrl = source => 'data:text/javascript;base64,' + Buffer.from(source).toString('base64');
const packaged = 'usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/.ymdsh-root/node_modules/@deepseek-ai/';
const cosmokitUrl = makeUrl(extract(packaged + 'cosmokit/lib/index.js'));
const schemaSource = extract(packaged + 'schemastery/lib/index.mjs')
  .replace('"@deepseek-ai/cosmokit"', JSON.stringify(cosmokitUrl));
const schemasteryUrl = makeUrl(schemaSource);
const isolated = source => source
  .replace('"@deepseek-ai/schemastery"', JSON.stringify(schemasteryUrl))
  .replace('import { PERSONA_PREFIX_SECTION, PERSONA_SUFFIX_SECTION } from "@deepseek-ai/dsh-system-prompt";',
    'const PERSONA_PREFIX_SECTION = "deployment:persona-prefix", PERSONA_SUFFIX_SECTION = "deployment:persona-suffix";');
async function importSource(source) {
  return import(makeUrl(isolated(source)));
}
const raw = await importSource(upstream);
const compatible = await importSource(patched);

const prefix = 'deployment:persona-prefix', suffix = 'deployment:persona-suffix';
const globalSections = new Map([[prefix, { name: prefix, text: 'Global persona' }],
                                [suffix, { name: suffix, text: 'Global suffix' }]]);
let globalSuppressions = 0;
function namedTable(table, scopeName) {
  return {
    get: name => table.get(name),
    insert(name, value) {
      if (table.has(name)) throw Error(scopeName === undefined
        ? 'prompt section "' + name + '" is already registered (for a per-agent override, register through that agent\'s `agent.ctx` instead)'
        : 'prompt section "' + name + '" is already registered in this scope');
      table.set(name, value);
      return () => table.delete(name);
    }
  };
}
function suppressors(owner) {
  return { append() { owner.suppressed++; return () => owner.suppressed--; } };
}
const globalLayer = { sections: namedTable(globalSections, undefined), suppressed: 0 };
globalLayer.runtimeContextSuppressors = suppressors(globalLayer);
const scoped = new Map();
function scopeKeyOf(ctx) {
  for (let cursor = ctx; cursor !== null && cursor !== undefined; cursor = Object.getPrototypeOf(cursor))
    for (const key of Object.getOwnPropertySymbols(cursor))
      if (key.description === 'dsh.scope' && cursor[key] !== undefined) return cursor[key];
  return undefined;
}
function scopedLayer() {
  const map = new Map();
  const layer = { sectionsMap: map, sections: namedTable(map, 'scope'), suppressed: 0 };
  layer.runtimeContextSuppressors = suppressors(layer);
  return layer;
}
const prompt = {
  getSectionOrder: name => name === 'DEPLOYMENT_PERSONA_PREFIX' ? 0 : 10200,
  section(value) { return globalLayer.sections.insert(value.name, value); },
  suppressRuntimeContext() { return globalLayer.runtimeContextSuppressors.append(true); },
  layers: {
    global: globalLayer,
    effect(ctx, action, options) {
      return ctx.effect(() => {
        const key = scopeKeyOf(ctx);
        let layer;
        if (key === undefined) layer = globalLayer;
        else {
          if (!scoped.has(key)) scoped.set(key, scopedLayer());
          layer = scoped.get(key);
        }
        return action(layer);
      }, options?.label);
    }
  }
};
function makeCtx(scopeKey) {
  const ctx = Object.create({});
  ctx.cleanup = [];
  ctx.effect = function (callback) {
    const dispose = callback();
    if (typeof dispose !== 'function') return dispose;
    let active = true;
    const once = () => { if (active) { active = false; dispose(); } };
    this.cleanup.push(once);
    return once;
  };
  ctx.systemPrompt = prompt;
  ctx.dispose = function () { for (const undo of this.cleanup.reverse()) undo(); };
  if (scopeKey !== undefined) Object.defineProperty(ctx, Symbol.for('dsh.scope'), { value: scopeKey });
  return ctx;
}

const legacyText = '来自旧 DSHA 的 Persona\n保留中文和 # 特殊字符';
assert.throws(() => raw.apply(makeCtx('broken'), { prefix: legacyText }), /already registered/,
  'original rc2 must reproduce the global section collision');
assert.equal(globalSections.get(prefix).text, 'Global persona');

const oldPreset = { text: legacyText, suffix: 'legacy suffix', includeRuntimeContext: false };
const validated = compatible.Config(oldPreset);
assert.equal(validated.prefix, legacyText);
assert.equal(compatible.Config({ prefix: 'new', text: 'old' }).prefix, 'new');
assert.throws(() => compatible.Config({ text: 42 }), /prefix|required/);
assert.throws(() => compatible.Config({ prefix: 5 }), /prefix/);

const agentA = makeCtx('A'), agentB = makeCtx('B');
compatible.apply(agentA, validated);
compatible.apply(agentB, compatible.Config({ prefix: 'Agent B', suffix: 'B suffix' }));
assert.equal(scoped.get('A').sectionsMap.get(prefix).text, legacyText);
assert.equal(scoped.get('A').sectionsMap.get(suffix).text, 'legacy suffix');
assert.equal(scoped.get('B').sectionsMap.get(prefix).text, 'Agent B');
assert.equal(scoped.get('A').suppressed, 1);
assert.equal(scoped.get('B').suppressed, 0);
assert.equal(globalSuppressions, 0);
assert.equal(globalSections.get(prefix).text, 'Global persona');
agentA.dispose();
assert.equal(scoped.get('A').sectionsMap.size, 0);
assert.equal(scoped.get('A').suppressed, 0);
assert.equal(scoped.get('B').sectionsMap.size, 2);
agentB.dispose();
assert.equal(scoped.get('B').sectionsMap.size, 0);

// A tag minted by an unpatched second dsh-scope copy uses Symbol('dsh.scope'),
// not Symbol.for. The reader must still recognize it instead of colliding.
const legacySymbol = Symbol('dsh.scope');
const agentC = makeCtx(undefined);
Object.defineProperty(agentC, legacySymbol, { value: 'legacy-copy' });
compatible.apply(agentC, { prefix: 'Legacy scoped persona' });
assert.equal(scoped.get('legacy-copy').sectionsMap.get(prefix).text, 'Legacy scoped persona');
agentC.dispose();
assert.equal(scoped.get('legacy-copy').sectionsMap.size, 0);

// Genuinely global legacy rows (old DSHA profiles) override the deployment
// persona text in place instead of failing session creation.
const legacyGlobal = makeCtx(undefined);
compatible.apply(legacyGlobal, { prefix: 'Legacy deployment persona', suffix: '' });
assert.equal(globalSections.get(prefix).text, 'Legacy deployment persona');
assert.equal(globalSections.get(suffix).text, '');
legacyGlobal.dispose();
assert.equal(globalSections.get(prefix).text, 'Global persona');
assert.equal(globalSections.get(suffix).text, 'Global suffix');
console.log('PASS DSH 0.2.1-rc.2 persona: collision reproduced; scoped overrides, second scope copy, legacy global row, legacy text and disposal fixed');
