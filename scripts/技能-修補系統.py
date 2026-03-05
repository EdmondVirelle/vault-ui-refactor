#!/usr/bin/env python3
"""
patch_skill_system.py — 技能系統大重構

Usage: python scripts/patch_skill_system.py <stage>

Stages:
  icons      - Assign iconIndex to skills 1002-1341
  anims      - Assign animationId to skills 1002-1341
  defense    - Defense system restructure (1974→1978, states, counters)
  debuffs    - Debuff state conversion (code 32 → states 61-78)
  fix_descs  - Remove code 32 effects + fix description terminology
  learn_tags - Add missing Learn tags (混元 group + 3 ultimates)
  fix_buffs  - Fix buff JS + wuxing/tianxiang Learn tags
  verify     - Run all verification checks
"""

import json
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "Consilience" / "data"

# ── Shared helpers ──────────────────────────────────────────────────────

def write_json_array(path: Path, data: list):
    """Write a JSON array with one entry per line (RPG Maker MZ format)."""
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('[\n')
        last = len(data) - 1
        for i, entry in enumerate(data):
            line = json.dumps(entry, ensure_ascii=False, separators=(',', ':'))
            if i < last:
                line += ','
            f.write(line + '\n')
        f.write(']\n')


def load_json(filename: str) -> list:
    path = DATA_DIR / filename
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save_json(filename: str, data: list):
    write_json_array(DATA_DIR / filename, data)


# ── Separator skill IDs (not to be modified) ────────────────────────────

SEPARATORS = {
    1001, 1017, 1030, 1043, 1056, 1069, 1082, 1095, 1108, 1121, 1134,
    1147, 1160, 1173, 1186, 1199, 1212, 1225, 1238, 1251, 1264, 1277,
    1290, 1303, 1316, 1329,
}

# ── Defense skill IDs ───────────────────────────────────────────────────

DEFENSE_SKILL_IDS = {
    1014, 1027, 1040, 1053, 1066, 1079, 1092,
    # 1105 is NOT a defense skill (弓術 attack)
    1118, 1131, 1144, 1157, 1170,
    1183, 1196, 1209,
    1222, 1235, 1248, 1261, 1274,
    1287, 1300, 1313, 1326, 1339,
}

# IDs to remove from skill 1974 (江湖武學) Known Skills List
DEFENSE_IDS_REMOVE_FROM_1974 = {
    1014, 1027, 1040, 1053, 1066, 1079, 1092, 1105,
    1118, 1131, 1144, 1157, 1170, 1183, 1196, 1209,
    1222, 1235, 1248, 1261, 1274, 1287, 1300, 1313, 1326, 1339,
}

# ════════════════════════════════════════════════════════════════════════
#  STAGE 1: ICON ASSIGNMENT
# ════════════════════════════════════════════════════════════════════════

# (start_id, end_id, iconIndex)
ICON_GROUPS = [
    # Weapon groups
    (1002, 1016, 3154),  # 劍法
    (1018, 1029, 3155),  # 刀法
    (1031, 1042, 3156),  # 棍法
    (1044, 1055, 3157),  # 槍法
    (1057, 1068, 3158),  # 拳掌
    (1070, 1081, 3159),  # 音律
    (1083, 1094, 3165),  # 奇門
    (1096, 1107, 3164),  # 弓術
    (1109, 1120, 3160),  # 筆法
    (1122, 1133, 3166),  # 暗器
    (1135, 1146, 3172),  # 短兵
    (1148, 1159, 3171),  # 醫術
    (1161, 1172, 3170),  # 毒術
    # Inner groups
    (1174, 1185, 3022),  # 陰
    (1187, 1198, 3010),  # 陽
    (1200, 1211, 3021),  # 混元
    # Element groups
    (1213, 1224, 1799),  # 木
    (1226, 1237, 1509),  # 火
    (1239, 1250, 1572),  # 土
    (1252, 1263, 2130),  # 金
    (1265, 1276, 1571),  # 水
    (1278, 1289, 1573),  # 風
    (1291, 1302, 1582),  # 雷
    (1304, 1315, 1568),  # 炎
    (1317, 1328, 1570),  # 電
    (1330, 1341, 1568),  # 寒
]

ICON_EXCEPTIONS = {
    1157: 3145,  # 藥師琉璃 → 降療
}


def stage_icons():
    """Assign iconIndex to all skills 1002-1341."""
    print("=== Stage: Icons ===")
    skills = load_json("Skills.json")
    count = 0

    for start, end, icon in ICON_GROUPS:
        for sid in range(start, end + 1):
            if sid in SEPARATORS:
                continue
            skill = skills[sid]
            if skill is None:
                continue
            new_icon = ICON_EXCEPTIONS.get(sid, icon)
            if skill["iconIndex"] != new_icon:
                skill["iconIndex"] = new_icon
                count += 1

    # Fix 寒組 1339-1341 iconIndex=0 (already handled by group, but verify)
    for sid in [1339, 1340, 1341]:
        if skills[sid]["iconIndex"] == 0:
            skills[sid]["iconIndex"] = 1568
            print(f"  [FIX] Skill {sid} iconIndex 0 → 1568")

    save_json("Skills.json", skills)
    print(f"  Updated {count} skill icons")
    return 0


# ════════════════════════════════════════════════════════════════════════
#  STAGE 2: ANIMATION ASSIGNMENT
# ════════════════════════════════════════════════════════════════════════

# group range → {scope_type: animation_id}
ANIM_MAP: dict[tuple[int, int], dict[str, int]] = {
    # Weapon groups
    (1002, 1016): {"single": 6,   "all": 8,   "heal": 41, "buff": 51},   # 劍法
    (1018, 1029): {"single": 6,   "all": 7,   "heal": 41, "buff": 51},   # 刀法
    (1031, 1042): {"single": 1,   "all": 2,   "heal": 41, "buff": 51},   # 棍法
    (1044, 1055): {"single": 11,  "all": 12,  "heal": 41, "buff": 51},   # 槍法
    (1057, 1068): {"single": 16,  "all": 17,  "heal": 41, "buff": 51},   # 拳掌
    (1070, 1081): {"single": 209, "all": 210, "heal": 41, "buff": 51},   # 音律
    (1083, 1094): {"single": 30,  "all": 31,  "heal": 41, "buff": 51},   # 奇門
    (1096, 1107): {"single": 29,  "all": 113, "heal": 41, "buff": 51},   # 弓術
    (1109, 1120): {"single": 11,  "all": 26,  "heal": 41, "buff": 51},   # 筆法
    (1122, 1133): {"single": 30,  "all": 113, "heal": 41, "buff": 51},   # 暗器
    (1135, 1146): {"single": 6,   "all": 8,   "heal": 41, "buff": 51},   # 短兵
    (1148, 1159): {"single": 41,  "all": 43,  "heal": 41, "buff": 51},   # 醫術
    (1161, 1172): {"single": 59,  "all": 227, "heal": 41, "buff": 51},   # 毒術
    # Inner groups
    (1174, 1185): {"single": 101, "all": 103, "heal": 41, "buff": 51},   # 陰
    (1187, 1198): {"single": 96,  "all": 98,  "heal": 41, "buff": 51},   # 陽
    (1200, 1211): {"single": 106, "all": 108, "heal": 41, "buff": 51},   # 混元
    # Element groups
    (1213, 1224): {"single": 91,  "all": 93,  "heal": 41, "buff": 51},   # 木
    (1226, 1237): {"single": 66,  "all": 68,  "heal": 41, "buff": 51},   # 火
    (1239, 1250): {"single": 86,  "all": 88,  "heal": 41, "buff": 51},   # 土
    (1252, 1263): {"single": 96,  "all": 98,  "heal": 41, "buff": 51},   # 金
    (1265, 1276): {"single": 81,  "all": 83,  "heal": 41, "buff": 51},   # 水
    (1278, 1289): {"single": 91,  "all": 93,  "heal": 41, "buff": 51},   # 風
    (1291, 1302): {"single": 76,  "all": 78,  "heal": 41, "buff": 51},   # 雷
    (1304, 1315): {"single": 66,  "all": 68,  "heal": 41, "buff": 51},   # 炎
    (1317, 1328): {"single": 76,  "all": 78,  "heal": 41, "buff": 51},   # 電
    (1330, 1341): {"single": 71,  "all": 73,  "heal": 41, "buff": 51},   # 寒
}

DEFENSE_ANIM = 229  # プロテクション


def scope_to_anim_type(scope: int) -> str:
    """Map RPG Maker scope to animation type key."""
    if scope in (1, 3, 4, 5, 6):
        return "single"
    elif scope == 2:
        return "all"
    elif scope in (7, 8, 9, 10):
        return "heal"
    elif scope == 11:
        return "buff"
    return "single"  # fallback


def stage_anims():
    """Assign animationId to all skills 1002-1341."""
    print("=== Stage: Animations ===")
    skills = load_json("Skills.json")
    count = 0

    for (start, end), anims in ANIM_MAP.items():
        for sid in range(start, end + 1):
            if sid in SEPARATORS:
                continue
            skill = skills[sid]
            if skill is None:
                continue

            # Defense skills always get 229
            if sid in DEFENSE_SKILL_IDS:
                new_anim = DEFENSE_ANIM
            else:
                atype = scope_to_anim_type(skill["scope"])
                new_anim = anims.get(atype, anims.get("single", 0))

            if skill["animationId"] != new_anim:
                skill["animationId"] = new_anim
                count += 1

    save_json("Skills.json", skills)
    print(f"  Updated {count} skill animations")
    return 0


# ════════════════════════════════════════════════════════════════════════
#  STAGE 3: DEFENSE SYSTEM RESTRUCTURE
# ════════════════════════════════════════════════════════════════════════

def parse_known_skills(note: str) -> list[int]:
    """Parse all Known Skills List tags from a skill's note."""
    ids = []
    for m in re.finditer(r'<Known Skills List:\s*(.+?)>', note):
        content = m.group(1)
        for part in content.split(','):
            part = part.strip()
            if ' to ' in part:
                a, b = part.split(' to ')
                ids.extend(range(int(a.strip()), int(b.strip()) + 1))
            else:
                ids.append(int(part))
    return ids


def fmt_ids(ids: list[int]) -> str:
    """Format skill ID list for Known Skills List tag."""
    return ", ".join(str(i) for i in ids)


# State definitions for weapon defense (101-113)
# state_id → { "name": ..., "resist_elements": [(elem_id, value), ...] }
WEAPON_DEFENSE_STATES = {
    101: {"name": "劍法防禦", "desc": "抵擋槍法、棍法攻擊傷害25%。",
          "resists": [(4, 0.75), (3, 0.75)]},
    102: {"name": "刀法防禦", "desc": "抵擋拳掌、劍法攻擊傷害25%。",
          "resists": [(5, 0.75), (1, 0.75)]},
    103: {"name": "棍法防禦", "desc": "抵擋短兵、暗器攻擊傷害25%。",
          "resists": [(11, 0.75), (10, 0.75)]},
    104: {"name": "槍法防禦", "desc": "抵擋刀法、音律攻擊傷害25%。",
          "resists": [(2, 0.75), (6, 0.75)]},
    105: {"name": "拳掌防禦", "desc": "抵擋音律、筆法攻擊傷害25%。",
          "resists": [(6, 0.75), (9, 0.75)]},
    106: {"name": "音律防禦", "desc": "抵擋毒術、弓術攻擊傷害25%。",
          "resists": [(13, 0.75), (8, 0.75)]},
    107: {"name": "奇門防禦", "desc": "抵擋醫術、毒術攻擊傷害25%。",
          "resists": [(12, 0.75), (13, 0.75)]},
    # 108 skipped (弓術 has no defense)
    109: {"name": "筆法防禦", "desc": "抵擋暗器、弓術攻擊傷害25%。",
          "resists": [(10, 0.75), (8, 0.75)]},
}

# States 110-113: ADD traits to existing shield states
WEAPON_DEFENSE_TRAITS_ADD = {
    110: {"resists": [(6, 0.75), (7, 0.75)]},     # 暗器 → resist 音律, 奇門
    111: {"resists": [(10, 0.75), (1, 0.75), (2, 0.75)]},  # 短兵 → resist 暗器, 劍法, 刀法
    112: {"heal_reduction": True},                  # 醫術 → 降療效果
    113: {"resists": [(12, 0.75), (5, 0.75)]},     # 毒術 → resist 醫術, 拳掌
}

# Inner defense states (114-116): ADD element resistance traits
INNER_DEFENSE_TRAITS_ADD = {
    114: {"resists": [(15, 0.75)]},   # 陰 → resist 陽
    115: {"resists": [(14, 0.75)]},   # 陽 → resist 陰
    116: {"resists": [(14, 0.75), (15, 0.75)]},  # 混元 → resist 陰, 陽
}

# 五行 defense states (117-121): ADD element resistance traits
WUXING_DEFENSE_TRAITS_ADD = {
    117: {"resists": [(19, 0.75)]},   # 木 → resist 土 (木剋土)
    118: {"resists": [(20, 0.75)]},   # 火 → resist 金 (火剋金)
    119: {"resists": [(21, 0.75)]},   # 土 → resist 水 (土剋水)
    120: {"resists": [(17, 0.75)]},   # 金 → resist 木 (金剋木)
    121: {"resists": [(18, 0.75)]},   # 水 → resist 火 (水剋火)
}

# 天象 defense states (122-126): CREATE new states
TIANXIANG_DEFENSE_STATES = {
    122: {"name": "風象防禦", "desc": "抵擋炎屬性攻擊傷害25%。",
          "resists": [(24, 0.75)]},   # 風 → resist 炎
    123: {"name": "雷象防禦", "desc": "抵擋風屬性攻擊傷害25%。",
          "resists": [(22, 0.75)]},   # 雷 → resist 風
    124: {"name": "炎象防禦", "desc": "抵擋寒屬性攻擊傷害25%。",
          "resists": [(26, 0.75)]},   # 炎 → resist 寒
    125: {"name": "電象防禦", "desc": "抵擋雷屬性攻擊傷害25%。",
          "resists": [(23, 0.75)]},   # 電 → resist 雷
    126: {"name": "寒象防禦", "desc": "抵擋電屬性攻擊傷害25%。",
          "resists": [(25, 0.75)]},   # 寒 → resist 電
}

# Defense skills missing Learn tags
MISSING_LEARN_TAGS = {
    1209: 1208,  # 混元 defense → requires previous skill
    1222: 1221,  # 木 defense
    1235: 1234,  # 火 defense
    1313: 1312,  # 炎 defense
}


def make_element_traits(resists: list[tuple[int, float]]) -> list[dict]:
    """Create element resistance trait list (code 11 = Element Rate)."""
    return [{"code": 11, "dataId": eid, "value": val} for eid, val in resists]


def make_defense_state(state_id: int, name: str, desc: str,
                       resists: list[tuple[int, float]]) -> dict:
    """Create a new defense state with element resistance traits."""
    return {
        "id": state_id,
        "autoRemovalTiming": 1,
        "chanceByDamage": 100,
        "traits": make_element_traits(resists),
        "iconIndex": 3297,
        "maxTurns": 3,
        "minTurns": 3,
        "message1": "", "message2": "", "message3": "", "message4": "",
        "motion": 0,
        "name": name,
        "note": f"<Help Description>\n\\c[16]{desc}\\c[0]\n</Help Description>\n<Positive State>",
        "overlay": 0,
        "priority": 50,
        "removeAtBattleEnd": True,
        "removeByDamage": False,
        "removeByRestriction": False,
        "removeByWalking": False,
        "restriction": 0,
        "stepsToRemove": 100,
        "messageType": 1,
    }


def stage_defense():
    """Restructure defense system: 1974→1978, states, counters, bug fixes."""
    print("=== Stage: Defense System ===")
    skills = load_json("Skills.json")
    states = load_json("States.json")
    errors = 0

    # ── 3.1: Remove defense skill IDs from 1974 ────────────────────────
    print("  [3.1] Removing defense IDs from 1974...")
    skill_1974 = skills[1974]
    old_ids = parse_known_skills(skill_1974["note"])
    new_ids = [sid for sid in old_ids if sid not in DEFENSE_IDS_REMOVE_FROM_1974]
    removed = len(old_ids) - len(new_ids)
    skill_1974["note"] = f"<Known Skills List: {fmt_ids(new_ids)}>"
    print(f"    Removed {removed} IDs (was {len(old_ids)}, now {len(new_ids)})")

    # ── 3.2: Skill 1157 description update ─────────────────────────────
    print("  [3.2] Updating skill 1157 description...")
    skill_1157 = skills[1157]
    skill_1157["description"] = (
        "（\\c[5]類型：醫術/降療\\c[0]｜\\c[2]範圍：自身\\c[0]｜"
        "\\c[3]醫術・防禦武學\\c[0]｜\\c[8]增加策略：5\\c[0]）\n"
        "\\c[20]●施放後使敵方受到的治療效果降低50%。\\c[0]\n"
        "\\c[16]藥師琉璃光，以毒攻毒，封鎖療癒之源。\\c[0]"
    )

    # ── 3.3-3.5: Update States 101-126 ──────────────────────────────────
    print("  [3.3] Updating weapon defense states 101-109...")
    for sid, info in WEAPON_DEFENSE_STATES.items():
        states[sid] = make_defense_state(sid, info["name"], info["desc"], info["resists"])
        print(f"    State {sid}: {info['name']}")

    print("  [3.4] Adding traits to weapon defense states 110-113...")
    for sid, info in WEAPON_DEFENSE_TRAITS_ADD.items():
        state = states[sid]
        if "heal_reduction" in info:
            # State 112: add 降療 trait (Recovery Effect Rate 50%)
            state["traits"].append({"code": 23, "dataId": 2, "value": 0.5})
            print(f"    State {sid}: +降療 (Recovery Rate 50%)")
        else:
            new_traits = make_element_traits(info["resists"])
            state["traits"].extend(new_traits)
            elem_names = [str(r[0]) for r in info["resists"]]
            print(f"    State {sid}: +resist elements {', '.join(elem_names)}")

    print("  [3.5] Adding traits to inner defense states 114-116...")
    for sid, info in INNER_DEFENSE_TRAITS_ADD.items():
        state = states[sid]
        new_traits = make_element_traits(info["resists"])
        state["traits"].extend(new_traits)
        print(f"    State {sid} ({state['name']}): +resist {info['resists']}")

    print("  [3.6] Adding traits to 五行 defense states 117-121...")
    for sid, info in WUXING_DEFENSE_TRAITS_ADD.items():
        state = states[sid]
        new_traits = make_element_traits(info["resists"])
        state["traits"].extend(new_traits)
        print(f"    State {sid} ({state['name']}): +resist {info['resists']}")

    print("  [3.7] Creating 天象 defense states 122-126...")
    for sid, info in TIANXIANG_DEFENSE_STATES.items():
        old_name = states[sid].get("name", "(empty)")
        states[sid] = make_defense_state(sid, info["name"], info["desc"], info["resists"])
        print(f"    State {sid}: {old_name} → {info['name']}")

    # ── 3.8: Fix 電 Multi-Element tags (1317-1328) ─────────────────────
    print("  [3.8] Fixing 電 Multi-Element tags (1317-1328)...")
    fix_count = 0
    for sid in range(1317, 1329):
        if sid in SEPARATORS:
            continue
        skill = skills[sid]
        if skill is None:
            continue
        old_note = skill["note"]
        # Replace 雷 with 電 in Multi-Element tags (only the element part)
        new_note = re.sub(
            r'<Multi-Element:\s*雷([,>])',
            r'<Multi-Element: 電\1',
            old_note
        )
        if new_note != old_note:
            skill["note"] = new_note
            fix_count += 1
    print(f"    Fixed {fix_count} Multi-Element tags")

    # ── 3.9: Fix missing Learn tags for defense skills ──────────────────
    print("  [3.9] Adding missing Learn tags...")
    for sid, prev_id in MISSING_LEARN_TAGS.items():
        skill = skills[sid]
        note = skill["note"]
        if "<Learn AP Cost:" not in note:
            learn_tags = (
                f"\n<Learn AP Cost: 35>"
                f"\n<Learn SP Cost: 5>"
                f"\n<Learn Item 1001 Cost: 3>"
                f"\n<Learn Require Skill: {prev_id}>"
            )
            skill["note"] = note + learn_tags
            print(f"    Skill {sid}: added Learn tags (requires {prev_id})")

    # ── 3.10: Fix 寒 group occasion ────────────────────────────────────
    print("  [3.10] Fixing 寒 group occasion (1339-1341)...")
    for sid in [1339, 1340, 1341]:
        skill = skills[sid]
        if skill["occasion"] == 0:
            skill["occasion"] = 1
            print(f"    Skill {sid}: occasion 0 → 1")

    # ── Save ────────────────────────────────────────────────────────────
    save_json("Skills.json", skills)
    save_json("States.json", states)
    print(f"  Saved Skills.json and States.json")
    return errors


# ════════════════════════════════════════════════════════════════════════
#  STAGE 4: DEBUFF STATE CONVERSION
# ════════════════════════════════════════════════════════════════════════

# RPG Maker code 32 dataId → (minor_state_id, medium_state_id)
# dataId: 2=ATK, 3=DEF, 4=MAT, 5=MDF, 6=AGI, 7=LUK
DEBUFF_STATE_MAP = {
    2: (61, 62),   # 外功: 微(61), 中(62)
    3: (67, 68),   # 外防: 微(67), 中(68)
    4: (64, 65),   # 內功: 微(64), 中(65)
    5: (70, 71),   # 內防: 微(70), 中(71)
    6: (73, 74),   # 輕功: 微(73), 中(74)
    7: (76, 77),   # 福緣: 微(76), 中(77)
}

# dataId 0 (MHP) and 1 (MMP) are skipped (keep code 32 only)
DEBUFF_SKIP_IDS = {0, 1}


def stage_debuffs():
    """Convert code 32 debuffs to also add corresponding states 61-78."""
    print("=== Stage: Debuff Conversion ===")
    skills = load_json("Skills.json")
    count = 0

    for sid in range(1002, 1342):
        if sid in SEPARATORS:
            continue
        skill = skills[sid]
        if skill is None:
            continue

        effects = skill.get("effects", [])
        new_effects_to_add = []

        for eff in effects:
            if eff.get("code") != 32:
                continue
            data_id = eff.get("dataId", -1)
            value1 = eff.get("value1", 0)

            if data_id in DEBUFF_SKIP_IDS:
                continue
            if data_id not in DEBUFF_STATE_MAP:
                continue

            minor_state, medium_state = DEBUFF_STATE_MAP[data_id]

            # Determine tier: ≤0.32 → minor, >0.32 → medium
            if value1 <= 0.32:
                target_state = minor_state
            else:
                target_state = medium_state

            # Check if this state effect already exists
            already_has = any(
                e.get("code") == 21 and e.get("dataId") == target_state
                for e in effects
            )
            if already_has:
                continue

            new_effects_to_add.append({
                "code": 21,
                "dataId": target_state,
                "value1": value1,
                "value2": 0,
            })

        if new_effects_to_add:
            skill["effects"].extend(new_effects_to_add)
            count += 1
            state_ids = [e["dataId"] for e in new_effects_to_add]
            name = skill['name'].encode('ascii', 'replace').decode('ascii')
            print(f"  Skill {sid} ({name}): +states {state_ids}")

    save_json("Skills.json", skills)
    print(f"  Updated {count} skills with debuff states")
    return 0


# ════════════════════════════════════════════════════════════════════════
#  STAGE: FIX DESCRIPTIONS (remove code 32, fix terminology)
# ════════════════════════════════════════════════════════════════════════

# RPG Maker default terms → custom Chinese terms
DESC_TERM_REPLACEMENTS = {
    "防禦力": "外防",
    "魔防力": "內防",
    "攻擊力": "外功",
    "魔攻力": "內功",
    "敏捷": "輕功",
    "運氣": "福緣",
}


def stage_fix_descs():
    """Remove code 32 effects and fix description terminology."""
    print("=== Stage: Fix Descriptions & Remove Code 32 ===")
    skills = load_json("Skills.json")
    code32_removed = 0
    desc_fixed = 0

    for sid in range(1002, 1342):
        if sid in SEPARATORS:
            continue
        skill = skills[sid]
        if skill is None:
            continue

        # 1) Remove code 32 effects (keep code 21 state effects)
        old_effects = skill.get("effects", [])
        new_effects = [e for e in old_effects if e.get("code") != 32]
        if len(new_effects) < len(old_effects):
            removed_count = len(old_effects) - len(new_effects)
            skill["effects"] = new_effects
            code32_removed += removed_count
            name = skill['name'].encode('ascii', 'replace').decode('ascii')
            print(f"  Skill {sid} ({name}): removed {removed_count} code 32 effect(s)")

        # 2) Fix description terminology
        desc = skill.get("description", "")
        original_desc = desc
        for old_term, new_term in DESC_TERM_REPLACEMENTS.items():
            desc = desc.replace(old_term, new_term)
        if desc != original_desc:
            skill["description"] = desc
            desc_fixed += 1

    save_json("Skills.json", skills)
    print(f"\n  Removed {code32_removed} code 32 effects total")
    print(f"  Fixed descriptions in {desc_fixed} skills")
    return 0


# ════════════════════════════════════════════════════════════════════════
#  STAGE: ADD MISSING LEARN TAGS
# ════════════════════════════════════════════════════════════════════════

# (skill_id, ap_cost, sp_cost_or_None, item_cost, require_skill_or_None)
MISSING_LEARN_TAGS = [
    # 混元 group (pattern follows 陰/陽 reference)
    (1200, 10, None, 1, None),
    (1201, 35, 5, 3, 1200),
    (1202, 55, 12, 5, 1201),
    (1203, 55, 12, 5, 1202),
    (1204, 80, 20, 8, 1203),
    (1205, 55, 12, 5, 1204),
    (1206, 35, 5, 3, 1205),
    (1207, 55, 12, 5, 1206),
    (1208, 80, 20, 8, 1207),
    # 1209 already has Learn tags — skip
    (1210, 80, 20, 8, 1209),
    (1211, 80, 20, 8, 1210),
    # 木 ultimate
    (1224, 80, 20, 8, 1223),
    # 火 ultimate
    (1237, 80, 20, 8, 1236),
    # 炎 ultimate
    (1315, 80, 20, 8, 1314),
]


def stage_learn_tags():
    """Add missing Learn tags to 混元 group and 3 ultimate skills."""
    print("=== Stage: Add Missing Learn Tags ===")
    skills = load_json("Skills.json")
    count = 0

    for sid, ap, sp, item_cost, req in MISSING_LEARN_TAGS:
        skill = skills[sid]
        if skill is None:
            print(f"  [WARN] Skill {sid} is null, skipping")
            continue

        note = skill.get("note", "")

        # Check if Learn tags already exist
        if "<Learn AP Cost:" in note:
            name = skill['name'].encode('ascii', 'replace').decode('ascii')
            print(f"  Skill {sid} ({name}): already has Learn tags, skipping")
            continue

        # Build Learn tag block
        tags = f"\n<Learn AP Cost: {ap}>"
        if sp is not None:
            tags += f"\n<Learn SP Cost: {sp}>"
        tags += f"\n<Learn Item 1001 Cost: {item_cost}>"
        if req is not None:
            tags += f"\n<Learn Require Skill: {req}>"
        tags += "\n"

        # Append to note (before trailing newline if present)
        if note.endswith("\n"):
            note = note[:-1] + tags
        else:
            note += tags

        skill["note"] = note
        count += 1
        name = skill['name'].encode('ascii', 'replace').decode('ascii')
        print(f"  Skill {sid} ({name}): added Learn tags (AP:{ap} SP:{sp} Item:{item_cost} Req:{req})")

    save_json("Skills.json", skills)
    print(f"\n  Added Learn tags to {count} skills")
    return 0


# ════════════════════════════════════════════════════════════════════════
#  STAGE: FIX BUFF SKILLS + WUXING/TIANXIANG LEARN TAGS
# ════════════════════════════════════════════════════════════════════════

# 12-skill group definitions: (separator_id, first_skill_id, last_skill_id)
TWELVE_SKILL_GROUPS = [
    # Inner
    (1173, 1174, 1185),
    (1186, 1187, 1198),
    (1199, 1200, 1211),
    # Wuxing
    (1212, 1213, 1224),
    (1225, 1226, 1237),
    (1238, 1239, 1250),
    (1251, 1252, 1263),
    (1264, 1265, 1276),
    # Tianxiang
    (1277, 1278, 1289),
    (1290, 1291, 1302),
    (1303, 1304, 1315),
    (1316, 1317, 1328),
    (1329, 1330, 1341),
]

# Learn cost pattern for 12-skill groups (ap, sp_or_None, item_cost)
LEARN_COST_12 = [
    (10, None, 1),   # pos 1 (basic)
    (35, 5, 3),      # pos 2
    (55, 12, 5),     # pos 3 (debuff)
    (55, 12, 5),     # pos 4
    (80, 20, 8),     # pos 5 (debuff AoE)
    (55, 12, 5),     # pos 6
    (35, 5, 3),      # pos 7
    (55, 12, 5),     # pos 8 (heal)
    (80, 20, 8),     # pos 9 (buff)
    (35, 5, 3),      # pos 10 (defense)
    (80, 20, 8),     # pos 11 (ultimate)
    (80, 20, 8),     # pos 12 (ultimate)
]

# The correct JS Pre-Start Action block for all-stat buff skills
JS_PRE_START_ACTION = (
    "<JS Pre-Start Action>\n"
    "const u = user;\n"
    "\n"
    "// 外功升級 (42微幅 -> 43中幅 -> 44大幅)\n"
    "if (!u.isStateAffected(44)) {\n"
    "  if (u.isStateAffected(43)) { u.removeState(43); u.addState(44); }\n"
    "  else if (u.isStateAffected(42)) { u.removeState(42); u.addState(43); }\n"
    "  else { u.addState(42); }\n"
    "}\n"
    "// 內功升級 (45微幅 -> 46中幅 -> 47大幅)\n"
    "if (!u.isStateAffected(47)) {\n"
    "  if (u.isStateAffected(46)) { u.removeState(46); u.addState(47); }\n"
    "  else if (u.isStateAffected(45)) { u.removeState(45); u.addState(46); }\n"
    "  else { u.addState(45); }\n"
    "}\n"
    "// 外防升級 (48微幅 -> 49中幅 -> 50大幅)\n"
    "if (!u.isStateAffected(50)) {\n"
    "  if (u.isStateAffected(49)) { u.removeState(49); u.addState(50); }\n"
    "  else if (u.isStateAffected(48)) { u.removeState(48); u.addState(49); }\n"
    "  else { u.addState(48); }\n"
    "}\n"
    "// 內防升級 (51微幅 -> 52中幅 -> 53大幅)\n"
    "if (!u.isStateAffected(53)) {\n"
    "  if (u.isStateAffected(52)) { u.removeState(52); u.addState(53); }\n"
    "  else if (u.isStateAffected(51)) { u.removeState(51); u.addState(52); }\n"
    "  else { u.addState(51); }\n"
    "}\n"
    "// 輕功升級 (54微幅 -> 55中幅 -> 56大幅)\n"
    "if (!u.isStateAffected(56)) {\n"
    "  if (u.isStateAffected(55)) { u.removeState(55); u.addState(56); }\n"
    "  else if (u.isStateAffected(54)) { u.removeState(54); u.addState(55); }\n"
    "  else { u.addState(54); }\n"
    "}\n"
    "// 福緣升級 (57微幅 -> 58中幅 -> 59大幅)\n"
    "if (!u.isStateAffected(59)) {\n"
    "  if (u.isStateAffected(58)) { u.removeState(58); u.addState(59); }\n"
    "  else if (u.isStateAffected(57)) { u.removeState(57); u.addState(58); }\n"
    "  else { u.addState(57); }\n"
    "}\n"
    "</JS Pre-Start Action>"
)

# Buff skill IDs (scope 11, #00BFFF, NOT defense)
BUFF_SKILL_IDS = {
    # Weapon groups
    1013, 1026, 1039, 1052, 1065, 1078, 1091, 1104,
    1117, 1130, 1143, 1156, 1169,
    # Inner groups
    1182, 1195, 1208,
    # Wuxing
    1221, 1234, 1247, 1260, 1273,
    # Tianxiang
    1286, 1299, 1312, 1325, 1338,
}


def _add_learn_tags_to_note(note: str, ap: int, sp, item_cost: int,
                            require_skill) -> str:
    """Append Learn tags to a note string."""
    tags = f"\n<Learn AP Cost: {ap}>"
    if sp is not None:
        tags += f"\n<Learn SP Cost: {sp}>"
    tags += f"\n<Learn Item 1001 Cost: {item_cost}>"
    if require_skill is not None:
        tags += f"\n<Learn Require Skill: {require_skill}>"
    tags += "\n"
    if note.endswith("\n"):
        return note[:-1] + tags
    return note + tags


def _replace_js_block(note: str) -> str:
    """Replace old <JS Post-Apply>...</JS Post-Apply> with the correct
    <JS Pre-Start Action> block. Also fixes existing Pre-Start blocks."""
    # Remove old JS Post-Apply block
    note = re.sub(
        r'<JS Post-Apply>\n.*?</JS Post-Apply>\n',
        '', note, flags=re.DOTALL,
    )
    # Remove old JS Pre-Start Action block (to re-add correct one)
    note = re.sub(
        r'<JS Pre-Start Action>\n.*?</JS Pre-Start Action>\n',
        '', note, flags=re.DOTALL,
    )
    # Insert new JS block before <Boost Turns> or at end
    if '<Boost Turns>' in note:
        note = note.replace('<Boost Turns>', JS_PRE_START_ACTION + '\n<Boost Turns>')
    else:
        if note.endswith("\n"):
            note = note[:-1] + "\n" + JS_PRE_START_ACTION + "\n"
        else:
            note += "\n" + JS_PRE_START_ACTION + "\n"
    return note


def stage_fix_buffs():
    """Fix buff skill JS + add Learn tags to wuxing/tianxiang groups."""
    print("=== Stage: Fix Buff Skills + Learn Tags ===")
    skills = load_json("Skills.json")
    js_fixed = 0
    learn_added = 0

    # Part 1: Fix JS on all buff skills (1002-1341)
    print("\n  --- Part 1: Fix JS Pre-Start Action ---")
    for sid in BUFF_SKILL_IDS:
        skill = skills[sid]
        if skill is None:
            continue
        note = skill.get("note", "")
        new_note = _replace_js_block(note)
        if new_note != note:
            skill["note"] = new_note
            js_fixed += 1
            name = skill['name'].encode('ascii', 'replace').decode('ascii')
            print(f"  Skill {sid} ({name}): JS updated")

    # Part 2: Add Learn tags to wuxing/tianxiang 12-skill groups
    print("\n  --- Part 2: Add Learn Tags ---")
    for sep_id, first_id, last_id in TWELVE_SKILL_GROUPS:
        # Only process wuxing (1212+) and tianxiang groups
        if first_id < 1213:
            continue
        for pos_idx in range(12):
            sid = first_id + pos_idx
            skill = skills[sid]
            if skill is None:
                continue
            note = skill.get("note", "")
            if "<Learn AP Cost:" in note:
                continue  # Already has Learn tags

            ap, sp, item_cost = LEARN_COST_12[pos_idx]
            require = (sid - 1) if pos_idx > 0 else None

            skill["note"] = _add_learn_tags_to_note(note, ap, sp, item_cost, require)
            learn_added += 1
            name = skill['name'].encode('ascii', 'replace').decode('ascii')
            print(f"  Skill {sid} ({name}): +Learn (AP:{ap} SP:{sp} Item:{item_cost} Req:{require})")

    save_json("Skills.json", skills)
    print(f"\n  JS blocks fixed: {js_fixed}")
    print(f"  Learn tags added: {learn_added}")
    return 0


# ════════════════════════════════════════════════════════════════════════
#  VERIFICATION
# ════════════════════════════════════════════════════════════════════════

def stage_verify():
    """Run all verification checks."""
    print("=== Verification ===")
    skills = load_json("Skills.json")
    states = load_json("States.json")
    errors = 0

    # 1. All 1002-1341 non-separator skills have iconIndex > 0
    print("\n  [1] Checking iconIndex...")
    icon_zero = []
    for sid in range(1002, 1342):
        if sid in SEPARATORS:
            continue
        skill = skills[sid]
        if skill and skill["iconIndex"] == 0:
            icon_zero.append(sid)
    if icon_zero:
        print(f"    [FAIL] Skills with iconIndex=0: {icon_zero}")
        errors += 1
    else:
        print(f"    [OK] All non-separator skills have iconIndex > 0")

    # 2. All 1002-1341 non-separator skills have animationId != 0
    print("\n  [2] Checking animationId...")
    anim_zero = []
    for sid in range(1002, 1342):
        if sid in SEPARATORS:
            continue
        skill = skills[sid]
        if skill and skill["animationId"] == 0:
            anim_zero.append(sid)
    if anim_zero:
        print(f"    [FAIL] Skills with animationId=0: {anim_zero}")
        errors += 1
    else:
        print(f"    [OK] All non-separator skills have animationId != 0")

    # 3. 1974 does not contain any defense skill IDs
    print("\n  [3] Checking 1974 Known Skills...")
    ids_1974 = parse_known_skills(skills[1974]["note"])
    defense_in_1974 = [sid for sid in DEFENSE_IDS_REMOVE_FROM_1974 if sid in ids_1974]
    if defense_in_1974:
        print(f"    [FAIL] Defense skills still in 1974: {defense_in_1974}")
        errors += 1
    else:
        print(f"    [OK] 1974 contains no defense skill IDs")

    # 4. 1978 contains all defense skill IDs
    print("\n  [4] Checking 1978 Known Skills...")
    ids_1978 = parse_known_skills(skills[1978]["note"])
    defense_not_in_1978 = [sid for sid in DEFENSE_SKILL_IDS if sid not in ids_1978]
    if defense_not_in_1978:
        print(f"    [FAIL] Defense skills missing from 1978: {defense_not_in_1978}")
        errors += 1
    else:
        print(f"    [OK] 1978 contains all {len(DEFENSE_SKILL_IDS)} defense skill IDs")

    # 5. States 101-113 (except 108) have element resistance traits
    print("\n  [5] Checking weapon defense states 101-113...")
    for sid in list(range(101, 108)) + list(range(109, 114)):
        state = states[sid]
        has_resist = any(t.get("code") == 11 for t in state.get("traits", []))
        has_heal_reduce = any(
            t.get("code") == 23 and t.get("dataId") == 2
            for t in state.get("traits", [])
        )
        if sid == 112:
            if not has_heal_reduce:
                print(f"    [FAIL] State 112: missing 降療 trait")
                errors += 1
            else:
                print(f"    [OK] State 112: has 降療 trait")
        elif not has_resist:
            print(f"    [FAIL] State {sid}: no element resistance trait")
            errors += 1
        else:
            print(f"    [OK] State {sid} ({state['name']}): has element resistance")

    # 6. 五行相剋: 金→木→土→水→火→金
    print("\n  [6] Checking 五行 counter cycle...")
    wuxing_cycle = {
        120: 17,  # 金 resists 木
        117: 19,  # 木 resists 土
        119: 21,  # 土 resists 水
        121: 18,  # 水 resists 火
        118: 20,  # 火 resists 金
    }
    for sid, expected_elem in wuxing_cycle.items():
        state = states[sid]
        resists = [t["dataId"] for t in state.get("traits", []) if t.get("code") == 11]
        if expected_elem in resists:
            print(f"    [OK] State {sid} ({state['name']}): resists element {expected_elem}")
        else:
            print(f"    [FAIL] State {sid}: expected resist {expected_elem}, got {resists}")
            errors += 1

    # 7. 天象相剋: 風→炎→寒→電→雷→風
    print("\n  [7] Checking 天象 counter cycle...")
    tianxiang_cycle = {
        122: 24,  # 風 resists 炎
        124: 26,  # 炎 resists 寒
        126: 25,  # 寒 resists 電
        125: 23,  # 電 resists 雷
        123: 22,  # 雷 resists 風
    }
    for sid, expected_elem in tianxiang_cycle.items():
        state = states[sid]
        resists = [t["dataId"] for t in state.get("traits", []) if t.get("code") == 11]
        if expected_elem in resists:
            print(f"    [OK] State {sid} ({state['name']}): resists element {expected_elem}")
        else:
            print(f"    [FAIL] State {sid}: expected resist {expected_elem}, got {resists}")
            errors += 1

    # 8. 1317-1328 Multi-Element has 電 (not 雷)
    print("\n  [8] Checking 電 Multi-Element tags...")
    dian_wrong = []
    for sid in range(1317, 1329):
        if sid in SEPARATORS:
            continue
        skill = skills[sid]
        if skill and "<Multi-Element:" in skill.get("note", ""):
            if re.search(r'<Multi-Element:\s*雷', skill["note"]):
                dian_wrong.append(sid)
    if dian_wrong:
        print(f"    [FAIL] Skills still using 雷 instead of 電: {dian_wrong}")
        errors += 1
    else:
        print(f"    [OK] All 電 skills have correct Multi-Element tag")

    # 9. Skill 1157 iconIndex = 3145
    print("\n  [9] Checking skill 1157 icon...")
    if skills[1157]["iconIndex"] == 3145:
        print(f"    [OK] Skill 1157 iconIndex = 3145")
    else:
        print(f"    [FAIL] Skill 1157 iconIndex = {skills[1157]['iconIndex']} (expected 3145)")
        errors += 1

    # 10. No code 32 effects remain in 1002-1341
    print("\n  [10] Checking no code 32 remains...")
    code32_remaining = []
    for sid in range(1002, 1342):
        if sid in SEPARATORS:
            continue
        skill = skills[sid]
        if skill is None:
            continue
        for eff in skill.get("effects", []):
            if eff.get("code") == 32:
                code32_remaining.append(sid)
                break
    if code32_remaining:
        print(f"    [FAIL] Skills still have code 32: {code32_remaining}")
        errors += 1
    else:
        print(f"    [OK] No code 32 effects remain in 1002-1341")

    # 11. No RPG Maker default terms in descriptions
    print("\n  [11] Checking description terminology...")
    bad_terms = ["防禦力", "魔防力", "攻擊力", "魔攻力"]
    bad_desc_skills = []
    for sid in range(1002, 1342):
        if sid in SEPARATORS:
            continue
        skill = skills[sid]
        if skill is None:
            continue
        desc = skill.get("description", "")
        for term in bad_terms:
            if term in desc:
                bad_desc_skills.append((sid, term))
                break
    if bad_desc_skills:
        print(f"    [FAIL] Skills with old terminology: {bad_desc_skills[:10]}...")
        errors += 1
    else:
        print(f"    [OK] All descriptions use correct terminology")

    # 12. All wuxing/tianxiang skills have Learn tags
    print("\n  [12] Checking Learn tags for wuxing/tianxiang...")
    learn_missing = []
    for sep_id, first_id, last_id in TWELVE_SKILL_GROUPS:
        if first_id < 1200:  # skip 陰/陽 (already complete)
            continue
        for sid in range(first_id, last_id + 1):
            skill = skills[sid]
            if skill and "<Learn AP Cost:" not in skill.get("note", ""):
                learn_missing.append(sid)
    if learn_missing:
        print(f"    [FAIL] Skills missing Learn tags: {learn_missing}")
        errors += 1
    else:
        print(f"    [OK] All 混元/五行/天象 skills have Learn tags")

    # 13. All buff skills use JS Pre-Start Action (not JS Post-Apply)
    print("\n  [13] Checking buff skill JS format...")
    js_wrong = []
    for sid in BUFF_SKILL_IDS:
        skill = skills[sid]
        if skill is None:
            continue
        note = skill.get("note", "")
        if "<JS Post-Apply>" in note:
            js_wrong.append((sid, "has old JS Post-Apply"))
        elif "<JS Pre-Start Action>" not in note:
            js_wrong.append((sid, "missing JS Pre-Start Action"))
    if js_wrong:
        print(f"    [FAIL] {js_wrong}")
        errors += 1
    else:
        print(f"    [OK] All {len(BUFF_SKILL_IDS)} buff skills have JS Pre-Start Action")

    # Summary
    print(f"\n{'=' * 40}")
    if errors:
        print(f"  FAILED: {errors} error(s)")
    else:
        print(f"  ALL CHECKS PASSED!")
    return errors


# ════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════

STAGES = {
    "icons": stage_icons,
    "anims": stage_anims,
    "defense": stage_defense,
    "debuffs": stage_debuffs,
    "fix_descs": stage_fix_descs,
    "learn_tags": stage_learn_tags,
    "fix_buffs": stage_fix_buffs,
    "verify": stage_verify,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in STAGES:
        print(f"Usage: {sys.argv[0]} <stage>")
        print(f"Stages: {', '.join(STAGES)}")
        return 1

    stage = sys.argv[1]
    print(f"\nRunning stage: {stage}")
    print("=" * 60)
    result = STAGES[stage]()
    print("=" * 60)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
