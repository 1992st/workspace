# lumi_file_manager

`lumi_file_manager` 用于统一文档路径治理，支持自然语言查询新文档存放位置。

## 核心约束

- 路径结构：`docs/<doc_type>/<platform>/<stage>/`
- `stage` 固定：`working`、`publish`
- 不自动创建目录，仅返回路径

## 与 doc-beautify 的联动

`doc-beautify` 在处理文档前应先调用 `lumi_file_manager`：

1. 校验输入路径是否合规（`validate_path`）
2. 新稿定位推荐路径（`locate_new_doc`）
3. 再按 `rules_profile_path` 加载美化规则
