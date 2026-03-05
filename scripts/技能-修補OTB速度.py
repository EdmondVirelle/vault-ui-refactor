#!/usr/bin/env python3
"""
patch_otb_speed.py

Apply OTB-appropriate speed values to skills:

1. 輕功 (601-638): Positive speed (movement = faster next turn)
2. 防禦技能 (2001-2091): Positive speed (defensive stance = quick reaction)
3. 個人技能 (1352-1723): Speed based on MP/TP cost tier
   - Skip skills that already have speed != 0
   - Skip separators (occasion: 0)

OTB Speed Logic (database "Speed" field):
  - Positive = act sooner NEXT turn
  - Negative = act later NEXT turn
  - TP100 ultras already have +50 (keep)

Usage:
    python scripts/patch_otb_speed.py
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"


def find_by_id(arr, target_id):
    for i, item in enumerate(arr):
        if item and isinstance(item, dict) and item.get("id") == target_id:
            return i
    return None


def get_combat_speed(mp_cost: int, tp_cost: int) -> int:
    """Determine speed value for combat skills based on cost.

    Higher cost = more powerful = more delay after use.
    TP100 already handled (speed: 50), skip here.
    """
    if tp_cost == 100:
        return None  # Don't touch — already set to 50
    if tp_cost >= 50:
        return -15   # Semi-ultimate (e.g. 古弦結界 TP50)
    if mp_cost <= 8:
        return 0     # Basic attacks — neutral
    if mp_cost <= 14:
        return 0     # Normal attacks — neutral
    if mp_cost <= 18:
        return -5    # Mid-tier — slight delay
    if mp_cost <= 28:
        return -10   # Heavy attacks — moderate delay
    if mp_cost >= 30:
        return -15   # Strong techniques — significant delay
    return 0


def get_qinggong_speed(mp_cost: int) -> int:
    """Speed bonus for 輕功 skills. Movement = faster next turn."""
    if mp_cost <= 12:
        return 5
    if mp_cost <= 20:
        return 10
    if mp_cost <= 35:
        return 15
    if mp_cost <= 50:
        return 20
    return 25  # 51-60 MP: legendary


def main():
    skills_path = BASE / "Skills.json"
    skills = json.loads(skills_path.read_text(encoding="utf-8"))

    stats = {"輕功": 0, "防禦": 0, "個人技能": 0, "skipped": 0}

    # ═══════════════════════════════════════════════════════════════
    # 1. 輕功 skills (601-638)
    # ═══════════════════════════════════════════════════════════════

    print("=== 輕功 (601-638) ===")
    for sid in range(601, 639):
        idx = find_by_id(skills, sid)
        if idx is None:
            continue
        s = skills[idx]
        if s.get("occasion") == 0:
            continue  # separator
        spd = get_qinggong_speed(s["mpCost"])
        old_spd = s.get("speed", 0)
        s["speed"] = spd
        print(f"  {sid} {s['name']:12s}  MP{s['mpCost']:>3}  speed: {old_spd} → {spd}")
        stats["輕功"] += 1

    # ═══════════════════════════════════════════════════════════════
    # 2. 防禦技能 (2001-2091, skip separators)
    # ═══════════════════════════════════════════════════════════════

    print("\n=== 防禦技能 (2001-2091) ===")
    for sid in range(2000, 2092):
        idx = find_by_id(skills, sid)
        if idx is None:
            continue
        s = skills[idx]
        if s.get("occasion") == 0:
            continue  # separator
        old_spd = s.get("speed", 0)
        s["speed"] = 10
        stats["防禦"] += 1

    print(f"  Set speed=10 for {stats['防禦']} defensive skills")

    # ═══════════════════════════════════════════════════════════════
    # 3. 個人技能 (1352-1723) — personal combat skills
    #    Only patch skills that currently have speed == 0
    # ═══════════════════════════════════════════════════════════════

    print("\n=== 個人技能 (1352-1723) ===")
    for sid in range(1352, 1724):
        idx = find_by_id(skills, sid)
        if idx is None:
            continue
        s = skills[idx]
        if s.get("occasion") == 0:
            continue  # separator
        if s.get("speed", 0) != 0:
            stats["skipped"] += 1
            continue  # already has speed value

        spd = get_combat_speed(s["mpCost"], s["tpCost"])
        if spd is None:
            stats["skipped"] += 1
            continue  # TP100, don't touch

        if spd != 0:
            s["speed"] = spd
            print(f"  {sid} {s['name']:12s}  MP{s['mpCost']:>3} TP{s['tpCost']:>3}  → speed {spd}")
            stats["個人技能"] += 1

    # ═══════════════════════════════════════════════════════════════
    # 4. 武器通用技 (1002-1341) — weapon block skills
    #    Only patch skills that currently have speed == 0
    # ═══════════════════════════════════════════════════════════════

    print("\n=== 武器通用技 (1002-1341) ===")
    weapon_count = 0
    for sid in range(1002, 1342):
        idx = find_by_id(skills, sid)
        if idx is None:
            continue
        s = skills[idx]
        if s.get("occasion") == 0:
            continue
        if s.get("speed", 0) != 0:
            continue

        spd = get_combat_speed(s["mpCost"], s["tpCost"])
        if spd is None or spd == 0:
            continue

        s["speed"] = spd
        weapon_count += 1

    print(f"  Set speed for {weapon_count} weapon skills")
    stats["個人技能"] += weapon_count

    # ═══════════════════════════════════════════════════════════════
    # Save
    # ═══════════════════════════════════════════════════════════════

    skills_path.write_text(
        json.dumps(skills, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    print(f"\n=== Summary ===")
    print(f"  輕功:     {stats['輕功']} skills patched")
    print(f"  防禦:     {stats['防禦']} skills patched")
    print(f"  戰鬥技:   {stats['個人技能']} skills patched")
    print(f"  Skipped:  {stats['skipped']} (already had speed or TP100)")
    print("Done!")


if __name__ == "__main__":
    main()
