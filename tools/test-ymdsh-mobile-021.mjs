import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync('app/src/main/assets/builtin-plugins/dsh-web-mobile/lib/client.js', 'utf8');
const children = [];
let payload;
const document = {
  head: { appendChild(item) { children.push(item); } },
  documentElement: { appendChild(item) { children.push(item); } },
  createElement() { return { id: '', textContent: '', remove() {
    const index = children.indexOf(this);
    if (index >= 0) children.splice(index, 1);
  } }; },
  getElementById(id) { return children.find(item => item.id === id) ?? null; },
};
vm.runInNewContext(source, {
  window: { __ModuleLoader__: { load(module) { payload = module; } } },
  document,
});

assert.equal(payload.id, 'dsh-web-mobile');
const module = payload.factory();
assert.equal(module.name, 'dsh-web-mobile');
assert.deepEqual(Array.from(module.inject), []);
let clean;
module.apply({ effect(effect) { clean = effect(); } });
assert.equal(children.length, 1);
assert.equal(children[0].id, 'ymdsh-mobile-021');
assert.match(children[0].textContent, /max-width: 768px/);
assert.match(children[0].textContent, /max-height: calc\(100dvh/);
module.apply({ effect(effect) { effect(); } });
assert.equal(children.length, 1, 'plugin reapplication must not add duplicate CSS');
clean();
assert.equal(children.length, 0, 'CSS must be removed on plugin dispose');
assert.doesNotMatch(source, /setInterval|MutationObserver|fetch\(/);
console.log('YMDSH mobile 0.2.1 checks passed: independent, idempotent, disposable, no polling');
