# -*- coding: utf-8 -*-
"""
生产模式静态服务（替代 Nginx 的轻量方案，零额外依赖）

- 学校版：http://0.0.0.0:8080  -> frontend-school/dist
- 家用版：http://0.0.0.0:8081  -> frontend-home/dist
- /api/* 与 /uploads/* 反代到 127.0.0.1:5000（后端 Flask）
- 支持 SPA 路由（history 模式）：未命中文件一律回 index.html

用法：
  E:\\Program\\gansu-livestock\\backend\\venv\\Scripts\\python.exe scripts\\serve_prod.py school   # 8080
  E:\\Program\\gansu-livestock\\backend\\venv\\Scripts\\python.exe scripts\\serve_prod.py home    # 8081
  E:\\Program\\gansu-livestock\\backend\\venv\\Scripts\\python.exe scripts\\serve_prod.py         # 双服务一起起
"""
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = "http://127.0.0.1:5000"

FRONTS = {
    # 8080 被本机 java.exe 占用（2026-10-10 实测 WinError 10013），学校版改 8082
    "school": (8082, os.path.join(ROOT, "frontend-school", "dist")),
    "home": (8081, os.path.join(ROOT, "frontend-home", "dist")),
}


class ProdHandler(SimpleHTTPRequestHandler):
    """静态文件 + /api 反代 + SPA 回退"""

    def __init__(self, *args, dist_dir=None, **kw):
        self.dist_dir = dist_dir or os.getcwd()
        super().__init__(*args, directory=self.dist_dir, **kw)

    def _is_api(self):
        path = urlsplit(self.path).path
        return path.startswith("/api/") or path.startswith("/uploads/")

    def _proxy(self, method):
        try:
            req = urllib.request.Request(BACKEND + self.path, method=method)
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else None
            if body:
                req.data = body
            for h in ("Content-Type", "Authorization", "Accept"):
                if self.headers.get(h):
                    req.add_header(h, self.headers[h])
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
                self.send_response(resp.status)
                ctype = resp.headers.get("Content-Type", "application/json")
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", e.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            msg = ('{"code":502,"msg":"backend unreachable: %s"}' % str(e)[:60]).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def do_GET(self):
        if self._is_api():
            return self._proxy("GET")
        # SPA：文件不存在回 index.html
        path = urlsplit(self.path).path.lstrip("/")
        if path and not os.path.exists(os.path.join(self.dist_dir, path)):
            self.path = "/index.html"
        super().do_GET()

    def do_HEAD(self):
        if self._is_api():
            return self._proxy("HEAD")
        super().do_HEAD()

    def do_POST(self):
        if self._is_api():
            return self._proxy("POST")
        self.send_error(405)

    def do_PUT(self):
        if self._is_api():
            return self._proxy("PUT")
        self.send_error(405)

    def do_DELETE(self):
        if self._is_api():
            return self._proxy("DELETE")
        self.send_error(405)

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (self.address_string(), fmt % args))


def serve(port, dist_dir):
    handler = lambda *a, **kw: ProdHandler(*a, dist_dir=dist_dir, **kw)
    httpd = ThreadingHTTPServer(("0.0.0.0", port), handler)
    print("serving %s -> http://0.0.0.0:%d" % (dist_dir, port), flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    targets = list(FRONTS.items()) if which == "all" else [(which, FRONTS[which])]
    for name, (port, dist) in targets:
        if not os.path.exists(os.path.join(dist, "index.html")):
            print("dist 不存在，先 npm run build:", dist)
            sys.exit(1)
    threads = [threading.Thread(target=serve, args=(p, d), daemon=True)
               for _, (p, d) in targets]
    for t in threads:
        t.start()
    print("全部就绪，Ctrl+C 停止", flush=True)
    threading.Event().wait()
