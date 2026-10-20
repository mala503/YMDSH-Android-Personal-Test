package com.deepseekharness.app.ui;

import android.content.Context;
import android.app.Activity;
import androidx.appcompat.app.AppCompatDelegate;
import com.deepseekharness.app.R;
import com.deepseekharness.app.core.ConfigStore;
import com.deepseekharness.app.util.UiThemePreference;

/** 统一保存和应用外观选择；Activity 重建由 AppCompat 处理。 */
public final class ThemeController {
  private ThemeController() {}

  public static void apply(Context context) {
    AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO);
  }

  public static void applyActivity(Activity activity) {
    String mode = preference(activity);
    activity.setTheme(UiThemePreference.CLAUDE.equals(mode) ? R.style.Theme_DSHA_Claude
        : UiThemePreference.PORCELAIN.equals(mode) ? R.style.Theme_DSHA_Porcelain
            : R.style.Theme_DSHA_Paper);
  }

  public static int surfaceColor(Context context) {
    String mode = preference(context);
    return context.getColor(UiThemePreference.CLAUDE.equals(mode) ? R.color.ym_claude_surface
        : UiThemePreference.PORCELAIN.equals(mode)
            ? R.color.ym_porcelain_surface : R.color.ym_paper_surface);
  }

  public static int accentColor(Context context) {
    String mode = preference(context);
    return context.getColor(UiThemePreference.CLAUDE.equals(mode) ? R.color.ym_claude_primary
        : UiThemePreference.PORCELAIN.equals(mode)
            ? R.color.ym_porcelain_primary : R.color.ym_paper_primary);
  }

  public static void select(Context context, String mode) {
    new ConfigStore(context).setUiTheme(mode);
    apply(context);
  }

  public static boolean isDark(Context context) {
    return false;
  }

  public static String preference(Context context) {
    return new ConfigStore(context).getUiTheme();
  }

  public static String cycle(Context context) {
    String next = UiThemePreference.next(preference(context));
    select(context, next);
    return next;
  }

  public static void followSystem(Context context) {
    select(context, UiThemePreference.PAPER);
  }

  public static void toggle(Context context) {
    cycle(context);
  }
}
