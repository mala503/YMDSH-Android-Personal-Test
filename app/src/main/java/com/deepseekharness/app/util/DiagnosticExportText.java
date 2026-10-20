package com.deepseekharness.app.util;

/** 诊断导出的最后一道保护：无论上游状态如何，都不允许输出空白报告。 */
public final class DiagnosticExportText {
  private DiagnosticExportText() {}

  public static String compose(String report, String userSteps) {
    String body =
        report == null || report.isBlank()
            ? "YMDSH 诊断报告\n诊断内容尚未准备好，请返回诊断页点击“重新诊断”。\n"
            : report;
    String steps = userSteps == null ? "" : userSteps;
    return body + "\n用户补充复现步骤：\n" + steps;
  }
}
