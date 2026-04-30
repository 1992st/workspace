---
name: xiaohongshu-ops
description: Use this skill when the user wants Xiaohongshu operations research, topic judgment, low-follower high-like sample analysis, platform-fit checks, method/article synthesis from Xiaohongshu and Toutiao, deep review, or long-term Xiaohongshu knowledge updates without turning the skill into a knowledge store.
---

# xiaohongshu-ops

## Purpose

把“小红书运营研究”做成轻流程系统：

- 一句话触发
- 先研究，再判断
- 先落文档，再沉淀结论
- skill 只管方法，不管存知识正文

## Read First

先读这些单一事实源：

1. `guides/xiaohongshu-ops-spec.md`
2. `guides/xiaohongshu-topic-method.md`
3. `research/xiaohongshu/knowledge/knowledge-canon.md`
4. `research/xiaohongshu/knowledge/error-log.md`

## Entry Style

优先识别运营研究类表达，例如：

- 盘一下这个小红书选题
- 做一轮小红书研究
- 看看小红书平台怎么写这个题
- 跑一轮小红书运营分析
- 拆一下这批小红书爆款

## Workflow

### 1. Decide the run type

先判断这次更像哪一类：

- 选题研究
- 采集归档
- 知识提炼
- 深复盘

### 2. Choose the document target

- 轻量运行：先写 `research/xiaohongshu/analysis/`
- 跨来源深研或形成正式结论：升级为 task 或同步长期知识

### 3. Collect before judging

先收样本，再判断。

不要跳过原始样本直接下结论。

### 4. Use prompts, not rigid scoring

选题判断、知识提炼、错误合并都优先用 prompt 引导。

不要把输出写成机械打分表。

### 5. Update stable docs only when warranted

只有形成稳定结论时，才更新：

- `knowledge-canon.md`
- `error-log.md`

## Tool Rules

- 小红书：主平台样本
- 今日头条：方法文、案例文补充
- 浏览器/网页工具：留摘要、留路径、留日期
- 手机端：补首句、字数、图片数、评论区信息

遇到登录门槛时：

1. 提示用户先登录
2. 继续处理其他可采部分
3. 标记缺口

## Prompt Files

需要时优先复用这些模板：

- `templates/topic-judgment-prompt.md`
- `templates/knowledge-synthesis-prompt.md`
- `templates/document-keypoints-prompt.md`
- `templates/error-merge-prompt.md`

## Short Examples

- “盘一下这个小红书选题，先看平台感，再给能不能做。”
- “整理这批方法文，别逐篇摘要，压成一份知识稿。”
- “这个坑记进错误日志，先看看能不能并入旧条目。”
