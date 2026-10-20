# YMDSH 1.0.13 源码与 APK 交接

版本 `1.0.13-dsh0.2.1-rc.2`，`versionCode=14`，应用包名 `com.yunmeng.dsh`。
标准版面向 Android 11+（API 30+）、ARM64；内置 DSH `0.2.1-rc.2`。

## 本轮实际修复

1. 对用户提供的 `0.0.11.zip` 和 `YMDSH-v1.0.11-FULL-SOURCE(2).zip` 做了完整 ZIP CRC 检查；两份来源包含相同的 2,559 个文件。源包虽然 CRC 正常，其中的 `assets/dsh-runtime.bin` 却是截断内容。使用已验证的上版正式 APK 提取完整运行时并替换，恢复 7 处 Android 私有文件系统兼容补丁。
2. Claude 暖色主题增加弹窗的专用 Material / AppCompat 配色；主题选择卡片的底色、说明文字现在随 Paper、Porcelain、Claude 各自切换，而不再落回硬编码灰色。
3. 修复主机测试清单缺少五个真实测试脚本、语言目录一个缺失消息 ID、APK 验证脚本使用可被 Python `-O` 消除的 `assert`。
4. 修复 Linux/macOS Node 测试消费者未绑定生成测试证明时 Python 可执行文件、哈希与版本的问题；测试会话在解释器更换或证明被篡改时拒绝复用暂存元数据，仍保留完整字节证明最终核查。
5. 保留项目既有的 ARM64、ADB 桥接、Android 私有目录兼容、首次安装默认省电以及运行时维护恢复逻辑；不更改用户配置/升级存储格式。

## 构建与实测

- JDK 17 / Gradle 9.3.1 / Android SDK 37.0 / Build Tools 36.0.0 / NDK 26.3.11579264。
- `:app:compileStandardDebugJavaWithJavac`：**BUILD SUCCESSFUL**。
- `:app:assembleStandardRelease`：**BUILD SUCCESSFUL**；已通过 Gradle 的发布证书身份门禁与 Release lintVital。
- APK ZIP 完整性：`unzip -tq` **通过**。
- APK 包身份：`com.yunmeng.dsh`，`versionCode=14`，`versionName=1.0.13-dsh0.2.1-rc.2`，`minSdk=30`，`targetSdk=37`，ARM64。
- `apksigner verify --verbose --print-certs`：**通过**，本 Android 11+ 标准包使用 v3 签名，签名证书 SHA-256 `66de1b2a511f64f09d4081dd44eb35df24033db3e57f5ef88aff57d0d82a0746`，与上版 1.0.11 一致。
- `tools/verify-ymdsh-021-apk.py` 对正式 APK：**通过**。内置 DSH `0.2.1-rc.2`，7 处补丁、兼容 shim 全部存在，原始运行时 SHA-256 为 `3dce0f76ccb57a5280d1b4d89d949282e186370aea3a0cf5c63243d5a05fe3fa`。
- UI 回归：32 项通过；运行时测试证明回归：10 项通过、1 项 Windows 专用跳过。
- 快速主机测试：42 项通过、6 项未通过。未通过项涉及旧上游发布格式硬编码与架构边界检查、隔离环境中的进程/网络测试，以及尚未提供的 mobile-upstream 和 semver fixture。不能据此声称全量测试全绿。
- 本次无可用的 Android 手机/ADB 设备；**未实测手机安装、首次离线初始化、WebView 登录及应用内实际运行性能**，不能把 APK 签名验证等同于真机验收。

## 使用说明

源码 ZIP 内提供 Android 工程、Java 源码、脚本、测试、完整离线运行归档及 Gradle 构建配置；不含 `app/build/`、Gradle 缓存、发布私钥或签名密码。

发布证书请继续使用用户已有 `YMDSH-release-2026.p12` 和其口令（不要提交到源码）。通过 `DSHA_KEYSTORE`、`DSHA_KEYSTORE_PASSWORD`、`DSHA_KEY_PASSWORD` 环境变量配置，在 JDK 17 与所需 Android 工具链中运行 `./gradlew :app:assembleStandardRelease`。

**升级注意：**同一张 YMDSH 2026 证书签出的 1.0.11/1.0.12 可以尝试直接安装 1.0.13；若设备原安装包使用更早且不同的证书，Android 将拒绝覆盖。请先备份数据，再卸载旧包安装，切勿为了升级直接删除工作区或应用数据。

**校验值（正式 Standard APK）：** SHA-256 `1add584059a0a17e1796b945b284d8f4fb72634cacb4b0011de7e74e023f82b5`。
