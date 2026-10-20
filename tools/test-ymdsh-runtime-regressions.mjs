#!/usr/bin/env node
// 无 Android 的定向回归：验证锁定依赖的嵌套路径和 Linux 检查门禁已分离。
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdtemp, mkdir, readFile, rm, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';

const repo=resolve(fileURLToPath(new URL('..',import.meta.url)));
const plugin=await readFile(join(repo,'app/src/main/assets/runtime-trial-plugin.js'),'utf8');
const functionText=plugin.match(/function storageEntry\([^)]*\)\{[\s\S]*?\n\}/)?.[0];
assert.ok(functionText,'Storage resolver source must be present');
const source=functionText.replace('import.meta.url',JSON.stringify(import.meta.url));
const storageEntry=vm.runInNewContext(`(${source})`,{join,createRequire});
const directory=await mkdtemp(join(tmpdir(),'ymdsh-storage-test-'));
try{
 const nested=join(directory,'node_modules/.ymdsh-root/node_modules/@deepseek-ai/dsh-base/node_modules/@deepseek-ai/dsh-storage-json');
 await mkdir(join(nested,'lib'),{recursive:true});
 await writeFile(join(nested,'package.json'),JSON.stringify({name:'@deepseek-ai/dsh-storage-json',main:'lib/index.js'}));
 await writeFile(join(nested,'lib/index.js'),'export class JsonStorageBackend {}\n');
 assert.equal(storageEntry(directory),join(nested,'lib/index.js'));
 console.log('PASS: 0.2.1 nested dsh-base storage-json resolves');
}finally{await rm(directory,{recursive:true,force:true})}

const runtime=await readFile(join(repo,'app/src/main/java/com/deepseekharness/app/runtime/RuntimeInstallationState.java'),'utf8');
const pipeline=await readFile(join(repo,'app/src/main/java/com/deepseekharness/app/runtime/InstallPipeline.java'),'utf8');
const bootstrap=await readFile(join(repo,'app/src/main/java/com/deepseekharness/app/runtime/ProotBootstrap.java'),'utf8');
assert.match(runtime,/public boolean isBaseEnvironmentReady\(\)\s*\{[\s\S]*?isOfflineExtracted\(\)[\s\S]*?hasBash\(\)[\s\S]*?offlineVersionFile\(\)[\s\S]*?sameBase\(/);
assert.match(pipeline,/public boolean ready\(\)\s*\{\s*return proot\.isBaseEnvironmentReady\(\);/);
assert.match(bootstrap,/public boolean isBaseEnvironmentReady\(\)\s*\{\s*return installation\.isBaseEnvironmentReady\(\);/);
assert.match(runtime,/public boolean isEnvironmentReady\(\)\s*\{[\s\S]*?rootfsVersionMatches\(\)/);
console.log('PASS: Ubuntu base gate independent from strict runtime health');

const coldTools=await readFile(join(repo,'app/src/main/java/com/deepseekharness/app/runtime/ColdToolsInstaller.java'),'utf8');
assert.match(coldTools,/new AndroidTrustedAssetFileSystem\(boot\.rootfsDir\)/);
assert.match(coldTools,/new File\(checkedRoot, "root\/\.dsha-ubuntu-tools-version"\)/);
assert.match(coldTools,/new File\(checkedRoot, "var\/lib\/dpkg\/status"\)/);
assert.match(coldTools,/verified\.small\(marker, 128\)/);
assert.match(coldTools,/verified\.read\(status, verified\.stat\(status\)\)/);
console.log('PASS: cold tool metadata stays on its verified NOFOLLOW root');
