#!/bin/bash
# Stone v5.0 部署脚本

set -e

STONE_WORKSPACE="/Volumes/zhangstExtern/openclaw/workspace/stone"
AGENT_DIR="$HOME/.openclaw/agents/stone"
AGENT_SUBDIR="$AGENT_DIR/agent"

echo "========================================="
echo "🗿 Stone v5.0 部署"
echo "========================================="
echo ""

# 1. 确保目录存在
echo "📁 创建目录结构..."
mkdir -p "$AGENT_DIR"
mkdir -p "$AGENT_SUBDIR"
echo "✅ 目录创建完成"
echo ""

# 2. 复制 AGENTS.md
echo "📋 复制 AGENTS.md..."
cp "$STONE_WORKSPACE/AGENTS.md" "$AGENT_DIR/"
echo "✅ AGENTS.md 已复制"
echo ""

# 3. 确保 agent 子目录配置正确
echo "🔧 检查 agent 配置..."
if [ ! -f "$AGENT_SUBDIR/models.json" ]; then
    echo "❌ 错误: models.json 不存在"
    exit 1
fi
echo "✅ agent 配置文件存在"
echo ""

# 4. 检查核心配置
echo "⚙️ 检查核心配置..."
if [ ! -f "$STONE_WORKSPACE/core/config.js" ]; then
    echo "❌ 错误: core/config.js 不存在"
    exit 1
fi
echo "✅ 核心配置文件存在"
echo ""

# 5. 检查模块
echo "📦 检查模块..."
MODULES=("event-listener.js" "wakeup-manager.js" "result-handler.js" "status-monitor.js")
for module in "${MODULES[@]}"; do
    if [ ! -f "$STONE_WORKSPACE/modules/$module" ]; then
        echo "❌ 错误: modules/$module 不存在"
        exit 1
    fi
done
echo "✅ 所有模块文件存在"
echo ""

# 6. 测试 Node.js 环境
echo "🧪 测试 Node.js 环境..."
if ! command -v node &> /dev/null; then
    echo "❌ 错误: Node.js 未安装"
    exit 1
fi
NODE_VERSION=$(node -v)
echo "✅ Node.js 版本: $NODE_VERSION"
echo ""

# 7. 测试模块导入
echo "🧪 测试模块导入..."
cd "$STONE_WORKSPACE"
if ! node -e "import('./core/index.js').then(() => console.log('✅ 模块导入成功')).catch(e => { console.error('❌ 模块导入失败:', e); process.exit(1); })" 2>/dev/null; then
    echo "❌ 错误: 模块导入测试失败"
    exit 1
fi
echo "✅ 模块导入测试通过"
echo ""

# 8. 部署总结
echo "========================================="
echo "✅ 部署完成"
echo "========================================="
echo ""
echo "📊 部署信息:"
echo "  - 工作区: $STONE_WORKSPACE"
echo "  - Agent 目录: $AGENT_DIR"
echo "  - 配置文件: $AGENT_DIR/AGENTS.md"
echo "  - 模块数量: ${#MODULES[@]}"
echo "  - Node.js: $NODE_VERSION"
echo ""
echo "📋 下一步:"
echo "  1. 配置 OpenClaw cron 任务"
echo "  2. 发送测试消息给 Stone"
echo "  3. 检查 MONITOR-LOG.md 日志"
echo ""
echo "📄 Cron 配置示例:"
echo '  {"cron": {"stone-monitor": {"schedule": "*/30 * * * *", "message": "运行监控", "targetAgent": "stone"}}}'
echo ""
