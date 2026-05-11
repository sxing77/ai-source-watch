from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .items import WatchItem


def write_report(
    items: list[WatchItem],
    warnings: list[str],
    output_path: Path,
    report_format: str = "markdown",
    title: str = "AI 新品监控报告",
) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if report_format == "json":
        body = _json_report(items, warnings, title)
    else:
        body = _markdown_report(items, warnings, title)
    output_path.write_text(body, encoding="utf-8")
    return body


def _json_report(items: list[WatchItem], warnings: list[str], title: str) -> str:
    payload = {
        "title": title,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "count": len(items),
        "warnings": warnings,
        "items": [
            {
                "source": item.source,
                "name": item.name,
                "url": item.url,
                "description": item.description,
                "category": item.category,
                "published_at": item.published_at,
                "discovered_at": item.discovered_at,
            }
            for item in items
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _markdown_report(items: list[WatchItem], warnings: list[str], title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- 新增数量：{len(items)}",
    ]

    if warnings:
        lines.extend(["", "## 注意"])
        lines.extend(f"- {warning}" for warning in warnings)

    if not items:
        lines.extend(["", "NO_NEW_ITEMS"])
        return "\n".join(lines).rstrip() + "\n"

    grouped: dict[str, list[WatchItem]] = defaultdict(list)
    for item in items:
        grouped[item.source].append(item)

    labels = {
        "replicate": "Replicate 新模型",
        "toolify": "Toolify 新 AI 工具",
    }
    for source, source_items in grouped.items():
        lines.extend(["", f"## {labels.get(source, source)}"])
        for item in source_items:
            lines.append(f"- [{item.name}]({item.url})")
            if item.description:
                lines.append(f"  - 简介：{item.description}")
            if item.published_at:
                lines.append(f"  - 发布时间：{item.published_at}")
            lines.append(f"  - 发现时间：{item.discovered_at}")

    return "\n".join(lines).rstrip() + "\n"

