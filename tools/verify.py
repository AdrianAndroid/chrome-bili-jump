#!/usr/bin/env python3
"""
chrome-bili-jump 行为验证脚本

复现 README「实验方案」里的四组实验，全部通过 Chrome DevTools Protocol
直接读取运行时数据 / 模拟真实点击，不依赖肉眼观察截图。

依赖:
    python3 -m pip install websocket-client
    Chrome 需安装在 /Applications/Google Chrome.app

用法:
    python3 tools/verify.py

输出四组结果:
    [1] 应用窗口 vs 浏览器标签页的 display-mode 等环境量
    [2] 应用窗口里 target=_blank 是否留在同一窗口
    [3] 站点可安装性（Chrome 的 installability 检查）
    [4] 页面状态机：标签页停留 / 应用窗口自动跳转 / ?stay=1 暂停
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

try:
    import websocket  # websocket-client
except ImportError:
    sys.exit("缺少依赖：python3 -m pip install websocket-client")

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8899
URL = f"http://127.0.0.1:{PORT}/index.html"


class Session:
    """极简 CDP 客户端：一个 Chrome 进程 + 一个页面会话"""

    def __init__(self, tag, args, port=None):
        import socket
        if port is None:
            sk = socket.socket(); sk.bind(("127.0.0.1", 0))
            port = sk.getsockname()[1]; sk.close()
        self.port = port
        self.tmp = tempfile.mkdtemp(prefix=f"bili-verify-{tag}-")
        self.proc = subprocess.Popen(
            [CHROME, f"--remote-debugging-port={port}",
             f"--user-data-dir={self.tmp}", "--no-first-run",
             "--no-default-browser-check"] + args,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        time.sleep(3)
        ver = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version"))
        self.ws = websocket.create_connection(ver["webSocketDebuggerUrl"], timeout=20)
        self._id = 0
        targets = self.send("Target.getTargets")["result"]["targetInfos"]
        page = [t for t in targets if t["type"] == "page"][-1]
        self.target_id = page["targetId"]
        self.sess = self.send("Target.attachToTarget",
                              {"targetId": page["targetId"], "flatten": True})["result"]["sessionId"]
        self.send("Runtime.enable", session=self.sess)
        self.send("Page.enable", session=self.sess)

    def send(self, method, params=None, session=None):
        self._id += 1
        msg = {"id": self._id, "method": method, "params": params or {}}
        if session:
            msg["sessionId"] = session
        self.ws.send(json.dumps(msg))
        while True:
            data = json.loads(self.ws.recv())
            if data.get("id") == self._id:
                return data

    def eval(self, expr):
        res = self.send("Runtime.evaluate",
                        {"expression": expr, "returnByValue": True}, session=self.sess)
        return res.get("result", {}).get("result", {}).get("value")

    def window_id(self, target_id):
        return self.send("Browser.getWindowForTarget",
                         {"targetId": target_id}).get("result", {}).get("windowId")

    def close(self):
        try:
            self.ws.close()
        finally:
            self.proc.terminate()
            time.sleep(1)


ENV_SCRIPT = """JSON.stringify({
  standalone: matchMedia('(display-mode: standalone)').matches,
  minimal: matchMedia('(display-mode: minimal-ui)').matches,
  browser: matchMedia('(display-mode: browser)').matches,
  wcoSupported: !!navigator.windowControlsOverlay,
  wcoVisible: navigator.windowControlsOverlay ? navigator.windowControlsOverlay.visible : null,
  innerH: innerHeight, outerH: outerHeight, gap: outerHeight - innerHeight
})"""


def exp_env():
    print("\n[1] 环境量对比")
    for tag, args in (("tab", [URL]), ("app", ["--app=" + URL])):
        s = Session(tag, args)
        time.sleep(1)
        print(f"  {tag:4s} → {s.eval(ENV_SCRIPT)}")
        s.close()


def exp_blank():
    print("\n[2] 应用窗口里 target=_blank 的落点")
    # 构造同源测试页，避免依赖外网
    tmp = tempfile.mkdtemp(prefix="bili-links-")
    with open(os.path.join(tmp, "a.html"), "w") as f:
        f.write('<meta charset="utf-8"><body style="padding:24px;font:16px sans-serif">'
                '<a id="x" href="b.html" target="_blank">open blank</a></body>')
    with open(os.path.join(tmp, "b.html"), "w") as f:
        f.write('<meta charset="utf-8"><body>b</body>')
    import socket
    sk = socket.socket(); sk.bind(("127.0.0.1", 0)); lp = sk.getsockname()[1]; sk.close()
    srv = subprocess.Popen(["python3", "-m", "http.server", str(lp), "--directory", tmp],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)

    s = Session("blank", [f"--app=http://127.0.0.1:{lp}/a.html"])
    time.sleep(2)
    app_win = s.window_id(s.target_id)
    expr = ("(()=>{const r=document.getElementById('x').getBoundingClientRect();"
            "return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2})})()")
    raw = None
    for _ in range(10):
        raw = s.eval(expr)
        if raw:
            break
        time.sleep(0.5)
    if not raw:
        print("  跳过：测试页未加载完成", s.eval("location.href + '|' + document.readyState"), s.eval("document.body ? document.body.innerHTML.slice(0,60) : 'no-body'"))
        s.close()
        srv.terminate()
        return
    box = json.loads(raw)
    for kind in ("mousePressed", "mouseReleased"):
        s.send("Input.dispatchMouseEvent",
               {"type": kind, "x": box["x"], "y": box["y"], "button": "left", "clickCount": 1},
               session=s.sess)
    time.sleep(2)
    print(f"  应用窗口 id: {app_win}")
    for t in s.send("Target.getTargets")["result"]["targetInfos"]:
        if t["type"] == "page":
            w = s.window_id(t["targetId"])
            print(f"   - {t['url']:32s} 窗口 {w} 同窗口: {w == app_win}")
    s.close()
    srv.terminate()


def exp_installability():
    print("\n[3] 可安装性")
    s = Session("installable", [URL])
    time.sleep(2)
    res = s.send("Page.getInstallabilityErrors", session=s.sess).get("result", {})
    print("  installabilityErrors:", json.dumps(res.get("installabilityErrors"), ensure_ascii=False))
    s.close()


def exp_states():
    print("\n[4] 页面状态机")
    s = Session("states", [URL])
    time.sleep(1.5)
    print("  标签页停留:", bool(s.eval("!document.getElementById('firstRun').hidden")))
    s.close()

    s = Session("states-app", ["--app=" + URL])
    time.sleep(2.5)
    print("  应用窗口跳转后地址:", s.eval("location.hostname"))
    s.close()

    s = Session("states-stay", ["--app=" + URL + "?stay=1"])
    time.sleep(2)
    print("  ?stay=1 停留:", bool(s.eval("!document.getElementById('firstRun').hidden")))
    s.close()


if __name__ == "__main__":
    if not os.path.exists(CHROME):
        sys.exit(f"找不到 Chrome：{CHROME}")
    srv = subprocess.Popen(["python3", "-m", "http.server", str(PORT), "--directory", REPO],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        exp_env()
        exp_blank()
        exp_installability()
        exp_states()
    finally:
        srv.terminate()
    print("\n完成。以上数值应与 README 中记录的一致。")
