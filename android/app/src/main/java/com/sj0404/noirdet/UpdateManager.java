package com.sj0404.noirdet;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Enumeration;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/**
 * Самообновление веб-части игры.
 *
 * Каждый релиз публикует на GitHub ассет noir-det-web.zip (веб-сборка).
 * Приложение сравнивает тег последнего релиза с сохранённой версией и
 * (если есть сеть) скачивает zip в приватное хранилище, распаковывает в
 * versions/&lt;tag&gt; и применяет при следующем запуске. Оффлайн при этом
 * не ломается: без сети запускается встроенная сборка или последняя
 * скачанная — всё локально, ни одного внешнего запроса во время игры.
 */
public final class UpdateManager {

    private static final String TAG = "NoirUpdater";

    private static final String GITHUB_API = "https://api.github.com/repos/sj0404-collab/noir-3d/releases/latest";
    private static final String ASSET_NAME = "noir-det-web.zip";
    private static final String PREFS = "noir_updater";
    private static final String KEY_VERSION = "currentVersion";
    private static final int CONNECT_TIMEOUT_MS = 8000;
    private static final int READ_TIMEOUT_MS = 30000;

    private static final ExecutorService POOL = Executors.newSingleThreadExecutor();
    private static final Handler MAIN = new Handler(Looper.getMainLooper());

    public enum Result { NONE, NEW, ERROR }

    public interface Callback {
        void onResult(Result result, String version);
    }

    private UpdateManager() {}

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    /** Версия установленного APK (baseline: встроенная сборка). */
    private static String installedVersionName(Context ctx) {
        try {
            return ctx.getPackageManager()
                    .getPackageInfo(ctx.getPackageName(), 0)
                    .versionName;
        } catch (Exception e) {
            return "";
        }
    }

    /** Версия, которой реально питается игра (пустая — значит встроенная). */
    public static String currentVersion(Context ctx) {
        return prefs(ctx).getString(KEY_VERSION, "");
    }

    public static File versionsDir(Context ctx) {
        return new File(ctx.getFilesDir(), "versions");
    }

    public static File versionDir(Context ctx, String version) {
        return new File(versionsDir(ctx), version);
    }

    public static boolean isInstalled(Context ctx, String version) {
        File dir = versionDir(ctx, version);
        return dir.isDirectory() && new File(dir, "index.html").isFile();
    }

    /** Запускает проверку обновлений в фоне; результат — в main-потоке. */
    public static void checkForUpdates(Context ctx, Callback cb) {
        final Context app = ctx.getApplicationContext();
        final String baseline = installedVersionName(ctx);
        POOL.execute(() -> {
            Result result = Result.NONE;
            String version = "";
            try {
                Release latest = fetchLatest();
                String last = currentVersion(app);
                if (last == null || last.isEmpty()) last = baseline;
                if (latest == null) {
                    result = Result.NONE;
                } else if (Version.compare(latest.tag, last) > 0 && downloadAndInstall(app, latest)) {
                    result = Result.NEW;
                    version = latest.tag;
                }
            } catch (IOException e) {
                Log.w(TAG, "update check failed (offline?): " + e.getMessage());
                result = Result.ERROR;
            } catch (Exception e) {
                Log.w(TAG, "update failed: " + e.getMessage());
                result = Result.ERROR;
            }
            final Result fr = result;
            final String fv = version;
            MAIN.post(() -> cb.onResult(fr, fv));
        });
    }

    private static Release fetchLatest() throws IOException {
        URL url = new URL(GITHUB_API);
        HttpURLConnection c = (HttpURLConnection) url.openConnection();
        try {
            c.setRequestMethod("GET");
            c.setConnectTimeout(CONNECT_TIMEOUT_MS);
            c.setReadTimeout(READ_TIMEOUT_MS);
            c.setRequestProperty("Accept", "application/vnd.github+json");
            c.setRequestProperty("User-Agent", "noir-det");
            int code = c.getResponseCode();
            if (code != 200) {
                Log.w(TAG, "GitHub API HTTP " + code);
                return null;
            }
            StringBuilder body = new StringBuilder();
            try (InputStream in = new BufferedInputStream(c.getInputStream())) {
                byte[] buf = new byte[8192];
                int n;
                while ((n = in.read(buf)) > 0) body.append(new String(buf, 0, n, "UTF-8"));
            }
            return parseRelease(body.toString());
        } finally {
            c.disconnect();
        }
    }

    private static Release parseRelease(String json) {
        String tag = getString(json, "tag_name");
        if (tag == null) return null;
        String download = null;
        int idx = json.indexOf("\"assets\"");
        if (idx >= 0) {
            int tail = json.indexOf(']', idx);
            if (tail < 0) tail = json.length() - 1;
            String assets = json.substring(idx, tail + 1);
            int pos = 0;
            while ((pos = assets.indexOf("\"name\"", pos)) >= 0) {
                int from = assets.indexOf('"', pos + 7);
                int to = assets.indexOf('"', from + 1);
                String name = assets.substring(from + 1, to);
                if (ASSET_NAME.equals(name)) {
                    int du = assets.indexOf("\"browser_download_url\"", to);
                    int df = assets.indexOf('"', du + 22);
                    int dt = assets.indexOf('"', df + 1);
                    download = assets.substring(df + 1, dt);
                    break;
                }
                pos = to + 1;
            }
        }
        if (download == null) return null;
        return new Release(tag, download);
    }

    private static String getString(String json, String key) {
        int i = json.indexOf("\"" + key + "\"");
        if (i < 0) return null;
        int from = json.indexOf('"', i + key.length() + 2);
        if (from < 0) return null;
        int to = json.indexOf('"', from + 1);
        return json.substring(from + 1, to);
    }

    private static boolean downloadAndInstall(Context ctx, Release release) throws IOException {
        File dir = versionDir(ctx, release.tag);
        if (isInstalled(ctx, release.tag)) { // уже есть
            markVersion(ctx, release.tag);
            return true;
        }
        File zip = new File(ctx.getCacheDir(), "noir-det-web.zip");
        try {
            downloadZip(release.url, zip);
            if (!unzip(zip, dir)) return false;
            if (!new File(dir, "index.html").isFile()) return false;
            markVersion(ctx, release.tag);
            Log.i(TAG, "installed web version " + release.tag + " -> " + dir);
            return true;
        } finally {
            // zip в кэше больше не нужен
            //noinspection ResultOfMethodCallIgnored
            zip.delete();
        }
    }

    private static void markVersion(Context ctx, String tag) {
        prefs(ctx).edit().putString(KEY_VERSION, tag).apply();
    }

    private static void downloadZip(String url, File out) throws IOException {
        URL u = new URL(url);
        HttpURLConnection c = (HttpURLConnection) u.openConnection();
        try {
            c.setInstanceFollowRedirects(true);
            c.setConnectTimeout(CONNECT_TIMEOUT_MS);
            c.setReadTimeout(READ_TIMEOUT_MS);
            c.setRequestProperty("User-Agent", "noir-det");
            int code = c.getResponseCode();
            if (code != 200 && code != 302 && code != 301) {
                throw new IOException("download HTTP " + code);
            }
            try (InputStream in = new BufferedInputStream(c.getInputStream());
                 FileOutputStream fos = new FileOutputStream(out)) {
                byte[] buf = new byte[65536];
                int n;
                while ((n = in.read(buf)) > 0) fos.write(buf, 0, n);
            }
        } finally {
            c.disconnect();
        }
    }

    private static boolean unzip(File zip, File root) throws IOException {
        if (!root.exists() && !root.mkdirs()) return false;
        try (ZipFile zf = new ZipFile(zip)) {
            Enumeration<? extends ZipEntry> entries = zf.entries();
            while (entries.hasMoreElements()) {
                ZipEntry e = entries.nextElement();
                if (e.isDirectory()) {
                    new File(root, e.getName()).mkdirs();
                    continue;
                }
                File target = safePath(root, e.getName());
                if (target == null) {
                    Log.w(TAG, "skip unsafe zip entry: " + e.getName());
                    continue;
                }
                File parent = target.getParentFile();
                if (parent != null && !parent.exists() && !parent.mkdirs()) return false;
                try (InputStream in = new BufferedInputStream(zf.getInputStream(e));
                     FileOutputStream fos = new FileOutputStream(target);
                     BufferedOutputStream bos = new BufferedOutputStream(fos)) {
                    byte[] buf = new byte[65536];
                    int n;
                    while ((n = in.read(buf)) > 0) bos.write(buf, 0, n);
                }
            }
        }
        return true;
    }

    /** Не даёт злому zip уйти выше корня. */
    private static File safePath(File root, String name) {
        File f = new File(root, name);
        String rp;
        String fp;
        try {
            rp = root.getCanonicalPath();
            fp = f.getCanonicalPath();
        } catch (IOException e) {
            return null;
        }
        if (!fp.startsWith(rp + File.separator) && !fp.equals(rp)) return null;
        return f;
    }

    private static final class Release {
        final String tag;
        final String url;

        Release(String tag, String url) {
            this.tag = tag;
            this.url = url;
        }
    }
}