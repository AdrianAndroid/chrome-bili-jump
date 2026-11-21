# chrome-bili-jump

一个托管在 GitHub Pages 上的**纯静态跳转跳板页**，个人自用；也可以安装成桌面应用（PWA）。

在浏览器标签页里打开时它不跳转，只说明用途并给出「安装到桌面」入口；**在应用窗口里打开时自动直达** [bilibili.com](https://www.bilibili.com)——靠 `display-mode` 判断，不弹倒计时，也不依赖本地记忆。全站不依赖任何第三方库、后端服务或 iframe。

> 线上地址：<https://adrianandroid.github.io/chrome-bili-jump/>
>
> 当前版本：**v1.0.0**（封版）· [Release 说明](https://github.com/AdrianAndroid/chrome-bili-jump/releases/tag/v1.0.0)

## 页面预览

| 电脑端（1280 × 800） | 手机端（390 × 844） |
| --- | --- |
| ![电脑端预览](docs/preview-desktop.png) | ![手机端预览](docs/preview-mobile.png) |

上面两张都是用 Chrome DevTools 设备模拟（`Emulation.setDeviceMetricsOverride`）对本地页面直接截的，截的是**首次打开、停在原地的状态**，不是设计稿也不是后期拼图。

应用窗口里（用 `--app` 打开、加了 `?stay=1` 让它停在原地）是这样：

![应用窗口内的页面](docs/preview-app-mode.png)

顶部那枚「已作为应用运行 · 本次不跳转」的徽标，就是页面识别出自己跑在应用窗口里的证据。

## macOS 桌面应用版

除了网页跳转，仓库里还带了一个构建脚本，把 B 站装成 macOS 上可以双击打开的「应用」：

![应用窗口](docs/preview-app-window.png)

窗口没有地址栏、没有标签栏，就是一个应用窗口；登录态、插件跟本机 Chrome 共用。

### 为什么不是「Chrome 应用」

Chrome Apps（`.crx` 应用平台）在 2022 年就已经下线，Windows / macOS / Linux 上都不再支持；Chrome 现在唯一的「装成应用」入口是 PWA 安装，而 B 站页面没有 `manifest.json`（不是可安装 PWA），右键菜单里不会出现安装项。

所以这里用的是 **Chrome 的应用模式窗口**（`--app=URL`）：它本来就是给「把某个网站当独立应用打开」用的，只是 Chrome 没给 macOS 提供手动生成 `.app` 的界面。

### 实现

`macos/build-app.sh` 生成一个标准 `.app` bundle：

```
哔哩哔哩.app/
└── Contents/
    ├── Info.plist           # CFBundleExecutable=launcher，图标 app.icns
    ├── MacOS/launcher       # exec Chrome --app=https://www.bilibili.com/
    └── Resources/app.icns   # 由 macos/icon.svg 渲染生成
```

关键点：

- 启动脚本直接 `exec` 到 Chrome，不额外常驻进程，所以关掉窗口就等于退出；
- 不带 `--user-data-dir`，即复用主 Chrome 配置，B 站登录态、插件、代理设置全都沿用，不用重新扫码登录；
- `--no-first-run --no-default-browser-check` 避免首次启动弹引导页；
- 图标用 Chrome 无头模式把 SVG 渲染成 1024 PNG（透明底），再 `sips` + `iconutil` 拼 icns；
- `Info.plist` 用 Python `plistlib` 生成，避免手写 XML 出错；
- ad-hoc 签名 + 去掉 quarantine 属性，本地打开不会被 Gatekeeper 拦。

一个踩过的坑：Chrome「安装网页应用」生成的那种 bundle 用的是 `app_mode_loader` + `CrAppModeShortcutURL`，我照着复刻过一版 —— 手工拼的 bundle 会因为没在 Chrome profile 的应用注册表里而报 `No suitable profile found`，最后退化成普通标签页；签名还必须带 `com.apple.security.cs.disable-library-validation`，否则 ad-hoc 签名的 loader 加载不了 Google 签名的 Chrome Framework。所以最终走的是脚本 + `--app` 这条更直接的路。

### 构建与安装

```bash
cd chrome-bili-jump
bash macos/build-app.sh
open ~/Applications/哔哩哔哩.app
```

装好后从 Launchpad 就能看到「哔哩哔哩」，也可以把它拖进 Dock。

已知取舍：

- 进程实体是 Chrome，所以菜单栏和 Dock 运行态显示的是 Chrome 图标/名称，Launchpad 和 Finder 里显示的是自己的粉色图标；
- 想彻底拥有独立图标和独立身份，需要原生 WKWebView 壳（另一套方案，登录态也要单独维护）。

### 桌面应用 vs 网页跳转页

两者不冲突：桌面应用是「日常打开 B 站」的入口，直接进官网；`index.html` 是浏览器里访问时的兜底跳转页（比如从收藏夹、快捷指令、其他设备点进来）。

## 功能

- **在浏览器标签页里打开时不会跳转**：只说明用途，并给出安装入口和「进入哔哩哔哩」按钮
- **在应用窗口里（`.app` 或已安装的 PWA）自动直接跳转**，靠 `display-mode` 识别，无需任何记忆开关
- 想在应用窗口里临时不跳：网址后加 `?stay=1`
- 可作为 PWA **安装到桌面**（Chrome 地址栏安装图标 / 菜单「安装页面为应用」）
- 手机 / 电脑双端自适应，安全区（刘海屏、手势条）留白；可安装后跑在独立窗口里
- 带完整免责声明，无第三方依赖

## 文件结构

```
chrome-bili-jump/
├── index.html              # 全部页面：HTML + CSS + JS 都在这一个文件里
├── manifest.webmanifest    # PWA 清单（安装入口依赖它）
├── sw.js                   # 极简 Service Worker，只满足安装条件，不缓存不改写
├── icons/                  # 180 / 192 / 512 应用图标
├── macos/
│   ├── build-app.sh        # 一键生成 macOS 桌面应用
│   └── icon.svg            # 应用图标源文件
├── tools/
│   └── verify.py           # 四组 CDP 行为验证脚本（原理/实验方案的复现工具）
├── docs/
│   ├── preview-desktop.png # README 用的电脑端截图
│   ├── preview-mobile.png  # README 用的手机端截图
│   ├── preview-app-mode.png   # 应用窗口内（识别为 standalone、不跳转）
│   └── preview-app-window.png # 桌面应用窗口（已进入 B 站首页）
└── README.md
```

## 安装为桌面应用（PWA）

打开 <https://adrianandroid.github.io/chrome-bili-jump/> 后，Chrome 会在地址栏右侧显示一个安装图标，菜单里也有「保存并分享 → 安装页面为应用」。点它，页面就成了一个独立窗口的应用（有桌面 / 启动器图标，没有地址栏）。

判定条件（页面对应的实现）：

| Chrome 要求 | 本仓库 |
| --- | --- |
| HTTPS | GitHub Pages 自带 |
| `name` / `short_name` | `manifest.webmanifest` 里已写 |
| 192 与 512 图标 | `icons/icon-192.png`、`icons/icon-512.png` |
| `start_url`、`scope` | 都写成相对路径 `./`，所以挂在 `/chrome-bili-jump/` 子路径下也正确 |
| `display` 为 standalone | 已设置，装完是独立窗口 |
| Service Worker（Chrome 112 起已不强制） | 仍加了一个空的 `sw.js`，只为兼容更老的版本 |

**一个必须说清的限制**：装出来的应用，窗口里显示的是这个跳板页；点「进入哔哩哔哩」跳转到 `bilibili.com` 时，由于目标在 PWA 的 scope 之外，Chrome 会把它放到普通浏览器标签页里，独立窗口留在跳板页。跨域页面无法留在应用窗口内（要留只能 iframe，而 B 站禁止被框，本项目也明确不用）。

所以两种用法各有取舍：

- 想「一个独立窗口里一直是 B 站」→ 用 macOS 的 `.app`（Chrome 应用模式，导航不换窗口），见上一节；
- 想「任何电脑点一下就能装上、记录偏好」→ 用 PWA，但每次跳转都会落到浏览器标签页。

## 工作原理

整个项目只做一件事：**同一个页面，在「应用窗口」里就跳 B 站，在「浏览器标签页」里就停住**。判断依据是浏览器给的窗口形态，不是用户偏好、不是倒计时、也不是本地存储。

```
                       ┌───────────────────────────────┐
  GitHub Pages  ──────▶│ index.html（唯一页面）         │
  (main 分支根目录)     │  manifest.webmanifest / sw.js │
                       └───────────────┬───────────────┘
                                       │ 加载即判断
                        matchMedia('(display-mode: standalone/minimal-ui/fullscreen)')
                                       │
              ┌────────────────────────┴─────────────────────────┐
     浏览器标签页（browser）                          应用窗口（standalone）
              │                                                 │
   停在首页：说明 + 安装 + 手动进入                 两帧后 location.replace(bilibili.com)
              │                                                 │
     beforeinstallprompt → 「安装到桌面」                失败则显示「点这里」兜底
              │
     装成 PWA（独立窗口，下次打开即自动跳）
```

三条链路：

1. **网页链路**：Pages 托管静态文件 → Chrome 拉 `index.html` → JS 读窗口形态 → 决定停留还是跳转。全流程零后端、零第三方请求。
2. **安装链路**：Chrome 判定站点可安装（HTTPS + `manifest.webmanifest` + 图标 + `start_url`）→ 派发 `beforeinstallprompt` → 页面接管成自己的按钮 → 用户点击后生成独立窗口的应用。
3. **桌面链路**：`macos/build-app.sh` 生成一个 `.app`，它的可执行文件就是一行 `exec Chrome --app=<Pages 地址>`；所以它同样打开这个页面，同样走上面那套判断。

关键的三个设计决策：

- **不用倒计时**：倒计时只解决「用户想不想跳」，解决不了「这是不是应用窗口」。应用窗口里直接跳，标签页里永远不跳，语义更干净。
- **不用 localStorage 记忆**：PWA 和标签页同源，共用同一份 localStorage；一旦写入「自动跳」的偏好，标签页也会跟着跳，正好违背需求。窗口形态是运行时事实，跨设备、跨浏览器都成立。
- **不用 iframe**：B 站禁止被框，本项目也明确不嵌入任何 B 站内容，只做纯导航。

### 为什么「应用窗口里点 B 站卡片会另开窗口」改不了

Chrome 的 `--app` 窗口没有标签栏，遇到 `target="_blank"` 的链接只能新开一个窗口——这是浏览器的窗口模型决定的，页面侧没有任何 API 能拦住（`window.open` 的 target 由被点击的链接决定，跳转页管不到 B 站自己页面里的链接）。实测见下一节实验 [2]：同一个 `--app` 窗口里点 `target=_blank`，新页面落在**不同 windowId** 上。

要彻底解决只有两条路，都超出本项目边界：一是注入/改写 B 站页面的 DOM（属于明确的红线），二是自己写原生 WKWebView 壳去接管 `_blank`。所以这里接受现状：**首页能留在应用窗口，卡片链接另开窗口**。

## 实验方案与验证

这个项目的每个结论都不是「看着像」，而是用 **Chrome DevTools Protocol（CDP）** 直接读运行时数值验证的：独立 `--user-data-dir` 起一个干净 Chrome，连上 WebSocket，用 `Runtime.evaluate` 读环境量、用 `Input.dispatchMouseEvent` 模拟真实点击、用 `Browser.getWindowForTarget` 取窗口 id、用 `Page.getInstallabilityErrors` 查安装资格。

验证脚本已随仓库提供：`tools/verify.py`（只用 Python 标准库 + `websocket-client`）。

### 四组实验

| # | 想验证什么 | 手段 | 观测量 | 结论 |
| --- | --- | --- | --- | --- |
| 1 | 应用窗口和标签页能否被区分 | 分别用 `--app=URL` 和普通 `URL` 起浏览器，`Runtime.evaluate` 读 `matchMedia` 与高度差 | `display-mode` 三个值、`outerHeight-innerHeight`、`windowControlsOverlay.visible` | 可以，`display-mode` 是可靠判据 |
| 2 | 应用窗口里 `target=_blank` 会不会留在原窗口 | `Input.dispatchMouseEvent` 在 `--app` 窗口里点一个 `target=_blank` 链接（真实点击而非 `element.click()`，后者会被弹窗拦截） | 新旧页面的 `Browser.getWindowForTarget` windowId | 不会，一律新开窗口 |
| 3 | 这个站点到底能不能装成应用 | `Page.getInstallabilityErrors`（Chrome 自己的安装判定） | `installabilityErrors` 数组 | 可以，空数组即无阻断项 |
| 4 | 页面状态机是否符合预期 | 三种打开方式各起一个会话，读 `#firstRun` 是否可见 / 最终 hostname | 标签页是否停留、应用窗口是否跳转、`?stay=1` 是否暂停 | 三者均符合设计 |

### 实测输出（Chrome 157 / macOS / 2026-11）

```
[1] 环境量对比
  tab  → {"standalone":false,"minimal":false,"browser":true,
          "wcoSupported":true,"wcoVisible":false,"innerH":1235,"outerH":1322,"gap":87}
  app  → {"standalone":true,"minimal":false,"browser":false,
          "wcoSupported":true,"wcoVisible":false,"innerH":1294,"outerH":1322,"gap":28}

[2] 应用窗口里 target=_blank 的落点
  应用窗口 id: 2129532731
   - http://127.0.0.1:58381/a.html    窗口 2129532731 同窗口: True
   - http://127.0.0.1:58381/b.html    窗口 2129532734 同窗口: False

[3] 可安装性
  installabilityErrors: []

[4] 页面状态机
  标签页停留: True
  应用窗口跳转后地址: www.bilibili.com
  ?stay=1 停留: True
```

从数据里读出的几条判断：

- `standalone` 与 `browser` 在两个场景里严格互斥，可以直接当主判据；
- `navigator.windowControlsOverlay.visible` 两种模式下都是 `false`，**不可用**（虽然对象存在）；
- 高度差 28 vs 87 也能区分，但会被缩放、全屏、自定义窗口干扰，只作旁证；
- 新窗口的 windowId 不同，说明「另开窗口」是浏览器行为，不是页面能控制的。

### 自己复现

```bash
# 依赖
python3 -m pip install websocket-client

# Chrome 需在 /Applications/Google Chrome.app
python3 tools/verify.py
```

脚本会自己在本地起 `python3 -m http.server` 服务当前目录，每次用独立的临时 profile 和随机端口，不会碰你正在用的 Chrome 配置；跑完把四组数值和上面记录对照即可。

> 排查记录：脚本第一版在实验 [2] 一直拿不到页面元素，原因是调试端口写死（`9403`）被上一次残留的 Chrome 占着，CDP 连上的是旧实例；改成自动挑空闲端口后恢复正常。这类「连到了旧浏览器」是 CDP 自动化最常见的坑。

## 实现思路

### 1. 为什么是单文件

项目定位是「一个跳转页」，部署目标是 GitHub Pages 的静态托管。既然只此一屏内容，把 CSS 和 JS 内联进 `index.html` 有三个直接好处：

- 只有 1 次 HTTP 请求，首屏没有额外的 CSS/JS 往返，跳转页越快越不打扰；
- 分享、备份、改版都只涉及一个文件，不会出现「改了样式忘了改引用」；
- 不需要任何构建工具链，`git push` 即部署。

代价是可维护性弱于拆分多文件，但对这种体量的页面可以接受。

### 2. 布局：单卡片居中

- `body` 用 flex 居中，`min-height: 100dvh` 而不是 `100vh`，避免手机浏览器工具栏导致的「上下露白」；
- 卡片 `max-width: 460px`，配合 `width: 100%`，宽屏时是一张居中小卡，窄屏时自动铺满可用宽度；
- 内边距用 `padding: max(24px, env(safe-area-inset-*))` 处理刘海屏和底部手势条；
- 字体尺寸用 `clamp()`（如 `clamp(19px, 4.6vw, 22px)`），字号随视口平滑变化，不需要为每个断点写一套 media query；
- 数字类文本统一用 `font-variant-numeric: tabular-nums`，宽度不随数值变化抖动。

### 3. 用窗口模式决定要不要自动跳

不再依赖 localStorage 记忆，而是**判断当前是不是应用窗口**：

```js
var isAppWindow =
  matchMedia('(display-mode: standalone)').matches ||
  matchMedia('(display-mode: minimal-ui)').matches ||
  matchMedia('(display-mode: fullscreen)').matches ||
  navigator.standalone === true;

// 应用窗口 → 「正在前往…」一帧后直接 location.replace(target)
// 浏览器标签页 → 停在首页，只提供说明 / 安装 / 手动进入
```

**实测依据（Chrome 157 / macOS，用 CDP 直接读值，不靠肉眼）**

| 检测项 | Chrome 应用模式窗口（`--app=`） | 普通标签页 |
| --- | --- | --- |
| `(display-mode: standalone)` | **true** | false |
| `(display-mode: browser)` | false | **true** |
| `outerHeight - innerHeight` | 28（只有标题栏） | 87（标题栏 + 标签栏 +地址栏） |
| `navigator.windowControlsOverlay.visible` | false | false |

结论：

- `display-mode` 这个媒体查询是可靠信号，两个场景互斥；`windowControlsOverlay.visible` 在两种模式下都是 `false`，**不能用**；高度差虽然也能区分（28 vs 87），但会被缩放、全屏、自定义窗口干扰，只作参考不作主判据。
- 已安装的 PWA 跑起来同样是 `display-mode: standalone`，所以 PWA 窗口和 `.app` 窗口都会被认成「应用窗口」，行为一致。

细节：

- 用两帧（`requestAnimationFrame` × 2）再跳，让「正在前往…」先画出来，避免整页白屏闪；实际约 30ms。
- 跳转用 `location.replace()`，浏览器「后退」不会又回到跳转页再跳一次；`jumping` 标志位防止重复触发。
- 跳不出去时（网络拦截等），页面上留着「没有自动跳转？点这里」兜底。
- 想在应用窗口里临时不跳：地址后加 `?stay=1`，此时即使识别为应用窗口也停在首页。

### 3.5 安装入口（beforeinstallprompt）

Chrome 判定站点可安装后会派发 `beforeinstallprompt`。页面把它拦下来，转成自己的「安装到桌面」按钮：

```js
window.addEventListener("beforeinstallprompt", function (e) {
  e.preventDefault();          // 不弹 Chrome 默认小气泡
  deferredPrompt = e;
  installBtn.classList.add("show");
});
```

点了按钮才调用 `deferredPrompt.prompt()`，再用 `userChoice` 的结果切换文案；`appinstalled` 事件把按钮换成「已安装」。

按钮平时是隐藏的——不满足安装条件（Safari、旧版 Chrome、已经装过）就根本不出现，不会出现一个点了没反应的死按钮。浏览器里 2.5 秒后还没等到该事件，会给一条手动路径的提示（菜单里安装）。

### 4. 视觉

- 主色 `#FB7299` 取自 B 站品牌粉，只作为强调色（图标、数字、按钮），正文仍是深灰，保证对比度；
- 所有颜色收在顶部 `:root` 的 CSS 变量里（`--brand`、`--ink`、`--line`、`--surface`、`--page`），后续换配色只改这几行；
- 背景是两层 `radial-gradient` 叠在浅灰底上，营造一点氛围又不会抢内容；
- 顶部图标是内联 SVG（一个电视机轮廓），不引入图片、不引入第三方图标库；
- 进场用一次 0.6s 的 `translateY + opacity` 动画，并遵守 `prefers-reduced-motion`：系统开了「减弱动态效果」就完全不做动画。

### 5. 免责与合规

页面底部固定一块说明：本页面仅为跳转跳板，不是哔哩哔哩官方产品，不托管任何 B 站内容，不解析视频、不注入脚本、不提供绕过或抓取功能，版权归哔哩哔哩及其权利人所有。

对应地，实现上严格守住几条红线：

- 只用原生 HTML / CSS / JavaScript，没有第三方库或框架；
- 没有 iframe，页面里不存在任何嵌入的 B 站内容；
- 没有任何跨域请求、爬虫、解析、DOM 注入、去广告、会员绕过逻辑；
- 页面里唯一的外链就是 `https://www.bilibili.com`。

## 本地运行

```bash
git clone git@github.com:AdrianAndroid/chrome-bili-jump.git
cd chrome-bili-jump
python3 -m http.server 8080
# 浏览器打开 http://localhost:8080
```

`file://` 下 `display-mode` 一直是 `browser`，所以页面永远停在首页，方便慢慢调样式。

直接双击 `index.html`（`file://`）也能看页面，但 `file://` 下 Service Worker 不注册、Chrome 不会出现安装入口——**测安装相关行为必须用 `http://localhost` 或 HTTPS**。

注意：用 `file://` 打开时 `display-mode` 是 `browser`，所以永远停在首页，适合调样式；要验证自动跳转，用 `--app=http://localhost:8080/` 启动 Chrome，或直接装成 PWA 后打开。

## 部署（GitHub Pages）

仓库是公开的，使用 Pages 的「分支 + 根目录」模式，发布源为 `main` 分支的 `/`，所以只需要 `index.html` 在仓库根目录，无需 CI / Actions。

如果换新仓库要重新配置，在仓库 **Settings → Pages** 里选择：

- Source: `Deploy from a branch`
- Branch: `main`，目录 `/ (root)`
- 保存后等待 1~2 分钟，访问 `https://<用户名>.github.io/<仓库名>/`

<details>
<summary>用命令行（GitHub API）配置 Pages</summary>

```bash
# 需要一枚具备 repo 权限的 token
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/AdrianAndroid/chrome-bili-jump/pages \
  -d '{"source":{"branch":"main","path":"/"}}'

# 查部署状态
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/AdrianAndroid/chrome-bili-jump/pages
```

</details>

## 日常改版流程

```bash
cd chrome-bili-jump
# 改 index.html / manifest.webmanifest / sw.js
git add -A
git commit -m "feat: 调整跳转逻辑"
git push origin main
```

推送后 Pages 会自动重新构建，通常 30 秒 ~ 2 分钟生效，可强刷（`Cmd + Shift + R`）确认。

注意：装过的 PWA 有缓存版本，改完 manifest 或页面后如果没变化，先在 Chrome 里「卸载」再重新安装。

## 可调参数

| 想改什么 | 改哪里 |
| --- | --- |
| 应用窗口里临时不跳 | 网址后加 `?stay=1` |
| 自动跳转的判定条件 | `isAppWindow` 里那几条 `matchMedia` 判断 |
| 跳转目标 | `CONFIG.target`，以及 `<a href>` 两处链接 |
| 安装按钮文案 | `#installBtn` 文本、`#installNote` 提示 |
| 应用名 / 图标 | `manifest.webmanifest` 的 `name` / `short_name` / `icons`，图标在 `icons/` |
| 主色 | `:root` 里的 `--brand` / `--brand-dark` / `--brand-soft` |
| 卡片宽度 | `.card` 的 `max-width` |
| 说明步骤 | `#firstRun` 里的 `.steps` 列表 |
