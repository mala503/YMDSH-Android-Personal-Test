package com.deepseekharness.app.util;

import com.deepseekharness.app.backup.BackupFileSystem;
import java.io.File;
import java.io.IOException;
import java.util.List;

/**
 * DSH 0.2.1 的内置插件 ESM 模块入口。不能依赖全局 node_modules，也不改动用户插件。
 * 目录作为受管运行时的一部分事务化更新，避免维护完成后发生模块找不到的问题。
 */
public final class BuiltinModuleBridge {
  public static final String DIRECTORY = "usr/local/share/dsha/builtin-node-modules";

  // 旧移动端插件引用过的最多 18 个模块；0.2.1 已移除部分包，不能为其制造悬空链接。
  public static final List<String> PACKAGES =
      List.of(
          "cordis",
          "dsh-client-locale",
          "dsh-client-runtime",
          "dsh-client-ui-conversation",
          "dsh-client-ui-layout",
          "dsh-client-ui-primitives",
          "dsh-client-ui-settings",
          "dsh-client-ui-sidebar",
          "dsh-client-ui-sidebar-right",
          "dsh-client-ui-slots",
          "dsh-client-ui-workspace",
          "dsh-computer-use",
          "dsh-experimental-auto-review",
          "dsh-llm",
          "dsh-llm-pi-ai",
          "dsh-mcp-client",
          "dsh-session-log-export",
          "dsh-system-prompt");

  private static final String MODULES =
      "usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/";

  private BuiltinModuleBridge() {}

  public static void prepare(BackupFileSystem fs, File root) throws IOException {
    final String scope = DIRECTORY + "/@deepseek-ai";
    fs.parents(root, scope + "/placeholder");
    File scopeDir = fs.child(root, scope);
    for (String name : PACKAGES) {
      String direct = MODULES + "@deepseek-ai/" + name;
      String transitive = MODULES + ".ymdsh-root/node_modules/@deepseek-ai/" + name;
      String path;
      if (fs.stat(new File(root, direct)).type.equals("DIRECTORY")) path = direct;
      else if (fs.stat(new File(root, transitive)).type.equals("DIRECTORY")) path = transitive;
      else {
        if (name.equals("cordis") || name.equals("dsh-llm") || name.equals("dsh-mcp-client"))
          throw new IOException("BUNDLED_MODULE_MISSING:@deepseek-ai/" + name);
        continue;
      }
      // 相对于 /usr/local/share/dsha/builtin-node-modules/@deepseek-ai。
      String target = "../../../../" + path.substring("usr/local/".length());
      File link = new File(scopeDir, name);
      var existing = fs.stat(link);
      if (existing.type.equals("LINK") && target.equals(fs.readLink(link))) continue;
      if (!existing.type.equals("MISSING"))
        throw new IOException("BUNDLED_MODULE_CONFLICT:@deepseek-ai/" + name);
      fs.symlink(target, link);
    }
    fs.syncDirectory(scopeDir);
  }
}
