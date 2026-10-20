# ymdsh · 安卓手机上的 DSH

ymdsh 是基于 [DSHA](https://github.com/DSH-APP/DSHA) 的 Android 原生改版，沿用上游 MIT 许可。当前安卓包 **v1.0.14**，名称 **ymdsh**，包名 **`com.yunmeng.dsh`**；与上游 `com.dsh.client` 可分别安装，但不自动共享数据。

## 功能

- 内置已锁定的 `@deepseek-ai/dsh@0.2.1-rc.2`，完整随包携带离线 Ubuntu、Node 和 DSH 运行时。
- 原生 Material 3 界面，三套独立浅色主题：暖白「素纸」、冷白「瓷白」、赤陶暖白「Claude」，可从顶部调色盘或设置页切换。
- ADB、无线调试和配对码功能沿用 DSHA 的原生桥接模块；不要求 root。
- 三页独立设计的欢迎引导（移动工作台、ADB 配对、环境准备），品牌化顶部导航及运行状态卡；保留离线环境安装向导、诊断与恢复、备份工具。
- DeepSeek 账号登录入口说明引导用户通过 DSH 官方授权页使用自己账号，不要求手动复制 Cookie，也不会由 ymdsh 收集密码。

## 第一次使用（Android 13）

1. 安装 APK，首次运行阅读三页欢迎引导。
2. 点击环境安装，耐心等待离线包解压（需要预留数 GB 空间，视手机性能可能需要几分钟）。
3. 在「启动」页启动 DSH，等待服务就绪后打开网页版。
4. 如需 ADB，在 Android「设置 → 关于手机」连续点击版本号开启开发者选项，再进入「系统 → 开发者选项 → 无线调试」。
5. 在无线调试中选择「使用配对码配对设备」，返回 ymdsh 的设备授权/ADB 页输入系统显示的地址、端口和配对码，按页面提示连接。
6. 切换主题：主界面顶部的调色盘按钮，或「设置 → 选择白色主题」。账号登录：设置 → DeepSeek 账号登录 → 前往启动，在官方授权页输入账号密码。

## 版本更新

- **v1.0.14（包版本码 15）**：修复新建会话报 `agent-preset/invalid` 和 `deployment:persona-prefix is already registered` 的问题：`dsh-persona` 的提示词覆盖注册、运行上下文抑制全部绑定 Agent 作用域，且 0.2.1 更新时确实执行受管补丁。兼容原 DSHA 第三方预设的 `persona.text` 旧字段。修正设备引导、虚拟屏、电脑操作、Auto review 插件的 0.2.0 旧依赖版本，移除 DSH 0.2.1 已不存在且未实际导入的 `dsh-computer-use` 伪依赖。保留 1.0.13 Claude 配色、省电策略及完整离线资源。
- **v1.0.13（包版本码 14）**：恢复完整的离线 DSH 归档、主题预览及原生弹窗统一配色，增强部分验证门禁。
- **v1.0.10（包版本码 11）**：修复 DSH 0.2.1-rc.2 的新式嵌套模块路径导致「运行环境维护」检查失败；将 Android 容器中的两份会话 JSONL 发布和五份文件/附件发布模块改为兼容的独占写入方式；重新生成离线运行时、受管文件摘要与发布描述。覆盖安装保留现有应用数据，但实际机型仍需验证完整运行链。
- **v1.0.9（包版本码 10）**：修复 DSH 0.2.1 的内置插件模块路径、MCP 配置和旧版 Web 补丁冲突；模块桥纳入事务更新；以无轮询响应式层替换旧 3.0.5 客户端；新增 Claude 原生配色。保留升级签名、用户数据和 ADB 功能。
- **v1.0.4（包版本码 5）**：修正空白诊断报告导出，未完成检查时保留只读现场与历史安装错误；修正报告品牌标题与文件名；同步新版 DSH 依赖布局的归档检验及调试验收代码。
- **v1.0.3（包版本码 4）**：修正 1.0.2 打包的 DSH 归档存在重复路径导致维护失败的问题。
- **v1.0.1（包版本码 2）**：修正欢迎页“认识 DSHA”等旧品牌字样、系统配对助手标签与关于页面；重做三页引导、主工作台标题和设置主题入口。签名证书与 v1.0.0 相同，可以正常覆盖安装。
- 升级前建议自行导出备份。旧版内部文件目录和桥接协议的标识为兼容目的暂时保留，并不是应用显示名称。

## 登录与反代的边界

**当前 APK 没有内置第三方 DeepSeek 网页转 OpenAI 兼容 API 的反向代理服务。** DSH 官方账号授权与这种反代不是同一功能；登录是否可用还取决于 DSH 官方认证端点以及实际网络环境。不要把账号密码填写到来源不明的代理页面。

## 构建说明

本分支基于 DSHA 官方 `v0.2.0-rc2`（build170）源码和经 SHA-256 校验的 APK 离线运行资源。需 JDK 17、Android SDK 37.0、Android NDK 26.3 以及 Gradle 9.3.1。

1. 准备与当前版本匹配的 YMDSH 完整 APK，验证其签名与 SHA-256；不可直接用旧版上游 DSHA 的 DSH 0.2.0 离线资产替换当前运行时。
2. 本次完整源码 ZIP 已包含 `app/src/main/assets/` 下的完整离线归档和恢复归档，不需要从旧 DSHA APK 拼接运行时。如果单独取得轻量源码，再从匹配的 YMDSH APK 恢复归档并按 `tools/recovery-runtime/lock.json` 检查。
3. 运行 `python3 -B tools/prepare-backup-assets.py --write` 及 `python3 -B tools/prepare-runtime-descriptor.py --write`，同步运行时校验文件。
4. 使用 `gradle -Pymdsh.releaseApk=/absolute/path/to/official.apk :app:assembleStandardDebug` 打出测试版。需用自行控制的签名密钥对 release 包签名，切勿冒用上游发布签名。

如需可持续升级的正式 APK：构建时额外添加 `-Pdsha.unsignedPackage=true :app:assembleStandardRelease`，得到未签名包后用 Android SDK 的 `zipalign` 对齐，再用 `apksigner sign --ks <专属密钥文件> --ks-key-alias ymdsh` 签名。生成专属签名证书的第一次就应妥善保存密钥及口令；丢失后无法保持原有包名覆盖升级。

当前缺少 Android 13 实机设备用于无线调试、授权登录和长期运行验收；成功打出 APK 不等于上述外部交互均已实测通过。
