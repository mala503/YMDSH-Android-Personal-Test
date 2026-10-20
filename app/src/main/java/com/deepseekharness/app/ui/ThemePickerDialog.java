package com.deepseekharness.app.ui;

import android.app.Activity;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import androidx.appcompat.app.AlertDialog;
import com.deepseekharness.app.R;
import com.deepseekharness.app.util.UiText;
import com.deepseekharness.app.util.UiThemePreference;

/** ymdsh 原创主题画廊：预览与选择卡片使用各自的真实语义色。 */
public final class ThemePickerDialog {
  private ThemePickerDialog() {}

  private static int dp(Activity activity, float value) {
    return (int) (value * activity.getResources().getDisplayMetrics().density + 0.5f);
  }

  private static GradientDrawable rounded(int color, int radius, int stroke, int strokeColor) {
    GradientDrawable background = new GradientDrawable();
    background.setColor(color);
    background.setCornerRadius(radius);
    if (stroke > 0) background.setStroke(stroke, strokeColor);
    return background;
  }

  private static TextView text(Activity activity, String label, int sp, int color, boolean bold) {
    TextView view = new TextView(activity);
    view.setText(label);
    view.setTextSize(sp);
    view.setTextColor(color);
    view.setGravity(Gravity.CENTER_VERTICAL);
    if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
    view.setIncludeFontPadding(false);
    return view;
  }

  private static View preview(Activity activity, String id) {
    boolean porcelain = UiThemePreference.PORCELAIN.equals(id);
    boolean claude = UiThemePreference.CLAUDE.equals(id);
    int main = activity.getColor(claude ? R.color.ym_claude_primary
        : porcelain ? R.color.ym_porcelain_primary : R.color.ym_paper_primary);
    int surface = activity.getColor(claude ? R.color.ym_claude_surface
        : porcelain ? R.color.ym_porcelain_surface : R.color.ym_paper_surface);
    int raised = activity.getColor(claude ? R.color.ym_claude_raised
        : porcelain ? R.color.ym_porcelain_raised : R.color.ym_paper_raised);
    int card = activity.getColor(claude ? R.color.ym_claude_card
        : porcelain ? R.color.ym_porcelain_card : R.color.ym_paper_card);
    LinearLayout mock = new LinearLayout(activity);
    mock.setOrientation(LinearLayout.VERTICAL);
    mock.setPadding(dp(activity, 10), dp(activity, 10), dp(activity, 10), dp(activity, 10));
    mock.setBackground(rounded(surface, dp(activity, 14), 0, 0));
    LinearLayout line = new LinearLayout(activity);
    line.setGravity(Gravity.CENTER_VERTICAL);
    View dot = new View(activity);
    dot.setBackground(rounded(main, dp(activity, 8), 0, 0));
    line.addView(dot, new LinearLayout.LayoutParams(dp(activity, 15), dp(activity, 15)));
    TextView title = text(activity, "ymdsh", 12, main, true);
    LinearLayout.LayoutParams titleParams = new LinearLayout.LayoutParams(0, dp(activity, 20), 1);
    titleParams.leftMargin = dp(activity, 6);
    line.addView(title, titleParams);
    mock.addView(line);
    View content = new View(activity);
    content.setBackground(rounded(card, dp(activity, 9), 0, 0));
    LinearLayout.LayoutParams cardParams = new LinearLayout.LayoutParams(-1, dp(activity, 35));
    cardParams.topMargin = dp(activity, 8);
    mock.addView(content, cardParams);
    View action = new View(activity);
    action.setBackground(rounded(raised, dp(activity, 7), 0, 0));
    LinearLayout.LayoutParams actionParams = new LinearLayout.LayoutParams(dp(activity, 85), dp(activity, 10));
    actionParams.topMargin = dp(activity, 8);
    mock.addView(action, actionParams);
    return mock;
  }

  private static void addChoice(Activity activity, LinearLayout list, String id,
      String name, String description, AlertDialog[] dialog) {
    boolean checked = id.equals(ThemeController.preference(activity));
    boolean porcelain = UiThemePreference.PORCELAIN.equals(id);
    boolean claude = UiThemePreference.CLAUDE.equals(id);
    int border = activity.getColor(claude ? R.color.ym_claude_line
        : porcelain ? R.color.ym_porcelain_line : R.color.ym_paper_line);
    int accent = activity.getColor(claude ? R.color.ym_claude_primary
        : porcelain ? R.color.ym_porcelain_primary : R.color.ym_paper_primary);
    int card = activity.getColor(claude ? R.color.ym_claude_card
        : porcelain ? R.color.ym_porcelain_card : R.color.ym_paper_card);
    int muted = activity.getColor(claude ? R.color.ym_claude_muted
        : porcelain ? R.color.ym_porcelain_muted : R.color.ym_paper_muted);
    LinearLayout choice = new LinearLayout(activity);
    choice.setOrientation(LinearLayout.VERTICAL);
    choice.setPadding(dp(activity, 14), dp(activity, 12), dp(activity, 14), dp(activity, 12));
    choice.setBackground(rounded(card, dp(activity, 20), dp(activity, checked ? 2 : 1),
        checked ? accent : border));
    choice.setFocusable(true);
    choice.setClickable(true);
    choice.setContentDescription(name + (checked ? UiText.choose("，已选中", ", selected") : ""));
    LinearLayout header = new LinearLayout(activity);
    header.setGravity(Gravity.CENTER_VERTICAL);
    TextView heading = text(activity, name, 17, accent, true);
    header.addView(heading, new LinearLayout.LayoutParams(0, dp(activity, 30), 1));
    TextView marker = text(activity, checked ? "✓" : "○", 21, accent, true);
    header.addView(marker);
    choice.addView(header);
    TextView subtitle = text(activity, description, 12, muted, false);
    LinearLayout.LayoutParams subtitleParams = new LinearLayout.LayoutParams(-1, -2);
    subtitleParams.bottomMargin = dp(activity, 11);
    choice.addView(subtitle, subtitleParams);
    choice.addView(preview(activity, id), new LinearLayout.LayoutParams(-1, -2));
    LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
    params.bottomMargin = dp(activity, 12);
    list.addView(choice, params);
    choice.setOnClickListener(v -> {
      dialog[0].dismiss();
      if (!id.equals(ThemeController.preference(activity))) {
        ThemeController.select(activity, id);
        activity.recreate();
      }
    });
  }

  public static void show(Activity activity) {
    ScrollView scroll = new ScrollView(activity);
    scroll.setFillViewport(false);
    LinearLayout list = new LinearLayout(activity);
    list.setOrientation(LinearLayout.VERTICAL);
    list.setPadding(dp(activity, 16), dp(activity, 6), dp(activity, 16), dp(activity, 3));
    scroll.addView(list);
    AlertDialog[] dialog = new AlertDialog[1];
    addChoice(activity, list, UiThemePreference.PAPER,
        UiText.choose("素纸 · Paper", "Paper"),
        UiText.choose("微暖的白，像一本干净的笔记。", "Warm whites and quiet graphite."),
        dialog);
    addChoice(activity, list, UiThemePreference.PORCELAIN,
        UiText.choose("瓷白 · Porcelain", "Porcelain"),
        UiText.choose("透亮的白，带一点冷蓝光泽。", "Clear whites with a porcelain-blue accent."),
        dialog);
    addChoice(activity, list, UiThemePreference.CLAUDE,
        UiText.choose("暖杏 · Claude", "Claude"),
        UiText.choose("奶油白与赤陶色，安静而温暖。", "Cream-white surfaces with terracotta accents."),
        dialog);
    dialog[0] = new DshaDialogBuilder(activity)
        .setTitle(UiText.choose("选择外观", "Appearance"))
        .setView(scroll)
        .setNegativeButton(UiText.choose("关闭", "Close"), null)
        .create();
    dialog[0].show();
  }
}
