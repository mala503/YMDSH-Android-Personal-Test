# YMDSH 1.0.11 完整源码交接

本压缩包是 `ymdsh` Android 工程的完整可编辑源码与离线构建输入快照，版本为 `1.0.11-dsh0.2.1-rc.2`（`versionCode 12`），包名固定为 `com.yunmeng.dsh`。

## 目录与范围

- `app/`：Android 原生 Java 工程、XML 资源、测试、JNI 库、内置离线 Ubuntu / DSH / Node / pnpm 等运行归档。
- `tools/`：Android 资源准备、运行身份、恢复运行时归档、专项测试与脚本。
- `gradle/`、`gradlew`、`build.gradle`、`settings.gradle` 等：Gradle 工程配置和 Wrapper。
- `ci/`、`docs/`、`website/`、`scripts/` 等：发布身份、审计与开发参考。

为减少体积并避免泄漏，本快照不含构建产物 `app/build/` 和 `build/`、Gradle 缓存 `.gradle/`、用户设备配置及发布私钥。源码内历史文档中可能仍有上游 DSHA 的旧命名或链接；**当前应用真实包名、版本和证书以 `app/build.gradle`、`ci/release-identity.json` 为准**。

## 重新构建

1. 准备 JDK 17、Gradle 9.3.1、Android SDK API 37、Android Build Tools 36.0.0、NDK 26.3.11579264、Python 3，以及 Gradle 所需网络依赖。
2. 解压整个压缩包，进入 `ymdsh-release/`，保持目录结构不变。大型 `.bin` 离线运行资源已在此源码快照内，无需再次从旧 APK 提取。
3. 如需发布包，另外使用单独交付的 `YMDSH-release-2026.p12` 及其密码文件。通过 `DSHA_KEYSTORE`、`DSHA_KEYSTORE_PASSWORD`、`DSHA_KEY_PASSWORD` 环境变量提供给 Gradle，别把密码写进代码仓库；密钥别名为 `ymdsh`。
4. 运行 `./gradlew :app:assembleStandardRelease`。若需要复用此前发布包的已验证优化版 Ubuntu，按 `BUILD.md` 或 `tools/prepare-standard-assets.py` 的参数说明指定 `-Pymdsh.releaseApk=/absolute/path/to/trusted.apk`，只使用已校验哈希的匹配 APK。
5. 产物位于 `app/build/outputs/apk/standard/release/`。使用 Android SDK 的 `apksigner verify --print-certs` 核对证书指纹。

## 发布身份

- 应用名称：`ymdsh`
- 包名：`com.yunmeng.dsh`
- 版本：`1.0.11-dsh0.2.1-rc.2`
- 内置 DSH：`0.2.1-rc.2`（上游预发布候选版）
- 正式 APK SHA-256：`1e805f97fe2a99f34533a704e0ea7306f40a6bbd5977d6c0aa9a30078b71b7bb`
- 发布证书 SHA-256：`66de1b2a511f64f09d4081dd44eb35df24033db3e57f5ef88aff57d0d82a0746`

## 验证范围

正式 Standard 包编译、Android 打包校验与签名验证通过。重点回归测试 25/25 通过；本地全量单测共 1331 项：1328 通过、2 项真实 Linux 进程相关测试在当前容器里失败、1 项跳过。尚未在真实 Android 13 手机上完成 Linux 首次安装、ADB 和登录功能的全流程验收。

特别提醒：新发布证书和旧版证书不同，旧版 APK 不能直接覆盖安装本版。先备份应用数据，再卸载旧版安装。**签名 `.p12` 和密码文件需要分别长期备份；缺少任何一个都无法用相同证书连续升级。**
