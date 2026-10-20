# YMDSH 1.0.17-dsh0.2.1-rc.2 修复说明

本目录是在 `YMDSH-v1.0.14-FULL-SOURCE` 基础上修复后的源码。
版本号已从 `1.0.14 / 15` 提升到 `1.0.17 / 18`（1.0.16/17 是上一轮临时构建），可直接覆盖安装。

## 修复的 Bug

### 1. 新建会话失败：`agent-preset/invalid: ... "deployment:persona-prefix" is already registered`

根因不是 persona 插件本身，而是 DSH 0.2.1-rc.2 运行时**同时打包了 14 份
`@deepseek-ai/dsh-scope`**（顶层一份，`.ymdsh-root` 下各插件依赖里各一份）。
旧实现用模块私有 `Symbol("dsh.scope")` 标记作用域，于是：

- `dsh-agent-preset-registry` 用 A 副本建出 agent scope；
- `dsh-base` 里的 `dsh-system-prompt` 用 B 副本读取该 scope；
- B 看不到 A 的 Symbol，`scopeOf(ctx)` 返回 `undefined`；
- persona 被当成“全局”注册，与 deployment persona 撞名并抛错。

修复分两层，都在安装/升级时由 `RuntimeTools.applyPatchChain()` 自动应用：

1. **`scope-identity-patch.json`（新增）**：把 14 份 `dsh-scope` 的
   `kScope` 换成 `Symbol.for("dsh.scope")`，父子表 / 载体表挂到
   `globalThis` 共享；并给 `scopeOf()` 增加回退，能读懂尚未打补丁的
   旧副本留下的 `Symbol("dsh.scope")` 标签。
2. **`persona-compat-patch.json`（加强）**：作用域内仍用
   `prompt.layers.effect(ctx, ...)` 注册；只有“确实没有作用域”的旧全局
   行才原地覆盖 deployment persona 的文本（销毁时恢复），不再抛异常。

### 2. 旧版 DSHA 预设的兼容

保留 `text` → `prefix` 的旧配置别名，旧预设不必手动改 YAML。


### 3. 补回 DSHA 缺失的内置插件：`dsh-destructive-guard`

上游 DSHA 默认自带、而本源码缺失的破坏性命令守卫已完整移植：

- 插件本体 `builtin-plugins/dsh-destructive-guard/`：安装到 `/root/dsha-destructive-guard`，
  注册表标记 `internal: true`，随 APK 提供且不允许用户停用；
- 强制策略包 `assets/destructive-policy/`：安装到
  `/usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/dsha-destructive-policy`，
  在工具执行前/分派前/文件写入前核验；
- 四个 0.2.1 锚点补丁：`guard-tools-patch.json`、`guard-bash-patch.json`、
  `guard-fs-patch.json`、`guard-editor-patch.json`；其中 `@deepseek-ai/dsh-tools`
  的 import 锚点已按 0.2.1 的 `import { Service, symbols }` 修正；
- `cordis.patch.yml` 覆盖 `approval`/`permission` 两行，新增
  `guarded-full-access` 档位，破坏性命令弹一次确认；
- 分类器纯逻辑回归 274 项通过（`node tools/test-destructive-guard.mjs`）。

## 改动的文件

- `app/src/main/assets/scope-identity-patch.json`（新增）
- `app/src/main/assets/destructive-policy/`（新增：index.js / destructive.js / workdir.js / package.json）
- `app/src/main/assets/builtin-plugins/dsh-destructive-guard/`（新增）
- `app/src/main/assets/guard-tools-patch.json`、`guard-bash-patch.json`、`guard-fs-patch.json`、`guard-editor-patch.json`（新增，已适配 0.2.1 锚点）
- `app/src/main/assets/builtin-plugins.json`、`register-builtin-plugins.py`
- `app/src/main/java/com/deepseekharness/app/util/BuiltinPluginRegistry.java`（重新生成）
- `app/src/main/assets/persona-compat-patch.json`
- `app/src/main/assets/runtime-patches.json`
- `app/src/main/assets/managed-runtime-inputs.json`
- `app/src/main/assets/runtime-descriptor.json`（由脚本重新生成）
- `app/src/main/java/com/deepseekharness/app/runtime/RuntimeTools.java`
- `app/build.gradle`（1.0.17 / versionCode 18）
- `tools/check-builtin-runtime-compat.py`
- `tools/test-persona-021.mjs`
- `tools/test-scope-identity-021.mjs`（新增）
- `tools/host-tests.manifest.json`
- `tools/asset-deployment.json`

## 打包 / 签名

和 1.0.14 完全一样，使用 `ci/release-identity.json` 锁定的同一张证书即可
（即 p12 里的 `ymdsh` 别名）。示例：

```bash
export DSHA_KEYSTORE=/绝对路径/YMDSH-release-2026.p12
export DSHA_KEYSTORE_PASSWORD='p12 密码'
export DSHA_KEY_ALIAS=ymdsh
export DSHA_KEY_PASSWORD='key 密码'
./gradlew :app:assembleStandardRelease
```

`versionCode=18` 已大于线上 17，可直接覆盖安装，**不需要卸载，不会丢会话**。
首次启动会按新 APK 身份重新应用受管补丁。

## 自检

```bash
python3 tools/check-builtin-runtime-compat.py
python3 tools/test-runtime-descriptor-inputs.py
node tools/test-persona-021.mjs
node tools/test-scope-identity-021.mjs
node tools/test-destructive-guard.mjs
python3 tools/test-asset-deployment.py
```

### 验证记录（0.2.1-rc.2 真实运行时）

- `node tools/test-destructive-guard.mjs`：274 项分类规则 + 16 条历史绕过批准，全部通过；
- `node tools/test-destructive-guard-pipeline.mjs`（`DSHA_RAW_RUNTIME` 指向解包后的 0.2.1 运行时）：
  120 个用例，真实 `ToolRuntime` / `ApprovalService` / fs / editor / bash 全链路通过，
  普通只读命令不弹窗，写覆盖必须一次性批准，批准后被并发改写会拒绝；
- `node tools/test-persona-021.mjs`、`node tools/test-scope-identity-021.mjs` 通过；
- `python3 tools/check-builtin-runtime-compat.py`、`python3 tools/test-runtime-descriptor-inputs.py`、
  `python3 tools/test-asset-deployment.py`、`python3 tools/test-host-test-runner.py` 通过。
