package com.deepseekharness.app.util;

/** ymdsh 三套专属浅色主题；旧版本主题偏好平滑迁移。 */
public final class UiThemePreference {
  public static final String PAPER = "paper", PORCELAIN = "porcelain", CLAUDE = "claude";
  public static final String SYSTEM = "system", LIGHT = "light", DARK = "dark";

  private UiThemePreference() {}

  public static String normalize(String value) {
    return PORCELAIN.equals(value) ? PORCELAIN : CLAUDE.equals(value) ? CLAUDE : PAPER;
  }

  public static boolean isDark(String value, boolean systemDark) {
    return false;
  }

  public static String next(String value) {
    String current = normalize(value);
    return PAPER.equals(current) ? PORCELAIN : PORCELAIN.equals(current) ? CLAUDE : PAPER;
  }
}
