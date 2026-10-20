package com.deepseekharness.app.util;

import org.junit.Test;
import static org.junit.Assert.*;

public class UiThemePreferenceTest {
  @Test
  public void oldPreferenceReturnsToPaper() {
    for (String value : new String[] {null, "", "auto", "DARK", "system", "dark", "light"}) {
      assertEquals("paper", UiThemePreference.normalize(value));
      assertFalse(UiThemePreference.isDark(value, false));
      assertFalse(UiThemePreference.isDark(value, true));
    }
  }

  @Test
  public void threeThemesStayLightRegardlessOfSystem() {
    for (boolean systemDark : new boolean[] {false, true}) {
      assertFalse(UiThemePreference.isDark("paper", systemDark));
      assertFalse(UiThemePreference.isDark("porcelain", systemDark));
      assertFalse(UiThemePreference.isDark("claude", systemDark));
    }
  }

  @Test
  public void cycleMovesBetweenThreeDesignedThemes() {
    assertEquals("porcelain", UiThemePreference.next("paper"));
    assertEquals("claude", UiThemePreference.next("porcelain"));
    assertEquals("paper", UiThemePreference.next("claude"));
    assertEquals("porcelain", UiThemePreference.next(null));
    assertEquals("claude", UiThemePreference.normalize("claude"));
  }
}
