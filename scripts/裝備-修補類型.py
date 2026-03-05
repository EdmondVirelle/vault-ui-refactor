"""
Compact equipTypes by removing empty slots 4 and 5.

Before: ["", "武器", "身體", "指環", "", "", "功法", "輕功", "殘卷", "典籍"]
After:  ["", "武器", "身體", "指環", "功法", "輕功", "殘卷", "典籍"]

Changes:
  1. System.json equipTypes: remove indices 4,5
  2. Armors.json etypeId: 6→4, 7→5, 8→6, 9→7
  3. Actors.json equips arrays: drop slots [3],[4], shift [5-8]→[3-6]
  4. System.json testBattlers equips: same remapping

Usage:
    python scripts/patch_equip_types.py
"""

import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"

# etypeId remapping: old → new
ETYPE_MAP = {6: 4, 7: 5, 8: 6, 9: 7}

# Old equips layout (0-indexed):
#   [0]=weapon [1]=body [2]=ring [3]=slot4(empty) [4]=slot5(empty)
#   [5]=gongfa [6]=qinggong [7]=canjuan [8]=dianji
# New equips layout:
#   [0]=weapon [1]=body [2]=ring [3]=gongfa [4]=qinggong [5]=canjuan [6]=dianji
OLD_SLOT_COUNT = 9
NEW_SLOT_COUNT = 7
# Mapping: new_index → old_index
SLOT_MAP = {0: 0, 1: 1, 2: 2, 3: 5, 4: 6, 5: 7, 6: 8}


def load_json(filename: str):
    with open(BASE / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data):
    path = BASE / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  Saved {path}")


def remap_equips(old_equips: list) -> list:
    """Remap an equips array from 9-slot to 7-slot layout."""
    # Pad old array to 9 if shorter
    padded = list(old_equips) + [0] * (OLD_SLOT_COUNT - len(old_equips))
    new_equips = []
    for new_i in range(NEW_SLOT_COUNT):
        old_i = SLOT_MAP[new_i]
        if old_i < len(padded):
            new_equips.append(padded[old_i])
        else:
            new_equips.append(0)
    return new_equips


def main():
    print("Loading data files...")
    system = load_json("System.json")
    armors = load_json("Armors.json")
    actors = load_json("Actors.json")

    # ── Part 1: System.json equipTypes ──────────────────────────────
    print("\n[1] Compacting equipTypes...")
    old_types = system["equipTypes"]
    print(f"  Before ({len(old_types)}): {old_types}")

    new_types = ["", "武器", "身體", "指環", "功法", "輕功", "殘卷", "典籍"]
    system["equipTypes"] = new_types
    print(f"  After  ({len(new_types)}): {new_types}")

    # ── Part 2: Armors.json etypeId ─────────────────────────────────
    print("\n[2] Remapping armor etypeIds...")
    armor_counts = {6: 0, 7: 0, 8: 0, 9: 0}
    for armor in armors:
        if not armor or not isinstance(armor, dict):
            continue
        old_etype = armor.get("etypeId", 0)
        if old_etype in ETYPE_MAP:
            armor["etypeId"] = ETYPE_MAP[old_etype]
            armor_counts[old_etype] += 1

    for old, new in ETYPE_MAP.items():
        name = {6: "功法", 7: "輕功", 8: "殘卷", 9: "典籍"}[old]
        print(f"  etypeId {old}→{new} ({name}): {armor_counts[old]} armors")
    print(f"  Total: {sum(armor_counts.values())} armors remapped")

    # ── Part 3: Actors.json equips ──────────────────────────────────
    print("\n[3] Remapping actor equips arrays...")
    actor_count = 0
    for actor in actors:
        if not actor or not isinstance(actor, dict):
            continue
        old_eq = actor.get("equips", [])
        if not old_eq:
            continue
        new_eq = remap_equips(old_eq)
        actor["equips"] = new_eq
        actor_count += 1
        name = actor.get("name", "?")
        if old_eq != new_eq[:len(old_eq)] or len(old_eq) != len(new_eq):
            print(f"  [{actor['id']:2d}] {name:<8s} {old_eq} → {new_eq}")

    print(f"  Total: {actor_count} actors remapped")

    # ── Part 4: System.json testBattlers equips ─────────────────────
    print("\n[4] Remapping testBattlers equips...")
    for i, tb in enumerate(system.get("testBattlers", [])):
        old_eq = tb.get("equips", [])
        new_eq = remap_equips(old_eq)
        tb["equips"] = new_eq
        print(f"  [{i}] actorId={tb['actorId']} {old_eq} → {new_eq}")

    # ── Verification ────────────────────────────────────────────────
    print("\nVerification...")
    ok = True

    # Check equipTypes
    if system["equipTypes"] != new_types:
        print("  FAIL: equipTypes mismatch")
        ok = False
    if len(system["equipTypes"]) != 8:
        print(f"  FAIL: equipTypes length = {len(system['equipTypes'])}, expected 8")
        ok = False

    # Check no armor still has etypeId 6-9
    for armor in armors:
        if not armor or not isinstance(armor, dict):
            continue
        etype = armor.get("etypeId", 0)
        if etype > 7:
            print(f"  FAIL: Armor [{armor['id']}] {armor['name']} still has etypeId={etype}")
            ok = False
            break

    # Check armor counts by new etypeId
    new_counts = {}
    for armor in armors:
        if not armor or not isinstance(armor, dict):
            continue
        et = armor.get("etypeId", 0)
        new_counts[et] = new_counts.get(et, 0) + 1
    print(f"  Armor distribution: { {k: new_counts.get(k,0) for k in range(1,8)} }")

    # Check actor equips are all 7 slots or fewer
    for actor in actors:
        if not actor or not isinstance(actor, dict):
            continue
        eq = actor.get("equips", [])
        if len(eq) > NEW_SLOT_COUNT:
            print(f"  FAIL: Actor [{actor['id']}] has {len(eq)} equip slots, max {NEW_SLOT_COUNT}")
            ok = False
            break

    # Check testBattlers equips
    for i, tb in enumerate(system.get("testBattlers", [])):
        eq = tb.get("equips", [])
        if len(eq) > NEW_SLOT_COUNT:
            print(f"  FAIL: testBattler [{i}] has {len(eq)} equip slots")
            ok = False

    if ok:
        print("  All checks passed!")
    else:
        print("\nVerification FAILED. Not saving.")
        return 1

    # ── Save ────────────────────────────────────────────────────────
    print("\nSaving...")
    save_json("System.json", system)
    save_json("Armors.json", armors)
    save_json("Actors.json", actors)

    print(f"\nDone!")
    print(f"  equipTypes: 10 → 8 (removed empty slots 4,5)")
    print(f"  Armors: {sum(armor_counts.values())} remapped (6→4, 7→5, 8→6, 9→7)")
    print(f"  Actors: {actor_count} equips arrays compacted (9-slot → 7-slot)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
