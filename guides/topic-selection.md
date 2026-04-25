# Topic Selection Protocol · 选题规范

> 本规范是对 `AGENTS.md` 中 `Topic Refinement Protocol` 的细化与补充。

---

## 选题流程（四层深研）

1. **L1 热点池**：至少 20 条候选，记录来源、时间、一句话事件
2. **L2 证据评分**：按 新颖性 / 可验证性 / 传播性 / 商业相关 四维打分
3. **L3 深度复核**：补反证、边界条件、失败风险与触发条件
4. **L4 成稿决策**：输出 Top 3 选题卡（受众/核心冲突/推荐理由/3 条可执行动作）

---

## 强制展示规则（新增）

**L1 阶段搜索到的所有原始内容，必须完整展示给用户。**

- **目的**：避免模型幻觉、信息截断、来源误判导致选题偏差。
- **执行方式**：
  - 若使用 `web_search`，需将搜索结果的标题/链接/摘要完整列入汇报或文档。
  - 若使用 `browser` 抓取，需把关键页面的 snapshot / 摘要写入文档并给出路径。
  - 不允许在未经回显的情况下直接进入 L2 评分。
- **交付物**：`memory/YYYY-MM-DD.md` 或 `intel/hot/YYYY-MM-DD-*.md` 中须包含 `L1 Raw Feed` 章节。

---

## 选题卡输出标准

每个 L4 选题卡必须包含以下结构化字段：

- `topic_id`
- `score_breakdown`
- `evidence_links`
- `why_now`
- `risks`
- `next_actions`

---

## 引用

- `AGENTS.md#Topic Refinement Protocol`
- `AGENTS.md#Research Domains`
