package com.sj0404.noirdet;

import android.util.Log;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Крошечный локальный http-сервер для скачанной веб-версии игры.
 * Слушает только 127.0.0.1, отдаёт статику из каталога версии.
 * Нужен, потому что встроенные ассеты APK изменить нельзя, а обновлённую
 * сборку игра должна откуда-то взять — из скачанного каталога.
 */
public final class AssetHttpServer {

    private static final String TAG = "NoirHttp";

    private static final Map<String, String> MIME = new HashMap<>();

    static {
        MIME.put(".html", "text/html; charset=utf-8");
        MIME.put(".htm", "text/html; charset=utf-8");
        MIME.put(".js", "text/javascript; charset=utf-8");
        MIME.put(".mjs", "text/javascript; charset=utf-8");
        MIME.put(".css", "text/css; charset=utf-8");
        MIME.put(".json", "application/json");
        MIME.put(".map", "application/json");
        MIME.put(".png", "image/png");
        MIME.put(".jpg", "image/jpeg");
        MIME.put(".jpeg", "image/jpeg");
        MIME.put(".webp", "image/webp");
        MIME.put(".svg", "image/svg+xml");
        MIME.put(".gif", "image/gif");
        MIME.put(".ico", "image/x-icon");
        MIME.put(".glb", "model/gltf-binary");
        MIME.put(".gltf", "model/gltf+json");
        MIME.put(".bin", "application/octet-stream");
        MIME.put(".wasm", "application/wasm");
        MIME.put(".mp4", "video/mp4");
        MIME.put(".webm", "video/webm");
        MIME.put(".ttf", "font/ttf");
        MIME.put(".woff", "font/woff");
        MIME.put(".woff2", "font/woff2");
        MIME.put(".txt", "text/plain; charset=utf-8");
    }

    private final File root;
    private final int port;
    private ExecutorService pool;
    private ServerSocket server;
    private boolean running;

    public AssetHttpServer(File root, int port) {
        this.root = root;
        this.port = port;
    }

    public void start() throws IOException {
        pool = Executors.newFixedThreadPool(4);
        server = new ServerSocket(port, 8, InetAddress.getLoopbackAddress());
        running = true;
        Thread t = new Thread(this::acceptLoop, "noir-http");
        t.setDaemon(true);
        t.start();
        Log.i(TAG, "serving " + root + " on 127.0.0.1:" + port);
    }

    public synchronized void stop() {
        running = false;
        try {
            if (server != null) server.close();
        } catch (IOException ignored) {
        }
        if (pool != null) pool.shutdownNow();
    }

    private void acceptLoop() {
        while (running) {
            try {
                Socket s = server.accept();
                pool.execute(() -> handle(s));
            } catch (IOException e) {
                if (running) Log.w(TAG, "accept: " + e.getMessage());
            }
        }
    }

    private void handle(Socket socket) {
        try (socket) {
            socket.setSoTimeout(15000);
            BufferedInputStream in = new BufferedInputStream(socket.getInputStream());
            OutputStream out = new BufferedOutputStream(socket.getOutputStream());

            String requestLine = readLine(in);
            if (requestLine == null) return;
            String[] parts = requestLine.split(" ");
            if (parts.length < 2 || !"GET".equals(parts[0])) {
                respond(out, 405, "Method Not Allowed", "text/plain; charset=utf-8", null);
                return;
            }
            // остаток заголовков читаем до пустой строки (игнорируем)
            String line;
            while ((line = readLine(in)) != null && !line.isEmpty()) {
            }

            String path = parts[1];
            if (path.contains("?")) path = path.substring(0, path.indexOf('?'));
            path = java.net.URLDecoder.decode(path, StandardCharsets.UTF_8);

            File file = resolve(path);
            if (file == null) {
                respond(out, 404, "Not Found", "text/plain; charset=utf-8", null);
                return;
            }
            serveFile(out, file);
        } catch (Exception e) {
            Log.w(TAG, "conn: " + e.getMessage());
        }
    }

    private File resolve(String path) {
        String name = path.startsWith("/") ? path.substring(1) : path;
        if (name.isEmpty()) name = "index.html";
        if (name.contains("..") || name.startsWith("/") || name.contains("\u0000")) return null;
        File f = new File(root, name);
        try {
            String rp = root.getCanonicalPath();
            String fp = f.getCanonicalPath();
            if (!fp.startsWith(rp + File.separator)) return null;
        } catch (IOException e) {
            return null;
        }
        if (!f.isFile()) return null;
        return f;
    }

    private void serveFile(OutputStream out, File file) throws IOException {
        String mime = MIME.getOrDefault(extension(file), "application/octet-stream");
        long len = file.length();
        StringBuilder head = new StringBuilder();
        head.append("HTTP/1.1 200 OK\r\n");
        head.append("Content-Type: ").append(mime).append("\r\n");
        head.append("Content-Length: ").append(len).append("\r\n");
        head.append("Cache-Control: no-cache\r\n");
        head.append("Connection: close\r\n\r\n");
        out.write(head.toString().getBytes(StandardCharsets.ISO_8859_1));
        try (BufferedInputStream bin = new BufferedInputStream(new FileInputStream(file))) {
            byte[] buf = new byte[65536];
            int n;
            while ((n = bin.read(buf)) > 0) out.write(buf, 0, n);
        }
        out.flush();
    }

    private void respond(OutputStream out, int code, String reason, String mime, byte[] body) throws IOException {
        byte[] b = body != null ? body : reason.getBytes(StandardCharsets.UTF_8);
        StringBuilder head = new StringBuilder();
        head.append("HTTP/1.1 ").append(code).append(' ').append(reason).append("\r\n");
        head.append("Content-Type: ").append(mime).append("\r\n");
        head.append("Content-Length: ").append(b.length).append("\r\n");
        head.append("Connection: close\r\n\r\n");
        out.write(head.toString().getBytes(StandardCharsets.ISO_8859_1));
        out.write(b);
        out.flush();
    }

    private static String extension(File f) {
        String n = f.getName();
        int i = n.lastIndexOf('.');
        return i < 0 ? "" : n.substring(i).toLowerCase();
    }

    private static String readLine(BufferedInputStream in) throws IOException {
        StringBuilder sb = new StringBuilder();
        int c;
        while ((c = in.read()) >= 0) {
            if (c == '\n') return sb.toString().replace("\r", "");
            sb.append((char) c);
            if (sb.length() > 8192) return null;
        }
        return sb.length() == 0 ? null : sb.toString();
    }
}