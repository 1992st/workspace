# Pi 项目配置

`.pi/settings.json` 初始内容为 `{}`，不覆盖全局配置。全局目录默认是 `~/.pi/agent`；设置 `PI_CODING_AGENT_DIR` 时以该目录为准。

- 默认 provider、model 和 thinking level 继承全局 `settings.json`。按需在项目配置中设置 `defaultProvider`、`defaultModel`、`defaultThinkingLevel` 才会覆盖对应值。不要为了继承而填入空字符串或 null。
- 模型定义和授权继续使用全局 `models.json`、`auth.json`，不要复制到项目。界面选择的会话模型和已恢复会话仍可使用自己的模型。
- 根目录 `AGENTS.md` 是 Pi 原生读取的项目说明；已有文件不会被 DetachAgent 改写。`AGENTS.override.md` 优先级更高。
- `.pi/skills/detaches-agent/SKILL.md` 是本地 Pi 协作入口，说明群聊、任务和文件交付。已有同名 skill 目录不会自动覆盖或升级；全局同名 skill 可能优先被 Pi 发现，必要时直接读取项目入口。
- `.pi/skills/`、`prompts/`、`extensions/`、`themes/` 可按需放置项目资源。
- `.pi/SYSTEM.md` 会替换系统提示词；`.pi/APPEND_SYSTEM.md` 会优先于全局同名追加提示文件。默认不创建它们。

添加 Agent 只登记当前 workspace。移除登记不会删除这些文件。安装 skill 不等于当前会话已获得 DetachAgent 接口权限。

## win_stock 专用模型（2026-09-30）

使用 pi 原生配置：在 `~/.pi/agent/models.json` 的 `providers.Deepseek` 定义官方 provider，在本工作区 `.pi/settings.json` 中选择 `Deepseek/deepseek-flash`。官方地址为 `https://api.deepseek.com`。全局默认 provider 和已有 ApiFusion 定义保持不变；其他工作区的默认模型不变，但模型列表会新增 Deepseek。

请把 `~/.pi/agent/models.json` 中 `providers.Deepseek.apiKey` 的 `YOUR_DEEPSEEK_API_KEY` 替换为官方密钥。pi 校验要求 apiKey 非空，因此使用占位文本；填入前不能正常调用。无需读取 OpenClaw 凭据。

填写后在此工作区重新启动 pi，创建新会话；如提示信任工作区，需信任才能加载项目默认配置。旧会话可能保留旧模型。避免通过 /model 改全局默认值。

原项目扩展已移到 `.pi/win-stock-deepseek.ts.disabled`，不再自动加载。费用按高峰价格估算，文本输入，输出上限 32768，默认 high 思考等级。
