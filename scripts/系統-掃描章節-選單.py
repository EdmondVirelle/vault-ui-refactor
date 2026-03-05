#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
輸出章節清單供 Tauri Task Manifest 的 options_source 使用。
輸出格式:
[
  {"label": "第一章", "value": "第一章_劃月風雲.md"},
  ...
]
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    writer_dir = root / "consilience-writer"
    candidates = []
    for md in writer_dir.glob("*.md"):
        name = md.name
        if (
            name.startswith("第")
            and "章" in name
            and name.endswith(".md")
            and "主線任務" not in name
            and "支線任務" not in name
        ):
            label = name.split("_", 1)[0]
            candidates.append({"label": label, "value": name})
    candidates.sort(key=lambda x: x["value"])
    print(json.dumps(candidates, ensure_ascii=False))


if __name__ == "__main__":
    main()
