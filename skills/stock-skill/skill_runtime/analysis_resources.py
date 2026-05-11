from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


class AnalysisResourceLoader:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.repo_root = root.parents[1]
        self.prompts_dir = root / "resources" / "prompts" / "v1"
        self.knowledge_dir = root / "resources" / "knowledge" / "v1"
        self.strategy_prompt_root = self.repo_root / "prompts"
        self.active_strategy_dir = self.strategy_prompt_root / "current" / "compiled"

    def load_stock_analysis_bundle(self) -> Dict[str, object]:
        prompt_files = [
            "master.md",
            "market-analysis.md",
            "stock-analysis.md",
            "insufficient-data.md",
            "output-style.md",
            "review-framework.md",
        ]
        knowledge_files = [
            "evidence-thresholds.md",
            "short-swing-playbook.md",
            "data-quality-guidelines.md",
        ]
        prompts = self._load_entries(self.prompts_dir, prompt_files)
        knowledge = self._load_entries(self.knowledge_dir, knowledge_files)
        data_requirements_context = self.load_data_requirements_context()
        financial_methodology_context = self.load_financial_methodology_context()
        compiled_prompt = "\n\n".join(
            [f"# {entry['name']}\n{entry['content']}" for entry in prompts]
        )
        compiled_prompt = (
            f"{compiled_prompt}\n\n# dynamic-data-requirements\n"
            f"{data_requirements_context['summary']}\n\n"
            f"# dynamic-financial-methodology\n"
            f"{financial_methodology_context['summary']}"
        )
        strategy_artifacts = self._load_strategy_artifacts()
        return {
            "version": "v1",
            "prompt_modules": prompts,
            "knowledge_entries": knowledge,
            "compiled_prompt": compiled_prompt,
            "evidence_threshold": self._extract_evidence_threshold(knowledge),
            "analysis_requirements": self._build_analysis_requirements(data_requirements_context),
            "data_requirements_context": data_requirements_context,
            "financial_methodology_context": financial_methodology_context,
            "error_case_signals": self._load_error_case_signals(),
            "strategy_artifacts": strategy_artifacts,
        }

    def _load_entries(self, base: Path, names: List[str]) -> List[Dict[str, str]]:
        entries: List[Dict[str, str]] = []
        for name in names:
            path = base / name
            content = path.read_text(encoding="utf-8").strip()
            entries.append(
                {
                    "name": name,
                    "path": str(path),
                    "content": content,
                }
            )
        return entries

    def _extract_evidence_threshold(self, knowledge: List[Dict[str, str]]) -> Dict[str, object]:
        threshold = {
            "minimum_sections_for_trade_plan": [
                "quote",
                "kline",
                "market_snapshot",
                "sector_map",
                "sector_heat",
                "flow_main",
            ],
            "hard_blockers": [
                "quote.get",
                "kline.get",
                "market.snapshot.get",
                "sector.map.get",
            ],
            "guidance": "",
        }
        for entry in knowledge:
            if entry["name"] == "evidence-thresholds.md":
                threshold["guidance"] = entry["content"]
                break
        return threshold

    def _build_analysis_requirements(self, data_requirements_context: Dict[str, Any]) -> Dict[str, object]:
        # Source of truth: references/data_requirements_spec.md
        declared_caps = data_requirements_context.get("confidence_caps", {})
        return {
            "source_path": data_requirements_context.get("source_path"),
            "default_analysis_type": "standard",
            "types": {
                "scan": {
                    "required_sections": ["quote", "kline"],
                    "optional_sections": ["fundamental_valuation", "market_snapshot"],
                    "min_kline_bars": 5,
                    "confidence_cap": int(declared_caps.get("scan", 50)),
                    "fallback_type": "scan",
                },
                "standard": {
                    "required_sections": [
                        "quote",
                        "kline",
                        "market_snapshot",
                        "sector_map",
                        "fundamental_valuation",
                    ],
                    "optional_sections": [
                        "flow_main",
                        "flow_order_size",
                        "news_stock",
                        "news_market",
                    ],
                    "min_kline_bars": 40,
                    "confidence_cap": int(declared_caps.get("standard", 75)),
                    "fallback_type": "scan",
                },
                "deep": {
                    "required_sections": [
                        "quote",
                        "kline",
                        "market_snapshot",
                        "sector_map",
                        "fundamental_valuation",
                        "fundamental_metrics",
                    ],
                    "optional_sections": [
                        "flow_main",
                        "flow_order_size",
                        "news_stock",
                        "news_market",
                    ],
                    "min_kline_bars": 80,
                    "confidence_cap": int(declared_caps.get("deep", 85)),
                    "fallback_type": "standard",
                },
                "review": {
                    "required_sections": ["quote", "kline", "market_snapshot"],
                    "optional_sections": ["sector_map", "flow_main"],
                    "min_kline_bars": 2,
                    "confidence_cap": int(declared_caps.get("review", 65)),
                    "fallback_type": "scan",
                },
            },
        }

    def load_data_requirements_context(self) -> Dict[str, Any]:
        path = self.repo_root / "references" / "data_requirements_spec.md"
        content = path.read_text(encoding="utf-8").strip()
        caps = {
            key: int(value)
            for key, value in re.findall(r"###\s*(快速扫描|标准分析|深度分析|复盘验证).*?置信度上限\**:\s*(?:<\s*)?(\d+)", content, re.DOTALL)
            for key in [self._normalize_analysis_type_label(key)]
        }
        summary_parts = [
            "分析前先识别 Scan/Standard/Deep/Review 类型，再按必须项/建议项检查数据完整度。",
            "必须项缺失时先补数，补不到再降级；不得伪装成原级别完整分析。",
            "输出必须声明分析类型、数据完整度、缺失项和置信度上限。",
            "同一只股票的分析完成后应沉淀到 profile，供后续复用历史关键位和股性。",
        ]
        usage_rules = [
            "Scan 仅用于快速概览，结论强度受限。",
            "Standard 是默认正式分析级别，要求 60 日 K 线、行情、市场、行业、估值齐备。",
            "Deep 用于重大加减仓决策，除标准分析数据外，还应补更长周期和财报/行业对比。",
            "必须项缺失时先补数，补不到再降级，并同步下调置信度上限。",
        ]
        return {
            "source_path": str(path),
            "raw_excerpt": content[:1200],
            "summary": "\n".join(f"- {item}" for item in summary_parts),
            "usage_rules": usage_rules,
            "confidence_caps": caps,
        }

    def load_financial_methodology_context(self) -> Dict[str, Any]:
        path = self.repo_root / "references" / "financial_analysis_resources.md"
        content = path.read_text(encoding="utf-8").strip()
        summary_parts = [
            "财报分析至少同时看三大报表关系：资产负债表看家底，利润表看赚钱能力，现金流量表看真金白银。",
            "核心指标要覆盖盈利能力、成长性、运营效率、偿债能力和估值，不得只看 PE/PB 单一维度。",
            "深度分析时必须检查财务健康度、盈利质量、风险识别和估值判断，避免只凭技术面下重结论。",
            "若经营现金流、扣非增长、偿债能力或财务造假信号明显转弱，应作为强反证进入结论。",
        ]
        usage_rules = [
            "Scan 只在估值或财务异常时辅助引用财报方法，不展开完整财报分析。",
            "Standard 若已有估值和基本财务指标，应参考财报方法摘要做基本面约束。",
            "Deep 若存在 fundamental_metrics，必须至少检查财报健康度、盈利质量、风险信号三个维度。",
            "财报方法只能增强基本面判断，不能替代市场、板块、资金证据。",
        ]
        return {
            "source_path": str(path),
            "raw_excerpt": content[:1600],
            "summary": "\n".join(f"- {item}" for item in summary_parts),
            "usage_rules": usage_rules,
        }

    def _normalize_analysis_type_label(self, label: str) -> str:
        mapping = {
            "快速扫描": "scan",
            "标准分析": "standard",
            "深度分析": "deep",
            "复盘验证": "review",
        }
        return mapping.get(label, label.lower())

    def _load_error_case_signals(self) -> List[Dict[str, str]]:
        case_path = self.repo_root / "references" / "error_cases" / "case_001_601211_recency_bias.md"
        if not case_path.exists():
            return []
        content = case_path.read_text(encoding="utf-8")
        rules = [
            ("recency_bias", "不得仅基于极短时间窗给出中高置信度结论。"),
            ("single_variable_decision", "不得只用量价两个维度替代完整判断。"),
            ("narrative_over_evidence", "不得使用无数字支撑的叙事词替代证据。"),
            ("missing_counter_evidence", "必须列出最强反对证据，再说明为何主结论未被推翻。"),
            ("cross_ticker_framework", "不得直接复用其他股票的量价解释框架。"),
        ]
        return [
            {
                "code": code,
                "summary": summary,
                "source_path": str(case_path),
                "excerpt": self._extract_excerpt(content, summary[:8]),
            }
            for code, summary in rules
        ]

    def _extract_excerpt(self, content: str, hint: str) -> str:
        match = re.search(rf".{{0,60}}{re.escape(hint)}.{{0,80}}", content, re.MULTILINE)
        if match:
            return match.group(0).replace("\n", " ").strip()
        return content[:120].replace("\n", " ").strip()

    def _load_strategy_artifacts(self) -> Dict[str, object]:
        compiled_dir, activation_source = self._resolve_strategy_artifact_dir()
        if compiled_dir is None:
            return {
                "bundle_version": None,
                "compiled_at": None,
                "activation_source": "unavailable",
                "base_prompt": "",
                "catalog": [],
                "conditional_profiles": {},
                "manifest_path": None,
            }

        manifest_path = compiled_dir / "strategy_manifest.json"
        base_prompt_path = compiled_dir / "stock_strategy_base.md"
        catalog_path = compiled_dir / "stock_strategy_catalog.json"
        conditional_path = compiled_dir / "stock_strategy_conditional.json"

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        conditional_profiles = json.loads(conditional_path.read_text(encoding="utf-8"))
        base_prompt = base_prompt_path.read_text(encoding="utf-8").strip()
        return {
            "bundle_version": manifest["bundle_version"],
            "compiled_at": manifest["compiled_at"],
            "activation_source": activation_source,
            "scene": manifest["scene"],
            "source_books": manifest["source_books"],
            "base_prompt": base_prompt,
            "catalog": catalog,
            "conditional_profiles": conditional_profiles,
            "manifest_path": str(manifest_path),
        }

    def _resolve_strategy_artifact_dir(self) -> tuple[Path | None, str]:
        manifest = self.active_strategy_dir / "strategy_manifest.json"
        if manifest.exists():
            return self.active_strategy_dir, "current"
        return None, "unavailable"
