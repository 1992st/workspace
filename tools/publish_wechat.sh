#!/bin/bash
#
# Agent 小茶馆 - 微信公众号发布助手
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_FILE="$ROOT_DIR/memory/publish-wechat/state.yaml"
TASKS_DIR="$ROOT_DIR/tasks"
QUEUE_DIR="$ROOT_DIR/publish_queue"

MP_EDITOR_URL="https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=10&lang=zh_CN"
MDNICE_URL="https://editor.mdnice.com/"

ensure_state_file() {
    mkdir -p "$(dirname "$STATE_FILE")"
    if [ ! -f "$STATE_FILE" ]; then
        cat > "$STATE_FILE" << 'YAML'
task_id: ""
status: "NEW"
mdnice:
  doc_id: ""
  url: ""
  last_sync: ""
content:
  title: ""
  author: "Agent小茶馆"
  word_count: 0
  theme: "重影"
draft:
  channel: "browser"
  saved: false
next_action: "idle"
last_error: ""
updated_at: ""
YAML
    fi
}

yaml_get_top() {
    local key="$1"
    grep -E "^${key}:" "$STATE_FILE" | head -1 | sed -E "s/^${key}: //" | sed -E 's/^"(.*)"$/\1/'
}

yaml_get_nested() {
    local key="$1"
    grep -E "^  ${key}:" "$STATE_FILE" | head -1 | sed -E "s/^  ${key}: //" | sed -E 's/^"(.*)"$/\1/'
}

load_state() {
    ensure_state_file

    ST_TASK_ID="$(yaml_get_top task_id)"
    ST_STATUS="$(yaml_get_top status)"
    ST_NEXT_ACTION="$(yaml_get_top next_action)"
    ST_LAST_ERROR="$(yaml_get_top last_error)"
    ST_UPDATED_AT="$(yaml_get_top updated_at)"

    ST_MDNICE_DOC_ID="$(yaml_get_nested doc_id)"
    ST_MDNICE_URL="$(yaml_get_nested url)"
    ST_MDNICE_LAST_SYNC="$(yaml_get_nested last_sync)"

    ST_CONTENT_TITLE="$(yaml_get_nested title)"
    ST_CONTENT_AUTHOR="$(yaml_get_nested author)"
    ST_CONTENT_WORD_COUNT="$(yaml_get_nested word_count)"
    ST_CONTENT_THEME="$(yaml_get_nested theme)"

    ST_DRAFT_CHANNEL="$(yaml_get_nested channel)"
    ST_DRAFT_SAVED="$(yaml_get_nested saved)"

    ST_STATUS="${ST_STATUS:-NEW}"
    ST_NEXT_ACTION="${ST_NEXT_ACTION:-idle}"
    ST_CONTENT_AUTHOR="${ST_CONTENT_AUTHOR:-Agent小茶馆}"
    ST_CONTENT_WORD_COUNT="${ST_CONTENT_WORD_COUNT:-0}"
    ST_CONTENT_THEME="${ST_CONTENT_THEME:-重影}"
    ST_DRAFT_CHANNEL="${ST_DRAFT_CHANNEL:-browser}"
    ST_DRAFT_SAVED="${ST_DRAFT_SAVED:-false}"
}

save_state() {
    local now
    now="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    cat > "$STATE_FILE" << YAML
task_id: "${ST_TASK_ID}"
status: "${ST_STATUS}"
mdnice:
  doc_id: "${ST_MDNICE_DOC_ID}"
  url: "${ST_MDNICE_URL}"
  last_sync: "${ST_MDNICE_LAST_SYNC}"
content:
  title: "${ST_CONTENT_TITLE}"
  author: "${ST_CONTENT_AUTHOR}"
  word_count: ${ST_CONTENT_WORD_COUNT}
  theme: "${ST_CONTENT_THEME}"
draft:
  channel: "${ST_DRAFT_CHANNEL}"
  saved: ${ST_DRAFT_SAVED}
next_action: "${ST_NEXT_ACTION}"
last_error: "${ST_LAST_ERROR}"
updated_at: "${now}"
YAML
}

open_url() {
    local url="$1"
    if command -v open >/dev/null 2>&1; then
        if ! open "$url"; then
            echo -e "${YELLOW}浏览器打开失败，请手动访问:${NC} $url"
        fi
    elif command -v xdg-open >/dev/null 2>&1; then
        if ! xdg-open "$url"; then
            echo -e "${YELLOW}浏览器打开失败，请手动访问:${NC} $url"
        fi
    else
        echo -e "${YELLOW}无法自动打开浏览器，请手动访问:${NC} $url"
    fi
}

generate_task_id() {
    local date_prefix
    local max_idx

    date_prefix="$(date +"%Y-%m-%d")"
    max_idx=0

    while IFS= read -r file; do
        local base idx
        base="$(basename "$file" .md)"
        idx="$(echo "$base" | sed -E 's/^.*-([0-9]{3})$/\1/')"
        if [[ "$idx" =~ ^[0-9]{3}$ ]] && [ "$idx" -gt "$max_idx" ]; then
            max_idx="$idx"
        fi
    done < <(find "$TASKS_DIR" -maxdepth 1 -type f -name "${date_prefix}-*.md" 2>/dev/null || true)

    printf "%s-%03d" "$date_prefix" $((10#$max_idx + 1))
}

ensure_task_file() {
    local task_id="$1"
    local task_file="$TASKS_DIR/${task_id}.md"

    mkdir -p "$TASKS_DIR"
    if [ ! -f "$task_file" ]; then
        cat > "$task_file" << TASK
# 任务记录

## ${task_id}: 微信公众号发布流程任务

### 任务信息
- **task_id**: ${task_id}
- **标题**: 待补充
- **类型**: 公众号文章
- **状态**: SCOPING

### 说明
- 该任务由 publish-wechat 工作流自动创建。
- mdnice 为正文单一来源，后续在同一文档原地修改。
TASK
    fi
}

find_source_file() {
    local task_id="$1"
    local arg_path="$2"

    if [ -n "$arg_path" ] && [ -f "$arg_path" ]; then
        echo "$arg_path"
        return
    fi

    if [ -f "$QUEUE_DIR/$task_id/article.md" ]; then
        echo "$QUEUE_DIR/$task_id/article.md"
        return
    fi

    find "$QUEUE_DIR" -maxdepth 2 -type f -name article.md 2>/dev/null | sort | tail -1
}

extract_title() {
    local file="$1"
    if [ -f "$file" ]; then
        grep -m 1 '^# ' "$file" | sed 's/^# //'
    fi
}

count_words() {
    local file="$1"
    if [ -f "$file" ]; then
        wc -w < "$file" | tr -d ' '
    else
        echo "0"
    fi
}

show_help() {
    cat << EOF
Agent 小茶馆 - 微信公众号发布助手

用法:
  $0 [命令] [参数]

新工作流命令:
  publish [task_id] [article.md]   一键进入公众号发布准备流程（推荐）
  saved [task_id] [word_count]     人工保存草稿后回执，更新状态为 PACKAGED
  resume                           按 state.yaml 恢复上次流程
  status                           查看当前流程状态

兼容命令:
  open                             打开公众号编辑器
  preview <file>                   预览文章
  format <file>                    格式化 Markdown 为公众号友好文本
  help                             显示帮助

示例:
  $0 publish
  $0 publish 2026-04-03-002 publish_queue/2025-04-03-claude-leak/article.md
  $0 saved 2026-04-03-002 1587
  $0 resume
EOF
}

open_editor() {
    echo -e "${GREEN}正在打开公众号编辑器...${NC}"
    echo -e "${YELLOW}请确保已登录微信公众号后台${NC}"
    open_url "$MP_EDITOR_URL"
}

format_article() {
    local file="$1"
    if [ ! -f "$file" ]; then
        echo -e "${RED}错误: 文件不存在: $file${NC}"
        exit 1
    fi

    echo -e "${GREEN}正在格式化文章...${NC}"
    echo ""
    echo "===== 格式化输出 ====="
    echo ""

    local title
    title="$(grep -m 1 '^# ' "$file" | sed 's/^# //')"
    echo "【标题】$title"
    echo ""

    echo "【正文】"
    cat "$file" | sed 's/^# //' | sed 's/^## /▍/' | sed 's/^### /· /' | \
    sed 's/\*\*\([^*]*\)\*\*/<strong>\1<\/strong>/g' | \
    sed 's/\*\([^*]*\)\*/<em>\1<\/em>/g' | \
    sed 's/^- /• /' | \
    sed 's/^[0-9]\+\. /\0 /'

    echo ""
    echo "===== 格式化完成 ====="
    echo ""
    echo -e "${YELLOW}提示: 以上内容可手动复制到公众号编辑器${NC}"
}

preview_article() {
    local file="$1"
    if [ ! -f "$file" ]; then
        echo -e "${RED}错误: 文件不存在: $file${NC}"
        exit 1
    fi

    echo -e "${GREEN}文章预览${NC}"
    echo "===================="
    cat "$file"
    echo ""
    echo "===================="
    echo ""
    echo -e "${YELLOW}下一步: 运行 '$0 publish' 进入发布流程${NC}"
}

publish_flow() {
    load_state

    local input_task_id="$1"
    local source_file

    if [ -n "$input_task_id" ]; then
        ST_TASK_ID="$input_task_id"
    elif [ -n "$ST_TASK_ID" ]; then
        :
    else
        ST_TASK_ID="$(generate_task_id)"
    fi

    ensure_task_file "$ST_TASK_ID"
    mkdir -p "$QUEUE_DIR/$ST_TASK_ID"

    source_file="$(find_source_file "$ST_TASK_ID" "$2")"
    ST_CONTENT_TITLE="$(extract_title "$source_file")"
    ST_CONTENT_WORD_COUNT="$(count_words "$source_file")"

    ST_STATUS="EDITING"
    ST_DRAFT_CHANNEL="browser"
    ST_DRAFT_SAVED="false"
    ST_LAST_ERROR=""
    ST_NEXT_ACTION="manual_copy_to_wechat"

    if [ -z "$ST_MDNICE_URL" ]; then
        ST_MDNICE_URL="$MDNICE_URL"
    fi

    save_state

    echo -e "${GREEN}发布流程已开始${NC}"
    echo "task_id: $ST_TASK_ID"
    echo "source: ${source_file:-未找到本地文章文件}"
    echo "title: ${ST_CONTENT_TITLE:-待在 mdnice 中填写}"
    echo ""

    echo -e "${GREEN}正在打开 mdnice 与公众号编辑器...${NC}"
    open_url "$ST_MDNICE_URL"
    open_url "$MP_EDITOR_URL"

    cat << STEPS

请按以下步骤人工完成：
1. 在 mdnice 文档中编辑并保存（命名: [${ST_TASK_ID}] 标题）
2. 点击“复制到公众号”
3. 切换公众号编辑器粘贴正文
4. 点击“保存为草稿”
5. 完成后运行：
   $0 saved ${ST_TASK_ID} <正文字数>
STEPS
}

mark_saved() {
    load_state

    local input_task_id="$1"
    local input_words="$2"

    if [ -n "$input_task_id" ]; then
        ST_TASK_ID="$input_task_id"
    fi

    if [ -z "$ST_TASK_ID" ]; then
        echo -e "${RED}错误: 缺少 task_id，请先执行 publish${NC}"
        exit 1
    fi

    if [ -n "$input_words" ]; then
        ST_CONTENT_WORD_COUNT="$input_words"
    fi

    if ! [[ "$ST_CONTENT_WORD_COUNT" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}错误: word_count 必须是数字${NC}"
        exit 1
    fi

    if [ "$ST_CONTENT_WORD_COUNT" -le 0 ]; then
        ST_STATUS="NEEDS_INPUT"
        ST_DRAFT_SAVED="false"
        ST_LAST_ERROR="草稿正文为空，请重新粘贴并保存。"
        ST_NEXT_ACTION="repaste_and_save"
        save_state
        echo -e "${RED}草稿正文字数为 0，已标记 NEEDS_INPUT${NC}"
        exit 1
    fi

    ST_STATUS="PACKAGED"
    ST_DRAFT_SAVED="true"
    ST_LAST_ERROR=""
    ST_NEXT_ACTION="wait_publish_command"
    ST_MDNICE_LAST_SYNC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    save_state

    echo -e "${GREEN}已记录草稿保存成功${NC}"
    echo "task_id: $ST_TASK_ID"
    echo "status: $ST_STATUS"
    echo "word_count: $ST_CONTENT_WORD_COUNT"
    echo ""
    echo "发布前请回显：task_id/标题/渠道/受众/风险/时间"
    echo "收到命令 '发布吧 $ST_TASK_ID' 后再执行外发。"
}

resume_flow() {
    load_state

    if [ -z "$ST_TASK_ID" ]; then
        echo -e "${YELLOW}没有可恢复的流程。请先执行 publish。${NC}"
        exit 0
    fi

    echo -e "${GREEN}恢复流程${NC}"
    echo "task_id: $ST_TASK_ID"
    echo "status: $ST_STATUS"
    echo "next_action: $ST_NEXT_ACTION"
    echo ""

    if [ -n "$ST_MDNICE_URL" ]; then
        echo -e "${GREEN}打开 mdnice 文档...${NC}"
        open_url "$ST_MDNICE_URL"
    fi

    if [ "$ST_STATUS" = "EDITING" ] || [ "$ST_STATUS" = "NEEDS_INPUT" ]; then
        open_url "$MP_EDITOR_URL"
        echo "继续完成粘贴并保存草稿，完成后执行: $0 saved $ST_TASK_ID <正文字数>"
    elif [ "$ST_STATUS" = "PACKAGED" ]; then
        echo "草稿已保存，等待发布确认命令。"
    else
        echo "当前状态无需额外恢复动作。"
    fi
}

show_status() {
    load_state
    echo "state_file: $STATE_FILE"
    echo "task_id: $ST_TASK_ID"
    echo "status: $ST_STATUS"
    echo "title: $ST_CONTENT_TITLE"
    echo "word_count: $ST_CONTENT_WORD_COUNT"
    echo "mdnice_url: $ST_MDNICE_URL"
    echo "draft_saved: $ST_DRAFT_SAVED"
    echo "next_action: $ST_NEXT_ACTION"
    echo "last_error: $ST_LAST_ERROR"
    echo "updated_at: $ST_UPDATED_AT"
}

case "${1:-}" in
    publish)
        publish_flow "$2" "$3"
        ;;
    saved)
        mark_saved "$2" "$3"
        ;;
    resume)
        resume_flow
        ;;
    status)
        show_status
        ;;
    open)
        open_editor
        ;;
    format)
        if [ -z "$2" ]; then
            echo -e "${RED}错误: 请指定要格式化的文件${NC}"
            show_help
            exit 1
        fi
        format_article "$2"
        ;;
    preview)
        if [ -z "$2" ]; then
            echo -e "${RED}错误: 请指定要预览的文件${NC}"
            show_help
            exit 1
        fi
        preview_article "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        show_help
        ;;
    *)
        echo -e "${RED}未知命令: $1${NC}"
        show_help
        exit 1
        ;;
esac
