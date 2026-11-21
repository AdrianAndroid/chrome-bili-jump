#!/bin/bash
# 构建 macOS 版「哔哩哔哩」桌面应用
#
# 思路：生成一个标准 .app bundle，图标用自己的，启动脚本 exec 到 Chrome 的
#      应用模式窗口（--app=URL）。窗口没有地址栏和标签栏，看起来就是一个独立应用，
#      同时复用本机 Chrome 的登录态与插件。
#
# 为什么不用 Chrome 的 app_mode_loader：那是 Chrome「安装网页应用」时生成的 bundle，
# Chrome 内部要求该应用已登记在 profile 的应用注册表里，手工拼一个 bundle 会报
# "No suitable profile found" 并退化成普通标签页。
#
# 用法: bash macos/build-app.sh
# 产物: ~/Applications/哔哩哔哩.app
set -euo pipefail

APP_NAME="哔哩哔哩"
# 应用中先打开跳转页：点一次「进入哔哩哔哩」后页面会记住选择，
# 之后每次打开应用都自动跳转。想直接进官网可用 TARGET_URL 覆盖。
TARGET_URL="${TARGET_URL:-https://adrianandroid.github.io/chrome-bili-jump/}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="${APP_PATH:-$HOME/Applications/$APP_NAME.app}"
CHROME_APP="/Applications/Google Chrome.app"

[ -d "$CHROME_APP" ] || { echo "找不到 Chrome: $CHROME_APP"; exit 1; }

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# 1. 图标：icon-1024.png 优先，否则用 Chrome 无头渲染 icon.svg（透明底）
ICON_PNG="$WORK/icon-1024.png"
if [ -f "$SCRIPT_DIR/icon.png" ]; then
  cp "$SCRIPT_DIR/icon.png" "$ICON_PNG"
else
  "$CHROME_APP/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
    --default-background-color=00000000 --force-device-scale-factor=1 \
    --window-size=1024,1024 --screenshot="$ICON_PNG" "file://$SCRIPT_DIR/icon.svg" >/dev/null 2>&1
fi

ICONSET="$WORK/AppIcon.iconset"
mkdir -p "$ICONSET"
for size in 16 32 128 256 512; do
  sips -z $size $size "$ICON_PNG" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  sips -z $((size * 2)) $((size * 2)) "$ICON_PNG" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$WORK/AppIcon.icns"

# 2. bundle 骨架
BUNDLE="$WORK/$APP_NAME.app"
mkdir -p "$BUNDLE/Contents/MacOS" "$BUNDLE/Contents/Resources"
cp "$WORK/AppIcon.icns" "$BUNDLE/Contents/Resources/app.icns"

cat > "$BUNDLE/Contents/MacOS/launcher" <<EOF
#!/bin/bash
CHROME="$CHROME_APP/Contents/MacOS/Google Chrome"
if [ ! -x "\$CHROME" ]; then
  osascript -e 'display alert "未找到 Google Chrome" message "请先安装 Google Chrome。"'
  exit 1
fi
exec "\$CHROME" --app="$TARGET_URL" --no-first-run --no-default-browser-check
EOF
chmod +x "$BUNDLE/Contents/MacOS/launcher"

python3 - "$BUNDLE/Contents/Info.plist" <<'PY'
import plistlib, sys
info = {
    "CFBundleExecutable": "launcher",
    "CFBundleIdentifier": "com.adrianandroid.bilibili.desktop",
    "CFBundleName": "哔哩哔哩",
    "CFBundleDisplayName": "哔哩哔哩",
    "CFBundleIconFile": "app",
    "CFBundlePackageType": "APPL",
    "CFBundleShortVersionString": "1.0",
    "CFBundleVersion": "1",
    "LSMinimumSystemVersion": "12.0",
    "LSApplicationCategoryType": "public.app-category.entertainment",
    "NSHighResolutionCapable": True,
}
with open(sys.argv[1], "wb") as f:
    plistlib.dump(info, f)
PY
plutil -lint "$BUNDLE/Contents/Info.plist" >/dev/null

# 3. 安装（ad-hoc 签名，避免 Gatekeeper 反复校验）
rm -rf "$APP_PATH"
mkdir -p "$(dirname "$APP_PATH")"
cp -R "$BUNDLE" "$APP_PATH"
codesign --force --deep --sign - "$APP_PATH" >/dev/null 2>&1 || true
xattr -dr com.apple.quarantine "$APP_PATH" 2>/dev/null || true

echo "已生成: $APP_PATH"
echo "启动方式: open \"$APP_PATH\"   （也可直接拖进 Dock / 从 Launchpad 打开）"
