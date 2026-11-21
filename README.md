# chrome-bili-jump

一个托管在 GitHub Pages 上的**纯静态跳转跳板页**，个人自用；也可以安装成桌面应用（PWA）。

首次打开会停在原地讲清楚用途，并给出「安装到桌面」入口；点一次「进入哔哩哔哩」后记住选择，**之后每次打开直接跳转**到 [bilibili.com](https://www.bilibili.com)。全站不依赖任何第三方库、后端服务或 iframe。

> 线上地址：<https://adrianandroid.github.io/chrome-bili-jump/>

## 页面预览

| 电脑端（1280 × 800） | 手机端（390 × 844） |
| --- | --- |
| ![电脑端预览](docs/preview-desktop.png) | ![手机端预览](docs/preview-mobile.png) |

两张预览图都是用 Chrome DevTools 设备模拟（`Emulation.setDeviceMetricsOverride`）对本地页面直接截的，截的是**首次打开、停在原地的状态**，不是设计稿也不是后期拼图。

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

- **首次打开停在原地，不跳转**：先把用途讲清楚，同时给出安装入口和「进入哔哩哔哩」按钮
- 点一次「进入哔哩哔哩」后，页面用 `localStorage` 记住选择；**之后每次打开直接跳转，不再等倒计时**
- 想恢复停留态：在网址后加 `?stay=1`（会清掉记忆并停在首页）
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
├── docs/
│   ├── preview-desktop.png # README 用的电脑端截图
│   ├── preview-mobile.png  # README 用的手机端截图
│   └── preview-app-window.png # 桌面应用窗口截图
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

### 3. 停留态与直接跳转

页面有两个状态，靠 `localStorage` 里的 `bili-jump:auto` 决定：

```js
var CONFIG = { target: "https://www.bilibili.com", autoKey: "bili-jump:auto" };

// 首次：firstRun 显示说明 + 安装 + 进入按钮，不计时
// 点「进入哔哩哔哩」→ prefSet(true) → location.replace(target)
// 已记住：autoRun 显示「正在前往…」，两帧后立刻 location.replace(target)
```

**首访为什么停住**：安装入口只在这个页面被打开时存在，一自动跳走就永远没机会点安装。所以首屏必须停下来，让人先装、再决定。

**为什么记住后不倒数**：这是跳板页，不是内容页——用户已经表达过「以后都进 B 站」，再多等 5 秒没有收益。所以直接 `location.replace()`。

用两帧（`requestAnimationFrame` × 2）再跳，是为了让「正在前往…」这一帧先画出来，避免整页白屏闪一下；实际耗时约 30ms，肉眼无感。

取消方式：

- 浏览器里访问 `?stay=1` 会清掉记忆并停在首页（启动时解析 `URLSearchParams`，命中就 `prefSet(false)`）；
- 页面上的「取消自动跳转」按钮仍然保留，用于跳转被拦下、页面没走掉的情况。

补充细节：

- 跳转用 `location.replace()` 而不是 `location.href`，浏览器「后退」不会又回到跳转页再跳一次；
- `localStorage` 全部包在 `try/catch` 里，隐私模式或 `file://` 下失败也不会报错；
- 跳转加了 `jumping` 标志位，避免重复触发；
- 跳不出去时（比如网络拦截），页面上留着「没有自动跳转？点这里」的按钮兜底。

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

首次停留在页面、不会自动跳，可以慢慢调样式。测完想回到「已记住」状态，在控制台执行 `localStorage.removeItem('bili-jump:auto')`，或点页面上的「取消自动跳转」。

直接双击 `index.html`（`file://`）也能看页面，但 `file://` 下 Service Worker 不注册、Chrome 不会出现安装入口——**测安装相关行为必须用 `http://localhost` 或 HTTPS**。

注意：点过「进入哔哩哔哩」后本地就会记住选择，下次打开直接跳转；想调试停留态，访问 `?stay=1`，或在控制台清掉 `bili-jump:auto`。

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
| 取消自动跳转 | 网址后加 `?stay=1`，或清掉 localStorage 的 `bili-jump:auto` |
| 是否默认自动跳 | `CONFIG.autoKey` 对应的 localStorage 值；或改 `prefGet()` 的默认返回 |
| 跳转目标 | `CONFIG.target`，以及 `<a href>` 两处链接 |
| 安装按钮文案 | `#installBtn` 文本、`#installNote` 提示 |
| 应用名 / 图标 | `manifest.webmanifest` 的 `name` / `short_name` / `icons`，图标在 `icons/` |
| 主色 | `:root` 里的 `--brand` / `--brand-dark` / `--brand-soft` |
| 卡片宽度 | `.card` 的 `max-width` |
| 说明步骤 | `#firstRun` 里的 `.steps` 列表 |
