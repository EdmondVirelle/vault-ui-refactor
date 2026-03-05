"""
防禦武學容器建立腳本
- 建立新容器技能 1978（防禦武學）
- 從江湖武學 1974 移除 22 個抵禦技能
- 從內功心法 1977 移除 3 個抵禦技能
- 所有有 1976 學習的職業加入 1978 學習
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "Consilience" / "data"

# === 25 defensive skill IDs ===
DEFENSIVE_SKILL_IDS = [
    # 武器抵禦 (12)
    1014, 1027, 1040, 1053, 1066, 1079, 1092, 1118, 1131, 1144, 1157, 1170,
    # 內功抵禦 (3)
    1183, 1196, 1209,
    # 五行抵禦 (5)
    1222, 1235, 1248, 1261, 1274,
    # 天象抵禦 (5)
    1287, 1300, 1313, 1326, 1339,
]
assert len(DEFENSIVE_SKILL_IDS) == 25

# IDs to remove from 1974 (all except the 3 內功 ones which are in 1977)
REMOVE_FROM_1974 = [
    1014, 1027, 1040, 1053, 1066, 1079, 1092, 1118, 1131, 1144, 1157, 1170,
    1222, 1235, 1248, 1261, 1274,
    1287, 1300, 1313, 1326, 1339,
]
assert len(REMOVE_FROM_1974) == 22


def patch_skills():
    skills_path = DATA_DIR / "Skills.json"
    skills = json.loads(skills_path.read_text(encoding="utf-8"))

    # --- 1. Create container skill 1978 ---
    skill_1978 = skills[1978]
    assert skill_1978["id"] == 1978
    assert skill_1978["name"] == "", f"Skill 1978 already has name: {skill_1978['name']}"

    # Use skill 1974 as template for container properties
    template = skills[1974]
    skill_1978["name"] = "防禦武學"
    skill_1978["description"] = template["description"]
    skill_1978["iconIndex"] = template["iconIndex"]
    skill_1978["stypeId"] = 1       # 套路
    skill_1978["scope"] = 0         # 無目標 (container)
    skill_1978["occasion"] = 1      # match container occasion
    skill_1978["hitType"] = 0
    skill_1978["mpCost"] = 0
    skill_1978["tpCost"] = 0
    skill_1978["tpGain"] = 0

    # Build the Known Skills List note
    id_str = ", ".join(str(x) for x in DEFENSIVE_SKILL_IDS)
    skill_1978["note"] = f"<Known Skills List: {id_str}>"

    print(f"[OK] Skill 1978 created: {skill_1978['name']}")
    print(f"     note: {skill_1978['note'][:80]}...")

    # --- 2. Remove 22 IDs from skill 1974 ---
    skill_1974 = skills[1974]
    assert skill_1974["id"] == 1974
    old_note = skill_1974["note"]

    # Parse the existing IDs from the note
    import re
    match = re.search(r"<Known Skills List:\s*(.+?)>", old_note)
    assert match, "Could not parse 1974 note"
    old_ids = [int(x.strip()) for x in match.group(1).split(",")]
    print(f"[INFO] Skill 1974 had {len(old_ids)} skill IDs")

    remove_set = set(REMOVE_FROM_1974)
    new_ids = [x for x in old_ids if x not in remove_set]
    removed = [x for x in old_ids if x in remove_set]
    print(f"[INFO] Removed {len(removed)} IDs: {removed}")
    assert len(removed) == 22, f"Expected 22 removals, got {len(removed)}"

    new_id_str = ", ".join(str(x) for x in new_ids)
    skill_1974["note"] = f"<Known Skills List: {new_id_str}>"
    print(f"[OK] Skill 1974 now has {len(new_ids)} skill IDs")

    # --- 3. Modify skill 1977 ranges ---
    skill_1977 = skills[1977]
    assert skill_1977["id"] == 1977
    old_1977_note = skill_1977["note"]
    print(f"[INFO] Skill 1977 old note: {old_1977_note}")

    # Replace each range to exclude the defensive IDs
    new_1977_note = old_1977_note
    new_1977_note = new_1977_note.replace(
        "<Known Skills List: 1174 to 1185>",
        "<Known Skills List: 1174 to 1182, 1184, 1185>"
    )
    new_1977_note = new_1977_note.replace(
        "<Known Skills List: 1187 to 1198>",
        "<Known Skills List: 1187 to 1195, 1197, 1198>"
    )
    new_1977_note = new_1977_note.replace(
        "<Known Skills List: 1200 to 1211>",
        "<Known Skills List: 1200 to 1208, 1210, 1211>"
    )
    skill_1977["note"] = new_1977_note
    print(f"[OK] Skill 1977 new note: {new_1977_note}")

    # Write back
    skills_path.write_text(json.dumps(skills, ensure_ascii=False), encoding="utf-8")
    print(f"\n[SAVED] {skills_path}")


def patch_classes():
    classes_path = DATA_DIR / "Classes.json"
    classes = json.loads(classes_path.read_text(encoding="utf-8"))

    count = 0
    for cls in classes:
        if cls is None:
            continue
        learnings = cls.get("learnings", [])
        has_1976 = any(l["skillId"] == 1976 for l in learnings)
        has_1978 = any(l["skillId"] == 1978 for l in learnings)

        if has_1976 and not has_1978:
            # Find the index of 1976 learning to insert 1978 right after it
            idx_1976 = next(i for i, l in enumerate(learnings) if l["skillId"] == 1976)
            new_entry = {"level": 1, "skillId": 1978}
            learnings.insert(idx_1976 + 1, new_entry)
            count += 1

    print(f"\n[OK] Added skill 1978 to {count} classes")

    classes_path.write_text(json.dumps(classes, ensure_ascii=False), encoding="utf-8")
    print(f"[SAVED] {classes_path}")


if __name__ == "__main__":
    patch_skills()
    patch_classes()
    print("\n=== All patches applied successfully ===")
