"""
Fix actor traits: remove code 41 (Add Skill Type) entries with dataId >= 3.

After compacting skillTypes to ["", "套路", "武學"] (3 entries),
any trait code 41 with dataId >= 3 references a non-existent skill type
and causes VisuMZ_1_SkillsStatesCore to crash with:
  "Cannot read property 'match' of undefined"

Usage:
    python scripts/patch_actor_skill_types.py
"""

import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"
MAX_VALID_STYPE = 2  # skillTypes array has indices 0, 1, 2


def load_json(filename: str):
    with open(BASE / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data):
    path = BASE / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  Saved {path}")


def main():
    print("Loading Actors.json...")
    actors = load_json("Actors.json")

    # Also check Classes.json for safety
    print("Loading Classes.json...")
    classes = load_json("Classes.json")

    print(f"\nScanning actors for trait code 41 with dataId > {MAX_VALID_STYPE}...\n")

    total_removed = 0

    for actor in actors:
        if not actor or not isinstance(actor, dict):
            continue

        traits = actor.get("traits", [])
        invalid = [t for t in traits if t.get("code") == 41 and t.get("dataId", 0) > MAX_VALID_STYPE]

        if invalid:
            actor_id = actor.get("id", "?")
            name = actor.get("name", "?")
            invalid_ids = [t["dataId"] for t in invalid]
            valid = [t for t in traits if not (t.get("code") == 41 and t.get("dataId", 0) > MAX_VALID_STYPE)]

            print(f"  Actor [{actor_id:2d}] {name}")
            print(f"    Before: code 41 dataIds = {[t['dataId'] for t in traits if t.get('code') == 41]}")
            print(f"    Remove: {invalid_ids}")

            actor["traits"] = valid
            remaining = [t["dataId"] for t in valid if t.get("code") == 41]
            print(f"    After:  code 41 dataIds = {remaining}")

            total_removed += len(invalid)

    print(f"\n  Total: {total_removed} invalid traits removed from actors\n")

    # Check classes too
    print(f"Scanning classes for trait code 41 with dataId > {MAX_VALID_STYPE}...\n")

    class_removed = 0
    for cls in classes:
        if not cls or not isinstance(cls, dict):
            continue

        traits = cls.get("traits", [])
        invalid = [t for t in traits if t.get("code") == 41 and t.get("dataId", 0) > MAX_VALID_STYPE]

        if invalid:
            cls_id = cls.get("id", "?")
            name = cls.get("name", "?")
            invalid_ids = [t["dataId"] for t in invalid]
            valid = [t for t in traits if not (t.get("code") == 41 and t.get("dataId", 0) > MAX_VALID_STYPE)]

            print(f"  Class [{cls_id:2d}] {name}")
            print(f"    Before: code 41 dataIds = {[t['dataId'] for t in traits if t.get('code') == 41]}")
            print(f"    Remove: {invalid_ids}")

            cls["traits"] = valid
            remaining = [t["dataId"] for t in valid if t.get("code") == 41]
            print(f"    After:  code 41 dataIds = {remaining}")

            class_removed += len(invalid)

    if class_removed == 0:
        print("  No invalid class traits found.")
    print(f"\n  Total: {class_removed} invalid traits removed from classes\n")

    # Verification
    print("Verification...")
    ok = True

    for actor in actors:
        if not actor or not isinstance(actor, dict):
            continue
        for t in actor.get("traits", []):
            if t.get("code") == 41 and t.get("dataId", 0) > MAX_VALID_STYPE:
                print(f"  FAIL: Actor [{actor['id']}] still has code 41 dataId={t['dataId']}")
                ok = False

    for cls in classes:
        if not cls or not isinstance(cls, dict):
            continue
        for t in cls.get("traits", []):
            if t.get("code") == 41 and t.get("dataId", 0) > MAX_VALID_STYPE:
                print(f"  FAIL: Class [{cls['id']}] still has code 41 dataId={t['dataId']}")
                ok = False

    if ok:
        print("  All checks passed!")
    else:
        print("\n  Verification FAILED. Not saving.")
        return 1

    # Save
    print("\nSaving...")
    save_json("Actors.json", actors)
    if class_removed > 0:
        save_json("Classes.json", classes)

    print(f"\nDone! Removed {total_removed} actor traits + {class_removed} class traits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
