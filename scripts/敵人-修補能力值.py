"""
敵人數值強化腳本 — 方案 D
MHP x1.3, DEF x1.15, MDF x1.15
跳過: null、分隔線、沙包(id=1)、空名佔位條目
params 索引: [0]MHP [1]MMP [2]ATK [3]DEF [4]MAT [5]MDF [6]AGI [7]LUK
"""
import json
from pathlib import Path

ENEMIES_PATH = Path(__file__).resolve().parent.parent / "Consilience" / "data" / "Enemies.json"

HP_MULT = 1.3
DEF_MULT = 1.15
MDF_MULT = 1.15

# 不處理的 ID（沙包）
SKIP_IDS = {1}

def should_skip(enemy: dict) -> bool:
    """跳過分隔線、空名佔位、沙包"""
    if enemy["id"] in SKIP_IDS:
        return True
    name = enemy.get("name", "")
    # 分隔線：name 以 '--' 開頭
    if name.startswith("--"):
        return True
    # 空名佔位條目
    if not name.strip():
        return True
    return False

def main():
    raw = ENEMIES_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)

    changed = 0
    print(f"{'ID':>4} {'名稱':<16} {'原HP':>7} {'新HP':>7} {'原DEF':>5} {'新DEF':>5} {'原MDF':>5} {'新MDF':>5}")
    print("-" * 75)

    for enemy in data:
        if enemy is None:
            continue
        if should_skip(enemy):
            continue

        p = enemy["params"]
        old_hp, old_def, old_mdf = p[0], p[3], p[5]

        p[0] = round(old_hp * HP_MULT)
        p[3] = round(old_def * DEF_MULT)
        p[5] = round(old_mdf * MDF_MULT)

        print(f"{enemy['id']:>4} {enemy['name']:<16} {old_hp:>7} {p[0]:>7} {old_def:>5} {p[3]:>5} {old_mdf:>5} {p[5]:>5}")
        changed += 1

    # 保持 RPG Maker MZ 格式：每個條目一行
    lines = ["["]
    for i, entry in enumerate(data):
        suffix = "," if i < len(data) - 1 else ""
        if entry is None:
            lines.append(f"null{suffix}")
        else:
            lines.append(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + suffix)
    lines.append("]")
    ENEMIES_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n共修改 {changed} 筆敵人資料，已寫入 {ENEMIES_PATH}")

if __name__ == "__main__":
    main()
