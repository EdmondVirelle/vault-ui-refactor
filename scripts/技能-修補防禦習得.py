#!/usr/bin/env python3
"""
patch_defensive_learn.py

1. Replace 珞堇's skill 2038 (弦音護陣) with 砸琴神功 (copied from 1719)
2. Set all defensive skill (2001-2091) icons to 3344 and animations to 137
3. Add Learn tags to all 69 defensive skills (first skill FREE per character)
4. Update skill 1976 (防禦之術) with Known Skills List → 2000~2091
5. Add <Learn Skills: 2000 to 2091> to all 69 battle classes
6. Remove skill 1719 from 珞堇's class Learn Skills lists
7. Clean Learn tags from old skill 1719

Usage:
    python scripts/patch_defensive_learn.py
"""

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"

# ═══════════════════════════════════════════════════════════════════════════════
# Character → defensive skill mapping
# (name, separator_id, [skill1, skill2, skill3])
# ═══════════════════════════════════════════════════════════════════════════════

CHAR_DEFENSIVE = [
    ("東方啟",   2000, [2001, 2002, 2003]),
    ("青兒",     2004, [2005, 2006, 2007]),
    ("湮菲花",   2008, [2009, 2010, 2011]),
    ("闕崇陽",   2012, [2013, 2014, 2015]),
    ("絲塔娜",   2016, [2017, 2018, 2019]),
    ("瑤琴劍",   2020, [2021, 2022, 2023]),
    ("沅花",     2024, [2025, 2026, 2027]),
    ("談笑",     2028, [2029, 2030, 2031]),
    ("白沫檸",   2032, [2033, 2034, 2035]),
    ("珞堇",     2036, [2037, 2038, 2039]),
    ("龍玉",     2040, [2041, 2042, 2043]),
    ("司徒長生", 2044, [2045, 2046, 2047]),
    ("楊古晨",   2048, [2049, 2050, 2051]),
    ("殷染幽",   2052, [2053, 2054, 2055]),
    ("墨汐若",   2056, [2057, 2058, 2059]),
    ("聶思泠",   2060, [2061, 2062, 2063]),
    ("無名丐",   2064, [2065, 2066, 2067]),
    ("郭霆黃",   2068, [2069, 2070, 2071]),
    ("藍靜冥",   2072, [2073, 2074, 2075]),
    ("黃凱竹",   2076, [2077, 2078, 2079]),
    ("劉靜靜",   2080, [2081, 2082, 2083]),
    ("七霜",     2084, [2085, 2086, 2087]),
    ("莫縈懷",   2088, [2089, 2090, 2091]),
]

# ═══════════════════════════════════════════════════════════════════════════════
# Tier system (same as patch_skill_learn_system.py)
# ═══════════════════════════════════════════════════════════════════════════════

TIER_COSTS = {
    "入門": {"ap": 10,  "sp": 0,  "frag": 1},
    "初階": {"ap": 20,  "sp": 3,  "frag": 2},
    "中階": {"ap": 35,  "sp": 5,  "frag": 3},
    "進階": {"ap": 55,  "sp": 12, "frag": 5},
    "高階": {"ap": 80,  "sp": 20, "frag": 8},
}

FRAGMENT_ID = 1009  # 江湖武學碎片


def get_tier(mp_cost: int, tp_cost: int) -> str:
    if tp_cost == 100:
        return "絕學"
    if mp_cost <= 8:
        return "入門"
    if mp_cost <= 14:
        return "初階"
    if mp_cost <= 18:
        return "中階"
    if mp_cost <= 28:
        return "進階"
    return "高階"


# All 69 battle class IDs
ALL_CLASS_IDS = [
    2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20,
    22, 23, 24, 26, 27, 28, 30, 31, 32, 34, 35, 36, 38, 39, 40,
    42, 43, 44, 46, 47, 48, 50, 51, 52, 54, 55, 56,
    58, 59, 60, 62, 63, 64, 66, 67, 68,
    70, 71, 72, 74, 75, 76, 78, 79, 80,
    82, 83, 84, 86, 87, 88, 90, 91, 92,
]


def find_by_id(arr, target_id):
    """Find array index for element with given id."""
    for i, item in enumerate(arr):
        if item is not None and isinstance(item, dict) and item.get("id") == target_id:
            return i
    return None


def main():
    skills_path = BASE / "Skills.json"
    classes_path = BASE / "Classes.json"

    skills = json.loads(skills_path.read_text(encoding="utf-8"))
    classes = json.loads(classes_path.read_text(encoding="utf-8"))

    # ═══════════════════════════════════════════════════════════════
    # 1. Replace skill 2038 (弦音護陣) with 砸琴神功
    # ═══════════════════════════════════════════════════════════════

    src_idx = find_by_id(skills, 1719)
    if src_idx is None:
        print("ERROR: Skill 1719 (砸琴神功) not found!")
        return
    src_skill = skills[src_idx]

    tgt_idx = find_by_id(skills, 2038)
    if tgt_idx is None:
        print("ERROR: Skill 2038 (弦音護陣) not found!")
        return

    # Build the JS Post-Apply block from original
    js_block = (
        "<JS Post-Apply>\n"
        "if (target.isDead()) {\n"
        "  const v = $gameVariables.value(500);\n"
        "  if (v < 595) $gameVariables.setValue(500, v + 1);\n"
        "}\n"
        "$gameVariables.setValue(501, Math.min(5 + $gameVariables.value(500), 600));\n"
        "</JS Post-Apply>"
    )

    skills[tgt_idx] = {
        "id": 2038,
        "name": "砸琴神功",
        "animationId": 137,
        "damage": {
            "critical": True,
            "elementId": 0,
            "formula": "Math.min(5 + $gameVariables.value(500), 600)",
            "type": 1,
            "variance": 0,
        },
        "description": src_skill["description"],
        "effects": [],
        "hitType": 1,
        "iconIndex": 3344,
        "message1": "",
        "message2": "",
        "messageType": 1,
        "mpCost": 0,
        "occasion": 1,
        "repeats": 1,
        "requiredWtypeId1": 0,
        "requiredWtypeId2": 0,
        "scope": 1,
        "speed": 0,
        "stypeId": 0,
        "successRate": 100,
        "tpCost": 0,
        "tpGain": 5,
        "note": "",  # Will be set in step 3
    }
    print("  [1] Replaced skill 2038 (弦音護陣 → 砸琴神功)")

    # ═══════════════════════════════════════════════════════════════
    # 2. Set all defensive skill icons to 3344 and animations to 137
    # ═══════════════════════════════════════════════════════════════

    all_skill_ids = []
    for _, _, sids in CHAR_DEFENSIVE:
        all_skill_ids.extend(sids)

    for sid in all_skill_ids:
        idx = find_by_id(skills, sid)
        if idx is not None:
            skills[idx]["iconIndex"] = 3344
            skills[idx]["animationId"] = 137

    print(f"  [2] Updated icon=3344, animation=137 for {len(all_skill_ids)} skills")

    # ═══════════════════════════════════════════════════════════════
    # 3. Add Learn tags to all 69 defensive skills
    # ═══════════════════════════════════════════════════════════════

    tagged_free = 0
    tagged_cost = 0

    for char_name, sep_id, skill_ids in CHAR_DEFENSIVE:
        for pos, sid in enumerate(skill_ids):
            idx = find_by_id(skills, sid)
            if idx is None:
                print(f"  WARNING: Skill {sid} not found!")
                continue

            skill = skills[idx]

            if sid == 2038:
                # 砸琴神功 — special handling
                note_lines = [
                    "<Color: #FFD700>",
                    "<Cooldown: 0>",
                    "<Learn AP Cost: 10>",
                    f"<Learn Item {FRAGMENT_ID} Cost: 1>",
                    f"<Learn Require Skill: {skill_ids[0]}>",
                    js_block,
                ]
                skill["note"] = "\n".join(note_lines) + "\n"
                tagged_cost += 1
                continue

            # Normal defensive skills
            existing_note = skill.get("note", "")
            # Strip any old Learn tags if re-running
            existing_note = re.sub(r"<Learn [^>]+>\n?", "", existing_note)

            if pos == 0:
                # First skill: FREE (no Learn cost tags)
                skill["note"] = existing_note
                tagged_free += 1
            else:
                # Second/third skill: tier-based costs + prerequisite
                mp = skill["mpCost"]
                tp = skill["tpCost"]
                tier = get_tier(mp, tp)
                costs = TIER_COSTS.get(tier, TIER_COSTS["進階"])

                learn_tags = [f"<Learn AP Cost: {costs['ap']}>"]
                if costs["sp"] > 0:
                    learn_tags.append(f"<Learn SP Cost: {costs['sp']}>")
                learn_tags.append(f"<Learn Item {FRAGMENT_ID} Cost: {costs['frag']}>")
                learn_tags.append(f"<Learn Require Skill: {skill_ids[pos - 1]}>")

                if existing_note and not existing_note.endswith("\n"):
                    existing_note += "\n"
                existing_note += "\n".join(learn_tags) + "\n"
                skill["note"] = existing_note
                tagged_cost += 1

    print(f"  [3] Learn tags: {tagged_free} FREE + {tagged_cost} with costs = {tagged_free + tagged_cost} total")

    # ═══════════════════════════════════════════════════════════════
    # 4. Update skill 1976 (防禦之術) Known Skills List
    # ═══════════════════════════════════════════════════════════════

    idx_1976 = find_by_id(skills, 1976)
    if idx_1976 is not None:
        known_ids = sorted(all_skill_ids)
        known_str = ", ".join(str(s) for s in known_ids)
        skills[idx_1976]["note"] = f"<Known Skills List: {known_str}>"
        print(f"  [4] Updated skill 1976 (防禦之術) Known Skills List ({len(known_ids)} skills)")
    else:
        print("  WARNING: Skill 1976 (防禦之術) not found!")

    # ═══════════════════════════════════════════════════════════════
    # 5. Add <Learn Skills: 2000 to 2091> to all 69 classes
    #    Remove 1719 from 珞堇's class Learn Skills (38, 39, 40)
    # ═══════════════════════════════════════════════════════════════

    modified = 0
    for cid in ALL_CLASS_IDS:
        if cid >= len(classes) or classes[cid] is None:
            continue

        cls = classes[cid]
        note = cls.get("note", "")

        # Remove 1719 from 珞堇's Learn Skills tags
        if cid in (38, 39, 40):
            note = note.replace(", 1719", "").replace("1719, ", "")

        # Add defensive skills Learn tag
        if "<Learn Skills: 2000 to 2091>" not in note:
            if note and not note.endswith("\n"):
                note += "\n"
            note += "<Learn Skills: 2000 to 2091>\n"

        cls["note"] = note
        modified += 1

    print(f"  [5] Updated {modified} classes with <Learn Skills: 2000 to 2091>")

    # ═══════════════════════════════════════════════════════════════
    # 6. Clean Learn tags from old skill 1719
    # ═══════════════════════════════════════════════════════════════

    old_note = skills[src_idx].get("note", "")
    old_note = re.sub(r"<Learn [^>]+>\n?", "", old_note)
    skills[src_idx]["note"] = old_note
    print("  [6] Cleaned Learn tags from old skill 1719 (砸琴神功)")

    # ═══════════════════════════════════════════════════════════════
    # Save
    # ═══════════════════════════════════════════════════════════════

    skills_path.write_text(
        json.dumps(skills, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    classes_path.write_text(
        json.dumps(classes, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    # ═══════════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════════

    print("\n=== Cost Summary ===")
    for char_name, sep_id, skill_ids in CHAR_DEFENSIVE:
        print(f"\n  {char_name}:")
        for pos, sid in enumerate(skill_ids):
            idx = find_by_id(skills, sid)
            if idx is None:
                continue
            s = skills[idx]
            mp = s["mpCost"]
            tp = s["tpCost"]
            tier = get_tier(mp, tp)
            costs = TIER_COSTS.get(tier, TIER_COSTS["進階"])
            if pos == 0:
                print(f"    {sid} {s['name']:12s}  MP{mp:>3}  FREE")
            else:
                print(f"    {sid} {s['name']:12s}  MP{mp:>3}  "
                      f"AP={costs['ap']}  SP={costs['sp']}  "
                      f"碎片={costs['frag']}  (req:{skill_ids[pos-1]})")

    print("\nDone! Skills.json and Classes.json updated.")


if __name__ == "__main__":
    main()
