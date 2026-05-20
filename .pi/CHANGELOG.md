# 抖音分析工具 - 更新记录

## 创建时间

2026-03-08 14:08

## 创建的文件

| 文件名 | 类型 | 说明 |
|--------|------|------|
| `config.yaml` | 配置文件 | 主配置文件（包含 API Keys） |
| `config.yaml.example` | 配置模板 | 配置文件模板（不含敏感信息） |
| `douyin-analyzer.py` | Python 脚本 | 主程序（搜索、分析、生成反馈） |
| `start.sh` | Bash 脚本 | 启动脚本（自动安装依赖） |
| `test-config.py` | Python 脚本 | 配置测试脚本 |
| `requirements.txt` | Python 依赖 | Python 包依赖列表 |
| `README.md` | 文档 | 使用说明文档 |
| `.gitignore` | Git 配置 | Git 忽略文件配置 |

## 功能特性

### 核心功能
1. **搜索抖音视频**
   - 关键词搜索
   - 批量获取视频数据
   - 支持自定义搜索数量

2. **视频数据分析**
   - 标题、描述、作者
   - 播放量、点赞数、评论数
   - 视频元数据

3. **LLM 智能分析**
   - 内容分析（类型、风格、受众）
   - 数据分析（表现、互动率）
   - 改进建议
   - 话题标签生成

4. **结果管理**
   - 自动保存到 JSON 文件
   - 增量追加（不覆盖历史）
   - 日志记录

### 高级特性
- 异步处理（提高性能）
- 批量分析（并行处理多个视频）
- 配置化（灵活调整参数）
- 错误处理（自动重试、异常捕获）
- 日志系统（DEBUG/INFO/WARNING/ERROR）

## 使用方法

### 快速开始

```bash
# 1. 配置 API Keys
# 编辑 config.yaml，填入 TikHub API Key 和 OpenClaw API Token

# 2. 运行
./start.sh 美食

# 或直接运行
python3 douyin-analyzer.py 美食
```

### 配置说明

#### TikHub API Key
- 获取地址：https://tikhub.io
- 免费额度：每日签到
- 功能：搜索抖音视频

#### OpenClaw API Token
- 获取方式：`cat ~/.openclaw/openclaw.json`
- 功能：LLM 智能分析

### 定时任务

```bash
# 添加到 crontab
0 * * * * cd /path/to/.pi && ./start.sh 美食
```

## 配置文件详解

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

### 控制台输出
```
【1】超简单！3分钟学会做番茄炒蛋

内容分析：教学类短视频，步骤清晰，适合初学者
数据分析：播放量高，互动好，用户粘性强
改进建议：增加字幕，优化背景音乐，添加慢动作
话题标签：#美食 #家常菜 #简单
```

### 结果文件 (results.json)
```json
[
  {
    "video": {
      "title": "超简单！3分钟学会做番茄炒蛋",
      "desc": "...",
      "play_count": 100000,
      "like_count": 5000
    },
    "analysis": "内容分析：...\n数据分析：...",
    "timestamp": "2026-03-08T14:08:00"
  }
]
```

## 技术实现

### 技术栈
- Python 3.8+
- httpx - 异步 HTTP 客户端
- pyyaml - YAML 配置解析
- TikHub API - 抖音数据接口
- OpenClaw - LLM 分析

### 核心流程
```
1. 加载配置
   ↓
2. 搜索抖音视频（TikHub API）
   ↓
3. 获取视频详情
   ↓
4. 构建 LLM Prompt
   ↓
5. 调用 OpenClaw 分析
   ↓
6. 保存结果
   ↓
7. 输出报告
```

### 异步处理
- 使用 `asyncio` 实现异步 I/O
- 并行处理多个视频分析
- 提高处理效率

### 错误处理
- HTTP 请求超时处理
- API 调用失败重试
- 配置验证
- 日志记录

## 优化建议

### 性能优化
1. 使用连接池（httpx）
2. 限制并发数（避免 API 限流）
3. 缓存视频数据（避免重复请求）

### 功能扩展
1. 添加飞书群通知
2. 添加数据可视化
3. 添加对比分析
4. 添加趋势分析

### 用户体验
1. 添加进度条
2. 添加彩色输出
3. 添加交互式配置
4. 添加 Web 界面

## 故障排查

### 问题：搜索返回空列表
**解决方案**：
- 检查 TikHub API Key
- 确认 TikHub 账号额度
- 检查关键词有效性

### 问题：分析失败
**解决方案**：
- 检查 OpenClaw API Token
- 确认 OpenClaw Gateway 运行
- 检查日志文件

### 问题：权限错误
**解决方案**：
```bash
chmod +x start.sh
chmod +x douyin-analyzer.py
```

## 安全建议

1. **不要提交 config.yaml 到 Git**
   - 使用 `.gitignore` 忽略敏感文件
   - 使用 `config.yaml.example` 作为模板

2. **定期更新 API Keys**
   - TikHub API Key（定期更换）
   - OpenClaw API Token（定期更换）

3. **限制文件权限**
   ```bash
   chmod 600 config.yaml
   ```

4. **使用环境变量**（可选）
   - 不在配置文件中硬编码 API Keys
   - 使用 `os.getenv()` 读取环境变量

## 版本历史

### v1.0 (2026-03-08 14:08)
- ✅ 初始版本
- ✅ 实现搜索、分析、生成功能
- ✅ 支持配置化
- ✅ 添加日志系统
- ✅ 添加测试脚本

## 待实现功能

- [ ] 飞书群通知
- [ ] 数据可视化
- [ ] Web 界面
- [ ] 定时任务管理
- [ ] 历史数据查询
- [ ] 对比分析
- [ ] 趋势分析

## 联系方式

如有问题或建议，请联系开发者。

---

**创建者**: Stone 🗿
**日期**: 2026-03-08
