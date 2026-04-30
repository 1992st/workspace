---
name: lumi_file_manager
version: 1
format: markdown+frontmatter
owner: lumi-writer
last_reviewed: 2026-04-14
---

# Lumi File Manager Config

本配置用于文档路径规范与自然语言查询。

## Rules

- 路径主键：先 `doc_type` 后 `platform`
- 生命周期层级：`working` / `publish`
- 查询策略：返回目标路径，不自动创建目录

## RoutingSpec

```json
{
  "root_dir": "docs",
  "taxonomy_order": ["doc_type", "platform"],
  "stages": ["working", "publish"],
  "defaults": {
    "doc_type": "prd",
    "platform": "internal",
    "platform_by_type": {
      "wechat": "wechat",
      "xiaohongshu": "xiaohongshu",
      "code-doc": "internal",
      "prd": "internal"
    }
  },
  "supported": {
    "doc_types": ["wechat", "xiaohongshu", "code-doc", "prd"],
    "platforms": ["wechat", "xiaohongshu", "internal"]
  },
  "aliases": {
    "doc_type": {
      "wechat": ["wechat", "公众号", "公号", "微信文章"],
      "xiaohongshu": ["xiaohongshu", "小红书", "红薯", "种草文"],
      "code-doc": ["code-doc", "技术文档", "接口文档", "api文档", "开发文档"],
      "prd": ["prd", "需求文档", "产品文档", "产品需求"]
    },
    "platform": {
      "wechat": ["wechat", "公众号", "公号", "微信"],
      "xiaohongshu": ["xiaohongshu", "小红书", "红薯"],
      "internal": ["internal", "内部", "团队", "公司内"]
    }
  },
  "routes": {
    "wechat": {
      "wechat": "docs/{doc_type}/{platform}",
      "internal": "docs/{doc_type}/{platform}"
    },
    "xiaohongshu": {
      "xiaohongshu": "docs/{doc_type}/{platform}",
      "internal": "docs/{doc_type}/{platform}"
    },
    "code-doc": {
      "internal": "docs/{doc_type}/{platform}"
    },
    "prd": {
      "internal": "docs/{doc_type}/{platform}"
    }
  }
}
```
