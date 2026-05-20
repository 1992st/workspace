# 抖音视频分析工具

自动搜索抖音视频，获取数据，使用 LLM 分析并生成反馈。

## 功能

- ✅ 搜索抖音视频（关键词搜索）
- ✅ 获取视频详细信息
- ✅ LLM 智能分析
- ✅ 生成内容、数据分析和改进建议
- ✅ 自动保存结果
- ✅ 支持批量分析

## 快速开始

### 1. 获取 API Keys

**TikHub API Key**（免费）：
1. 访问 https://tikhub.io
2. 注册账号
3. 每日签到获取免费额度
4. 复制 API Key

**OpenClaw API Token**：
1. 运行 `cat ~/.openclaw/openclaw.json`
2. 复制 `token` 字段的值

### 2. 配置

编辑 `config.yaml`：

```yaml
tikhub:
  api_key: "your_tikhub_api_key_here"  # 替换为你的 TikHub API Key

openclaw:
  api_token: "your_openclaw_token_here"  # 替换为你的 OpenClaw API Token
```

### 3. 运行

```bash
# 使用启动脚本（推荐）
./start.sh

# 或指定关键词
./start.sh 美食

# 或直接运行 Python 脚本
python3 douyin-analyzer.py 美食
```

## 文件说明

- `config.yaml` - 配置文件
- `douyin-analyzer.py` - 主程序
- `start.sh` - 启动脚本
- `requirements.txt` - Python 依赖
- `results.json` - 分析结果（自动生成）
- `analyzer.log` - 日志文件（自动生成）

## 配置说明

### 搜索配置

```yaml
search:
  default_keyword: "热门"  # 默认搜索关键词
  default_count: 10       # 每次搜索返回的视频数
  max_videos: 5           # 每次最多分析的视频数
```

### 分析配置

```yaml
analysis:
  style: "concise"        # 分析风格：concise（简洁）| detailed（详细）
  topics_count: 3         # 生成的话题标签数量
  suggestions_count: 3    # 改进建议数量
```

### 输出配置

```yaml
output:
  save_to_file: true                    # 是否保存到文件
  file_path: "./results.json"           # 保存路径
  send_to_feishu: false                 # 是否发送到飞书群
  feishu_chat_id: "chat:xxx"           # 飞书群 ID
```

## 输出示例

```
【1】超简单！3分钟学会做番茄炒蛋

内容分析：教学类短视频，步骤清晰，适合初学者
数据分析：播放量高，互动好，用户粘性强
改进建议：增加字幕，优化背景音乐，添加慢动作
话题标签：#美食 #家常菜 #简单
```

## 定时任务

每小时自动分析：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（修改路径）
0 * * * * cd /path/to/.pi && ./start.sh 美食
```

## 故障排查

### 问题：搜索返回空列表

**解决方案**：
- 检查 TikHub API Key 是否正确
- 确认 TikHub 账号有足够额度
- 检查关键词是否有效

### 问题：分析失败

**解决方案**：
- 检查 OpenClaw API Token 是否正确
- 确认 OpenClaw Gateway 正在运行
- 检查 `analyzer.log` 日志文件

### 问题：权限错误

**解决方案**：
```bash
chmod +x start.sh
chmod +x douyin-analyzer.py
```

## 技术栈

- Python 3.8+
- httpx - 异步 HTTP 客户端
- pyyaml - YAML 配置解析
- TikHub API - 抖音数据接口
- OpenClaw - LLM 分析

## 许可证

MIT
