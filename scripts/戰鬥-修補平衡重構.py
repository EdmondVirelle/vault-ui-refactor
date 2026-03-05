"""
Comprehensive Balance Overhaul + Separator Insertion
=====================================================

Part 1: Skills 1001-1315 → 1001-1341
  - Insert 26 ----name---- separator skills (one per discipline)
  - Update balance tags: Color, Cooldown, Boost, Multi-Element,
    Armor/Magic Penetration, OTB penalty for ultimates

Part 2: Skills 391-410 (逍遙筆法)
  - Add missing Boost tags

Part 3: Skills 601-638 (輕功)
  - Add Boost Turns and Cooldown tags

Part 4: Skills 901-930 (畫境/詩境)
  - Add Cooldowns (critical — currently missing entirely)
  - Add Boost tags

Reference checks confirmed ZERO external references to skills 1001-1315:
  - Items.json: 0 refs
  - CommonEvents.json: 0 refs
  - Map files: 0 refs
  - Equipment traits: 0 refs
  - Skill containers: 0 refs
  => ID shifting is safe.

Note: VisuMZ_3_LimitedSkillUses and VisuMZ_3_AutoSkillTriggers are NOT
installed, so <Limited Uses> and <Auto Trigger> tags are NOT used.

Usage:
    python scripts/patch_balance_overhaul.py
"""

import json
import sys
import io
import re
import copy
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"

# ═══════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════

# (name, old_start_id, skill_count, primary_element_name)
DISCIPLINES = [
    ("劍法", 1001, 15, "劍法"),
    ("刀法", 1016, 12, "刀法"),
    ("棍法", 1028, 12, "棍法"),
    ("槍法", 1040, 12, "槍法"),
    ("拳掌", 1052, 12, "拳掌"),
    ("音律", 1064, 12, "音律"),
    ("奇門", 1076, 12, "奇門"),
    ("弓術", 1088, 12, "弓術"),
    ("筆法", 1100, 12, "筆法"),
    ("暗器", 1112, 12, "暗器"),
    ("短兵", 1124, 12, "短兵"),
    ("醫術", 1136, 12, "醫術"),
    ("毒術", 1148, 12, "毒術"),
    ("陰",   1160, 12, "陰"),
    ("陽",   1172, 12, "陽"),
    ("混元", 1184, 12, "混元"),
    ("木",   1196, 12, "木"),
    ("火",   1208, 12, "火"),
    ("土",   1220, 12, "土"),
    ("金",   1232, 12, "金"),
    ("水",   1244, 12, "水"),
    ("風",   1256, 12, "風"),
    ("雷",   1268, 12, "雷"),
    ("炎",   1280, 12, "炎"),
    ("電",   1292, 12, "電"),
    ("寒",   1304, 12, "寒"),
]

# Cooldown by template position (1-12).  Position 1 = basic (no CD).
POS_CD = {1: 0, 2: 2, 3: 3, 4: 3, 5: 4, 6: 2, 7: 2,
           8: 3, 9: 5, 10: 3, 11: 6, 12: 7}

NEW_START = 1001


# ═══════════════════════════════════════════════════════════════════════
# Utility
# ═══════════════════════════════════════════════════════════════════════

def load_json(fn):
    with open(BASE / fn, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(fn, data):
    p = BASE / fn
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  Saved {p}")


def has(note, prefix):
    """Check if note contains a tag with given prefix."""
    return prefix in note


def append_tag(note, tag):
    """Append tag to note (newline-separated)."""
    return (note + "\n" + tag) if note else tag


def make_separator(sid, name):
    """Create a blank separator skill entry."""
    return {
        "id": sid, "animationId": 0,
        "damage": {"critical": False, "elementId": 0,
                    "formula": "0", "type": 0, "variance": 0},
        "description": "", "effects": [],
        "hitType": 0, "iconIndex": 0,
        "message1": "", "message2": "", "messageType": 1,
        "mpCost": 0, "name": name, "note": "",
        "occasion": 0, "repeats": 1,
        "requiredWtypeId1": 0, "requiredWtypeId2": 0,
        "scope": 0, "speed": 0, "stypeId": 0,
        "successRate": 100, "tpCost": 0, "tpGain": 0,
    }


# ═══════════════════════════════════════════════════════════════════════
# Balance-tag helpers
# ═══════════════════════════════════════════════════════════════════════

def auto_color(skill):
    """Determine color tier from skill role and power level."""
    dt = skill["damage"]["type"]
    if dt in (3, 4):              # recovery → green
        return "#00FF7F"
    if dt == 0:                   # buff/utility → cyan
        return "#00BFFF"
    # Attack skills — tier by resource cost
    mp = skill["mpCost"]
    tp = skill["tpCost"]
    if mp >= 50 or (mp == 0 and tp >= 50):
        return "#FFD700"          # gold / ultimate
    if mp >= 25:
        return "#FF8C00"          # orange / mid
    return "#FF5151"              # red / basic


def auto_boost(skill):
    """Determine Boost type from skill properties."""
    dt = skill["damage"]["type"]
    sc = skill["scope"]
    if dt in (1, 2, 5):           # HP/MP damage or drain
        if sc in (3, 4, 5, 6):   # random multi-hit
            return "Repeat"
        return "Damage"
    if dt in (3, 4):              # recovery
        return "Effect Gain"
    return "Turns"                # buff / utility


def cd_from_mp(mp):
    """Heuristic cooldown from MP cost."""
    if mp <= 10:  return 0
    if mp <= 20:  return 2
    if mp <= 32:  return 3
    if mp <= 45:  return 4
    if mp <= 60:  return 5
    if mp <= 75:  return 6
    return 7


def is_gold_attack(skill):
    """True if skill is a gold-tier (ultimate) attack."""
    dt = skill["damage"]["type"]
    if dt not in (1, 2, 5):
        return False
    mp = skill["mpCost"]
    tp = skill["tpCost"]
    return mp >= 50 or (mp == 0 and tp >= 50)


# ═══════════════════════════════════════════════════════════════════════
# Part 1 — Separators + Balance for skills 1001-1315
# ═══════════════════════════════════════════════════════════════════════

def part1(skills):
    print("\n" + "=" * 60)
    print("Part 1: Skills 1001-1315 → 1001-1341")
    print("       (26 separators + balance tags)")
    print("=" * 60)

    total_skills = sum(c for _, _, c, _ in DISCIPLINES)
    n_disc = len(DISCIPLINES)
    new_end = NEW_START + total_skills + n_disc - 1  # 1341

    print(f"  {n_disc} disciplines, {total_skills} skills")
    print(f"  New range: {NEW_START}–{new_end}")

    # Safety check — stubs at 1316..new_end must be empty
    for i in range(1316, new_end + 1):
        s = skills[i]
        if s and isinstance(s, dict) and s.get("name"):
            print(f"  ABORT: Slot {i} occupied by {s['name']!r}")
            return False
    print("  Stubs 1316-1341 confirmed empty ✓")

    # ── Extract all old skills (deep copy) ─────────────────────────
    old = {}
    for _, start, count, _ in DISCIPLINES:
        for j in range(count):
            oid = start + j
            old[oid] = copy.deepcopy(skills[oid])
    print(f"  Extracted {len(old)} skills")

    # ── Build ID mapping (for reference) ───────────────────────────
    id_map = {}  # old_id → new_id
    idx = NEW_START
    for _, old_start, count, _ in DISCIPLINES:
        idx += 1  # separator
        for j in range(count):
            oid = old_start + j
            id_map[oid] = idx
            idx += 1

    # ── Write new layout + apply balance ───────────────────────────
    idx = NEW_START
    n_sep = n_bal = 0

    for disc_name, old_start, count, elem in DISCIPLINES:
        # — Separator —
        skills[idx] = make_separator(idx, f"----{disc_name}----")
        n_sep += 1
        idx += 1

        # — Skills —
        for j in range(count):
            oid = old_start + j
            sk = old[oid]
            sk["id"] = idx
            pos = j + 1       # 1-based position within discipline
            note = sk.get("note", "")
            changed = False

            # 1. Color — update to tier-appropriate
            new_color = auto_color(sk)
            if has(note, "<Color:"):
                updated = re.sub(r"<Color:\s*[^>]+>", f"<Color: {new_color}>", note)
                if updated != note:
                    note = updated
                    changed = True
            else:
                note = (f"<Color: {new_color}>\n" + note) if note else f"<Color: {new_color}>"
                changed = True

            # 2. Cooldown — add if missing (position-based for 1-12, MP-based for extras)
            if pos <= 12:
                cd = POS_CD[pos]
            else:
                cd = cd_from_mp(sk["mpCost"])
            if cd > 0 and not has(note, "<Cooldown:") and not has(note, "<Warmup:"):
                note = append_tag(note, f"<Cooldown: {cd}>")
                changed = True

            # 3. Boost — add if missing
            if not has(note, "<Boost"):
                note = append_tag(note, f"<Boost {auto_boost(sk)}>")
                changed = True

            # 4. Multi-Element — fix missing (especially 劍法 which has none)
            if not has(note, "<Multi-Element:"):
                note = append_tag(note, f"<Multi-Element: {elem}, 江湖武學>")
                note = append_tag(note, "<Multi-Element Rule: Multiply>")
                changed = True
            elif not has(note, "<Multi-Element Rule:"):
                note = append_tag(note, "<Multi-Element Rule: Multiply>")
                changed = True

            # 5. Armor/Magic Penetration — gold-tier attacks only
            if is_gold_attack(sk):
                pt = "Magic Penetration" if sk["hitType"] == 2 else "Armor Penetration"
                if not has(note, f"<{pt}:"):
                    pct = "30%" if sk["scope"] in (1, 7, 9, 11) else "20%"
                    note = append_tag(note, f"<{pt}: {pct}>")
                    changed = True

            # 6. OTB penalty — gold-tier attacks cost next turn
            if is_gold_attack(sk) and not has(note, "<OTB User Next Turn:"):
                note = append_tag(note, "<OTB User Next Turn: -1>")
                changed = True

            sk["note"] = note
            skills[idx] = sk
            if changed:
                n_bal += 1
            idx += 1

    print(f"\n  Separators created: {n_sep}")
    print(f"  Skills with balance updates: {n_bal} / {total_skills}")
    print(f"  Last index written: {idx - 1}")

    # Print a few samples
    print("\n  Sample results:")
    samples = [NEW_START + 1, NEW_START + 12, NEW_START + 17]
    for si in samples:
        sk = skills[si]
        if sk and sk.get("name") and not sk["name"].startswith("----"):
            note_preview = sk["note"][:120].replace("\n", " | ")
            print(f"    [{si}] {sk['name']}: {note_preview}...")

    return True


# ═══════════════════════════════════════════════════════════════════════
# Part 2 — Balance for 391-410 (逍遙筆法)
# ═══════════════════════════════════════════════════════════════════════

def part2(skills):
    print("\n" + "=" * 60)
    print("Part 2: Skills 391-410 (逍遙筆法) — Add Boost")
    print("=" * 60)

    n = 0
    for i in range(391, 411):
        sk = skills[i]
        if not sk or not isinstance(sk, dict) or not sk.get("name"):
            continue
        note = sk.get("note", "")
        if not has(note, "<Boost"):
            bt = auto_boost(sk)
            sk["note"] = append_tag(note, f"<Boost {bt}>")
            n += 1
            print(f"  [{i}] {sk['name']}: +<Boost {bt}>")
    print(f"  Total updated: {n}")


# ═══════════════════════════════════════════════════════════════════════
# Part 3 — Balance for 601-638 (輕功)
# ═══════════════════════════════════════════════════════════════════════

def part3(skills):
    print("\n" + "=" * 60)
    print("Part 3: Skills 601-638 (輕功) — Add Boost + Cooldown")
    print("=" * 60)

    n = 0
    for i in range(601, 639):
        sk = skills[i]
        if not sk or not isinstance(sk, dict) or not sk.get("name"):
            continue
        note = sk.get("note", "")
        changed = False

        # Boost — all 輕功 are self-buff / OTB utility
        if not has(note, "<Boost"):
            bt = auto_boost(sk)
            note = append_tag(note, f"<Boost {bt}>")
            changed = True

        # Cooldown — scaled by MP cost (conservative for low-cost buffs)
        mp = sk["mpCost"]
        if not has(note, "<Cooldown:") and not has(note, "<Warmup:") and mp > 8:
            if mp <= 12:    cd = 1
            elif mp <= 20:  cd = 2
            elif mp <= 35:  cd = 3
            elif mp <= 55:  cd = 4
            else:           cd = 5
            note = append_tag(note, f"<Cooldown: {cd}>")
            changed = True

        if changed:
            sk["note"] = note
            n += 1

    print(f"  Total updated: {n}")


# ═══════════════════════════════════════════════════════════════════════
# Part 4 — Balance for 901-930 (畫境 / 詩境)
# ═══════════════════════════════════════════════════════════════════════

def part4(skills):
    print("\n" + "=" * 60)
    print("Part 4: Skills 901-930 (畫境/詩境) — Add Cooldown + Boost")
    print("=" * 60)

    n = 0
    for i in range(901, 931):
        sk = skills[i]
        if not sk or not isinstance(sk, dict) or not sk.get("name"):
            continue
        note = sk.get("note", "")
        changed = False

        # Cooldown — CRITICAL: these powerful skills had NO cooldowns
        mp = sk["mpCost"]
        tp_gain = sk.get("tpGain", 0)
        if not has(note, "<Cooldown:") and not has(note, "<Warmup:"):
            if mp == 0 and tp_gain == 0:
                # Free/passive skills (e.g. 竹影堅毅, 禪心渡江): CD 3
                cd = 3
            else:
                cd = cd_from_mp(mp)
                cd = max(cd, 2)   # minimum CD 2 for these powerful skills
            note = append_tag(note, f"<Cooldown: {cd}>")
            changed = True

        # Boost
        if not has(note, "<Boost"):
            bt = auto_boost(sk)
            note = append_tag(note, f"<Boost {bt}>")
            changed = True

        if changed:
            sk["note"] = note
            n += 1
            print(f"  [{i}] {sk['name']}: mp={mp}, +CD +Boost")

    print(f"  Total updated: {n}")


# ═══════════════════════════════════════════════════════════════════════
# Verification
# ═══════════════════════════════════════════════════════════════════════

def verify(skills):
    print("\n" + "=" * 60)
    print("Verification")
    print("=" * 60)
    ok = True

    # ── Part 1: Check separator + skill layout ─────────────────────
    print("\n  [Part 1] Checking separators and skill layout...")
    idx = NEW_START
    for disc_name, _, count, _ in DISCIPLINES:
        sep = skills[idx]
        expected = f"----{disc_name}----"
        if not sep or sep.get("name") != expected:
            actual = sep.get("name", "null") if sep else "null"
            print(f"    FAIL: idx {idx} expected {expected!r}, got {actual!r}")
            ok = False
        idx += 1
        for j in range(count):
            sk = skills[idx]
            if not sk or not sk.get("name"):
                print(f"    FAIL: Missing skill at idx {idx}")
                ok = False
            elif sk["id"] != idx:
                print(f"    FAIL: Skill {idx} has id={sk['id']}")
                ok = False
            idx += 1

    # Check balance tags on samples
    print("  [Part 1] Checking balance tags on samples...")
    test_indices = [NEW_START + 1, NEW_START + 17, 1100, 1200, 1330]
    for ti in test_indices:
        sk = skills[ti]
        if not sk or not sk.get("name") or sk["name"].startswith("----"):
            continue
        note = sk.get("note", "")
        tags_ok = True
        for tag_prefix, label in [
            ("<Color:", "Color"),
            ("<Boost", "Boost"),
            ("<Multi-Element:", "Multi-Element"),
        ]:
            if not has(note, tag_prefix):
                print(f"    FAIL: [{ti}] {sk['name']} missing {label}")
                ok = tags_ok = False
        # Gold attacks should have penetration + OTB
        if is_gold_attack(sk):
            has_pen = has(note, "<Armor Penetration:") or has(note, "<Magic Penetration:")
            if not has_pen:
                print(f"    FAIL: [{ti}] {sk['name']} gold attack missing penetration")
                ok = tags_ok = False
            if not has(note, "<OTB User Next Turn:"):
                print(f"    FAIL: [{ti}] {sk['name']} gold attack missing OTB penalty")
                ok = tags_ok = False
        if tags_ok:
            print(f"    OK: [{ti}] {sk['name']}")

    # ── Part 2: 391-410 have Boost ────────────────────────────────
    print("\n  [Part 2] Checking 391-410 Boost tags...")
    p2_ok = True
    for i in range(391, 411):
        sk = skills[i]
        if sk and sk.get("name") and not has(sk.get("note", ""), "<Boost"):
            print(f"    FAIL: [{i}] {sk['name']} missing Boost")
            ok = p2_ok = False
    if p2_ok:
        print("    All 20 skills have Boost ✓")

    # ── Part 3: 601-638 have Boost ────────────────────────────────
    print("\n  [Part 3] Checking 601-638 Boost tags...")
    p3_ok = True
    for i in range(601, 639):
        sk = skills[i]
        if sk and sk.get("name") and not has(sk.get("note", ""), "<Boost"):
            print(f"    FAIL: [{i}] {sk['name']} missing Boost")
            ok = p3_ok = False
    if p3_ok:
        print("    All 輕功 skills have Boost ✓")

    # ── Part 4: 901-930 have Cooldown + Boost ─────────────────────
    print("\n  [Part 4] Checking 901-930 Cooldown + Boost...")
    p4_ok = True
    for i in range(901, 931):
        sk = skills[i]
        if not sk or not isinstance(sk, dict) or not sk.get("name"):
            continue
        note = sk.get("note", "")
        if not has(note, "<Cooldown:"):
            print(f"    FAIL: [{i}] {sk['name']} missing Cooldown")
            ok = p4_ok = False
        if not has(note, "<Boost"):
            print(f"    FAIL: [{i}] {sk['name']} missing Boost")
            ok = p4_ok = False
    if p4_ok:
        print("    All 畫境/詩境 skills have Cooldown + Boost ✓")

    # ── Overall ────────────────────────────────────────────────────
    if ok:
        print("\n  ═══ ALL CHECKS PASSED ✓ ═══")
    else:
        print("\n  ═══ VERIFICATION FAILED ═══")
    return ok


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("Loading Skills.json...")
    skills = load_json("Skills.json")
    print(f"  Array length: {len(skills)}")

    if not part1(skills):
        print("\nPart 1 failed. Aborting.")
        return 1

    part2(skills)
    part3(skills)
    part4(skills)

    if not verify(skills):
        print("\nVerification failed. NOT saving.")
        return 1

    print("\nSaving...")
    save_json("Skills.json", skills)

    # ── Final summary ──────────────────────────────────────────────
    total_skills = sum(c for _, _, c, _ in DISCIPLINES)
    n_disc = len(DISCIPLINES)
    new_end = NEW_START + total_skills + n_disc - 1

    print(f"\n{'=' * 60}")
    print("Done! Summary:")
    print(f"  Part 1: {n_disc} separators + {total_skills} skills → IDs {NEW_START}-{new_end}")
    print(f"          + Color, Cooldown, Boost, Multi-Element, Pen, OTB tags")
    print(f"  Part 2: 391-410 (逍遙筆法) + Boost tags")
    print(f"  Part 3: 601-638 (輕功) + Boost + Cooldown tags")
    print(f"  Part 4: 901-930 (畫境/詩境) + Cooldown + Boost tags")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
