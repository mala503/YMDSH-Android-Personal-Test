package com.deepseekharness.app.ui;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;

/** 纯本地关于对话框；不指向上游仓库或非 ymdsh 社群。 */
public final class AboutDialog {

  private AboutDialog() {}

  public static AlertDialog show(Context ctx) {
    String version = "unknown";
    try {
      version = ctx.getPackageManager().getPackageInfo(ctx.getPackageName(), 0).versionName;
    } catch (Exception ignored) {
    }
    android.view.View content =
        android.view.LayoutInflater.from(ctx)
            .inflate(com.deepseekharness.app.R.layout.dialog_about, null);
    ((android.widget.TextView) content.findViewById(com.deepseekharness.app.R.id.about_version))
        .setText(com.deepseekharness.app.util.UiText.format("ymdsh v%s", version));
    AlertDialog dialog = new DshaDialogBuilder(ctx).setView(content).create();
    content
        .findViewById(com.deepseekharness.app.R.id.about_close)
        .setOnClickListener(v -> dialog.dismiss());
    dialog.show();
    return dialog;
  }

  public static void openBrowser(Context ctx, String url) {
    try {
      ctx.startActivity(
          new Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
    } catch (Exception e) {
      Toast.makeText(
              ctx,
              com.deepseekharness.app.util.UiText.format("打不开，请手动访问：%s", url),
              Toast.LENGTH_SHORT)
          .show();
    }
  }

}
