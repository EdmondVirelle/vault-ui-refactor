"""
Patch script: Skill Expansion + Element System Overhaul

Parts:
  A) Rename bad skill/element names for 白沫檸
  B) Add 46 new elements (C2+C3) at indices 100-145
  C) Update Multi-Element tags on existing C2 skills
  D) Add 92 new skills (4 per character) at IDs 1604-1695
  E) Update container Known Skills Lists

Usage:
    python scripts/patch_skill_expansion.py
"""

import json
import sys
import io
import re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"


def load_json(filename: str):
    with open(BASE / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data):
    path = BASE / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  Saved {path}")


# ── Part B: New Elements ────────────────────────────────────────────
# C2 elements at indices 100-122, C3 elements at indices 123-145
NEW_ELEMENTS = [
    # C2 (100-122)
    "烈焰斬月",  # 100 東方啓
    "蘭刺穿心",  # 101 湮菲花
    "雷電破空",  # 102 闕崇陽
    "沙暴裂地",  # 103 絲塔娜
    "血刃無情",  # 104 殷染幽
    "冥毒噬魂",  # 105 藍靜冥
    "天雷裂岳",  # 106 楊古晨
    "幻影殺機",  # 107 司徒長生
    "棍掃千軍",  # 108 無名丐
    "鬼手摘星",  # 109 聶思泠
    "藍焰斬天",  # 110 郭霆黃
    "落花飛刃",  # 111 墨汐若
    "落花殺筆",  # 112 沅花
    "霜刃穿骨",  # 113 談笑
    "清流破浪",  # 114 白沫檸
    "霞影裂空",  # 115 青兒
    "弦震八方",  # 116 珞堇
    "冰劍寒鋒",  # 117 龍玉
    "翠針破穴",  # 118 七霜
    "九霄劍嘯",  # 119 瑤琴劍
    "音殺無形",  # 120 莫縈懷
    "機關暴雨",  # 121 黃凱竹
    "霜毒穿脈",  # 122 劉靜靜
    # C3 (123-145)
    "明月護身",  # 123 東方啓
    "蘭盾芳華",  # 124 湮菲花
    "風壁禦雷",  # 125 闕崇陽
    "金甲沙城",  # 126 絲塔娜
    "血海歸潮",  # 127 殷染幽
    "幽蠱化盾",  # 128 藍靜冥
    "雷鎧金身",  # 129 楊古晨
    "虛縷結界",  # 130 司徒長生
    "神棍擋關",  # 131 無名丐
    "靈巧避禍",  # 132 聶思泠
    "藍鋼護體",  # 133 郭霆黃
    "花雨凝甲",  # 134 墨汐若
    "花甲護身",  # 135 沅花
    "冰魄守心",  # 136 談笑
    "華木成林",  # 137 白沫檸
    "霞光凝盾",  # 138 青兒
    "古韻護魂",  # 139 珞堇
    "玄冰鐵壁",  # 140 龍玉
    "翡翠回春",  # 141 七霜
    "碧雲護天",  # 142 瑤琴劍
    "音盾隱身",  # 143 莫縈懷
    "鐵甲機陣",  # 144 黃凱竹
    "含蕊固本",  # 145 劉靜靜
]

# ── Part C: Character C2 element affinity ───────────────────────────
# Maps C2 container name -> natural element for Multi-Element rewrite
C2_ELEMENT_MAP = {
    "烈焰斬月": "金",
    "蘭刺穿心": "木",
    "雷電破空": "雷",
    "沙暴裂地": "土",
    "血刃無情": "水",
    "冥毒噬魂": "寒",
    "天雷裂岳": "雷",
    "幻影殺機": "電",
    "棍掃千軍": "水",
    "鬼手摘星": "火",
    "藍焰斬天": "金",
    "落花飛刃": "風",
    "落花殺筆": "木",
    "霜刃穿骨": "寒",
    "清流破浪": "水",
    "霞影裂空": "風",
    "弦震八方": "木",
    "冰劍寒鋒": "寒",
    "翠針破穴": "寒",
    "九霄劍嘯": "風",
    "音殺無形": "風",
    "機關暴雨": "木",
    "霜毒穿脈": "水",
}

# ── Character data for containers ───────────────────────────────────
# Order must match patch_skill_containers.py CHARACTERS list
# (actor, c1_name, c2_name, c3_name, c1_icon, c2_icon, c3_icon,
#  existing_c1_skills, existing_c2_skills, existing_c3_skills)
CHARACTERS = [
    # 0: 東方啓
    {"name": "東方啓",
     "c1": "劃月劍法", "c2": "烈焰斬月", "c3": "明月護身",
     "c1_icon": 3154, "c2_icon": 3154, "c3_icon": 3173,
     "c1_skills": [1352, 1353, 1354, 1356],
     "c2_skills": [1357, 1359, 1360, 1361],
     "c3_skills": [1355, 1358],
     "weapon": "劍法", "element": "金"},
    # 1: 湮菲花
    {"name": "湮菲花",
     "c1": "蘭心拳法", "c2": "蘭刺穿心", "c3": "蘭盾芳華",
     "c1_icon": 3158, "c2_icon": 3158, "c3_icon": 3173,
     "c1_skills": [1363, 1364, 1367, 1368],
     "c2_skills": [1371, 1372, 1365, 1366],
     "c3_skills": [1369, 1370],
     "weapon": "拳掌", "element": "木"},
    # 2: 闕崇陽
    {"name": "闕崇陽",
     "c1": "追風短刃", "c2": "雷電破空", "c3": "風壁禦雷",
     "c1_icon": 3172, "c2_icon": 3172, "c3_icon": 3173,
     "c1_skills": [1374, 1375, 1376, 1378],
     "c2_skills": [1379, 1380, 1381, 1382, 1383],
     "c3_skills": [1377],
     "weapon": "短兵", "element": "雷"},
    # 3: 絲塔娜
    {"name": "絲塔娜",
     "c1": "天罡棍法", "c2": "沙暴裂地", "c3": "金甲沙城",
     "c1_icon": 3156, "c2_icon": 3156, "c3_icon": 3173,
     "c1_skills": [1385, 1386, 1387, 1389],
     "c2_skills": [1390, 1392, 1393, 1394],
     "c3_skills": [1388, 1391],
     "weapon": "棍法", "element": "土"},
    # 4: 殷染幽
    {"name": "殷染幽",
     "c1": "血海劍法", "c2": "血刃無情", "c3": "血海歸潮",
     "c1_icon": 3154, "c2_icon": 3154, "c3_icon": 3173,
     "c1_skills": [1396, 1397, 1398, 1400],
     "c2_skills": [1401, 1403, 1404, 1405],
     "c3_skills": [1399, 1402],
     "weapon": "劍法", "element": "水"},
    # 5: 藍靜冥
    {"name": "藍靜冥",
     "c1": "萬蠱毒經", "c2": "冥毒噬魂", "c3": "幽蠱化盾",
     "c1_icon": 3170, "c2_icon": 3170, "c3_icon": 3173,
     "c1_skills": [1407, 1408, 1409, 1410],
     "c2_skills": [1411, 1413, 1414, 1415, 1416],
     "c3_skills": [1412],
     "weapon": "毒術", "element": "寒"},
    # 6: 楊古晨
    {"name": "楊古晨",
     "c1": "醉仙劍法", "c2": "天雷裂岳", "c3": "雷鎧金身",
     "c1_icon": 3154, "c2_icon": 3154, "c3_icon": 3173,
     "c1_skills": [1418, 1419, 1420, 1423],
     "c2_skills": [1424, 1425, 1427, 1426],
     "c3_skills": [1421, 1422],
     "weapon": "劍法", "element": "雷"},
    # 7: 司徒長生
    {"name": "司徒長生",
     "c1": "天機劍法", "c2": "幻影殺機", "c3": "虛縷結界",
     "c1_icon": 3154, "c2_icon": 3154, "c3_icon": 3173,
     "c1_skills": [1429, 1430, 1431, 1433],
     "c2_skills": [1434, 1435, 1436, 1437, 1438],
     "c3_skills": [1432],
     "weapon": "劍法", "element": "電"},
    # 8: 無名丐
    {"name": "無名丐",
     "c1": "神棍打法", "c2": "棍掃千軍", "c3": "神棍擋關",
     "c1_icon": 3156, "c2_icon": 3156, "c3_icon": 3173,
     "c1_skills": [1440, 1441, 1442, 1444],
     "c2_skills": [1447, 1448, 1449, 1445],
     "c3_skills": [1443, 1446],
     "weapon": "棍法", "element": "水"},
    # 9: 聶思泠
    {"name": "聶思泠",
     "c1": "百變身法", "c2": "鬼手摘星", "c3": "靈巧避禍",
     "c1_icon": 3158, "c2_icon": 3166, "c3_icon": 3173,
     "c1_skills": [1451, 1452, 1453, 1455],
     "c2_skills": [1457, 1458, 1459, 1460],
     "c3_skills": [1454, 1456],
     "weapon": "拳掌", "element": "火"},
    # 10: 郭霆黃
    {"name": "郭霆黃",
     "c1": "霸刀術", "c2": "藍焰斬天", "c3": "藍鋼護體",
     "c1_icon": 3155, "c2_icon": 3155, "c3_icon": 3173,
     "c1_skills": [1462, 1463, 1464, 1466],
     "c2_skills": [1467, 1468, 1469, 1471],
     "c3_skills": [1465, 1470],
     "weapon": "刀法", "element": "金"},
    # 11: 墨汐若
    {"name": "墨汐若",
     "c1": "梅花十三鞭法", "c2": "落花飛刃", "c3": "花雨凝甲",
     "c1_icon": 3162, "c2_icon": 3162, "c3_icon": 3173,
     "c1_skills": [1473, 1474, 1475, 1477],
     "c2_skills": [1480, 1481, 1482, 1476],
     "c3_skills": [1478, 1479],
     "weapon": "奇門", "element": "風"},
    # 12: 沅花
    {"name": "沅花",
     "c1": "丹青筆法", "c2": "落花殺筆", "c3": "花甲護身",
     "c1_icon": 3160, "c2_icon": 3160, "c3_icon": 3173,
     "c1_skills": [1484, 1485, 1486, 1487],
     "c2_skills": [1488, 1491, 1492, 1493],
     "c3_skills": [1489, 1490],
     "weapon": "筆法", "element": "木"},
    # 13: 談笑
    {"name": "談笑",
     "c1": "凝霜劍法", "c2": "霜刃穿骨", "c3": "冰魄守心",
     "c1_icon": 3154, "c2_icon": 3154, "c3_icon": 3173,
     "c1_skills": [1495, 1496, 1497, 1499],
     "c2_skills": [1500, 1502, 1503, 1504],
     "c3_skills": [1498, 1501],
     "weapon": "劍法", "element": "寒"},
    # 14: 白沫檸
    {"name": "白沫檸",
     "c1": "水擊槍法", "c2": "清流破浪", "c3": "華木成林",
     "c1_icon": 3157, "c2_icon": 3157, "c3_icon": 3173,
     "c1_skills": [1506, 1507, 1508, 1510],
     "c2_skills": [1512, 1513, 1514, 1515],
     "c3_skills": [1509, 1511],
     "weapon": "槍法", "element": "水"},
    # 15: 青兒
    {"name": "青兒",
     "c1": "天籟琴音", "c2": "霞影裂空", "c3": "霞光凝盾",
     "c1_icon": 3159, "c2_icon": 3159, "c3_icon": 3173,
     "c1_skills": [1517, 1518, 1522, 1524],
     "c2_skills": [1525, 1526, 1519, 1520],
     "c3_skills": [1521, 1523],
     "weapon": "音律", "element": "風"},
    # 16: 珞堇
    {"name": "珞堇",
     "c1": "古弦心法", "c2": "弦震八方", "c3": "古韻護魂",
     "c1_icon": 3159, "c2_icon": 3159, "c3_icon": 3173,
     "c1_skills": [1528, 1529, 1530, 1533],
     "c2_skills": [1534, 1535, 1536, 1537],
     "c3_skills": [1531, 1532],
     "weapon": "音律", "element": "木"},
    # 17: 龍玉
    {"name": "龍玉",
     "c1": "龍吟劍法", "c2": "冰劍寒鋒", "c3": "玄冰鐵壁",
     "c1_icon": 3154, "c2_icon": 3154, "c3_icon": 3173,
     "c1_skills": [1539, 1540, 1541, 1543],
     "c2_skills": [1546, 1547, 1548, 1544],
     "c3_skills": [1542, 1545],
     "weapon": "劍法", "element": "寒"},
    # 18: 七霜
    {"name": "七霜",
     "c1": "陰山醫術", "c2": "翠針破穴", "c3": "翡翠回春",
     "c1_icon": 3171, "c2_icon": 3172, "c3_icon": 3171,
     "c1_skills": [1550, 1551, 1555, 1557],
     "c2_skills": [1552, 1553, 1554, 1556],
     "c3_skills": [1558, 1559],
     "weapon": "短兵", "element": "寒"},
    # 19: 瑤琴劍
    {"name": "瑤琴劍",
     "c1": "九霄劍法", "c2": "九霄劍嘯", "c3": "碧雲護天",
     "c1_icon": 3154, "c2_icon": 3154, "c3_icon": 3173,
     "c1_skills": [1561, 1562, 1563, 1565],
     "c2_skills": [1566, 1568, 1569, 1570],
     "c3_skills": [1564, 1567],
     "weapon": "劍法", "element": "風"},
    # 20: 莫縈懷
    {"name": "莫縈懷",
     "c1": "片羽沾衣", "c2": "音殺無形", "c3": "音盾隱身",
     "c1_icon": 3162, "c2_icon": 3162, "c3_icon": 3173,
     "c1_skills": [1572, 1573, 1574, 1576],
     "c2_skills": [1577, 1579, 1580, 1581],
     "c3_skills": [1575, 1578],
     "weapon": "奇門", "element": "風"},
    # 21: 黃凱竹
    {"name": "黃凱竹",
     "c1": "鐘塔煉藥術", "c2": "機關暴雨", "c3": "鐵甲機陣",
     "c1_icon": 3165, "c2_icon": 3165, "c3_icon": 3173,
     "c1_skills": [1583, 1584, 1585, 1587],
     "c2_skills": [1588, 1590, 1591, 1592],
     "c3_skills": [1586, 1589],
     "weapon": "弓術", "element": "木"},
    # 22: 劉靜靜
    {"name": "劉靜靜",
     "c1": "海波暗殺術", "c2": "霜毒穿脈", "c3": "含蕊固本",
     "c1_icon": 3166, "c2_icon": 3170, "c3_icon": 3173,
     "c1_skills": [1594, 1595, 1596, 1598],
     "c2_skills": [1599, 1601, 1602, 1603],
     "c3_skills": [1597, 1600],
     "weapon": "奇門", "element": "水"},
]

# ── Part D: New Skills (92 total, 4 per character) ──────────────────
# Each entry: (id, name, container_type, skill_def)
# container_type: "c1", "c2", "c3"
# skill_def keys: scope, damage_type, formula, mp, cd, elements, effects,
#                 desc_type, desc_scope, desc_tags, desc_flavor,
#                 icon_override, hit_type, color, repeats, extra_notes

def atk_formula(tier):
    """Generate ATK damage formula by tier."""
    if tier == 2:
        return "Math.max(1,(a.atk*2.0-b.def*1.0+a.mat*0.4-b.mdf*0.2)*(1+(a.agi-b.agi)/250))"
    elif tier == 3:
        return "Math.max(1,(a.atk*2.8-b.def*1.2+a.mat*0.5-b.mdf*0.3)*(1+(a.agi-b.agi)/250))"
    elif tier == 4:
        return "Math.max(1,(a.atk*4.0-b.def*1.4+a.mat*0.8-b.mdf*0.4)*(1+(a.agi-b.agi)/200)+Math.max(0,(a.luk-b.luk)*0.15))"
    return "0"

def mat_formula(tier):
    """Generate MAT damage formula by tier."""
    if tier == 2:
        return "Math.max(1,(a.mat*2.0-b.mdf*1.0+a.atk*0.3-b.def*0.2)*(1+(a.agi-b.agi)/250))"
    elif tier == 3:
        return "Math.max(1,(a.mat*2.8-b.mdf*1.2+a.atk*0.4-b.def*0.3)*(1+(a.agi-b.agi)/250))"
    elif tier == 4:
        return "Math.max(1,(a.mat*4.0-b.mdf*1.4+a.atk*0.6-b.def*0.4)*(1+(a.agi-b.agi)/200)+Math.max(0,(a.luk-b.luk)*0.15))"
    return "0"

def heal_formula(level="medium"):
    if level == "medium":
        return "a.mat*2.5+a.mdf*1.5"
    elif level == "large":
        return "a.mat*3.5+a.mdf*2.5"
    return "a.mat*1.5+a.mdf*1.0"

def make_skill(skill_id, name, elements, scope, damage_type, formula,
               mp_cost, cd, tp_gain, icon, hit_type, color,
               desc, effects=None, repeats=1, extra_notes="",
               variance=20):
    """Build a complete skill dict."""
    # Build note
    note_parts = [f"<Color: {color}>"]
    if elements:
        note_parts.append(f"<Multi-Element: {', '.join(elements)}>")
        note_parts.append("<Multi-Element Rule: Multiply>")
    if cd and cd > 0:
        note_parts.append(f"<Cooldown: {cd}>")
    if damage_type in (1, 2):  # physical/magical damage
        note_parts.append("<Boost Damage>")
    if damage_type == 3:  # heal
        note_parts.append("<Boost Effect Gain>")
    if extra_notes:
        note_parts.append(extra_notes)

    return {
        "id": skill_id,
        "animationId": 0,
        "damage": {
            "critical": damage_type in (1, 2),
            "elementId": 0,
            "formula": formula,
            "type": damage_type if damage_type != 0 else 0,
            "variance": variance,
        },
        "description": desc,
        "effects": effects or [],
        "hitType": hit_type,
        "iconIndex": icon,
        "message1": "", "message2": "", "messageType": 1,
        "mpCost": mp_cost,
        "name": name,
        "note": "\n".join(note_parts),
        "occasion": 1,
        "repeats": repeats,
        "requiredWtypeId1": 0, "requiredWtypeId2": 0,
        "scope": scope,
        "speed": 0,
        "stypeId": 1,
        "successRate": 100,
        "tpCost": 0,
        "tpGain": tp_gain,
    }

# Scope constants
SINGLE = 1
GROUP = 2  # all enemies
RANDOM2 = 4
RANDOM3 = 5
SELF = 11
PARTY = 8  # all allies

# Damage type constants
PHYS = 1
MAG = 2
HEAL = 3
NONE = 0

# State effect helper
def state_effect(state_id, chance=1.0):
    return {"code": 21, "dataId": state_id, "value1": chance, "value2": 0}

# Buff effect helpers (code 31 = add buff, code 32 = add debuff)
# paramId: 0=MHP, 1=MMP, 2=ATK, 3=DEF, 4=MAT, 5=MDF, 6=AGI, 7=LUK
def add_buff(param_id):
    return {"code": 31, "dataId": param_id, "value1": 3, "value2": 0}

def desc_atk(type_label, scope_label, tags, tp, flavor):
    return (f"（\\c[5]類型：{type_label}\\c[0]｜\\c[2]範圍：{scope_label}\\c[0]｜"
            f"\\c[3]{tags}\\c[0]｜\\c[8]增加策略：{tp}\\c[0]）\n"
            f"\\c[20]●{flavor}\\c[0]")

def desc_buff(type_label, scope_label, tags, tp, flavor):
    return (f"（\\c[5]類型：{type_label}\\c[0]｜\\c[2]範圍：{scope_label}\\c[0]｜"
            f"\\c[3]{tags}\\c[0]｜\\c[8]增加策略：{tp}\\c[0]）\n"
            f"\\c[20]●{flavor}\\c[0]")

def desc_heal(scope_label, tags, tp, flavor):
    return (f"（\\c[5]類型：醫術/回復\\c[0]｜\\c[2]範圍：{scope_label}\\c[0]｜"
            f"\\c[3]{tags}\\c[0]｜\\c[8]增加策略：{tp}\\c[0]）\n"
            f"\\c[20]●{flavor}\\c[0]")


def build_new_skills():
    """Return list of 92 new skill dicts for IDs 1604-1695."""
    skills = []

    # Helper to simplify
    def atk(sid, name, elems, scope, tier, mp, cd, tp, icon, desc_s, desc_t, desc_f, repeats=1, extra=""):
        formula = atk_formula(tier)
        d = desc_atk(f"外功/攻擊", desc_s, desc_t, tp, desc_f)
        return make_skill(sid, name, elems, scope, PHYS, formula, mp, cd, tp, icon, 1,
                         "#FF5151" if tier == 2 else "#FF8C00" if tier == 3 else "#FFD700",
                         d, repeats=repeats, extra_notes=extra)

    def matk(sid, name, elems, scope, tier, mp, cd, tp, icon, desc_s, desc_t, desc_f, repeats=1, extra=""):
        formula = mat_formula(tier)
        d = desc_atk(f"內功/攻擊", desc_s, desc_t, tp, desc_f)
        return make_skill(sid, name, elems, scope, MAG, formula, mp, cd, tp, icon, 2,
                         "#FF5151" if tier == 2 else "#FF8C00" if tier == 3 else "#FFD700",
                         d, repeats=repeats, extra_notes=extra)

    def buff(sid, name, elems, scope, mp, cd, tp, icon, desc_s, desc_t, desc_f, effects, extra=""):
        d = desc_buff("百式/增益", desc_s, desc_t, tp, desc_f)
        return make_skill(sid, name, elems, scope, NONE, "0", mp, cd, tp, icon, 0,
                         "#00BFFF", d, effects=effects, extra_notes="<Boost Turns>" + ("\n" + extra if extra else ""))

    def heal(sid, name, elems, scope, mp, cd, tp, icon, desc_s, desc_t, desc_f, level="medium", effects=None, extra=""):
        formula = heal_formula(level)
        d = desc_heal(desc_s, desc_t, tp, desc_f)
        return make_skill(sid, name, elems, scope, HEAL, formula, mp, cd, tp, icon, 0,
                         "#00FF7F", d, effects=effects, extra_notes=extra)

    # ── 東方啓 (劍/金) — 1604-1607 ──
    skills.append(atk(1604, "月華流轉", ["劍法", "劃月劍法"], GROUP, 2, 18, 2, 8,
                      3154, "全體", "劍法・劃月劍法", "劍氣橫掃全場。"))
    skills.append(atk(1605, "金鋒穿雲", ["金", "烈焰斬月"], SINGLE, 3, 22, 3, 10,
                      3154, "單體", "金・烈焰斬月", "金光劍氣穿刺敵人。"))
    skills.append(buff(1606, "劃月步法", ["明月護身"], SELF, 15, 3, 5,
                       3163, "自身", "明月護身", "提升自身輕功。",
                       [state_effect(42), state_effect(54)]))
    skills.append(atk(1607, "烈陽破甲", ["金", "烈焰斬月"], SINGLE, 4, 28, 4, 10,
                      3154, "單體", "金・烈焰斬月", "金芒劍擊，無視30%護甲。",
                      extra="<Armor Penetration: 30%>"))

    # ── 湮菲花 (拳/木) — 1608-1611 ──
    skills.append(atk(1608, "蘭指點穴", ["拳掌", "蘭心拳法"], SINGLE, 2, 14, 2, 8,
                      3158, "單體", "拳掌・蘭心拳法", "點穴攻擊，20%機率附加麻痺。",
                      extra="", repeats=1))
    skills[-1]["effects"] = [state_effect(8, 0.2)]
    skills.append(atk(1609, "花針暗渡", ["木", "蘭刺穿心"], RANDOM3, 3, 20, 3, 8,
                      3158, "隨機三體", "木・蘭刺穿心", "花針連發攻擊隨機三名敵人。",
                      repeats=3))
    skills.append(heal(1610, "百草扶脈", ["蘭盾芳華"], PARTY, 25, 4, 5,
                       3171, "全體友軍", "蘭盾芳華", "回復全體友軍氣血。", level="medium"))
    skills.append(atk(1611, "蘭心穿透", ["木", "蘭刺穿心"], SINGLE, 4, 28, 4, 10,
                      3158, "單體", "木・蘭刺穿心", "拳勁穿透，無視25%護甲。",
                      extra="<Armor Penetration: 25%>"))

    # ── 闕崇陽 (短兵/雷) — 1612-1615 ──
    skills.append(atk(1612, "疾風連斬", ["短兵", "追風短刃"], RANDOM3, 2, 16, 2, 8,
                      3172, "隨機三體", "短兵・追風短刃", "短刃連斬攻擊隨機三名敵人。",
                      repeats=3))
    skills.append(atk(1613, "雷霆奔襲", ["雷", "雷電破空"], GROUP, 3, 22, 3, 8,
                      3172, "全體", "雷・雷電破空", "雷電席捲全場敵人。"))
    skills.append(buff(1614, "護雷蓄勢", ["風壁禦雷"], SELF, 15, 4, 5,
                       3163, "自身", "風壁禦雷", "提升自身外功與輕功。",
                       [state_effect(42), state_effect(54)]))
    skills.append(atk(1615, "天雷斬落", ["雷", "雷電破空"], SINGLE, 4, 28, 4, 10,
                      3172, "單體", "雷・雷電破空", "雷霆萬鈞斬落敵人。"))

    # ── 絲塔娜 (棍/土) — 1616-1619 ──
    skills.append(atk(1616, "旋風棍擊", ["棍法", "天罡棍法"], GROUP, 2, 18, 2, 8,
                      3156, "全體", "棍法・天罡棍法", "棍法橫掃全場敵人。"))
    skills.append(atk(1617, "烈沙穿甲", ["土", "沙暴裂地"], SINGLE, 4, 28, 4, 10,
                      3156, "單體", "土・沙暴裂地", "沙棍穿甲，無視30%護甲。",
                      extra="<Armor Penetration: 30%>"))
    skills.append(buff(1618, "沙盾吸收", ["金甲沙城"], SELF, 15, 3, 5,
                       3173, "自身", "金甲沙城", "提升自身外防與內防。",
                       [state_effect(48), state_effect(51)]))
    skills.append(atk(1619, "沙暴天劫", ["土", "沙暴裂地"], GROUP, 3, 22, 3, 8,
                      3156, "全體", "土・沙暴裂地", "沙暴席捲全場敵人。"))

    # ── 殷染幽 (劍/水) — 1620-1623 ──
    skills.append(atk(1620, "暗香旋劍", ["劍法", "血海劍法"], GROUP, 2, 18, 2, 8,
                      3154, "全體", "劍法・血海劍法", "暗香劍氣橫掃全場。"))
    skills.append(atk(1621, "冰刃穿心", ["水", "血刃無情"], SINGLE, 3, 22, 3, 10,
                      3154, "單體", "水・血刃無情", "冰刃劍氣穿刺敵人。"))
    skills.append(buff(1622, "血霧障眼", ["血海歸潮"], SELF, 12, 3, 5,
                       3173, "自身", "血海歸潮", "提升自身閃避。",
                       [state_effect(27), state_effect(54)]))
    skills.append(atk(1623, "血海沸騰", ["水", "血刃無情"], GROUP, 4, 30, 5, 8,
                      3154, "全體", "水・血刃無情", "血海劍氣爆發，席捲全場。"))

    # ── 藍靜冥 (毒/寒) — 1624-1627 ──
    skills.append(matk(1624, "蠱蟲噬體", ["毒術", "萬蠱毒經"], SINGLE, 2, 14, 2, 8,
                       3170, "單體", "毒術・萬蠱毒經", "蠱毒侵蝕敵人，20%機率附加中毒。"))
    skills[-1]["effects"] = [state_effect(4, 0.2)]
    skills.append(matk(1625, "冥毒寒針", ["寒", "冥毒噬魂"], GROUP, 3, 22, 3, 8,
                       3170, "全體", "寒・冥毒噬魂", "冥毒寒氣席捲全場。"))
    skills.append(buff(1626, "蠱盾凝冰", ["幽蠱化盾"], SELF, 15, 4, 5,
                       3173, "自身", "幽蠱化盾", "提升自身內防。",
                       [state_effect(51)]))
    skills.append(matk(1627, "極寒蠱噬", ["寒", "冥毒噬魂"], SINGLE, 4, 28, 4, 10,
                       3170, "單體", "寒・冥毒噬魂", "極寒蠱毒噬咬敵人。"))

    # ── 楊古晨 (劍/雷) — 1628-1631 ──
    skills.append(atk(1628, "醉步連劍", ["劍法", "醉仙劍法"], RANDOM3, 2, 16, 2, 8,
                      3154, "隨機三體", "劍法・醉仙劍法", "醉步劍法攻擊隨機三名敵人。",
                      repeats=3))
    skills.append(atk(1629, "酒雷爆裂", ["雷", "天雷裂岳"], GROUP, 3, 22, 3, 8,
                      3154, "全體", "雷・天雷裂岳", "酒氣化雷席捲全場。"))
    skills.append(buff(1630, "酒氣護身", ["雷鎧金身"], SELF, 15, 3, 5,
                       3173, "自身", "雷鎧金身", "提升自身外防與閃避。",
                       [state_effect(48), state_effect(27)]))
    skills.append(atk(1631, "雷酒焚天", ["雷", "天雷裂岳"], SINGLE, 4, 28, 4, 10,
                      3154, "單體", "雷・天雷裂岳", "雷酒合一，極強斬擊。"))

    # ── 司徒長生 (劍/電) — 1632-1635 ──
    skills.append(atk(1632, "三劍齊發", ["劍法", "天機劍法"], RANDOM3, 2, 16, 2, 8,
                      3154, "隨機三體", "劍法・天機劍法", "三劍連發攻擊隨機三名敵人。",
                      repeats=3))
    skills.append(atk(1633, "幻影三連", ["電", "幻影殺機"], RANDOM3, 3, 20, 3, 8,
                      3154, "隨機三體", "電・幻影殺機", "幻影劍氣攻擊隨機三名敵人。",
                      repeats=3))
    skills.append(buff(1634, "虛氣迴護", ["虛縷結界"], PARTY, 25, 5, 5,
                       3173, "全體友軍", "虛縷結界", "為全體友軍提升外防。",
                       [state_effect(48)]))
    skills.append(atk(1635, "天機萬劍", ["電", "幻影殺機"], GROUP, 4, 30, 4, 8,
                      3154, "全體", "電・幻影殺機", "天機劍陣席捲全場。"))

    # ── 無名丐 (棍/水) — 1636-1639 ──
    skills.append(atk(1636, "乞兒掃堂", ["棍法", "神棍打法"], GROUP, 2, 18, 2, 8,
                      3156, "全體", "棍法・神棍打法", "棍法橫掃全場敵人。"))
    skills.append(atk(1637, "水棍裂波", ["水", "棍掃千軍"], SINGLE, 3, 22, 3, 10,
                      3156, "單體", "水・棍掃千軍", "水棍猛擊，裂波穿甲。"))
    skills.append(buff(1638, "裝死遁法", ["神棍擋關"], SELF, 12, 4, 5,
                       3173, "自身", "神棍擋關", "提升閃避並附加再生。",
                       [state_effect(27), state_effect(17)]))
    skills.append(atk(1639, "神棍亂舞", ["水", "棍掃千軍"], GROUP, 4, 30, 4, 8,
                      3156, "全體", "水・棍掃千軍", "神棍亂舞席捲全場。"))

    # ── 聶思泠 (拳/火) — 1640-1643 ──
    skills.append(atk(1640, "迴旋飛踢", ["拳掌", "百變身法"], GROUP, 2, 18, 2, 8,
                      3158, "全體", "拳掌・百變身法", "迴旋飛踢攻擊全場敵人。"))
    skills.append(atk(1641, "炎爆暗算", ["火", "鬼手摘星"], SINGLE, 3, 22, 3, 10,
                      3166, "單體", "火・鬼手摘星", "暗器火爆攻擊單體敵人。"))
    skills.append(buff(1642, "機靈閃避", ["靈巧避禍"], SELF, 12, 3, 5,
                       3173, "自身", "靈巧避禍", "提升自身輕功與閃避。",
                       [state_effect(54), state_effect(27)]))
    skills.append(atk(1643, "金火連彈", ["火", "鬼手摘星"], RANDOM3, 4, 26, 4, 8,
                      3166, "隨機三體", "火・鬼手摘星", "火焰暗器連發攻擊隨機三名敵人。",
                      repeats=3))

    # ── 郭霆黃 (刀/金) — 1644-1647 ──
    skills.append(atk(1644, "霸刀橫掃", ["刀法", "霸刀術"], GROUP, 2, 18, 2, 8,
                      3155, "全體", "刀法・霸刀術", "霸刀橫掃全場敵人。"))
    skills.append(atk(1645, "藍焰裂空", ["金", "藍焰斬天"], GROUP, 3, 22, 3, 8,
                      3155, "全體", "金・藍焰斬天", "藍焰刀氣席捲全場。"))
    skills.append(buff(1646, "金鋼結陣", ["藍鋼護體"], PARTY, 25, 5, 5,
                       3173, "全體友軍", "藍鋼護體", "為全體友軍提升外防。",
                       [state_effect(48)]))
    skills.append(atk(1647, "血蓮狂斬", ["金", "藍焰斬天"], SINGLE, 4, 28, 4, 10,
                      3155, "單體", "金・藍焰斬天", "血蓮狂斬，極強刀擊。"))

    # ── 墨汐若 (奇門/風) — 1648-1651 ──
    skills.append(atk(1648, "梅花旋舞", ["奇門", "梅花十三鞭法"], GROUP, 2, 18, 2, 8,
                      3162, "全體", "奇門・梅花十三鞭法", "梅花鞭法橫掃全場。"))
    skills.append(atk(1649, "花刃穿林", ["風", "落花飛刃"], SINGLE, 3, 22, 3, 10,
                      3162, "單體", "風・落花飛刃", "花刃穿刺敵人。"))
    skills.append(buff(1650, "梅甲凝香", ["花雨凝甲"], PARTY, 25, 5, 5,
                       3173, "全體友軍", "花雨凝甲", "為全體友軍提升內防。",
                       [state_effect(51)]))
    skills.append(atk(1651, "暴風落梅", ["風", "落花飛刃"], GROUP, 4, 30, 4, 8,
                      3162, "全體", "風・落花飛刃", "暴風花刃席捲全場。"))

    # ── 沅花 (筆/木) — 1652-1655 ──
    skills.append(matk(1652, "潑墨掃群", ["筆法", "丹青筆法"], GROUP, 2, 18, 2, 8,
                       3160, "全體", "筆法・丹青筆法", "潑墨筆法攻擊全場敵人。"))
    skills.append(matk(1653, "千花烈筆", ["木", "落花殺筆"], SINGLE, 3, 22, 3, 10,
                       3160, "單體", "木・落花殺筆", "筆鋒化花穿刺敵人。"))
    skills.append(buff(1654, "畫中結界", ["花甲護身"], PARTY, 25, 5, 5,
                       3173, "全體友軍", "花甲護身", "為全體友軍提升外防與內防。",
                       [state_effect(48), state_effect(51)]))
    skills.append(matk(1655, "山河潑墨", ["木", "落花殺筆"], GROUP, 4, 30, 4, 8,
                       3160, "全體", "木・落花殺筆", "山河潑墨席捲全場。"))

    # ── 談笑 (劍/寒) — 1656-1659 ──
    skills.append(atk(1656, "冰花連斬", ["劍法", "凝霜劍法"], RANDOM3, 2, 16, 2, 8,
                      3154, "隨機三體", "劍法・凝霜劍法", "冰花劍法攻擊隨機三名敵人。",
                      repeats=3))
    skills.append(atk(1657, "霜寒劍氣", ["寒", "霜刃穿骨"], GROUP, 3, 22, 3, 8,
                      3154, "全體", "寒・霜刃穿骨", "霜寒劍氣席捲全場。"))
    skills.append(buff(1658, "凝霜護體", ["冰魄守心"], SELF, 15, 3, 5,
                       3173, "自身", "冰魄守心", "提升自身外防與內防。",
                       [state_effect(48), state_effect(51)]))
    skills.append(atk(1659, "紫霞冰破", ["寒", "霜刃穿骨"], SINGLE, 4, 28, 4, 10,
                      3154, "單體", "寒・霜刃穿骨", "極寒劍氣穿刺敵人。"))

    # ── 白沫檸 (槍/水) — 1660-1663 ──
    skills.append(atk(1660, "水擊橫掃", ["槍法", "水擊槍法"], GROUP, 2, 18, 2, 8,
                      3157, "全體", "槍法・水擊槍法", "水擊槍法橫掃全場。"))
    skills.append(atk(1661, "三千里刺", ["水", "清流破浪"], SINGLE, 3, 22, 3, 10,
                      3157, "單體", "水・清流破浪", "水流槍刺穿透敵人。"))
    skills.append(heal(1662, "木源回氣", ["華木成林"], SELF, 18, 4, 5,
                       3171, "自身", "華木成林", "回復自身氣血並附加再生。",
                       level="medium", effects=[state_effect(17)]))
    skills.append(atk(1663, "怒水穿甲", ["水", "清流破浪"], SINGLE, 4, 28, 4, 10,
                      3157, "單體", "水・清流破浪", "怒水槍擊，無視30%護甲。",
                      extra="<Armor Penetration: 30%>"))

    # ── 青兒 (音律/風) — 1664-1667 ──
    skills.append(matk(1664, "風鈴曲", ["音律", "天籟琴音"], GROUP, 2, 18, 2, 8,
                       3159, "全體", "音律・天籟琴音", "風鈴琴音攻擊全場敵人。"))
    skills.append(matk(1665, "霞光破魔", ["風", "霞影裂空"], SINGLE, 3, 22, 3, 10,
                       3159, "單體", "風・霞影裂空", "霞光琴音穿破敵人。"))
    skills.append(heal(1666, "琴音護靈", ["霞光凝盾"], PARTY, 25, 4, 5,
                       3171, "全體友軍", "霞光凝盾", "回復全體友軍氣血並清除減益。",
                       level="medium", extra="<Remove Debuffs>"))
    skills.append(matk(1667, "斷霞裂風", ["風", "霞影裂空"], GROUP, 4, 30, 4, 8,
                       3159, "全體", "風・霞影裂空", "斷霞琴音席捲全場。"))

    # ── 珞堇 (音律/木) — 1668-1671 ──
    skills.append(matk(1668, "琴弦掃擊", ["音律", "古弦心法"], GROUP, 2, 18, 2, 8,
                       3159, "全體", "音律・古弦心法", "琴弦振動攻擊全場敵人。"))
    skills.append(matk(1669, "破弦殺音", ["木", "弦震八方"], SINGLE, 3, 22, 3, 10,
                       3159, "單體", "木・弦震八方", "破弦殺音穿刺敵人。"))
    skills.append(buff(1670, "和弦護盾", ["古韻護魂"], PARTY, 25, 5, 5,
                       3173, "全體友軍", "古韻護魂", "為全體友軍提升內防。",
                       [state_effect(51)]))
    skills.append(matk(1671, "萬弦穿心", ["木", "弦震八方"], SINGLE, 4, 28, 4, 10,
                       3159, "單體", "木・弦震八方", "萬弦齊發穿刺敵人。"))

    # ── 龍玉 (劍/土→寒 per plan) — 1672-1675 ──
    skills.append(atk(1672, "龍鱗掃擊", ["劍法", "龍吟劍法"], GROUP, 2, 18, 2, 8,
                      3154, "全體", "劍法・龍吟劍法", "龍鱗劍氣橫掃全場。"))
    skills.append(atk(1673, "伏龍冰刃", ["寒", "冰劍寒鋒"], SINGLE, 3, 22, 3, 10,
                      3154, "單體", "寒・冰劍寒鋒", "伏龍冰刃穿刺敵人。"))
    skills.append(buff(1674, "龍甲凝結", ["玄冰鐵壁"], SELF, 15, 3, 5,
                       3173, "自身", "玄冰鐵壁", "提升自身外防。",
                       [state_effect(48)]))
    skills.append(atk(1675, "霜龍破界", ["寒", "冰劍寒鋒"], GROUP, 4, 30, 4, 8,
                      3154, "全體", "寒・冰劍寒鋒", "霜龍劍氣席捲全場。"))

    # ── 七霜 (短兵/寒) — 1676-1679 ──
    skills.append(atk(1676, "銀針連射", ["短兵", "陰山醫術"], RANDOM3, 2, 16, 2, 8,
                      3172, "隨機三體", "短兵・陰山醫術", "銀針連射攻擊隨機三名敵人。",
                      repeats=3))
    skills.append(atk(1677, "枯榮一擊", ["寒", "翠針破穴"], SINGLE, 3, 22, 3, 10,
                      3172, "單體", "寒・翠針破穴", "枯榮之力穿刺敵人。"))
    skills.append(heal(1678, "回春妙手", ["翡翠回春"], PARTY, 25, 4, 5,
                       3171, "全體友軍", "翡翠回春", "回復全體友軍氣血並附加再生。",
                       level="medium", effects=[state_effect(17)]))
    skills.append(heal(1679, "針灸疏通", ["翡翠回春"], SINGLE, 15, 3, 5,
                       3171, "單體", "翡翠回春", "針灸治療並清除減益。",
                       level="medium", extra="<Remove Debuffs>"))

    # ── 瑤琴劍 (劍/風) — 1680-1683 ──
    skills.append(atk(1680, "九霄旋斬", ["劍法", "九霄劍法"], GROUP, 2, 18, 2, 8,
                      3154, "全體", "劍法・九霄劍法", "九霄劍氣橫掃全場。"))
    skills.append(atk(1681, "琴嘯裂空", ["風", "九霄劍嘯"], GROUP, 3, 22, 3, 8,
                      3154, "全體", "風・九霄劍嘯", "琴嘯劍氣席捲全場。"))
    skills.append(buff(1682, "碧雲護場", ["碧雲護天"], PARTY, 25, 5, 5,
                       3173, "全體友軍", "碧雲護天", "為全體友軍提升外防與內防。",
                       [state_effect(48), state_effect(51)]))
    skills.append(atk(1683, "一氣化霄", ["風", "九霄劍嘯"], SINGLE, 4, 28, 4, 10,
                      3154, "單體", "風・九霄劍嘯", "一氣化霄，極強劍擊。"))

    # ── 莫縈懷 (奇門/風) — 1684-1687 ──
    skills.append(atk(1684, "白綾旋風", ["奇門", "片羽沾衣"], GROUP, 2, 18, 2, 8,
                      3162, "全體", "奇門・片羽沾衣", "白綾旋風攻擊全場敵人。"))
    skills.append(atk(1685, "兩儀幻殺", ["風", "音殺無形"], SINGLE, 3, 22, 3, 10,
                      3162, "單體", "風・音殺無形", "兩儀幻術穿刺敵人。"))
    skills.append(buff(1686, "隱身護體", ["音盾隱身"], SELF, 12, 3, 5,
                       3173, "自身", "音盾隱身", "提升閃避與輕功。",
                       [state_effect(27), state_effect(54)]))
    skills.append(atk(1687, "風刃絞殺", ["風", "音殺無形"], GROUP, 4, 30, 4, 8,
                      3162, "全體", "風・音殺無形", "風刃絞殺席捲全場。"))

    # ── 黃凱竹 (弓/木) — 1688-1691 ──
    skills.append(atk(1688, "連弩齊射", ["弓術", "鐘塔煉藥術"], GROUP, 2, 18, 2, 8,
                      3165, "全體", "弓術・鐘塔煉藥術", "連弩齊射攻擊全場敵人。"))
    skills.append(matk(1689, "毒霧爆破", ["木", "機關暴雨"], GROUP, 3, 22, 3, 8,
                       3165, "全體", "木・機關暴雨", "毒霧爆破席捲全場。"))
    skills.append(buff(1690, "機關防壁", ["鐵甲機陣"], PARTY, 25, 5, 5,
                       3173, "全體友軍", "鐵甲機陣", "為全體友軍提升外防。",
                       [state_effect(48)]))
    skills.append(atk(1691, "天機連弩", ["木", "機關暴雨"], RANDOM3, 4, 26, 4, 8,
                      3165, "隨機三體", "木・機關暴雨", "天機連弩攻擊隨機三名敵人。",
                      repeats=3))

    # ── 劉靜靜 (奇門/水) — 1692-1695 ──
    skills.append(atk(1692, "毒扇飛舞", ["奇門", "海波暗殺術"], GROUP, 2, 18, 2, 8,
                      3166, "全體", "奇門・海波暗殺術", "毒扇飛舞攻擊全場敵人。"))
    skills.append(atk(1693, "霜毒連刺", ["水", "霜毒穿脈"], RANDOM3, 3, 20, 3, 8,
                      3166, "隨機三體", "水・霜毒穿脈", "霜毒連刺攻擊隨機三名敵人。",
                      repeats=3))
    skills.append(buff(1694, "毒蕊護體", ["含蕊固本"], SELF, 12, 3, 5,
                       3173, "自身", "含蕊固本", "提升自身毒抗。",
                       [state_effect(51), state_effect(27)]))
    skills.append(matk(1695, "萬毒噬心", ["水", "霜毒穿脈"], SINGLE, 4, 28, 4, 10,
                       3170, "單體", "水・霜毒穿脈", "萬毒噬心穿刺敵人。"))

    assert len(skills) == 92, f"Expected 92 skills, got {len(skills)}"
    return skills


# ── Main Logic ──────────────────────────────────────────────────────

def part_a_renames(skills, system):
    """Part A: Rename element and skills for 白沫檸."""
    print("\n=== Part A: Renames ===")

    # Find and rename element "沫團槍法" -> "水擊槍法" in System.json elements
    elements = system["elements"]
    found_elem = False
    for i, e in enumerate(elements):
        if e == "沫團槍法":
            elements[i] = "水擊槍法"
            print(f"  Element [{i}]: 沫團槍法 -> 水擊槍法")
            found_elem = True
            break
    if not found_elem:
        print("  WARN: Element '沫團槍法' not found in elements array (may already be renamed)")

    # Rename skill 1506: 惡魯突刺 -> 破水突刺
    if skills[1506]["name"] == "惡魯突刺":
        skills[1506]["name"] = "破水突刺"
        print("  Skill 1506: 惡魯突刺 -> 破水突刺")
    else:
        print(f"  WARN: Skill 1506 name is '{skills[1506]['name']}', not '惡魯突刺'")

    # Rename skill 1514: 沫團猛攻 -> 水擊猛攻
    if skills[1514]["name"] == "沫團猛攻":
        skills[1514]["name"] = "水擊猛攻"
        print("  Skill 1514: 沫團猛攻 -> 水擊猛攻")
    else:
        print(f"  WARN: Skill 1514 name is '{skills[1514]['name']}', not '沫團猛攻'")

    # Update all skill notes referencing 沫團槍法 -> 水擊槍法
    renamed_notes = 0
    for s in skills:
        if s and isinstance(s, dict) and "note" in s:
            if "沫團槍法" in s["note"]:
                s["note"] = s["note"].replace("沫團槍法", "水擊槍法")
                renamed_notes += 1
            if "沫團槍法" in s.get("description", ""):
                s["description"] = s["description"].replace("沫團槍法", "水擊槍法")
    print(f"  Updated {renamed_notes} skill notes: 沫團槍法 -> 水擊槍法")

    # Update container 1937 name
    if skills[1937]["name"] == "沫團槍法":
        skills[1937]["name"] = "水擊槍法"
        print("  Container 1937: 沫團槍法 -> 水擊槍法")

    # Update separator 1936 name
    if "沫團槍法" in skills[1936].get("name", ""):
        skills[1936]["name"] = skills[1936]["name"].replace("沫團槍法", "水擊槍法")
        print(f"  Separator 1936 updated")


def part_b_elements(system):
    """Part B: Add 46 new elements at indices 100-145."""
    print("\n=== Part B: New Elements ===")
    elements = system["elements"]

    # Truncate to 100 entries (keep 0-99)
    if len(elements) > 100:
        removed = elements[100:]
        elements[:] = elements[:100]
        print(f"  Truncated elements from {100 + len(removed)} to 100 (removed: {removed})")

    # Pad to 100 if needed
    while len(elements) < 100:
        elements.append("")

    # Append 46 new elements
    for name in NEW_ELEMENTS:
        elements.append(name)

    assert len(elements) == 146, f"Expected 146 elements, got {len(elements)}"
    print(f"  Elements array now has {len(elements)} entries (indices 0-{len(elements)-1})")
    print(f"  C2 elements: [{elements[100]}...{elements[122]}] (100-122)")
    print(f"  C3 elements: [{elements[123]}...{elements[145]}] (123-145)")


def part_c_multi_element(skills):
    """Part C: Update Multi-Element tags on existing C2 skills."""
    print("\n=== Part C: Multi-Element Tag Updates ===")
    updated = 0

    # Build lookup: c2_name -> (natural_element, c2_name)
    # For each character, find their C2 skills and rewrite the Multi-Element tag
    for char in CHARACTERS:
        c1_name = char["c1"]
        c2_name = char["c2"]
        c3_name = char["c3"]
        weapon = char["weapon"]
        element = char["element"]

        # Process C2 skills: replace weapon+C1 references with element+C2
        for sid in char["c2_skills"]:
            s = skills[sid]
            note = s.get("note", "")
            m = re.search(r"<Multi-Element:\s*([^>]+)>", note)
            if not m:
                continue

            old_tag = m.group(0)
            old_elems = [e.strip() for e in m.group(1).split(",")]

            # Build new element list: replace weapon type and C1 name with element and C2 name
            new_elems = []
            for e in old_elems:
                if e == weapon or e == c1_name:
                    continue  # Remove old weapon/C1 references
                new_elems.append(e)

            # Ensure element and C2 name are present
            if element not in new_elems:
                new_elems.insert(0, element)
            if c2_name not in new_elems:
                new_elems.append(c2_name)

            new_tag = f"<Multi-Element: {', '.join(new_elems)}>"
            if old_tag != new_tag:
                s["note"] = note.replace(old_tag, new_tag)
                # Also update description tags
                desc = s.get("description", "")
                if f"\\c[3]{weapon}・{c1_name}" in desc:
                    desc = desc.replace(f"\\c[3]{weapon}・{c1_name}", f"\\c[3]{element}・{c2_name}")
                    s["description"] = desc
                updated += 1

        # Process C3 skills: add <Multi-Element: C3名> if not present
        for sid in char["c3_skills"]:
            s = skills[sid]
            note = s.get("note", "")
            if f"<Multi-Element:" not in note and c3_name:
                # Add Multi-Element tag for C3
                if "<Color:" in note:
                    # Insert after Color tag
                    note = note.replace("\n", f"\n<Multi-Element: {c3_name}>\n<Multi-Element Rule: Multiply>\n", 1)
                else:
                    note = f"<Multi-Element: {c3_name}>\n<Multi-Element Rule: Multiply>\n" + note
                s["note"] = note
                updated += 1

    print(f"  Updated {updated} skill Multi-Element tags")


def part_d_new_skills(skills):
    """Part D: Create 92 new skills at IDs 1604-1695."""
    print("\n=== Part D: New Skills ===")
    new_skills = build_new_skills()

    # Ensure skills array is large enough
    while len(skills) <= 1695:
        skills.append(None)

    for s in new_skills:
        sid = s["id"]
        old_name = skills[sid]["name"] if skills[sid] else "(null)"
        skills[sid] = s
        print(f"  [{sid}] {old_name} -> {s['name']}")

    print(f"  Created {len(new_skills)} new skills (IDs 1604-1695)")


def part_e_containers(skills):
    """Part E: Update container Known Skills Lists to include new skill IDs."""
    print("\n=== Part E: Container Updates ===")
    updated = 0

    # Container IDs start at 1881 (C1), 1882 (C2), 1883 (C3) for first char
    # Pattern: 1880 + char_idx*4 + 1/2/3
    CONTAINER_BASE = 1880

    # Map new skill IDs to their container type per character
    NEW_SKILL_BASE = 1604
    for char_idx, char in enumerate(CHARACTERS):
        new_base = NEW_SKILL_BASE + char_idx * 4
        # new_base+0 = C1 skill, +1 = C2 skill, +2 = C3 skill, +3 = C2 skill
        new_c1_ids = [new_base]      # 1 C1 skill
        new_c2_ids = [new_base + 1, new_base + 3]  # 2 C2 skills
        new_c3_ids = [new_base + 2]  # 1 C3 skill

        # Handle 七霜 special case: skill index+3 (1679) is C3 not C2
        if char["name"] == "七霜":
            new_c2_ids = [new_base + 1]  # only 1677
            new_c3_ids = [new_base + 2, new_base + 3]  # 1678 + 1679

        c1_container_id = CONTAINER_BASE + char_idx * 4 + 1
        c2_container_id = CONTAINER_BASE + char_idx * 4 + 2
        c3_container_id = CONTAINER_BASE + char_idx * 4 + 3

        for container_id, new_ids in [
            (c1_container_id, new_c1_ids),
            (c2_container_id, new_c2_ids),
            (c3_container_id, new_c3_ids),
        ]:
            container = skills[container_id]
            note = container["note"]
            m = re.search(r"<Known Skills List:\s*([^>]+)>", note)
            if m:
                existing_ids = [int(x.strip()) for x in m.group(1).split(",")]
                combined = existing_ids + new_ids
                new_list = ", ".join(str(x) for x in combined)
                new_tag = f"<Known Skills List: {new_list}>"
                container["note"] = note.replace(m.group(0), new_tag)
                updated += 1
                print(f"  Container {container_id} ({container['name']}): added {new_ids}")

    print(f"  Updated {updated} containers")


def verify(skills, system):
    """Verify all changes."""
    print("\n=== Verification ===")
    ok = True

    # Check element count
    if len(system["elements"]) != 146:
        print(f"  FAIL: Expected 146 elements, got {len(system['elements'])}")
        ok = False
    else:
        print(f"  OK: {len(system['elements'])} elements")

    # Check no 沫團槍法 remains
    for s in skills:
        if s and isinstance(s, dict):
            if "沫團槍法" in s.get("note", "") or "沫團槍法" in s.get("name", ""):
                print(f"  FAIL: Skill {s['id']} still references 沫團槍法")
                ok = False
    if "沫團槍法" in str(system["elements"]):
        print("  FAIL: Element still has 沫團槍法")
        ok = False

    # Check new skills exist
    for sid in range(1604, 1696):
        s = skills[sid]
        if not s or not s.get("name"):
            print(f"  FAIL: Skill {sid} missing")
            ok = False
    new_count = sum(1 for sid in range(1604, 1696) if skills[sid] and skills[sid].get("name"))
    print(f"  OK: {new_count}/92 new skills created")

    # Check containers have expanded lists
    for char_idx, char in enumerate(CHARACTERS):
        for offset in (1, 2, 3):
            cid = 1880 + char_idx * 4 + offset
            note = skills[cid].get("note", "")
            m = re.search(r"<Known Skills List:\s*([^>]+)>", note)
            if m:
                ids = [int(x.strip()) for x in m.group(1).split(",")]
                new_ids_in_range = [x for x in ids if 1604 <= x <= 1695]
                if not new_ids_in_range:
                    print(f"  FAIL: Container {cid} ({skills[cid]['name']}) has no new IDs")
                    ok = False

    if ok:
        print("  All checks passed!")
    return ok


def main():
    print("Loading data files...")
    skills = load_json("Skills.json")
    system = load_json("System.json")

    part_a_renames(skills, system)
    part_b_elements(system)
    part_c_multi_element(skills)
    part_d_new_skills(skills)
    part_e_containers(skills)

    if not verify(skills, system):
        print("\nVerification FAILED. Not saving.")
        return 1

    print("\nSaving files...")
    save_json("System.json", system)
    save_json("Skills.json", skills)

    print("\nDone!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
