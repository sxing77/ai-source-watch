#!/usr/bin/env python3
"""
将监控报告转换为 JSON 格式，供前端面板使用。
"""

import json
import sqlite3
import os
from datetime import datetime


def generate_json(output_path: str = "/var/www/freelance-calc/ai-watch/data/latest.json"):
    # 获取所有记录
    conn = sqlite3.connect("data/seen.sqlite")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT source, external_id, name, url, description, category, 
               published_at, discovered_at
        FROM seen_items
        ORDER BY discovered_at DESC
    """)
    
    items = []
    for row in cursor.fetchall():
        items.append({
            "source": row["source"],
            "external_id": row["external_id"],
            "name": row["name"],
            "url": row["url"],
            "description": row["description"] or "",
            "category": row["category"] or "",
            "published_at": row["published_at"] or "",
            "discovered_at": row["discovered_at"] or "",
            "is_new": False  # 基线数据不算新增
        })
    
    conn.close()
    
    data = {
        "generated_at": datetime.now().isoformat(),
        "total_count": len(items),
        "new_count": 0,
        "items": items,
        "warnings": []
    }
    
    # 写入 JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"JSON 数据已生成: {output_path}")
    print(f"总计: {len(items)} 条记录")


if __name__ == "__main__":
    generate_json()
