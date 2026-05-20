# Gateway HTTP API 配置文档

**创建时间**: 2026-03-02
**用途**: 记录 Gateway HTTP API 的配置和使用方法，用于 Agent 唤醒和消息传递

---

## 📋 概述

Gateway HTTP API 允许通过 RESTful 接口与 OpenClaw Gateway 交互，包括：
- 唤醒已停止/中断的 Agent
- 向 Agent 发送消息和指令
- 跨 Agent 通信（需要适当配置）

---

## 🔧 配置

### 1. Gateway 配置文件

**位置**: `/Users/zhangst/.openclaw/openclaw.json`

**必需配置**:
```json5
{
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "loopback",
    "auth": {
      "mode": "token",
      "token": "6026dcc4ffe9663a47656f60f08c0f77561b31a5ca0133a9"
    },
    "http": {
      "endpoints": {
        "responses": {
          "enabled": true
        }
      }
    }
  }
}
```

**关键字段说明**:
- `gateway.port`: Gateway 服务端口（默认 18789）
- `gateway.mode`: 运行模式（"local" 本地, "tunnel" 隧道）
- `gateway.bind`: 绑定地址（"loopback" 仅本机, "0.0.0.0" 监听所有接口）
- `gateway.auth.mode`: 认证模式（"token" 令牌认证）
- `gateway.auth.token`: 认证令牌（用于 Authorization header）
- `gateway.http.endpoints.responses.enabled`: 启用 `/v1/responses` 端点

### 2. 启动/重启 Gateway

配置修改后需要重启 Gateway：

```bash
# 检查 Gateway 状态
openclaw gateway status

# 重启 Gateway
openclaw gateway restart

# 或先停止再启动
openclaw gateway stop
openclaw gateway start
```

**注意**: Gateway 重启是必需的，否则新的配置不会生效。

---

## 📡 API 端点

### `/v1/responses`

向指定 Agent 发送消息或唤醒 Agent。

**方法**: `POST`

**URL**: `http://127.0.0.1:18789/v1/responses`

**Headers**:
```
Authorization: Bearer <token>
Content-Type: application/json
x-openclaw-agent-id: <agent_name>
```

**Header 说明**:
- `Authorization`: Gateway 认证令牌（必须）
- `Content-Type`: 请求内容类型（必须，固定为 `application/json`）
- `x-openclaw-agent-id`: 目标 Agent 名称（必须）

**请求体**:
```json
{
  "model": "openclaw",
  "input": "要发送的消息内容"
}
```

**字段说明**:
- `model`: 模型名称（固定为 `"openclaw"`）
- `input`: 要发送给 Agent 的消息内容

**成功响应**: `HTTP 200 OK`

**失败响应**: `HTTP 4xx/5xx`（带错误信息）

---

## 💡 使用场景

### 1. 唤醒已停止的 Agent

当 Agent 因错误或超时而停止工作时，可以通过 HTTP API 唤醒：

```bash
curl -X POST http://127.0.0.1:18789/v1/responses \
  -H "Authorization: Bearer 6026dcc4ffe9663a47656f60f08c0f77561b31a5ca0133a9" \
  -H "Content-Type: application/json" \
  -H "x-openclaw-agent-id: ffmedia" \
  -d '{
    "model": "openclaw",
    "input": "继续完成 MPP decoder 调试工作"
  }'
```

### 2. 发送新任务给 Agent

向空闲的 Agent 分配新任务：

```bash
curl -X POST http://127.0.0.1:18789/v1/responses \
  -H "Authorization: Bearer 6026dcc4ffe9663a47656f60f08c0f77561b31a5ca0133a9" \
  -H "Content-Type: application/json" \
  -H "x-openclaw-agent-id: agentmesh" \
  -d '{
    "model": "openclaw",
    "input": "分析最新的 AgentMesh 性能瓶颈"
  }'
```

### 3. Stone 监控脚本集成

Stone 可以在监控脚本中集成 HTTP API 调用，自动唤醒偏离的 Agent：

```python
import requests

def wake_up_agent(agent_name, message):
    url = "http://127.0.0.1:18789/v1/responses"
    headers = {
        "Authorization": "Bearer 6026dcc4ffe9663a47656f60f08c0f77561b31a5ca0133a9",
        "Content-Type": "application/json",
        "x-openclaw-agent-id": agent_name
    }
    data = {
        "model": "openclaw",
        "input": message
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 200
```

---

## 🔒 安全注意事项

1. **Token 保护**:
   - Gateway token 是敏感信息，不要泄露
   - 建议使用环境变量存储 token
   - 定期更换 token

2. **网络访问**:
   - 默认配置 `bind: "loopback"` 仅允许本机访问
   - 如果需要远程访问，改为 `bind: "0.0.0.0"`，但需配合防火墙
   - 生产环境建议使用 HTTPS（需要配置反向代理如 Nginx）

3. **Agent 访问控制**:
   - `x-openclaw-agent-id` header 必须是已注册的 Agent 名称
   - 否名无法唤醒不存在的 Agent

---

## 🐛 故障排查

### 问题 1: curl 连接失败

**症状**: `Failed to connect to 127.0.0.1 port 18789`

**原因**: Gateway 未运行

**解决**:
```bash
openclaw gateway status
openclaw gateway start
```

### 问题 2: HTTP 401 Unauthorized

**症状**: `401 Unauthorized`

**原因**: Token 错误或未提供

**解决**:
1. 检查 `openclaw.json` 中的 `gateway.auth.token`
2. 确认 Authorization header 格式正确（`Bearer <token>`）

### 问题 3: HTTP 404 Not Found

**症状**: `404 Not Found`

**原因**: 端点未启用

**解决**:
1. 检查 `openclaw.json` 中是否有 `gateway.http.endpoints.responses.enabled: true`
2. 重启 Gateway：`openclaw gateway restart`

### 问题 4: Agent 未响应

**症状**: HTTP 200 但 Agent 没有反应

**原因**: Agent 名称错误或 Agent 配置问题

**解决**:
1. 确认 Agent 名称正确（大小写敏感）
2. 检查 Agent 是否已注册：`openclaw agents list`
3. 查看 Agent 日志：`tail -f ~/.openclaw/agents/<agent_name>/logs/*.log`

---

## ⏱️ 超时问题

### 问题: curl 请求超时（HTTP_CODE:000）

**症状**: `curl: (28) Operation timed out after 10000 milliseconds`

**原因分析**:
1. **curl 超时设置过短**：默认 `--max-time 10` 秒可能不够
2. **Gateway 处理需要较长时间**：
   - 需要查找目标 Agent（可能不在运行）
   - 可能需要启动新的 Agent 进程
   - 需要验证认证令牌
   - 需要创建新的 session
3. **系统资源或网络延迟**

**解决方案**:

1. **增加 curl 超时时间**：
```bash
curl -X POST http://127.0.0.1:18789/v1/responses \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "x-openclaw-agent-id: <agent_name>" \
  -d '{"model": "openclaw", "input": "消息内容"}' \
  --connect-timeout 10 \
  --max-time 60  # 增加到 60 秒
```

2. **检查 Gateway 状态**：
```bash
openclaw gateway status
```

3. **备选方案**：使用 `sessions_spawn`
```python
# 使用 sessions_spawn 作为备选方案
sessions_spawn(
    task="任务描述",
    label="任务标签",
    runtime="subagent",
    agentId="<agent_name>",
    mode="run"
)
```

### 问题 5: Agent 未响应

### 本地开发环境

```json5
{
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "loopback",
    "auth": {
      "mode": "token",
      "token": "dev-token-123"
    },
    "http": {
      "endpoints": {
        "responses": {
          "enabled": true
        }
      }
    }
  }
}
```

### 生产环境（远程访问）

```json5
{
  "gateway": {
    "port": 18789,
    "mode": "tunnel",
    "bind": "0.0.0.0",
    "auth": {
      "mode": "token",
      "token": "prod-token-abc-xyz"
    },
    "http": {
      "endpoints": {
        "responses": {
          "enabled": true
        }
      }
    }
  }
}
```

**注意**: 生产环境建议配合 Nginx 反向代理提供 HTTPS。

---

## 🔗 相关文档

- OpenClaw Gateway 文档: `~/work/code/moltbot/docs/gateway.md`
- Agent 管理文档: `~/work/code/moltbot/docs/agents.md`
- 配置参考: `~/work/code/moltbot/docs/config.md`

---

## 📝 变更历史

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-03-02 | 1.0 | 初始版本，记录 `/v1/responses` 端点配置和使用方法 |
