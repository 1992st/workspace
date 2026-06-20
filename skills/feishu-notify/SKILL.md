---
name: feishu-notify
description: Win_Stock 飞书通知 Skill - 将分析结果、复盘报告、紧急新闻推送到飞书
version: 1.0
---

# 飞书通知 Skill

## 用途
将 Win_Stock 的分析结果、每日复盘、紧急新闻推送到飞书，实现移动端实时接收。

## 配置要求

### 1. 飞书应用配置
需要在飞书开放平台创建企业自建应用：
- 应用类型: 企业自建应用
- 权限: `im:message:send_as_bot`, `im:message.group_as_bot`
- 机器人能力: 启用

### 2. 环境变量
```bash
export FEISHU_APP_ID="cli_xxxxxxxxxxxx"
export FEISHU_APP_SECRET="xxxxxxxxxxxx"
export FEISHU_CHAT_ID="oc_xxxxxxxxxxxx"  # 群聊ID或用户ID
```

### 3. 配置文件
创建 `~/.openclaw/config.yaml`:
```yaml
feishu:
  app_id: ${FEISHU_APP_ID}
  app_secret: ${FEISHU_APP_SECRET}
  default_chat_id: ${FEISHU_CHAT_ID}
```

## 使用方式

### 发送文本消息
```python
from feishu_notify import FeishuNotifier

notifier = FeishuNotifier()
notifier.send_text("国泰海通(601211) 分析完成：BUY，置信度75%")
```

### 发送富文本消息（卡片）
```python
notifier.send_card(
    title="每日复盘报告",
    content="...",
    buttons=[{"text": "查看详情", "url": "..."}]
)
```

### 发送完整 Markdown 报告

早盘和盘后 cron 必须使用这个入口发送完整文档，不能只依赖 OpenClaw cron delivery 的最终摘要。

```bash
python3 skills/feishu-notify/feishu_notify.py send-report \
  --path reviews/daily/YYYY-MM-DD_复盘报告.md \
  --title "YYYY-MM-DD 盘后复盘报告"
```

发送策略：

- 文本分片不超过 3 段：按分片文本发送，便于直接阅读
- 文本分片超过 3 段：自动上传为飞书文件，再发送文件消息，避免刷屏

1. 发送标题卡片
2. 根据长度选择分片文本或文件消息
3. 发送报告绝对路径
4. 在报告同目录写入 `.delivery.json`

测试分片但不真实发送：

```bash
python3 skills/feishu-notify/feishu_notify.py send-report \
  --path reviews/morning/YYYY-MM-DD_早盘分析.md \
  --title "YYYY-MM-DD 早盘分析" \
  --dry-run
```

### 发送紧急新闻
```python
notifier.send_urgent(
    title="【紧急】央行宣布降准",
    content="...",
    stock_codes=["601211", "000001"]
)
```

## 通知场景

1. **每日复盘完成** - 收盘后发送复盘摘要
2. **紧急新闻** - 重大政策/公告即时推送
3. **分析完成** - 个股分析结论推送
4. **做T提醒** - 盘中做T机会提醒（可选）
5. **数据异常** - 数据获取失败告警

## 消息格式

### 分析结果卡片
```
┌─────────────────────────┐
│ 国泰海通(601211) 分析    │
├─────────────────────────┤
│ 操作: BUY               │
│ 置信度: 75%             │
│ 目标价: 18.50 (+11.4%)  │
│ 止损价: 15.80 (-4.8%)   │
├─────────────────────────┤
│ [查看完整报告]           │
└─────────────────────────┘
```

### 复盘摘要
```
┌─────────────────────────┐
│ 2026-04-28 复盘摘要      │
├─────────────────────────┤
│ 预测正确率: 3/4 (75%)   │
│ 做T可行率: 2/3 (66%)    │
│ 最佳标的: 歌尔股份      │
├─────────────────────────┤
│ [查看详细复盘]           │
└─────────────────────────┘
```

## 检查清单

- [ ] 飞书应用已创建并启用机器人
- [ ] 环境变量已配置
- [ ] 应用已添加到目标群聊
- [ ] 权限已开通
- [ ] 测试消息发送成功
