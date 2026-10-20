# YMDSH 1.0.10 定向修复（源码阶段，尚非 APK）

依据 2026-10-18 Android 13 / OPPO PDRM00 真机诊断：

1. `TRIAL_PLUGIN_FAILED`：原生模块阶段已通过，但试运行插件的 `require.resolve('@deepseek-ai/dsh-storage-json')` 从插件目录无法找到 DSH 0.2.1 的**嵌套**存储后端。新代码先从受管 `dsh-base` 依赖树解析，保留旧布局回退，不放宽存储重开校验。
2. `Linux 环境未就绪`：六步检测第 1 步原先依赖 `isEnvironmentReady()`，包括完整 DSH 健康收据。插件试运行失败会阻塞基础工具、Node、pnpm 等所有诊断。新代码将 **Ubuntu 标记、离线版本、安装基础身份、实际 Bash** 独立验证；完整启动仍然严格要求所有健康证明，未作降级。

## 定向回归

执行 `node tools/test-ymdsh-runtime-regressions.mjs`：

- DSH 0.2.1 嵌套 `dsh-base` 存储模块可解析；
- Linux 基础就绪检查不再依赖 DSH 插件健康收据；
- `node --check app/src/main/assets/runtime-trial-plugin.js` 通过。

以上测试是桌面逻辑与路径回归，**不是 Android 真机安装 / 启动验收**。

## 发布限制

- 这份源代码包没有原有 E7E3 签名私钥，也不包含完整离线 Ubuntu 资产。必须找回原发布密钥，并以原版 APK 作为受信离线资产来源，才能安全构建覆盖安装包。
- **不要**用另一个证书签名后声称可以直接覆盖已有 `com.yunmeng.dsh`；安卓会因签名不符拒绝安装，卸载重装又可能丢失个人数据。
- 更新前应保持应用数据不变；正式发布需测试从 1.0.10 覆盖后执行受管运行时维修、完整诊断和 DSH 启动。
