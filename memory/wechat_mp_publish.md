# 微信公众号发布工作记忆

## 账号信息
- **公众号名称**：Agent 小茶馆
- **类型**：订阅号/服务号（待确认）
- **当前状态**：新号，无历史发布
- **粉丝数**：1

## 后台入口
- 首页：`https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=1317980734`
- 登录方式：已登录，需定期扫码保持会话

## 发布流程

### 1. 新建文章路径
首页 → 新的创作 → 文章（ref=e106）
或直接访问：`https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=10&lang=zh_CN&token=1317980734`

### 2. 内容管理路径
首页 → 内容管理（ref=e20）
管理已发布/草稿文章

### 3. 发表记录
首页 → 近期发表 → 全部发表记录（ref=e160）

## 发布步骤（人工流程）
1. 点击"文章"进入编辑器
2. 填写标题
3. 填写正文（支持富文本）
4. 上传封面图（可选）
5. 设置摘要（可选）
6. 选择分类/话题（可选）
7. 预览检查
8. 点击"发表"

## 注意事项
- 公众号文章需**人工审核确认**才能发布（微信安全机制）
- 我无法直接点击"发表"按钮（需人工最终确认）
- 可以帮生成内容、排版、预览，但发布按钮需人工点

## 快捷入口
- 文章编辑页：`.../appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1`
- 草稿箱：`.../appmsg?t=media/appmsg_list&type=10&action=list`
- 已发表：`.../appmsg?t=media/appmsg_list&type=10&action=list&status=2`

## 工具能力边界
✅ 可以：打开编辑器、填写内容、上传图片、生成预览
❌ 不能：直接点击"发表"按钮（必须人工确认）
