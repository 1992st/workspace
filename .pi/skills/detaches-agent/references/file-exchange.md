# 群组与任务文件交换

仅在本轮实际下发文件交换上下文时使用。普通聊天、任务讨论与 Task Owner 不能假定拥有该能力。

上下文包含 `endpoint`、`token`、`groupId`、`memberId`、`runId`，任务运行还可能有 `taskId`。将本轮 JSON 保存到临时文件作为 `--context`，权限限制为当前用户，结束后删除。不要保存到 AGENTS.md、项目配置或版本库，不输出令牌，不跨运行复用。

## 使用随 skill 安装的脚本

将 `<skill-dir>` 替换为本 SKILL.md 所在目录的绝对路径，`<context-file>` 为本轮临时 JSON。使用支持 Pi 的 Node.js 运行时（Pi 0.84.2 要求 Node.js 22.19+）。无需额外 npm 依赖。

```sh
node <skill-dir>/bin/detaches-agent-adapter.mjs group-file-upload --context <context-file> --file <local-file>
node <skill-dir>/bin/detaches-agent-adapter.mjs group-file-register --context <context-file> --path <files/relative-path>
node <skill-dir>/bin/detaches-agent-adapter.mjs group-file-download --context <context-file> --path <files/relative-path> --output <local-file>
node <skill-dir>/bin/detaches-agent-adapter.mjs group-file-publish --context <context-file> --refs <file-refs.json> --request-id <stable-unique-id> [--members <member-id,...>] [--text <message>]
```

上传或登记返回 `{file}`。把返回的完整 `file` 对象放进 JSON 数组文件，传给 `--refs`，不要自行构造引用。发布返回 `{message}`。下载命令把文件写入 `--output`，检查退出状态和实际返回结果。

## HTTP 接口

路径相对于本轮 `endpoint`；该地址已包含 `/api/agent-group-files`，不要重复添加。鉴权头为 `Authorization: Bearer <token>`。除上传外，POST 使用 JSON。

| 方法与路径 | 输入 | 输出 |
|---|---|---|
| POST /upload | multipart 的 file 字段 | `{file}` |
| POST /register | `{relativePath}`，必须位于群工作区 files/ 下 | `{file}` |
| GET /download?path=... | URL 编码的 files/ 相对路径 | 文件字节流 |
| POST /publish | `{requestId, text?, workspaceFileRefs, targetMemberIds?}` | `{message}` |

## 交付规则

- 上传或登记不会发消息；显式 publish 才发布文件。仅创建文件或回复路径不代表发送。
- 发布不指定成员时只展示文件；指定成员才触发相应成员。重试同一次发布复用同一 requestId。
- 使用服务端返回的引用和本轮提供的群工作区相对路径，不把本地绝对路径当群文件路径。
- 发布成功不代表接收 Agent 已完成。发送失败时明确说明，不虚构已发送或已处理。
- 已通过 publish 触发某成员后，不要在最终回复中再 @ 同一成员重复处理同一文件。
- 令牌只对签发运行有效。无能力、401、任务结束或工作区切换导致失效时，报告原因并等待新的运行上下文，不复用旧令牌或猜测地址。
- 当前脚本还含远端桥接命令；这些命令不是本地 Pi 默认能力，不能因脚本存在就调用远端审批或桌面管理接口。
