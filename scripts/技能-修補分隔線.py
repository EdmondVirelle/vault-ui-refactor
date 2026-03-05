"""
Reorganize new skills (1604-1695) to include separator entries per character.

Before: 92 skills packed at 1604-1695 (4 per char × 23 chars)
After:  115 entries at 1604-1718 (separator + 4 skills per char × 23 chars)

Layout per character:
  ----角色名----     (blank separator)
  skill 1            (C1)
  skill 2            (C2)
  skill 3            (C3)
  skill 4            (C2)

Usage:
    python scripts/patch_skill_separators.py
"""

import json
import sys
import io
import re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"

CHAR_NAMES = [
    "東方啓", "湮菲花", "闕崇陽", "絲塔娜", "殷染幽",
    "藍靜冥", "楊古晨", "司徒長生", "無名丐", "聶思泠",
    "郭霆黃", "墨汐若", "沅花", "談笑", "白沫檸",
    "青兒", "珞堇", "龍玉", "七霜", "瑤琴劍",
    "莫縈懷", "黃凱竹", "劉靜靜",
]

OLD_BASE = 1604
OLD_PER_CHAR = 4
NEW_BASE = 1604
NEW_PER_CHAR = 5  # 1 separator + 4 skills


def load_json(filename: str):
    with open(BASE / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data):
    path = BASE / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  Saved {path}")


def make_separator(skill_id: int, name: str) -> dict:
    return {
        "id": skill_id,
        "animationId": 0,
        "damage": {
            "critical": False, "elementId": 0,
            "formula": "0", "type": 0, "variance": 0,
        },
        "description": "", "effects": [],
        "hitType": 0, "iconIndex": 0,
        "message1": "", "message2": "", "messageType": 1,
        "mpCost": 0, "name": name, "note": "",
        "occasion": 0, "repeats": 1,
        "requiredWtypeId1": 0, "requiredWtypeId2": 0,
        "scope": 0, "speed": 0, "stypeId": 0,
        "successRate": 100, "tpCost": 0, "tpGain": 0,
    }


def main():
    print("Loading Skills.json...")
    skills = load_json("Skills.json")

    # ── Build old→new ID mapping ────────────────────────────────────
    id_map = {}  # old_id -> new_id
    for i in range(len(CHAR_NAMES)):
        for j in range(OLD_PER_CHAR):
            old_id = OLD_BASE + i * OLD_PER_CHAR + j
            new_id = NEW_BASE + i * NEW_PER_CHAR + (j + 1)  # +1 for separator
            id_map[old_id] = new_id

    print(f"\nID mapping ({len(id_map)} skills):")
    for i, name in enumerate(CHAR_NAMES):
        old_ids = [OLD_BASE + i * OLD_PER_CHAR + j for j in range(OLD_PER_CHAR)]
        new_ids = [id_map[oid] for oid in old_ids]
        print(f"  {name}: {old_ids} -> {new_ids}")

    # ── Extract current skills ──────────────────────────────────────
    extracted = {}
    for old_id in range(OLD_BASE, OLD_BASE + len(CHAR_NAMES) * OLD_PER_CHAR):
        extracted[old_id] = skills[old_id].copy()

    # ── Ensure array is large enough ────────────────────────────────
    new_end = NEW_BASE + len(CHAR_NAMES) * NEW_PER_CHAR  # 1604 + 115 = 1719
    while len(skills) <= new_end:
        skills.append(None)

    # ── Write new layout ────────────────────────────────────────────
    print(f"\nWriting new layout (IDs {NEW_BASE}-{new_end - 1})...")
    for i, name in enumerate(CHAR_NAMES):
        sep_id = NEW_BASE + i * NEW_PER_CHAR
        sep_name = f"----{name}----"
        skills[sep_id] = make_separator(sep_id, sep_name)
        print(f"  [{sep_id}] {sep_name}")

        for j in range(OLD_PER_CHAR):
            old_id = OLD_BASE + i * OLD_PER_CHAR + j
            new_id = NEW_BASE + i * NEW_PER_CHAR + (j + 1)
            skill = extracted[old_id]
            skill["id"] = new_id
            skills[new_id] = skill
            print(f"    [{new_id}] {skill['name']}")

    # ── Update container Known Skills Lists ─────────────────────────
    print("\nUpdating container references...")
    container_range = range(1880, 1972)
    updated = 0
    for cid in container_range:
        container = skills[cid]
        if not container or not isinstance(container, dict):
            continue
        note = container.get("note", "")
        m = re.search(r"<Known Skills List:\s*([^>]+)>", note)
        if not m:
            continue

        skill_ids = [int(x.strip()) for x in m.group(1).split(",")]
        changed = False
        new_skill_ids = []
        for sid in skill_ids:
            if sid in id_map:
                new_skill_ids.append(id_map[sid])
                changed = True
            else:
                new_skill_ids.append(sid)

        if changed:
            new_list = ", ".join(str(x) for x in new_skill_ids)
            new_tag = f"<Known Skills List: {new_list}>"
            container["note"] = note.replace(m.group(0), new_tag)
            updated += 1
            print(f"  Container {cid} ({container['name']}): {skill_ids} -> {new_skill_ids}")

    print(f"  Updated {updated} containers")

    # ── Verify ──────────────────────────────────────────────────────
    print("\nVerification...")
    ok = True

    # Check separators
    for i, name in enumerate(CHAR_NAMES):
        sep_id = NEW_BASE + i * NEW_PER_CHAR
        if not skills[sep_id]["name"].startswith("----"):
            print(f"  FAIL: Separator {sep_id}")
            ok = False

    # Check skills have correct IDs
    for i in range(len(CHAR_NAMES)):
        for j in range(OLD_PER_CHAR):
            new_id = NEW_BASE + i * NEW_PER_CHAR + (j + 1)
            if skills[new_id]["id"] != new_id:
                print(f"  FAIL: Skill {new_id} has id={skills[new_id]['id']}")
                ok = False
            if not skills[new_id].get("name"):
                print(f"  FAIL: Skill {new_id} has no name")
                ok = False

    # Check no container references stale IDs (old IDs that aren't also valid new IDs)
    new_id_set = set(id_map.values())
    stale_id_set = set(id_map.keys()) - new_id_set
    for cid in container_range:
        container = skills[cid]
        if not container:
            continue
        note = container.get("note", "")
        m = re.search(r"<Known Skills List:\s*([^>]+)>", note)
        if m:
            ids = {int(x.strip()) for x in m.group(1).split(",")}
            stale = ids & stale_id_set
            if stale:
                print(f"  FAIL: Container {cid} still references stale IDs: {stale}")
                ok = False

    if ok:
        print("  All checks passed!")
    else:
        print("\nVerification FAILED. Not saving.")
        return 1

    # ── Save ────────────────────────────────────────────────────────
    print("\nSaving...")
    save_json("Skills.json", skills)
    print(f"\nDone! New range: {NEW_BASE}-{new_end - 1} "
          f"({len(CHAR_NAMES)} separators + {len(CHAR_NAMES) * OLD_PER_CHAR} skills)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
