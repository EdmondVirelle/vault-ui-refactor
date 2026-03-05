#!/usr/bin/env python3
"""
patch_boost_tags.py — Add VisuMZ_3_BoostAction notetags to Skills, States, Enemies, and Classes.

Patches:
  1. Skills.json  — Boost tags for enemy skills (12-211) and player skills (1352-1879)
  2. States.json  — <Boost Sealed> on State 7 (散功)
  3. Enemies.json — <Boost Skill> AI tags on boss enemies
  4. Classes.json — <Boost Points Battle Start> and <Boost Points Regen> on all classes
"""

import json
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "Consilience" / "data"

# ---------------------------------------------------------------------------
# Skill ID ranges to process
# ---------------------------------------------------------------------------
ENEMY_SKILL_RANGE = range(12, 212)       # IDs 12-211
PLAYER_SKILL_RANGE = range(1352, 1880)   # IDs 1352-1879

# Negative debuff states (stat-down states)
NEGATIVE_STAT_STATES = set(range(61, 76))  # 61-75: 外功/內功/外防/內防/輕功 下降
# Additional well-known negative states for debuff detection
DEBUFF_STATES = NEGATIVE_STAT_STATES | {
    3,   # 冰封
    4,   # 中毒
    5,   # 封內
    6,   # 破防
    7,   # 散功
    8,   # 暈眩
    9,   # 虛弱
    10,  # 重傷
    11,  # 劇毒
    12,  # 定身
    13,  # 恐懼
    14,  # 寒劫
    18,  # 擴散
    19,  # 降療
    25,  # 力竭
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def is_separator(skill: dict) -> bool:
    """Check if a skill entry is a separator (e.g. ----敵軍----)."""
    name = skill.get("name", "")
    return name.startswith("----") or name.startswith("【") or name == ""


def has_boost_tags(note: str) -> bool:
    """Check if note already contains Boost-related tags."""
    return "<Boost " in note or "<User Boost " in note or "<Target Boost " in note


def has_otb_instant(note: str) -> bool:
    """Check if skill has OTB Instant (shouldn't be boostable)."""
    return "<OTB Instant>" in note or "<OTB Instant Use>" in note


def append_note(obj: dict, tags: str) -> None:
    """Safely append tag(s) to an object's note field."""
    note = obj.get("note", "")
    if note and not note.endswith("\n"):
        note += "\n"
    note += tags
    obj["note"] = note


def is_damage_skill(skill: dict) -> bool:
    """Check if skill deals damage (type 1=HP damage, 5=HP drain, 6=MP drain)."""
    return skill["damage"]["type"] in (1, 5, 6)


def is_heal_skill(skill: dict) -> bool:
    """Check if skill heals (type 3=HP recover, 4=MP recover)."""
    return skill["damage"]["type"] in (3, 4)


def has_state_effects(skill: dict) -> bool:
    """Check if skill applies states via effects (code 21 = Add State)."""
    return any(e["code"] == 21 for e in skill.get("effects", []))


def has_revive_effect(skill: dict) -> bool:
    """Check if skill has revive effect (code 22 with dataId 0 = Recover HP %)."""
    # Actually in RPG Maker MZ, revive is typically:
    # - scope 9 (1 Ally Dead) or 10 (All Allies Dead)
    # - OR effects with code 33 (Remove State, dataId=1 for KO)
    scope = skill.get("scope", 0)
    if scope in (9, 10):
        return True
    # Check for effect code 22 (Recover HP) with an alive check
    return False


def applies_negative_states(skill: dict) -> bool:
    """Check if skill applies any negative/debuff states."""
    for e in skill.get("effects", []):
        if e["code"] == 21 and e["dataId"] in DEBUFF_STATES:
            return True
    return False


def targets_enemies(skill: dict) -> bool:
    """Check if skill targets enemies (scope 1-6)."""
    return skill.get("scope", 0) in (1, 2, 3, 4, 5, 6)


def is_capstone(skill: dict) -> bool:
    """Check if skill is a capstone (tpCost >= 50)."""
    return skill.get("tpCost", 0) >= 50


def classify_skill(skill: dict) -> str | None:
    """
    Classify a skill and return its primary Boost tag.
    Returns None if skill should be skipped.
    """
    # Multi-hit takes priority over damage
    if is_damage_skill(skill) and skill.get("repeats", 1) >= 2:
        return "<Boost Repeat>"

    # Damage (single or AoE)
    if is_damage_skill(skill):
        return "<Boost Damage>"

    # Heal
    if is_heal_skill(skill):
        return "<Boost Effect Gain>"

    # Revive
    if has_revive_effect(skill):
        return "<Boost Effect Gain>"

    # Buff/Debuff (state-applying, damage.type=0)
    if skill["damage"]["type"] == 0:
        if has_state_effects(skill):
            return "<Boost Turns>"

        # Pure utility (no states but still does something — TP/OTB manipulation)
        return "<Boost Turns>"

    return "<Boost Turns>"


# ---------------------------------------------------------------------------
# Part 1: Patch Skills
# ---------------------------------------------------------------------------

def patch_skills(skills: list) -> int:
    """Add Boost tags to skills in designated ranges. Returns count of modified skills."""
    count = 0
    for idx, skill in enumerate(skills):
        if skill is None:
            continue

        sid = skill.get("id", 0)
        if sid not in ENEMY_SKILL_RANGE and sid not in PLAYER_SKILL_RANGE:
            continue

        # Skip separators and empty skills
        if is_separator(skill):
            continue

        # Skip if occasion is 0 (never usable) — these are template/unused skills
        if skill.get("occasion", 0) == 0:
            continue

        note = skill.get("note", "")

        # Skip if already tagged
        if has_boost_tags(note):
            continue

        # Skip OTB Instant skills
        if has_otb_instant(note):
            continue

        # Classify and build tags
        primary_tag = classify_skill(skill)
        if primary_tag is None:
            continue

        tags = [primary_tag]

        # Capstone bonus: tpCost >= 50
        if is_capstone(skill):
            tags.append("<User Boost Points: +1>")

        # Debuff skills targeting enemies with negative states
        if targets_enemies(skill) and applies_negative_states(skill):
            tags.append("<Target Boost Points: -1>")

        append_note(skill, "\n".join(tags))
        count += 1

    return count


# ---------------------------------------------------------------------------
# Part 2: Patch States
# ---------------------------------------------------------------------------

def patch_states(states: list) -> int:
    """Add <Boost Sealed> to State 7 (散功). Returns count of modified states."""
    count = 0
    for state in states:
        if state is None:
            continue
        if state.get("id") == 7:
            note = state.get("note", "")
            if "<Boost Sealed>" not in note:
                append_note(state, "<Boost Sealed>")
                count += 1
    return count


# ---------------------------------------------------------------------------
# Part 3: Patch Enemies (Boss AI)
# ---------------------------------------------------------------------------

def is_boss(enemy: dict) -> bool:
    """Heuristic: is this enemy a boss?"""
    note = enemy.get("note", "")

    # Check Break Shields >= 6
    m = re.search(r"<Break Shields:\s*(\d+)>", note)
    if m and int(m.group(1)) >= 6:
        return True

    # Check for boss passive states (101, 102 are common boss passives)
    if "<Passive State: 101>" in note or "<Passive State: 102>" in note:
        return True

    # Check maxHP (params[0]) >= 3000 — bosses tend to have high HP
    params = enemy.get("params", [])
    if len(params) > 0 and params[0] >= 3000:
        return True

    return False


def is_mid_boss(enemy: dict) -> bool:
    """Heuristic: is this a mid-boss / elite? (not a full boss but stronger than trash)"""
    note = enemy.get("note", "")
    params = enemy.get("params", [])

    # Break Shields 4-5
    m = re.search(r"<Break Shields:\s*(\d+)>", note)
    if m and 4 <= int(m.group(1)) <= 5:
        return True

    # HP 1000-2999
    if len(params) > 0 and 1000 <= params[0] < 3000:
        return True

    return False


def get_best_skill(enemy: dict, skills: list) -> dict | None:
    """Find the enemy's highest-damage skill for AI tagging."""
    best_skill = None
    best_rating = -1

    for action in enemy.get("actions", []):
        sid = action.get("skillId", 0)
        if sid <= 0 or sid >= len(skills) or skills[sid] is None:
            continue

        skill = skills[sid]
        # Only consider damage skills
        if not is_damage_skill(skill):
            continue

        # Use a heuristic: prefer higher multiplier skills
        # We'll look at the rating as a rough indicator too
        # But mainly, try to find the skill with highest atk multiplier in formula
        formula = skill["damage"].get("formula", "")

        # Extract the first multiplier (e.g., a.atk*7.0 -> 7.0)
        multiplier = 0.0
        m = re.search(r"a\.(?:atk|mat)\s*\*\s*([\d.]+)", formula)
        if m:
            multiplier = float(m.group(1))

        if multiplier > best_rating:
            best_rating = multiplier
            best_skill = skill

    return best_skill


def patch_enemies(enemies: list, skills: list) -> int:
    """Add <Boost Skill> AI tags to boss/elite enemies. Returns count of modified."""
    count = 0
    for enemy in enemies:
        if enemy is None:
            continue

        name = enemy.get("name", "")
        if not name or name.startswith("----") or name.startswith("--BOSS--"):
            continue

        note = enemy.get("note", "")
        if "<Boost Skill" in note:
            continue

        boss = is_boss(enemy)
        mid = is_mid_boss(enemy) if not boss else False

        if not boss and not mid:
            continue

        best = get_best_skill(enemy, skills)
        if best is None:
            continue

        skill_name = best["name"]
        level = "Full" if boss else "At Least 3"
        tag = f"<Boost Skill {skill_name}: {level}>"
        append_note(enemy, tag)
        count += 1

    return count


# ---------------------------------------------------------------------------
# Part 4: Patch Classes
# ---------------------------------------------------------------------------

BOOST_CLASS_TAGS = "<Boost Points Battle Start: 1>\n<Boost Points Regen: +1>"


def patch_classes(classes: list) -> int:
    """Add Boost regen tags to all non-null, non-header classes. Returns count."""
    count = 0
    for cls in classes:
        if cls is None:
            continue

        name = cls.get("name", "")
        # Skip header classes (name starts with ---- and has no learnings)
        # Actually per plan: ALL 92 classes need tags
        if not name:
            continue

        note = cls.get("note", "")
        if "<Boost Points" in note:
            continue

        # Skip separator-style classes (name starts with ---- and has no learnings)
        # These are section headers like "----東方啟----"
        if name.startswith("----") and not cls.get("learnings", []):
            continue

        append_note(cls, BOOST_CLASS_TAGS)
        count += 1

    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Load all JSON files
    skills_path = DATA_DIR / "Skills.json"
    states_path = DATA_DIR / "States.json"
    enemies_path = DATA_DIR / "Enemies.json"
    classes_path = DATA_DIR / "Classes.json"

    for p in (skills_path, states_path, enemies_path, classes_path):
        if not p.exists():
            print(f"ERROR: {p} not found!", file=sys.stderr)
            sys.exit(1)

    skills = json.loads(skills_path.read_text(encoding="utf-8"))
    states = json.loads(states_path.read_text(encoding="utf-8"))
    enemies = json.loads(enemies_path.read_text(encoding="utf-8"))
    classes = json.loads(classes_path.read_text(encoding="utf-8"))

    # Patch
    n_skills = patch_skills(skills)
    n_states = patch_states(states)
    n_enemies = patch_enemies(enemies, skills)
    n_classes = patch_classes(classes)

    # Write back
    skills_path.write_text(json.dumps(skills, ensure_ascii=False), encoding="utf-8")
    states_path.write_text(json.dumps(states, ensure_ascii=False), encoding="utf-8")
    enemies_path.write_text(json.dumps(enemies, ensure_ascii=False), encoding="utf-8")
    classes_path.write_text(json.dumps(classes, ensure_ascii=False), encoding="utf-8")

    print(f"=== Boost Tags Patch Complete ===")
    print(f"  Skills modified:  {n_skills}")
    print(f"  States modified:  {n_states}")
    print(f"  Enemies modified: {n_enemies}")
    print(f"  Classes modified: {n_classes}")


if __name__ == "__main__":
    main()
