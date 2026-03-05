"""
Add VisuMZ_3_EnemyLevels notetags to all enemies in Enemies.json.

Follows reference docs:
  - 副本設計.md: chapter level ranges (Prologue Lv1-5 ... Ch8 Lv41-45)
  - 敵人設計.md: enemy roles (normal, elite, boss)
  - 遊戲系統.md: P3 priority = fixed levels for initial playthrough

Design:
  - Normal mobs: <Level: low to high> (random within chapter range)
  - Elite mobs:  <Level: mid to high> (upper half)
  - Bosses:      <Level: high> + <Level Bonus: +2>
  - Training dummy (ID 1): no level tag
  - Separators (----章節---- / --BOSS--): skipped

Usage:
    python scripts/patch_enemy_levels.py
"""

import json
import sys
import io
import re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"

# ── Chapter Definitions ──────────────────────────────────────────────
# (chapter_name, separator_id, level_low, level_high, enemy_ids_with_role)
# role: "normal", "elite", "boss"

CHAPTERS = [
    {
        "name": "序章",
        "sep_id": 3,
        "lv_low": 1,
        "lv_high": 5,
        "enemies": {
            # ID 1 (沙包) is training dummy — skipped
            2:  "normal",   # 帝國武民
            4:  "normal",   # 野狼
            5:  "normal",   # 毒蛇
            6:  "normal",   # 山賊
            7:  "normal",   # 帝國巡邏兵
            9:  "elite",    # 武裝兵將領
            10: "elite",    # 耳鼠
            12: "boss",     # 書中判官
            13: "normal",   # 帝國武民(2)
            14: "normal",   # 帝國弓手
            15: "normal",   # 遺跡石偶
            16: "normal",   # 黃裳冤魂
            17: "elite",    # 帝國哨兵隊長
            18: "normal",   # 遺跡守衛機關
        },
    },
    {
        "name": "第一章",
        "sep_id": 19,
        "lv_low": 6,
        "lv_high": 10,
        "enemies": {
            20: "normal",   # 劫道匪
            21: "normal",   # 帝國密探
            22: "normal",   # 打手
            23: "normal",   # 門派叛徒
            24: "normal",   # 暗殺者
            25: "normal",   # 帝國精銳兵
            26: "elite",    # 帝國騎士
            28: "boss",     # 劃月邪徒
        },
    },
    {
        "name": "第二章",
        "sep_id": 29,
        "lv_low": 11,
        "lv_high": 15,
        "enemies": {
            30: "normal",   # 沙漠毒蠍
            31: "normal",   # 黃沙狼群
            32: "normal",   # 帝國沙漠兵
            33: "normal",   # 沙暴精
            34: "normal",   # 西域商隊護衛
            35: "normal",   # 檮杌獸影
            36: "elite",    # 黑市殺手
            38: "boss",     # 沙漠巨蟲
        },
    },
    {
        "name": "第三章",
        "sep_id": 39,
        "lv_low": 16,
        "lv_high": 20,
        "enemies": {
            40: "normal",   # 仙池弟子
            41: "normal",   # 寒冰精
            42: "normal",   # 變異水獸
            43: "normal",   # 受蠱弟子
            44: "normal",   # 冰霜巨熊
            45: "normal",   # 窮奇幻象
            46: "elite",    # 仙池護法
            48: "boss",     # 初代奇美拉
        },
    },
    {
        "name": "第四章",
        "sep_id": 49,
        "lv_low": 21,
        "lv_high": 25,
        "enemies": {
            50: "normal",   # 帝國掘探隊
            51: "normal",   # 山中妖靈
            52: "normal",   # 靈脈獸
            53: "normal",   # 帝國工程兵
            54: "normal",   # 鬼面猿
            55: "normal",   # 巨型蜈蚣
            56: "elite",    # 帝國煉金術士
            58: "boss",     # 靈脈守護者
        },
    },
    {
        "name": "第五章",
        "sep_id": 59,
        "lv_low": 26,
        "lv_high": 30,
        "enemies": {
            60: "normal",   # 帝國重甲兵
            61: "normal",   # 陰帥小卒
            62: "normal",   # 亡魂
            64: "elite",    # 奇美拉二代
            65: "elite",    # 帝國審判官
            66: "normal",   # 黑袍教士
            67: "normal",   # 機械傀儡
            69: "boss",     # 甘珠爾守衛
        },
    },
    {
        "name": "第六章",
        "sep_id": 70,
        "lv_low": 31,
        "lv_high": 35,
        "enemies": {
            71: "normal",   # 枯木妖
            72: "normal",   # 饕餮獸僕
            73: "normal",   # 毒林蟲群
            74: "normal",   # 帝國暗部
            75: "normal",   # 戾神碎片
            76: "normal",   # 變異門徒
            77: "elite",    # 陰山鬼修
            79: "boss",     # 戾神化身
        },
    },
    {
        "name": "第七章",
        "sep_id": 80,
        "lv_low": 36,
        "lv_high": 40,
        "enemies": {
            81: "normal",   # 鐘塔守衛
            83: "elite",    # 奇美拉三代
            84: "normal",   # 理式構裝體
            85: "normal",   # 帝國鐘塔研究員
            86: "normal",   # 禁忌實驗體
            87: "normal",   # 虛空裂隙獸
            88: "boss",     # 帝國司令官
            90: "boss",     # 不可名狀幼體
        },
    },
    {
        "name": "第八章",
        "sep_id": 91,
        "lv_low": 41,
        "lv_high": 45,
        "enemies": {
            92:  "normal",  # 混沌殘影
            94:  "boss",    # 饕餮化身
            96:  "boss",    # 檮杌化身
            98:  "boss",    # 窮奇化身
            100: "boss",    # 帝國終極兵器
            102: "boss",    # 四兇融合體
            104: "boss",    # 混沌核心
            106: "boss",    # 虛空巨靈
            108: "boss",    # 不可名狀之物 (FINAL BOSS)
            109: "normal",  # 理式崩壞體
            110: "normal",  # 混沌侵蝕者
        },
    },
]

# IDs that are chapter separators or BOSS markers (skip entirely)
SEPARATOR_IDS = set()
BOSS_MARKER_IDS = set()

# Training dummy — no level
TRAINING_DUMMY_ID = 1

# Final boss gets highest level + biggest bonus
FINAL_BOSS_ID = 108


def load_json(filename: str):
    with open(BASE / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data):
    path = BASE / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  Saved {path}")


def build_level_tags(role: str, lv_low: int, lv_high: int, enemy_id: int) -> str:
    """Build VisuMZ_3_EnemyLevels notetag string for an enemy."""
    mid = (lv_low + lv_high) // 2 + 1  # upper-mid

    if enemy_id == FINAL_BOSS_ID:
        # Final boss: max level + big bonus
        return (
            f"<Level: {lv_high}>\n"
            f"<Level Bonus: +3>\n"
            f"<Minimum Level: {lv_low}>\n"
            f"<Maximum Level: 99>\n"
        )

    if role == "boss":
        # Chapter bosses: top of range + bonus
        return (
            f"<Level: {lv_high}>\n"
            f"<Level Bonus: +2>\n"
            f"<Minimum Level: {lv_low}>\n"
            f"<Maximum Level: {lv_high + 5}>\n"
        )

    if role == "elite":
        # Elite enemies: upper half of range
        return (
            f"<Level: {mid} to {lv_high}>\n"
            f"<Minimum Level: {lv_low}>\n"
            f"<Maximum Level: {lv_high + 2}>\n"
        )

    # Normal enemies: full chapter range
    return (
        f"<Level: {lv_low} to {lv_high}>\n"
        f"<Minimum Level: {lv_low}>\n"
        f"<Maximum Level: {lv_high}>\n"
    )


def is_separator(enemy: dict) -> bool:
    """Check if an enemy entry is a separator (----xxx---- or --BOSS--)."""
    if not enemy or not isinstance(enemy, dict):
        return True
    name = enemy.get("name", "")
    if not name:
        return True
    if name.startswith("----") or name == "--BOSS--":
        return True
    return False


def has_level_tag(note: str) -> bool:
    """Check if note already contains a <Level: ...> tag."""
    return bool(re.search(r"<Level:", note))


def main():
    print("Loading Enemies.json...")
    enemies = load_json("Enemies.json")
    print(f"  Total entries: {len(enemies)}")

    # ── Build enemy→chapter mapping ──────────────────────────────────
    enemy_map = {}  # enemy_id -> (role, lv_low, lv_high, chapter_name)
    for ch in CHAPTERS:
        for eid, role in ch["enemies"].items():
            enemy_map[eid] = (role, ch["lv_low"], ch["lv_high"], ch["name"])

    # ── Apply level tags ─────────────────────────────────────────────
    print("\nApplying level tags...")
    updated = 0
    skipped_sep = 0
    skipped_dummy = 0
    skipped_empty = 0
    skipped_existing = 0

    for i in range(1, len(enemies)):
        enemy = enemies[i]
        if not enemy or not isinstance(enemy, dict):
            continue

        eid = enemy.get("id", i)

        # Skip training dummy
        if eid == TRAINING_DUMMY_ID:
            skipped_dummy += 1
            continue

        # Skip separators
        if is_separator(enemy):
            skipped_sep += 1
            continue

        # Skip empty/unnamed enemies
        name = enemy.get("name", "")
        if not name:
            skipped_empty += 1
            continue

        # Skip if already has level tag
        note = enemy.get("note", "")
        if has_level_tag(note):
            skipped_existing += 1
            continue

        # Look up enemy in our chapter map
        if eid not in enemy_map:
            print(f"  WARNING: Enemy ID {eid} ({name}) not in chapter map — skipping")
            continue

        role, lv_low, lv_high, ch_name = enemy_map[eid]
        tags = build_level_tags(role, lv_low, lv_high, eid)

        # Prepend level tags to the note (before other tags)
        # Add after the first line if note starts with comment, otherwise prepend
        if note:
            enemy["note"] = tags + note
        else:
            enemy["note"] = tags

        updated += 1
        role_label = {"normal": "普通", "elite": "精英", "boss": "BOSS"}[role]
        print(f"  [{eid:3d}] {name:<12s} ({ch_name} {role_label}) Lv {lv_low}-{lv_high}")

    print(f"\nSummary:")
    print(f"  Updated:          {updated}")
    print(f"  Skipped (sep):    {skipped_sep}")
    print(f"  Skipped (dummy):  {skipped_dummy}")
    print(f"  Skipped (empty):  {skipped_empty}")
    print(f"  Skipped (exists): {skipped_existing}")

    # ── Verification ─────────────────────────────────────────────────
    print("\nVerification...")
    ok = True

    # Check all mapped enemies got level tags
    for eid, (role, lv_low, lv_high, ch_name) in enemy_map.items():
        if eid >= len(enemies):
            print(f"  FAIL: Enemy ID {eid} out of range")
            ok = False
            continue
        enemy = enemies[eid]
        if not enemy:
            print(f"  FAIL: Enemy ID {eid} is null")
            ok = False
            continue
        note = enemy.get("note", "")
        if not has_level_tag(note):
            print(f"  FAIL: Enemy ID {eid} ({enemy.get('name', '?')}) missing level tag")
            ok = False

    # Check no separator got tagged
    for i in range(1, len(enemies)):
        enemy = enemies[i]
        if not enemy or not isinstance(enemy, dict):
            continue
        if is_separator(enemy):
            note = enemy.get("note", "")
            if has_level_tag(note):
                print(f"  FAIL: Separator ID {enemy.get('id', i)} got a level tag!")
                ok = False

    # Check training dummy
    if enemies[TRAINING_DUMMY_ID]:
        note = enemies[TRAINING_DUMMY_ID].get("note", "")
        if has_level_tag(note):
            print(f"  FAIL: Training dummy got a level tag!")
            ok = False

    # Check level values make sense
    for eid, (role, lv_low, lv_high, ch_name) in enemy_map.items():
        enemy = enemies[eid]
        if not enemy:
            continue
        note = enemy.get("note", "")
        # Extract level value(s)
        m = re.search(r"<Level:\s*(\d+)(?:\s*to\s*(\d+))?\s*>", note)
        if m:
            level_a = int(m.group(1))
            level_b = int(m.group(2)) if m.group(2) else level_a
            if level_a < 1 or level_b > 99:
                print(f"  FAIL: Enemy {eid} has invalid level range: {level_a}-{level_b}")
                ok = False

    if ok:
        print("  All checks passed!")
    else:
        print("\nVerification FAILED. Not saving.")
        return 1

    # ── Save ──────────────────────────────────────────────────────────
    print("\nSaving...")
    save_json("Enemies.json", enemies)

    # ── Print level distribution ─────────────────────────────────────
    print("\n── Level Distribution ──")
    for ch in CHAPTERS:
        print(f"\n  {ch['name']} (Lv {ch['lv_low']}-{ch['lv_high']}):")
        for eid, role in sorted(ch["enemies"].items()):
            enemy = enemies[eid]
            name = enemy.get("name", "?")
            note = enemy.get("note", "")
            m = re.search(r"<Level:\s*([^>]+)>", note)
            lv_str = m.group(1) if m else "?"
            bonus_m = re.search(r"<Level Bonus:\s*([^>]+)>", note)
            bonus = f" (Bonus: {bonus_m.group(1)})" if bonus_m else ""
            role_label = {"normal": " ", "elite": "★", "boss": "◆"}[role]
            print(f"    {role_label} [{eid:3d}] {name:<14s} Lv {lv_str}{bonus}")

    print(f"\nDone! {updated} enemies updated with level tags.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
