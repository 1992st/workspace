#!/bin/zsh
set -e

DIR="/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-13-001-openclaw-ppt-design"
cd "$DIR"

# 1. 启动本地 HTTP 服务器
python3 -m http.server 8765 > /dev/null 2>&1 &
SERVER_PID=$!
sleep 1

echo "🖥  开始自动截图 (共10页)..."

# 2. JXA 控制 Safari 全屏并截图
osascript <<'EOF'
(function(){
  var safari = Application('Safari');
  safari.includeStandardAdditions = true;
  var se = Application('System Events');
  var base = "http://localhost:8765/";
  var files = [
    "01-cover.html","02-overview.html","03-architecture.html",
    "04-prompt-overview.html","05-inject-assemble.html","06-skills.html",
    "07-memory.html","08-optimizations.html","09-p100-case.html","10-summary.html"
  ];

  for (var i = 0; i < files.length; i++) {
    var url = base + files[i];
    safari.Documents.push({URL: url});
    safari.activate();
    delay(1.2);
    // 进入演示模式 (Cmd+Ctrl+F 在某些浏览器)
    try { se.keystroke('f', {using: ['command down', 'control down']}); } catch(e) {}
    delay(0.8);

    var png = files[i].replace('.html','.png');
    var outPath = "/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-13-001-openclaw-ppt-design/" + png;
    var cmd = "screencapture -x -R0,0,1920,1080 " + outPath;
    doShellScript(cmd);
    console.log("Captured " + png);

    // 退出全屏 (ESC)
    try { se.keyCode(53); } catch(e) {}
    delay(0.4);
  }
})();
EOF

# 3. 关闭服务器
kill $SERVER_PID || true

# 4. 拼成 PPT
echo "📊  生成 PPT..."
python3 build_ppt_from_images.py

echo "✅ 完成：OpenClaw_PPT_Final.pptx"
