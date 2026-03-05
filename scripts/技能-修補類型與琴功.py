"""
Three changes to Skills.json:

1. Skills 1351-1879: set stypeId = 0 (無 / hidden from menu)
2. Skills 1880-1971: set stypeId = 1 (武學 / 套路)
3. Skill 1719: create 砸琴成功 for 珞堇
   - Starts at 5 fixed damage
   - Each killing blow with this skill adds +1 (via variable 500)
   - Max damage cap: 600
   - Remove unnecessary Multi-Element tags

Also labels variable 500 as "砸琴成功殺敵數" in System.json.

Usage:
    python scripts/patch_skill_types_and_piano.py
"""

import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"

KILL_VAR = 500  # game variable for 砸琴成功 kill count


def load_json(filename: str):
    with open(BASE / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data):
    path = BASE / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  Saved {path}")


def main():
    print("Loading Skills.json and System.json...")
    skills = load_json("Skills.json")
    system = load_json("System.json")

    # ── Part 1: stypeId = 0 for 1351-1879 ───────────────────────────
    print("\n[1] Setting stypeId=0 for skills 1351-1879...")
    count1 = 0
    for sid in range(1351, 1880):
        if sid < len(skills) and skills[sid] and isinstance(skills[sid], dict):
            if skills[sid]["stypeId"] != 0:
                skills[sid]["stypeId"] = 0
                count1 += 1
    print(f"  Changed {count1} skills to stypeId=0")

    # ── Part 2: stypeId = 1 for 1880-1971 ───────────────────────────
    print("\n[2] Setting stypeId=1 for skills 1880-1971...")
    count2 = 0
    for sid in range(1880, 1972):
        if sid < len(skills) and skills[sid] and isinstance(skills[sid], dict):
            if skills[sid]["stypeId"] != 1:
                skills[sid]["stypeId"] = 1
                count2 += 1
    print(f"  Changed {count2} skills to stypeId=1")

    # ── Part 3: Create 砸琴成功 at ID 1719 ──────────────────────────
    print("\n[3] Creating 砸琴成功 (ID 1719)...")

    # Damage formula: fixed 5 + kill count, capped at 600
    formula = f"Math.min(5 + $gameVariables.value({KILL_VAR}), 600)"

    # Post-apply JS: increment variable on killing blow
    note = (
        "<Color: #FFD700>\n"
        "<Cooldown: 0>\n"
        "<Boost Damage>\n"
        "<JS Post-Apply>\n"
        "if (target.isDead()) {\n"
        f"  const v = $gameVariables.value({KILL_VAR});\n"
        f"  if (v < 595) $gameVariables.setValue({KILL_VAR}, v + 1);\n"
        "}\n"
        "</JS Post-Apply>"
    )

    description = (
        "（\\c[5]類型：外功/攻擊\\c[0]｜\\c[2]範圍：單體\\c[0]｜"
        "\\c[8]增加策略：5\\c[0]）\n"
        "\\c[20]●以琴身猛擊敵人。每次擊殺敵人時威力+1。\\c[0]\n"
        "\\c[16]初始威力5，最高600。\\c[0]"
    )

    skills[1719] = {
        "id": 1719,
        "animationId": 0,
        "damage": {
            "critical": True,
            "elementId": 0,  # normal attack element
            "formula": formula,
            "type": 1,       # HP damage
            "variance": 0,   # fixed damage, no variance
        },
        "description": description,
        "effects": [],
        "hitType": 1,        # physical attack
        "iconIndex": 3159,   # 音律 icon
        "message1": "",
        "message2": "",
        "messageType": 1,
        "mpCost": 0,         # no MP cost (unique weapon skill)
        "name": "砸琴成功",
        "note": note,
        "occasion": 1,       # battle only
        "repeats": 1,
        "requiredWtypeId1": 0,
        "requiredWtypeId2": 0,
        "scope": 1,          # single enemy
        "speed": 0,
        "stypeId": 0,        # 無 (accessed via container only)
        "successRate": 100,
        "tpCost": 0,
        "tpGain": 5,
    }

    print(f"  Name: 砸琴成功")
    print(f"  Formula: {formula}")
    print(f"  Kill counter: variable {KILL_VAR}")
    print(f"  stypeId: 0 (hidden, via container)")

    # ── Part 4: Label variable 500 in System.json ────────────────────
    print(f"\n[4] Labeling variable {KILL_VAR} in System.json...")
    while len(system["variables"]) <= KILL_VAR:
        system["variables"].append("")
    system["variables"][KILL_VAR] = "砸琴成功殺敵數"
    print(f"  var[{KILL_VAR}] = 砸琴成功殺敵數")

    # ── Verification ─────────────────────────────────────────────────
    print("\nVerification...")
    ok = True

    # Check stypeId for range 1351-1879
    for sid in range(1351, 1880):
        s = skills[sid]
        if s and isinstance(s, dict) and s.get("stypeId") != 0:
            print(f"  FAIL: Skill {sid} ({s.get('name','')}) stypeId={s['stypeId']} != 0")
            ok = False
            break

    # Check stypeId for range 1880-1971
    for sid in range(1880, 1972):
        s = skills[sid]
        if s and isinstance(s, dict) and s.get("stypeId") != 1:
            print(f"  FAIL: Skill {sid} ({s.get('name','')}) stypeId={s['stypeId']} != 1")
            ok = False
            break

    # Check 砸琴成功
    piano = skills[1719]
    if piano["name"] != "砸琴成功":
        print(f"  FAIL: Skill 1719 name = {piano['name']!r}")
        ok = False
    if piano["damage"]["type"] != 1:
        print(f"  FAIL: Skill 1719 damage type = {piano['damage']['type']}")
        ok = False
    if "Math.min" not in piano["damage"]["formula"]:
        print(f"  FAIL: Skill 1719 formula missing cap")
        ok = False
    if "Post-Apply" not in piano["note"]:
        print(f"  FAIL: Skill 1719 missing JS Post-Apply")
        ok = False
    if piano["stypeId"] != 0:
        print(f"  FAIL: Skill 1719 stypeId = {piano['stypeId']}")
        ok = False

    # Check variable
    if system["variables"][KILL_VAR] != "砸琴成功殺敵數":
        print(f"  FAIL: Variable {KILL_VAR} not labeled")
        ok = False

    if ok:
        print("  All checks passed!")
    else:
        print("\nVerification FAILED. Not saving.")
        return 1

    # ── Save ──────────────────────────────────────────────────────────
    print("\nSaving...")
    save_json("Skills.json", skills)
    save_json("System.json", system)

    print(f"\nDone!")
    print(f"  Skills 1351-1879: stypeId=0 (無) [{count1} changed]")
    print(f"  Skills 1880-1971: stypeId=1 (武學) [{count2} changed]")
    print(f"  Skill 1719: 砸琴成功 created (damage=5+kills, max 600)")
    print(f"  Variable {KILL_VAR}: 砸琴成功殺敵數")
    return 0


if __name__ == "__main__":
    sys.exit(main())
