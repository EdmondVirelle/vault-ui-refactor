#!/usr/bin/env python3
"""
patch_class_system.py — 職業系統重構

1. 合併 1976（防禦之術）的 Known Skills List 到 1978（防禦武學）
2. 重構全部 69 個流派職業：
   - learnings: 10 項 (all level 1)
   - note: Learn Skills + Battle Commands 標準化
   - 移除 1976 from learnings
   - 內功分配依元素（陰/陽/混元）
"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "Consilience" / "data"

# ── Hardcoded skill data ───────────────────────────────────────────────

# 1978 original Known Skills (25 skills — from plan)
SKILL_1978_ORIGINAL = [
    1014, 1027, 1040, 1053, 1066, 1079, 1092, 1118, 1131, 1144,
    1157, 1170, 1183, 1196, 1209, 1222, 1235, 1248, 1261, 1274,
    1287, 1300, 1313, 1326, 1339,
]

# 1976 Known Skills (69 skills — defense skills for all 23 characters)
SKILL_1976_KNOWN = [
    2001, 2002, 2003, 2005, 2006, 2007, 2009, 2010, 2011,
    2013, 2014, 2015, 2017, 2018, 2019, 2021, 2022, 2023,
    2025, 2026, 2027, 2029, 2030, 2031, 2033, 2034, 2035,
    2037, 2038, 2039, 2041, 2042, 2043, 2045, 2046, 2047,
    2049, 2050, 2051, 2053, 2054, 2055, 2057, 2058, 2059,
    2061, 2062, 2063, 2065, 2066, 2067, 2069, 2070, 2071,
    2073, 2074, 2075, 2077, 2078, 2079, 2081, 2082, 2083,
    2085, 2086, 2087, 2089, 2090, 2091,
]

# ── Weapon ranges (weapon_first → "X to Y" Learn Skills line) ─────────
# 1002 has 15 skills (劍), all others have 12 skills
WEAPON_RANGES = {
    1002: "1002 to 1016",
    1018: "1018 to 1029",
    1031: "1031 to 1042",
    1044: "1044 to 1055",
    1057: "1057 to 1068",
    1070: "1070 to 1081",
    1083: "1083 to 1094",
    1096: "1096 to 1107",
    1109: "1109 to 1120",
    1135: "1135 to 1146",
    1148: "1148 to 1159",
    1161: "1161 to 1172",
}


def _range12(start: int) -> list[int]:
    """Generate 12 consecutive skill IDs."""
    return list(range(start, start + 12))


# ── Element/extra skill ranges per character ──────────────────────────
# Some characters have additional skill ranges (element-specific groups).
# Data from the user's working tree (captured before modification).
ELEMENT_RANGES: dict[str, list[list[int]]] = {
    "東方啟":   [_range12(1252)],                       # 金
    "湮菲花":   [_range12(1122)],                        # 木
    "瑤琴劍":   [_range12(1278)],                        # 風
    "談笑":     [_range12(1330)],                        # 寒
    "龍玉":     [_range12(1239), _range12(1330)],        # 土 (two ranges)
    "司徒長生": [_range12(1317)],                        # 電
    "楊古晨":   [_range12(1291)],                        # 雷
    "殷染幽":   [_range12(1330)],                        # 寒
    "黃凱竹":   [_range12(1161)],                        # 炎 (secondary weapon range)
}
# Characters NOT listed here have no element ranges.

# ── Inner skill configuration ─────────────────────────────────────────
INNER_SKILL = {
    "陰":  {"first": 1174, "range": list(range(1174, 1186))},   # 1174-1185
    "陽":  {"first": 1187, "range": list(range(1187, 1199))},   # 1187-1198
    "混元": {"first": 1200, "range": list(range(1200, 1212))},  # 1200-1211
}

# ── Character configuration (from plan table) ─────────────────────────
CHARACTERS = [
    {"name": "東方啟",   "classes": [2, 3, 4],     "containers": [1881, 1882, 1883], "weapon_first": 1002, "inner": "陽",  "defense_first": 2001},
    {"name": "青兒",     "classes": [6, 7, 8],     "containers": [1941, 1942, 1943], "weapon_first": 1070, "inner": "陰",  "defense_first": 2005},
    {"name": "湮菲花",   "classes": [10, 11, 12],  "containers": [1885, 1886, 1887], "weapon_first": 1057, "inner": "陰",  "defense_first": 2009},
    {"name": "闕崇陽",   "classes": [14, 15, 16],  "containers": [1889, 1890, 1891], "weapon_first": 1135, "inner": "陽",  "defense_first": 2013},
    {"name": "絲塔娜",   "classes": [18, 19, 20],  "containers": [1893, 1894, 1895], "weapon_first": 1031, "inner": "混元", "defense_first": 2017},
    {"name": "瑤琴劍",   "classes": [22, 23, 24],  "containers": [1957, 1958, 1959], "weapon_first": 1002, "inner": "混元", "defense_first": 2021},
    {"name": "沅花",     "classes": [26, 27, 28],  "containers": [1929, 1930, 1931], "weapon_first": 1109, "inner": "陰",  "defense_first": 2025},
    {"name": "談笑",     "classes": [30, 31, 32],  "containers": [1933, 1934, 1935], "weapon_first": 1002, "inner": "陰",  "defense_first": 2029},
    {"name": "白沫檸",   "classes": [34, 35, 36],  "containers": [1937, 1938, 1939], "weapon_first": 1044, "inner": "陰",  "defense_first": 2033},
    {"name": "珞堇",     "classes": [38, 39, 40],  "containers": [1945, 1946, 1947], "weapon_first": 1070, "inner": "陽",  "defense_first": 2037},
    {"name": "龍玉",     "classes": [42, 43, 44],  "containers": [1949, 1950, 1951], "weapon_first": 1002, "inner": "混元", "defense_first": 2041},
    {"name": "司徒長生", "classes": [46, 47, 48],  "containers": [1909, 1910, 1911], "weapon_first": 1002, "inner": "混元", "defense_first": 2045},
    {"name": "楊古晨",   "classes": [50, 51, 52],  "containers": [1905, 1906, 1907], "weapon_first": 1002, "inner": "陽",  "defense_first": 2049},
    {"name": "殷染幽",   "classes": [54, 55, 56],  "containers": [1897, 1898, 1899], "weapon_first": 1083, "inner": "陰",  "defense_first": 2053},
    {"name": "墨汐若",   "classes": [58, 59, 60],  "containers": [1925, 1926, 1927], "weapon_first": 1083, "inner": "陽",  "defense_first": 2057},
    {"name": "聶思泠",   "classes": [62, 63, 64],  "containers": [1917, 1918, 1919], "weapon_first": 1057, "inner": "陽",  "defense_first": 2061},
    {"name": "無名丐",   "classes": [66, 67, 68],  "containers": [1913, 1914, 1915], "weapon_first": 1031, "inner": "陰",  "defense_first": 2065},
    {"name": "郭霆黃",   "classes": [70, 71, 72],  "containers": [1921, 1922, 1923], "weapon_first": 1018, "inner": "陽",  "defense_first": 2069},
    {"name": "藍靜冥",   "classes": [74, 75, 76],  "containers": [1901, 1902, 1903], "weapon_first": 1161, "inner": "陽",  "defense_first": 2073},
    {"name": "黃凱竹",   "classes": [78, 79, 80],  "containers": [1965, 1966, 1967], "weapon_first": 1096, "inner": "陽",  "defense_first": 2077},
    {"name": "劉靜靜",   "classes": [82, 83, 84],  "containers": [1969, 1970, 1971], "weapon_first": 1083, "inner": "陽",  "defense_first": 2081},
    {"name": "七霜",     "classes": [86, 87, 88],  "containers": [1953, 1954, 1955], "weapon_first": 1148, "inner": "陰",  "defense_first": 2085},
    {"name": "莫縈懷",   "classes": [90, 91, 92],  "containers": [1961, 1962, 1963], "weapon_first": 1083, "inner": "陰",  "defense_first": 2089},
]


# ── Helpers ────────────────────────────────────────────────────────────

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


def fmt(ids: list[int]) -> str:
    """Format a list of skill IDs for a Learn Skills tag."""
    return ", ".join(str(sid) for sid in ids)


def make_note(char_name: str, class_name: str, style_skills: list[int],
              weapon_range: str, element_ranges: list[list[int]],
              inner_range: list[int], defense_skills: list[int], stype: int) -> str:
    parts = [
        f"----{char_name}\u00b7{class_name}----",
        "<Boost Points Battle Start: 1>",
        "<Boost Points Regen: +1>",
        f"<Learn Skills: {fmt(style_skills)}>",
        f"<Learn Skills: {weapon_range}>",
    ]
    for er in element_ranges:
        parts.append(f"<Learn Skills: {fmt(er)}>")
    parts.append(f"<Learn Skills: {fmt(inner_range)}>")
    parts.append(f"<Learn Skills: {fmt(defense_skills)}>")
    parts.extend([
        "<Battle Commands>",
        "Attack",
        "SType: 1",
        f"SType: {stype}",
        "Item",
        "Escape",
        "</Battle Commands>",
    ])
    return "\n".join(parts)


def make_learnings(style_first: int, weapon_first: int, inner_first: int,
                   defense_first: int, container_id: int) -> list[dict]:
    return [
        {"level": 1, "skillId": style_first, "note": ""},
        {"level": 1, "skillId": weapon_first, "note": ""},
        {"level": 1, "skillId": inner_first, "note": ""},
        {"level": 1, "skillId": defense_first, "note": ""},
        {"level": 1, "skillId": container_id, "note": ""},
        {"level": 1, "skillId": 1974, "note": ""},
        {"level": 1, "skillId": 1973, "note": ""},
        {"level": 1, "skillId": 1975, "note": ""},
        {"level": 1, "skillId": 1978, "note": ""},
        {"level": 1, "skillId": 1977, "note": ""},
    ]


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


# ── Main ───────────────────────────────────────────────────────────────

def main():
    skills_path = DATA_DIR / "Skills.json"
    classes_path = DATA_DIR / "Classes.json"

    print("Loading data...")
    with open(skills_path, encoding='utf-8') as f:
        skills = json.load(f)
    with open(classes_path, encoding='utf-8') as f:
        classes = json.load(f)

    # ── Step 1: Set 1978 Known Skills (merged 25 + 69 = 94) ───────────
    print("\n=== Step 1: Merge 1976 -> 1978 ===")
    merged = SKILL_1978_ORIGINAL + SKILL_1976_KNOWN
    skills[1978]["note"] = f"<Known Skills List: {fmt(merged)}>"
    print(f"  1978: {len(SKILL_1978_ORIGINAL)} + {len(SKILL_1976_KNOWN)} = {len(merged)} skills")

    # ── Step 2: Build container skill map ──────────────────────────────
    print("\n=== Step 2: Build container map ===")
    container_skills: dict[int, list[int]] = {}
    for char in CHARACTERS:
        for cid in char["containers"]:
            skill = skills[cid]
            if skill is None:
                print(f"  [WARN] Container {cid} is null!")
                continue
            known = parse_known_skills(skill["note"])
            if not known:
                print(f"  [WARN] Container {cid} ({skill.get('name','?')}) has no Known Skills!")
            container_skills[cid] = known
    print(f"  Mapped {len(container_skills)} containers")

    # ── Step 3: Restructure 69 classes ─────────────────────────────────
    print("\n=== Step 3: Restructure classes ===")
    for char in CHARACTERS:
        name = char["name"]
        inner_info = INNER_SKILL[char["inner"]]
        defense_skills = [char["defense_first"], char["defense_first"] + 1, char["defense_first"] + 2]
        weapon_range = WEAPON_RANGES[char["weapon_first"]]
        element_ranges = ELEMENT_RANGES.get(name, [])

        for idx, (class_id, container_id) in enumerate(zip(char["classes"], char["containers"])):
            cls = classes[class_id]
            stype = idx + 2  # SType: 2, 3, 4

            style_skills = container_skills.get(container_id, [])
            style_first = style_skills[0] if style_skills else 0

            cls["note"] = make_note(
                name, cls["name"],
                style_skills, weapon_range, element_ranges,
                inner_info["range"], defense_skills, stype,
            )
            cls["learnings"] = make_learnings(
                style_first, char["weapon_first"],
                inner_info["first"], char["defense_first"],
                container_id,
            )

        info = f"  weapon=<{weapon_range}>"
        if element_ranges:
            info += f"  elements={len(element_ranges)}"
        print(f"  {name}: classes {char['classes']}  inner={char['inner']}{info}")

    # ── Step 4: Save ───────────────────────────────────────────────────
    print("\n=== Step 4: Save ===")
    write_json_array(skills_path, skills)
    print(f"  Wrote {skills_path}")
    write_json_array(classes_path, classes)
    print(f"  Wrote {classes_path}")

    # ── Step 5: Verify ─────────────────────────────────────────────────
    print("\n=== Step 5: Verification ===")
    errors = 0

    # 1. Check 1978 skill count
    final_1978 = parse_known_skills(skills[1978]["note"])
    if len(final_1978) == 94:
        print(f"  [OK] 1978 Known Skills: {len(final_1978)}")
    else:
        print(f"  [FAIL] 1978 Known Skills: {len(final_1978)} (expected 94)")
        errors += 1

    # 2-6. Check all 69 classes
    bc_count = 0
    learn_ok = 0
    no_1976 = 0
    inner_ok = 0
    weapon_ok = 0

    for char in CHARACTERS:
        inner_first = INNER_SKILL[char["inner"]]["first"]

        for class_id in char["classes"]:
            cls = classes[class_id]

            if "<Battle Commands>" in cls["note"]:
                bc_count += 1
            else:
                print(f"  [FAIL] Class {class_id}: missing Battle Commands")
                errors += 1

            if len(cls["learnings"]) == 10:
                learn_ok += 1
            else:
                print(f"  [FAIL] Class {class_id}: {len(cls['learnings'])} learnings (expected 10)")
                errors += 1

            skill_ids = [l["skillId"] for l in cls["learnings"]]
            if 1976 not in skill_ids:
                no_1976 += 1
            else:
                print(f"  [FAIL] Class {class_id}: still contains skillId 1976")
                errors += 1

        first_note = classes[char["classes"][0]]["note"]
        if str(inner_first) in first_note:
            inner_ok += 1
        else:
            print(f"  [FAIL] {char['name']}: inner skill {inner_first} not in note")
            errors += 1

        if str(char["weapon_first"]) in first_note:
            weapon_ok += 1
        else:
            print(f"  [FAIL] {char['name']}: weapon {char['weapon_first']} not in note")
            errors += 1

    print(f"  [OK] Battle Commands: {bc_count}/69 classes")
    print(f"  [OK] Learnings = 10: {learn_ok}/69 classes")
    print(f"  [OK] No 1976: {no_1976}/69 classes")
    print(f"  [OK] Inner skill: {inner_ok}/23 characters")
    print(f"  [OK] Weapon range: {weapon_ok}/23 characters")

    if errors:
        print(f"\n  [FAIL] {errors} error(s) found!")
        return 1
    else:
        print("\n  All checks passed!")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
