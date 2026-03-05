#!/usr/bin/env python3
"""
patch_defensive_learn_fix.py

Fix defensive skill Learn system:
1. Replace blanket <Learn Skills: 2000 to 2091> with character-specific skills
2. Make skill 1976 (防禦之術) learnable (free prerequisite)
3. Each character's first defensive skill requires 1976

Usage:
    python scripts/patch_defensive_learn_fix.py
"""

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"

# Character → (class_ids, defensive_skill_ids)
CHAR_MAP = {
    "東方啟":   ([2, 3, 4],       [2001, 2002, 2003]),
    "青兒":     ([6, 7, 8],       [2005, 2006, 2007]),
    "湮菲花":   ([10, 11, 12],    [2009, 2010, 2011]),
    "闕崇陽":   ([14, 15, 16],    [2013, 2014, 2015]),
    "絲塔娜":   ([18, 19, 20],    [2017, 2018, 2019]),
    "瑤琴劍":   ([22, 23, 24],    [2021, 2022, 2023]),
    "沅花":     ([26, 27, 28],    [2025, 2026, 2027]),
    "談笑":     ([30, 31, 32],    [2029, 2030, 2031]),
    "白沫檸":   ([34, 35, 36],    [2033, 2034, 2035]),
    "珞堇":     ([38, 39, 40],    [2037, 2038, 2039]),
    "龍玉":     ([42, 43, 44],    [2041, 2042, 2043]),
    "司徒長生": ([46, 47, 48],    [2045, 2046, 2047]),
    "楊古晨":   ([50, 51, 52],    [2049, 2050, 2051]),
    "殷染幽":   ([54, 55, 56],    [2053, 2054, 2055]),
    "墨汐若":   ([58, 59, 60],    [2057, 2058, 2059]),
    "聶思泠":   ([62, 63, 64],    [2061, 2062, 2063]),
    "無名丐":   ([66, 67, 68],    [2065, 2066, 2067]),
    "郭霆黃":   ([70, 71, 72],    [2069, 2070, 2071]),
    "藍靜冥":   ([74, 75, 76],    [2073, 2074, 2075]),
    "黃凱竹":   ([78, 79, 80],    [2077, 2078, 2079]),
    "劉靜靜":   ([82, 83, 84],    [2081, 2082, 2083]),
    "七霜":     ([86, 87, 88],    [2085, 2086, 2087]),
    "莫縈懷":   ([90, 91, 92],    [2089, 2090, 2091]),
}

# Build reverse map: class_id → defensive skill ids
CLASS_TO_DEF_SKILLS = {}
for name, (cids, sids) in CHAR_MAP.items():
    for cid in cids:
        CLASS_TO_DEF_SKILLS[cid] = sids


def find_by_id(arr, target_id):
    for i, item in enumerate(arr):
        if item and isinstance(item, dict) and item.get("id") == target_id:
            return i
    return None


def main():
    skills_path = BASE / "Skills.json"
    classes_path = BASE / "Classes.json"

    skills = json.loads(skills_path.read_text(encoding="utf-8"))
    classes = json.loads(classes_path.read_text(encoding="utf-8"))

    # ═══════════════════════════════════════════════════════════════
    # 1. Make skill 1976 (防禦之術) learnable — FREE prerequisite
    # ═══════════════════════════════════════════════════════════════

    idx_1976 = find_by_id(skills, 1976)
    if idx_1976 is None:
        print("ERROR: Skill 1976 not found!")
        return

    s1976 = skills[idx_1976]
    old_note = s1976.get("note", "")
    # Keep Known Skills List, add Learn AP Cost: 0 (free)
    if "<Learn AP Cost:" not in old_note:
        if old_note and not old_note.endswith("\n"):
            old_note += "\n"
        old_note += "<Learn AP Cost: 0>\n"
    s1976["note"] = old_note
    print(f"  [1] Skill 1976 (防禦之術) → FREE learnable prerequisite")

    # ═══════════════════════════════════════════════════════════════
    # 2. Add <Learn Require Skill: 1976> to each character's FIRST
    #    defensive skill (pos 0)
    # ═══════════════════════════════════════════════════════════════

    first_skills_updated = 0
    for name, (cids, sids) in CHAR_MAP.items():
        first_sid = sids[0]
        idx = find_by_id(skills, first_sid)
        if idx is None:
            continue
        s = skills[idx]
        note = s.get("note", "")
        # Remove any old Learn Require for this skill (in case of re-run)
        note = re.sub(r"<Learn Require Skill: \d+>\n?", "", note)
        # Add require 1976
        if note and not note.endswith("\n"):
            note += "\n"
        note += "<Learn Require Skill: 1976>\n"
        s["note"] = note
        first_skills_updated += 1

    print(f"  [2] Added <Learn Require Skill: 1976> to {first_skills_updated} first defensive skills")

    # ═══════════════════════════════════════════════════════════════
    # 3. Fix Classes.json — replace blanket range with specific skills
    # ═══════════════════════════════════════════════════════════════

    modified = 0
    for cid, def_sids in CLASS_TO_DEF_SKILLS.items():
        if cid >= len(classes) or classes[cid] is None:
            continue

        cls = classes[cid]
        note = cls.get("note", "")

        # Remove the old blanket tag
        note = note.replace("<Learn Skills: 2000 to 2091>\n", "")
        note = note.replace("<Learn Skills: 2000 to 2091>", "")

        # Build character-specific tag: 1976 + their 3 skills
        skill_list = ", ".join(str(s) for s in [1976] + def_sids)
        tag = f"<Learn Skills: {skill_list}>"

        # Add if not already present
        if tag not in note:
            if note and not note.endswith("\n"):
                note += "\n"
            note += tag + "\n"

        cls["note"] = note
        modified += 1

    print(f"  [3] Updated {modified} classes: blanket 2000-2091 → character-specific + 1976")

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
    # Verify
    # ═══════════════════════════════════════════════════════════════

    print("\n=== Verification ===")
    for name, (cids, sids) in CHAR_MAP.items():
        cid = cids[0]
        cls = classes[cid]
        note = cls.get("note", "")
        # Check the tag exists
        skill_list = ", ".join(str(s) for s in [1976] + sids)
        expected = f"<Learn Skills: {skill_list}>"
        has_tag = expected in note
        has_blanket = "2000 to 2091" in note
        status = "OK" if (has_tag and not has_blanket) else "FAIL"
        print(f"  {name:8s} class {cid:>2}: {expected}  [{status}]")

    # Check first skill requires 1976
    print()
    for name, (cids, sids) in CHAR_MAP.items():
        first_sid = sids[0]
        idx = find_by_id(skills, first_sid)
        s = skills[idx]
        has_req = "<Learn Require Skill: 1976>" in s.get("note", "")
        print(f"  {first_sid} {s['name']:12s}  requires 1976: {has_req}")

    print("\nDone!")


if __name__ == "__main__":
    main()
