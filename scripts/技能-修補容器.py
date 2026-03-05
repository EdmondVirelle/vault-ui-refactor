"""
Patch script: Create Skill Container system for VisuMZ_4_SkillContainers.

Layout per character (4 IDs each):
  separator  ----C1／C2／C3(角色名)----
  C1         container skill (primary style)
  C2         container skill (advanced style)
  C3         container skill (defense/support style)

IDs: 1880-1971 (23 chars × 4 = 92)

Usage:
    python scripts/patch_skill_containers.py
"""

import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"

# ── Character Data ───────────────────────────────────────────────────
# (actor_name,
#  c1_name, c1_icon, c1_skills,
#  c2_name, c2_icon, c2_skills,
#  c3_name, c3_icon, c3_skills,
#  class_ids)

CHARACTERS = [
    ("東方啓",
     "劃月劍法", 3154, [1352, 1353, 1354, 1356],
     "烈焰斬月", 3154, [1357, 1359, 1360, 1361],
     "明月護身", 3173, [1355, 1358],
     [2, 3, 4]),
    ("湮菲花",
     "蘭心拳法", 3158, [1363, 1364, 1367, 1368],
     "蘭刺穿心", 3158, [1371, 1372, 1365, 1366],
     "蘭盾芳華", 3173, [1369, 1370],
     [10, 11, 12]),
    ("闕崇陽",
     "追風短刃", 3172, [1374, 1375, 1376, 1378],
     "雷電破空", 3172, [1379, 1380, 1381, 1382, 1383],
     "風壁禦雷", 3173, [1377],
     [14, 15, 16]),
    ("絲塔娜",
     "天罡棍法", 3156, [1385, 1386, 1387, 1389],
     "沙暴裂地", 3156, [1390, 1392, 1393, 1394],
     "金甲沙城", 3173, [1388, 1391],
     [18, 19, 20]),
    ("殷染幽",
     "血海劍法", 3154, [1396, 1397, 1398, 1400],
     "血刃無情", 3154, [1401, 1403, 1404, 1405],
     "血海歸潮", 3173, [1399, 1402],
     [54, 55, 56]),
    ("藍靜冥",
     "萬蠱毒經", 3170, [1407, 1408, 1409, 1410],
     "冥毒噬魂", 3170, [1411, 1413, 1414, 1415, 1416],
     "幽蠱化盾", 3173, [1412],
     [74, 75, 76]),
    ("楊古晨",
     "醉仙劍法", 3154, [1418, 1419, 1420, 1423],
     "天雷裂岳", 3154, [1424, 1425, 1427, 1426],
     "雷鎧金身", 3173, [1421, 1422],
     [50, 51, 52]),
    ("司徒長生",
     "天機劍法", 3154, [1429, 1430, 1431, 1433],
     "幻影殺機", 3154, [1434, 1435, 1436, 1437, 1438],
     "虛縷結界", 3173, [1432],
     [46, 47, 48]),
    ("無名丐",
     "神棍打法", 3156, [1440, 1441, 1442, 1444],
     "棍掃千軍", 3156, [1447, 1448, 1449, 1445],
     "神棍擋關", 3173, [1443, 1446],
     [66, 67, 68]),
    ("聶思泠",
     "百變身法", 3158, [1451, 1452, 1453, 1455],
     "鬼手摘星", 3166, [1457, 1458, 1459, 1460],
     "靈巧避禍", 3173, [1454, 1456],
     [62, 63, 64]),
    ("郭霆黃",
     "霸刀術", 3155, [1462, 1463, 1464, 1466],
     "藍焰斬天", 3155, [1467, 1468, 1469, 1471],
     "藍鋼護體", 3173, [1465, 1470],
     [70, 71, 72]),
    ("墨汐若",
     "梅花十三鞭法", 3162, [1473, 1474, 1475, 1477],
     "落花飛刃", 3162, [1480, 1481, 1482, 1476],
     "花雨凝甲", 3173, [1478, 1479],
     [58, 59, 60]),
    ("沅花",
     "丹青筆法", 3160, [1484, 1485, 1486, 1487],
     "落花殺筆", 3160, [1488, 1491, 1492, 1493],
     "花甲護身", 3173, [1489, 1490],
     [26, 27, 28]),
    ("談笑",
     "凝霜劍法", 3154, [1495, 1496, 1497, 1499],
     "霜刃穿骨", 3154, [1500, 1502, 1503, 1504],
     "冰魄守心", 3173, [1498, 1501],
     [30, 31, 32]),
    ("白沫檸",
     "沫團槍法", 3157, [1506, 1507, 1508, 1510],
     "清流破浪", 3157, [1512, 1513, 1514, 1515],
     "華木成林", 3173, [1509, 1511],
     [34, 35, 36]),
    ("青兒",
     "天籟琴音", 3159, [1517, 1518, 1522, 1524],
     "霞影裂空", 3159, [1525, 1526, 1519, 1520],
     "霞光凝盾", 3173, [1521, 1523],
     [6, 7, 8]),
    ("珞堇",
     "古弦心法", 3159, [1528, 1529, 1530, 1533],
     "弦震八方", 3159, [1534, 1535, 1536, 1537],
     "古韻護魂", 3173, [1531, 1532],
     [38, 39, 40]),
    ("龍玉",
     "龍吟劍法", 3154, [1539, 1540, 1541, 1543],
     "冰劍寒鋒", 3154, [1546, 1547, 1548, 1544],
     "玄冰鐵壁", 3173, [1542, 1545],
     [42, 43, 44]),
    ("七霜",
     "陰山醫術", 3171, [1550, 1551, 1555, 1557],
     "翠針破穴", 3172, [1552, 1553, 1554, 1556],
     "翡翠回春", 3171, [1558, 1559],
     [86, 87, 88]),
    ("瑤琴劍",
     "九霄劍法", 3154, [1561, 1562, 1563, 1565],
     "九霄劍嘯", 3154, [1566, 1568, 1569, 1570],
     "碧雲護天", 3173, [1564, 1567],
     [22, 23, 24]),
    ("莫縈懷",
     "片羽沾衣", 3162, [1572, 1573, 1574, 1576],
     "音殺無形", 3162, [1577, 1579, 1580, 1581],
     "音盾隱身", 3173, [1575, 1578],
     [90, 91, 92]),
    ("黃凱竹",
     "鐘塔煉藥術", 3165, [1583, 1584, 1585, 1587],
     "機關暴雨", 3165, [1588, 1590, 1591, 1592],
     "鐵甲機陣", 3173, [1586, 1589],
     [78, 79, 80]),
    ("劉靜靜",
     "海波暗殺術", 3166, [1594, 1595, 1596, 1598],
     "霜毒穿脈", 3170, [1599, 1601, 1602, 1603],
     "含蕊固本", 3173, [1597, 1600],
     [82, 83, 84]),
]

ID_BASE = 1880
# Per character: 4 IDs (separator, C1, C2, C3)
# Total: 23 * 4 = 92 (1880-1971)
TOTAL_IDS = len(CHARACTERS) * 4

# Old container IDs to clean from class learnings (previous runs)
OLD_CONTAINER_IDS = set(range(1880, 1951))


def make_empty_skill(skill_id: int, name: str = "") -> dict:
    """Return a blank/separator skill entry."""
    return {
        "id": skill_id,
        "animationId": 0,
        "damage": {
            "critical": False, "elementId": 0,
            "formula": "0", "type": 0, "variance": 20,
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


def make_container_skill(skill_id: int, name: str, icon: int,
                         child_skill_ids: list[int]) -> dict:
    """Create a VisuMZ_4_SkillContainers container skill entry."""
    ids_str = ", ".join(str(s) for s in child_skill_ids)
    note = f"<Known Skills List: {ids_str}>"
    return {
        "id": skill_id,
        "animationId": 0,
        "damage": {
            "critical": False, "elementId": 0,
            "formula": "0", "type": 0, "variance": 20,
        },
        "description": "", "effects": [],
        "hitType": 0, "iconIndex": icon,
        "message1": "", "message2": "", "messageType": 1,
        "mpCost": 0, "name": name, "note": note,
        "occasion": 1, "repeats": 1,
        "requiredWtypeId1": 0, "requiredWtypeId2": 0,
        "scope": 0, "speed": 0, "stypeId": 1,
        "successRate": 100, "tpCost": 0, "tpGain": 0,
    }


def load_json(filename: str):
    with open(BASE / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data):
    path = BASE / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  Saved {path}")


def patch_system(system: dict) -> None:
    """Set skillTypes[5] to 妖邪之術."""
    st = system["skillTypes"]
    while len(st) <= 5:
        st.append("")
    old = st[5]
    st[5] = "\\I[3166]妖邪之術"
    print(f"  skillTypes[5]: '{old}' -> '{st[5]}'")


def patch_skills(skills: list) -> dict:
    """Create separator + 3 container skills per character.
    Returns {row_idx: (sep_id, c1_id, c2_id, c3_id)}.
    """
    id_map = {}

    # Clear full range
    for sid in range(ID_BASE, ID_BASE + TOTAL_IDS):
        skills[sid] = make_empty_skill(sid)

    for row_idx, char in enumerate(CHARACTERS):
        (actor_name,
         c1_name, c1_icon, c1_skills,
         c2_name, c2_icon, c2_skills,
         c3_name, c3_icon, c3_skills,
         class_ids) = char

        sep_id = ID_BASE + row_idx * 4
        c1_id  = sep_id + 1
        c2_id  = sep_id + 2
        c3_id  = sep_id + 3

        # Separator
        sep_label = f"----{c1_name}／{c2_name}／{c3_name}({actor_name})----"
        skills[sep_id] = make_empty_skill(sep_id, sep_label)

        # C1, C2, C3 containers
        skills[c1_id] = make_container_skill(c1_id, c1_name, c1_icon, c1_skills)
        skills[c2_id] = make_container_skill(c2_id, c2_name, c2_icon, c2_skills)
        skills[c3_id] = make_container_skill(c3_id, c3_name, c3_icon, c3_skills)

        id_map[row_idx] = (sep_id, c1_id, c2_id, c3_id)

        print(f"  {sep_id}: {sep_label}")
        print(f"    {c1_id}: {c1_name}  {c2_id}: {c2_name}  {c3_id}: {c3_name}")

    print(f"  Total: {len(CHARACTERS) * 3} containers + "
          f"{len(CHARACTERS)} separators = {TOTAL_IDS} skills")
    return id_map


def patch_classes(classes: list, id_map: dict) -> None:
    """Remove old container learnings, add new ones (C1, C2, C3)."""
    modified = 0

    for row_idx, char in enumerate(CHARACTERS):
        (actor_name, *_, class_ids) = char
        _, c1_id, c2_id, c3_id = id_map[row_idx]
        new_ids = {c1_id, c2_id, c3_id}

        for cls_id in class_ids:
            cls = classes[cls_id]

            # Remove old container learnings
            cls["learnings"] = [
                l for l in cls["learnings"]
                if l["skillId"] not in OLD_CONTAINER_IDS
            ]

            # Add new
            existing = {l["skillId"] for l in cls["learnings"]}
            for cid in sorted(new_ids):
                if cid not in existing:
                    cls["learnings"].append({
                        "level": 1, "note": "", "skillId": cid,
                    })
            modified += 1

        print(f"  {actor_name}: [{c1_id}, {c2_id}, {c3_id}] -> classes {class_ids}")

    print(f"  Total classes modified: {modified}")


def verify(skills, classes, system, id_map) -> bool:
    ok = True

    if system["skillTypes"][5] != "\\I[3166]妖邪之術":
        print("  FAIL: skillTypes[5]")
        ok = False

    new_container_ids = set()
    for row_idx in range(len(CHARACTERS)):
        _, c1, c2, c3 = id_map[row_idx]
        for sid in (c1, c2, c3):
            new_container_ids.add(sid)
            s = skills[sid]
            if not s.get("name") or "<Known Skills List:" not in s.get("note", ""):
                print(f"  FAIL: Skill {sid} missing name/notetag")
                ok = False

        sep_id = id_map[row_idx][0]
        if not skills[sep_id].get("name", "").startswith("----"):
            print(f"  FAIL: Separator {sep_id}")
            ok = False

    # Class learnings
    for row_idx, char in enumerate(CHARACTERS):
        (actor_name, *_, class_ids) = char
        _, c1, c2, c3 = id_map[row_idx]
        for cls_id in class_ids:
            learned = {l["skillId"] for l in classes[cls_id]["learnings"]}
            for cid in (c1, c2, c3):
                if cid not in learned:
                    print(f"  FAIL: Class {cls_id} missing {cid}")
                    ok = False

    # Stale check
    stale_range = OLD_CONTAINER_IDS - new_container_ids
    for row_idx, char in enumerate(CHARACTERS):
        (_, *_, class_ids) = char
        for cls_id in class_ids:
            learned = {l["skillId"] for l in classes[cls_id]["learnings"]}
            stale = learned & stale_range
            if stale:
                print(f"  FAIL: Class {cls_id} stale IDs {stale}")
                ok = False

    if ok:
        print("  All checks passed!")
    return ok


def main() -> int:
    print("Loading data files...")
    skills = load_json("Skills.json")
    classes = load_json("Classes.json")
    system = load_json("System.json")

    print("\n1. Patching System.json...")
    patch_system(system)

    print("\n2. Creating containers + separators in Skills.json...")
    id_map = patch_skills(skills)

    print("\n3. Updating class learnings...")
    patch_classes(classes, id_map)

    print("\n4. Verifying...")
    if not verify(skills, classes, system, id_map):
        print("\nVerification FAILED. Not saving.")
        return 1

    print("\n5. Saving files...")
    save_json("System.json", system)
    save_json("Skills.json", skills)
    save_json("Classes.json", classes)

    last_id = ID_BASE + TOTAL_IDS - 1
    print(f"\nDone! Range: {ID_BASE}-{last_id} "
          f"({len(CHARACTERS)*3} containers, {len(CHARACTERS)} separators)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
