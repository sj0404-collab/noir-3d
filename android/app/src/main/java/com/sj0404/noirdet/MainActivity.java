package com.sj0404.noirdet;

import android.os.Bundle;
import android.util.Log;

import com.getcapacitor.BridgeActivity;
import com.getcapacitor.CapConfig;

import java.io.File;

public class MainActivity extends BridgeActivity {

    private static final int UPDATE_PORT = 8097;
    private AssetHttpServer server;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        // Если уже есть скачанная версия игры — кормим её с локального
        // http-сервера. Иначе стартует встроенная сборка из ассетов APK
        // (это и есть оффлайн fallback — встроенные ресурсы всегда на месте).
        String version = UpdateManager.currentVersion(this);
        if (version != null && !version.isEmpty() && UpdateManager.isInstalled(this, version)) {
            File dir = UpdateManager.versionDir(this, version);
            try {
                server = new AssetHttpServer(dir, UPDATE_PORT);
                server.start();
            } catch (Exception e) {
                Log.w("NoirUpdater", "не смог поднять локальный сервер: " + e.getMessage());
                dir = null;
            }
            if (dir != null) {
                this.config = new CapConfig.Builder(this)
                        .setServerUrl("http://127.0.0.1:" + UPDATE_PORT)
                        .create();
            }
        }

        super.onCreate(savedInstanceState);

        // Фоном проверяем обновления. Ошибка сети тут не критична — игра
        // уже запущена и работает со встроенной/скачанной версией.
        UpdateManager.checkForUpdates(this, (result, newVersion) -> {
            if (result == UpdateManager.Result.NEW) {
                Log.i("NoirUpdater",
                        "скачана версия " + newVersion + " — применится при следующем запуске");
            } else if (result == UpdateManager.Result.NONE) {
                Log.i("NoirUpdater", "обновлений нет");
            } else {
                Log.i("NoirUpdater", "сеть недоступна — играем в оффлайн");
            }
        });
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (server != null) server.stop();
    }
}