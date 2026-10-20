package com.deepseekharness.app.util;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public final class DiagnosticExportTextTest {
  @Test
  public void emptyOrMissingDiagnosticNeverProducesEmptyExport() {
    for (String content : new String[] {"", "  \n", null}) {
      String exported = DiagnosticExportText.compose(content, "");
      assertTrue(exported.startsWith("YMDSH 诊断报告\n"));
      assertTrue(exported.contains("重新诊断"));
      assertTrue(exported.getBytes(java.nio.charset.StandardCharsets.UTF_8).length > 29);
    }
  }

  @Test
  public void populatedDiagnosticIsNotReplacedOrLost() {
    String exported = DiagnosticExportText.compose("故障码：DUPLICATE_PATH\n", "点击维护后失败");
    assertTrue(exported.startsWith("故障码：DUPLICATE_PATH\n"));
    assertTrue(exported.contains("点击维护后失败"));
    assertFalse(exported.contains("诊断内容尚未准备好"));
  }
}
