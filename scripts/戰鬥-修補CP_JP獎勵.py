"""
patch_cp_jp.py — 為所有敵人設定平衡的 CP / JP 獎勵
============================================================
公式設計:
  - 普通敵人: JP = round(EXP × 0.4),  CP = round(EXP × 0.04)
  - BOSS 敵人: JP = round(EXP × 0.5),  CP = round(EXP × 0.05)
  - 最低值:    JP ≥ 15 (普通) / 50 (BOSS),  CP ≥ 1 (普通) / 5 (BOSS)

設計理念:
  - 弱敵（序章 EXP 25）→ JP 15, CP 1（比預設 50-99 低，但更合理）
  - 中敵（第三章 EXP 200）→ JP 80, CP 8
  - 強敵（第八章 EXP 750）→ JP 300, CP 30
  - BOSS（最終 EXP 3000）→ JP 1500, CP 150
"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "Consilience" / "data"
ENEMIES_PATH = DATA_DIR / "Enemies.json"

# BOSS marker IDs (名稱為 "--BOSS--" 的佔位行)
# 實際 BOSS 為 marker 後一個 ID
BOSS_MARKER_IDS = {8, 11, 27, 37, 47, 57, 63, 68, 78, 82, 89, 93, 95, 97, 99, 101, 103, 105, 107}
BOSS_IDS = {mid + 1 for mid in BOSS_MARKER_IDS}
# = {9, 12, 28, 38, 48, 58, 64, 69, 79, 83, 90, 94, 96, 98, 100, 102, 104, 106, 108}

# 沙包（訓練用）不給獎勵
SANDBAG_ID = 1


def is_real_enemy(enemy: dict) -> bool:
    """判斷是否為有效敵人（非分隔行、非 BOSS 標記、非空白）"""
    if enemy is None:
        return False
    name = enemy.get("name", "")
    exp = enemy.get("exp", 0)
    if not name or name.startswith("----") or name == "--BOSS--":
        return False
    if exp <= 0:
        return False
    return True


def calc_rewards(eid: int, exp: int) -> tuple[int, int]:
    """計算 JP 和 CP 獎勵"""
    if eid == SANDBAG_ID:
        return 0, 0

    is_boss = eid in BOSS_IDS

    if is_boss:
        jp = max(round(exp * 0.5), 50)
        cp = max(round(exp * 0.05), 5)
    else:
        jp = max(round(exp * 0.4), 15)
        cp = max(round(exp * 0.04), 1)

    return jp, cp


def patch_note(note: str, cp: int, jp: int) -> str:
    """在 note 欄位中加入或更新 <CP: x> 和 <JP: x> 標記"""
    # 移除已存在的 CP/JP 標記
    note = re.sub(r"<CP:\s*\d+>\s*\n?", "", note)
    note = re.sub(r"<JP:\s*\d+>\s*\n?", "", note)

    # 清理尾端多餘空行
    note = note.rstrip("\n")

    # 加入新標記
    if note:
        note += "\n"
    note += f"<CP: {cp}>\n<JP: {jp}>\n"

    return note


def main():
    with open(ENEMIES_PATH, "r", encoding="utf-8") as f:
        enemies = json.load(f)

    patched = 0
    print(f"{'ID':>4}  {'名稱':<16}  {'EXP':>5}  {'類型':<6}  {'CP':>4}  {'JP':>5}")
    print("-" * 60)

    for enemy in enemies:
        if not is_real_enemy(enemy):
            continue

        eid = enemy["id"]
        exp = enemy["exp"]
        name = enemy["name"]
        jp, cp = calc_rewards(eid, exp)

        is_boss = eid in BOSS_IDS
        tag = "BOSS" if is_boss else "普通"

        enemy["note"] = patch_note(enemy.get("note", ""), cp, jp)
        patched += 1

        print(f"{eid:>4}  {name:<16}  {exp:>5}  {tag:<6}  {cp:>4}  {jp:>5}")

    print("-" * 60)
    print(f"共修改 {patched} 個敵人")

    with open(ENEMIES_PATH, "w", encoding="utf-8") as f:
        json.dump(enemies, f, ensure_ascii=False, indent=2)

    print(f"\n已寫入: {ENEMIES_PATH}")


if __name__ == "__main__":
    main()
