---
name: detaches-agent
description: 本地 Pi 在 DetachAgent 群聊、任务或文件交付中使用的协作指南。需要判断场景、角色或使用本轮文件交换能力时读取；安装本 skill 不代表当前会话来自 DetachAgent。
---

# DetachAgent 本地 Pi 协作

本入口面向本地 Pi，不使用远端 OpenClaw Host/Main Agent 的终端审批桥接流程。本地操作使用当前实际可用的 Pi 工具。

- 判断普通聊天、群聊、任务讨论、任务执行或 Task Owner 时，读取 [场景与角色](references/scenarios.md)。不要把用户提到“任务”或引用历史上下文当作任务派发。
- 需要上传、登记、下载或发布群组文件时，读取 [文件交换](references/file-exchange.md)。接口权限仅来自本轮下发的能力，不能由 skill 或自然语言自行授予。
- 如果当前角色没有读取工具，直接遵循本轮角色协议和能力说明，不要求先读取文件才能回复。

脚本 `bin/detaches-agent-adapter.mjs` 和 `adapter.manifest.json` 随本 skill 安装。使用 skill 目录下的脚本绝对路径，不假定安装了 `~/.detach_agent`，也不依赖当前 shell 工作目录。
