#!/usr/bin/env python3
"""
Fix boss markers in Enemies.json:
1. Remove【BOSS】prefix from boss names (restore original names)
2. Insert --BOSS-- separator rows before each boss (like chapter separators)
3. Update Troops.json enemy references to match new IDs
"""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent / "Consilience" / "data"
ENEMIES_PATH = BASE / "Enemies.json"
TROOPS_PATH = BASE / "Troops.json"

# Boss IDs in the CURRENT Enemies.json (before this script runs)
BOSS_OLD_IDS = {8, 10, 25, 34, 43, 52, 57, 61, 70, 73, 79, 82, 83, 84, 85, 86, 87, 88, 89}

def make_boss_separator(new_id):
    """Create a --BOSS-- separator entry matching chapter separator format."""
    return {
        "id": new_id,
        "actions": [],
        "battlerHue": 0,
        "battlerName": "",
        "dropItems": [
            {"dataId": 1, "denominator": 1, "kind": 0},
            {"dataId": 1, "denominator": 1, "kind": 0},
            {"dataId": 1, "denominator": 1, "kind": 0}
        ],
        "exp": 0,
        "traits": [],
        "gold": 0,
        "name": "--BOSS--",
        "note": "",
        "params": [1, 0, 1, 1, 1, 1, 1, 1]
    }

def write_rpgmaker_json(path, data):
    """Write JSON in RPG Maker MZ format (one entry per line)."""
    formatted = "[\n"
    for i, item in enumerate(data):
        if item is None:
            formatted += "null"
        else:
            formatted += json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        if i < len(data) - 1:
            formatted += ","
        formatted += "\n"
    formatted += "]"
    with open(path, "w", encoding="utf-8") as f:
        f.write(formatted)

def main():
    with open(ENEMIES_PATH, "r", encoding="utf-8") as f:
        enemies = json.load(f)
    with open(TROOPS_PATH, "r", encoding="utf-8") as f:
        troops = json.load(f)

    # Build new array with --BOSS-- markers inserted before each boss
    new_enemies = []
    id_map = {}  # old_id -> new_id (for ALL enemies, not just bosses)

    for old_idx, entry in enumerate(enemies):
        if entry is None:
            # Keep null (index 0)
            new_enemies.append(None)
            continue

        old_id = entry["id"]

        # Insert --BOSS-- marker before this boss
        if old_id in BOSS_OLD_IDS:
            marker = make_boss_separator(len(new_enemies))
            new_enemies.append(marker)

        # Remove【BOSS】prefix if present
        if entry["name"].startswith("\u3010BOSS\u3011"):
            entry["name"] = entry["name"][6:]

        # Assign new ID = current position in new array
        new_id = len(new_enemies)
        id_map[old_id] = new_id
        entry["id"] = new_id
        new_enemies.append(entry)

    # Update Troops.json enemy references
    troop_updates = 0
    for troop in troops:
        if troop is None:
            continue
        for member in troop.get("members", []):
            old_eid = member["enemyId"]
            if old_eid in id_map:
                new_eid = id_map[old_eid]
                if old_eid != new_eid:
                    member["enemyId"] = new_eid
                    troop_updates += 1

    # Write back both files
    write_rpgmaker_json(ENEMIES_PATH, new_enemies)
    write_rpgmaker_json(TROOPS_PATH, troops)

    # Report
    bosses_found = [oid for oid in sorted(BOSS_OLD_IDS) if oid in id_map]
    print(f"Inserted {len(bosses_found)} --BOSS-- separator entries")
    print(f"Removed [BOSS] prefix from boss names")
    print(f"Updated {troop_updates} troop member references")
    print(f"Array size: {len(enemies)} -> {len(new_enemies)}")
    print(f"\nBoss ID changes (old -> new):")
    for old_id in sorted(BOSS_OLD_IDS):
        if old_id in id_map:
            enemy_name = ""
            for e in new_enemies:
                if e and e["id"] == id_map[old_id]:
                    enemy_name = e["name"]
                    break
            print(f"  {old_id:3d} -> {id_map[old_id]:3d}  {enemy_name}")

if __name__ == "__main__":
    main()
