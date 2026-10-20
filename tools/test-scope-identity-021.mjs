/**
 * Regression for the rc2 "second dsh-scope copy" family: a scope minted by one
 * packaged copy must be visible to another copy's ScopedLayers. The old code
 * used a module-local Symbol, so preset personas were registered globally and
 * collided with the deployment persona. The patch also shares parent/carrier
 * tables and keeps reading tags minted by an unpatched copy.
 */
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const archive = path.join(root, 'app/src/main/assets/dsh-runtime.bin');
const recipe = JSON.parse(readFileSync(path.join(root, 'app/src/main/assets/scope-identity-patch.json'), 'utf8'));
const registry = JSON.parse(readFileSync(path.join(root, 'app/src/main/assets/runtime-patches.json'), 'utf8'));
assert.equal(recipe.dshVersion, registry.dshVersion);
assert(recipe.modules.includes('@deepseek-ai/dsh-scope/lib/index.js'));
assert(recipe.modules.some(name => name.includes('/dsh-base/')));
assert.equal(new Set(recipe.modules).size, recipe.modules.length);
assert(recipe.modules.length >= 2);
for (const name of recipe.modules) assert(name.endsWith('/dsh-scope/lib/index.js'));

function extract(member) {
  const result = spawnSync('tar', ['-xOzf', archive, member], {
    encoding: 'utf8', maxBuffer: 4 * 1024 * 1024, timeout: 30_000
  });
  assert.equal(result.status, 0, result.stderr);
  return result.stdout;
}
const relative = name => 'usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/' + name;
const upstream = extract(relative(recipe.modules[0]));
// Sample the two anchors instead of re-scanning the 124 MB archive for every
// copy; RuntimeTools applies the same recipe to the full declared list and
// fails when either anchor is absent.
const dshBase = recipe.modules.find(name => name.includes('/dsh-base/'));
assert.equal(extract(relative(dshBase)), upstream, 'dsh-base dsh-scope copy drifted');

let patched = upstream;
for (const { before, after } of recipe.patches) {
  assert.equal(patched.split(before).length, 2, 'rc2 anchor must occur exactly once');
  patched = patched.replace(before, after);
}
for (const marker of recipe.markers) assert(patched.includes(marker));

const makeUrl = source => 'data:text/javascript;base64,' + Buffer.from(source).toString('base64');
const isolated = source => source.replace('import { Context } from "@deepseek-ai/cordis";',
  'const Context = { filter: Symbol.for("test.cordis.filter") };');
async function instantiate(source, tag) {
  // Distinct data-URL comments force separate module instances; without them
  // the ESM cache would hand both names the same copy.
  return import(makeUrl(isolated(source) + '\n// ' + tag));
}
const rawA = await instantiate(upstream, 'rawA');
const rawB = await instantiate(upstream, 'rawB');
const fixedA = await instantiate(patched, 'fixedA');
const fixedB = await instantiate(patched, 'fixedB');

function makeRoot() {
  const root = {
    plugin() {
      const base = Object.create(root);
      return { ctx: { extend(meta) { return Object.assign(Object.create(base), meta); } } };
    }
  };
  return root;
}

const key = {};
const legacyScope = rawA.createScope(makeRoot(), key);
assert.equal(rawA.scopeOf(legacyScope.ctx), key);
assert.equal(rawB.scopeOf(legacyScope.ctx), undefined,
  'the second unpatched copy cannot see a module-local scope tag');

// A patched reader must still recognize a tag minted by an unpatched copy.
assert.equal(fixedB.scopeOf(legacyScope.ctx), key,
  'patched scopeOf must read a Symbol("dsh.scope") tag from another copy');

// Two patched copies share process-level identity.
const fixedScope = fixedA.createScope(makeRoot(), {});
assert.equal(fixedB.scopeOf(fixedScope.ctx), fixedScope.ctx[Symbol.for('dsh.scope')]);

// Parent bindings made through one copy are visible to the other only when
// both the symbol and the WeakMap are shared.
const parent = {}, child = {};
fixedA.bindScopeParent(child, parent);
assert.deepEqual(fixedB.scopeChainOf(child), [child, parent]);
assert.deepEqual(rawB.scopeChainOf(child), [child],
  'an unpatched copy keeps its private parent table');

// The shared carrier table keeps cross-copy routing intact.
assert.equal(fixedB.isScopeCarrier(fixedB.scopeTarget({}, key)), true);
assert.equal(fixedB.carrierKeyOf(fixedB.scopeTarget({}, key)), key);
console.log('PASS DSH 0.2.1-rc.2 scope identity: second copy collision reproduced; global symbol, legacy tag fallback and shared parent/carrier tables fixed');
