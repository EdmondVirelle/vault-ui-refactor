#!/usr/bin/env python3
"""
patch_skill_learn_system.py

Patches RPG Maker MZ data files to configure VisuMZ_2_SkillLearnSystem
for ALL 23 characters (69 battle classes):

  A. plugins.js   — Update AP/SP display names and gain formulas
  B. Items.json   — Create 25 manuscript fragment items (ID 1001-1025)
  C. Classes.json — Add <Learn Skills> tags to 69 battle classes
  D. Skills.json  — Add Learn Cost/Require tags to ~540 learnable skills
  E. Enemies.json — Add AP/SP rewards based on EXP tiers

Usage:
    python scripts/patch_skill_learn_system.py
"""

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "Consilience"

# ═══════════════════════════════════════════════════════════════════════════════
# Fragment Item Definitions (ID 1001-1025)
# ═══════════════════════════════════════════════════════════════════════════════

FRAGMENT_ITEMS = {
    # --- Existing (sword characters) ---
    1001: {"name": "江湖劍譜碎片", "desc": "江湖流傳的劍法秘笈碎片，可用於學習通用劍法。"},
    1002: {"name": "劃月劍譜碎片", "desc": "劃月宮珍藏的劍譜殘頁，蘊含劃月劍法的奧義。"},
    1003: {"name": "九霄劍譜碎片", "desc": "九霄派傳承的劍譜殘頁，記載九霄劍法的精髓。"},
    1004: {"name": "凝霜劍譜碎片", "desc": "仙池門的劍譜殘頁，凝聚凝霜劍法的心法。"},
    1005: {"name": "龍吟劍譜碎片", "desc": "龍門山莊的劍譜殘頁，承載龍吟劍法的真意。"},
    1006: {"name": "天機劍譜碎片", "desc": "天機閣的劍譜殘頁，暗藏天機劍法的玄機。"},
    1007: {"name": "醉仙劍譜碎片", "desc": "醉仙門的劍譜殘頁，流露醉仙劍法的飄逸。"},
    1008: {"name": "血海劍譜碎片", "desc": "血海門的劍譜殘頁，滲透血海劍法的殺意。"},
    # --- New (common + 16 non-sword characters) ---
    1009: {"name": "江湖武學碎片", "desc": "江湖流傳的武學碎片，可用於學習通用武器招式、輕功及六藝。"},
    1010: {"name": "琴音秘笈碎片", "desc": "記載天籟琴音的秘笈碎片，蘊含青兒獨門武學。"},
    1011: {"name": "蘭心秘笈碎片", "desc": "記載蘭心拳法的秘笈碎片，蘊含湮菲花獨門武學。"},
    1012: {"name": "追風秘笈碎片", "desc": "記載追風短刃的秘笈碎片，蘊含闕崇陽獨門武學。"},
    1013: {"name": "天罡秘笈碎片", "desc": "記載天罡棍法的秘笈碎片，蘊含絲塔娜獨門武學。"},
    1014: {"name": "丹青秘笈碎片", "desc": "記載丹青筆法的秘笈碎片，蘊含沅花獨門武學。"},
    1015: {"name": "水擊秘笈碎片", "desc": "記載水擊槍法的秘笈碎片，蘊含白沫檸獨門武學。"},
    1016: {"name": "古弦秘笈碎片", "desc": "記載古弦心法的秘笈碎片，蘊含珞堇獨門武學。"},
    1017: {"name": "梅花秘笈碎片", "desc": "記載梅花十三鞭法的秘笈碎片，蘊含墨汐若獨門武學。"},
    1018: {"name": "百變秘笈碎片", "desc": "記載百變身法的秘笈碎片，蘊含聶思泠獨門武學。"},
    1019: {"name": "神棍秘笈碎片", "desc": "記載神棍打法的秘笈碎片，蘊含無名丐獨門武學。"},
    1020: {"name": "霸刀秘笈碎片", "desc": "記載霸刀術的秘笈碎片，蘊含郭霆黃獨門武學。"},
    1021: {"name": "萬蠱秘笈碎片", "desc": "記載萬蠱毒經的秘笈碎片，蘊含藍靜冥獨門武學。"},
    1022: {"name": "鐘塔秘笈碎片", "desc": "記載鐘塔煉藥術的秘笈碎片，蘊含黃凱竹獨門武學。"},
    1023: {"name": "海波秘笈碎片", "desc": "記載海波暗殺術的秘笈碎片，蘊含劉靜靜獨門武學。"},
    1024: {"name": "陰山秘笈碎片", "desc": "記載陰山醫術的秘笈碎片，蘊含七霜獨門武學。"},
    1025: {"name": "片羽秘笈碎片", "desc": "記載片羽沾衣的秘笈碎片，蘊含莫縈懷獨門武學。"},
}

FRAGMENT_ICON = 3203

# ═══════════════════════════════════════════════════════════════════════════════
# Skill Container Definitions — container skill → learnable IDs (chain order)
# ═══════════════════════════════════════════════════════════════════════════════

CONTAINERS = {
    # ── Sword characters (existing) ──────────────────────────────────────────
    # 東方啟 — 劃月
    1881: [1352, 1353, 1354, 1356, 1605],
    1882: [1357, 1359, 1360, 1361, 1606, 1608],
    1883: [1355, 1358, 1607],
    # 瑤琴劍 — 九霄
    1957: [1561, 1562, 1563, 1565, 1700],
    1958: [1566, 1568, 1569, 1570, 1701, 1703],
    1959: [1564, 1567, 1702],
    # 談笑 — 凝霜
    1933: [1495, 1496, 1497, 1499, 1670],
    1934: [1500, 1502, 1503, 1504, 1671, 1673],
    1935: [1498, 1501, 1672],
    # 龍玉 — 龍吟
    1949: [1539, 1540, 1541, 1543, 1690],
    1950: [1546, 1547, 1548, 1544, 1691, 1693],
    1951: [1542, 1545, 1692],
    # 司徒長生 — 天機
    1909: [1429, 1430, 1431, 1433, 1640],
    1910: [1434, 1435, 1436, 1437, 1438, 1641, 1643],
    1911: [1432, 1642],
    # 楊古晨 — 醉仙
    1905: [1418, 1419, 1420, 1423, 1635],
    1906: [1424, 1425, 1427, 1426, 1636, 1638],
    1907: [1421, 1422, 1637],
    # 殷染幽 — 血海
    1897: [1396, 1397, 1398, 1400, 1625],
    1898: [1401, 1403, 1404, 1405, 1626, 1628],
    1899: [1399, 1402, 1627],

    # ── Non-sword characters (new) ───────────────────────────────────────────
    # 青兒 — 天籟琴音／霞影裂空／霞光凝盾
    1941: [1517, 1518, 1522, 1524, 1680],
    1942: [1525, 1526, 1519, 1520, 1681, 1683],
    1943: [1521, 1523, 1682],
    # 湮菲花 — 蘭心拳法／蘭刺穿心／蘭盾芳華
    1885: [1363, 1364, 1367, 1368, 1610],
    1886: [1371, 1372, 1365, 1366, 1611, 1613],
    1887: [1369, 1370, 1612],
    # 闕崇陽 — 追風短刃／雷電破空／風壁禦雷
    1889: [1374, 1375, 1376, 1378, 1615],
    1890: [1379, 1380, 1381, 1382, 1383, 1616, 1618],
    1891: [1377, 1617],
    # 絲塔娜 — 天罡棍法／沙暴裂地／金甲沙城
    1893: [1385, 1386, 1387, 1389, 1620],
    1894: [1390, 1392, 1393, 1394, 1621, 1623],
    1895: [1388, 1391, 1622],
    # 沅花 — 丹青筆法／落花殺筆／花甲護身
    1929: [1484, 1485, 1486, 1487, 1665],
    1930: [1488, 1491, 1492, 1493, 1666, 1668],
    1931: [1489, 1490, 1667],
    # 白沫檸 — 水擊槍法／清流破浪／華木成林
    1937: [1506, 1507, 1508, 1510, 1675],
    1938: [1512, 1513, 1514, 1515, 1676, 1678],
    1939: [1509, 1511, 1677],
    # 珞堇 — 古弦心法／弦震八方／古韻護魂
    1945: [1528, 1529, 1530, 1533, 1685, 1719],
    1946: [1534, 1535, 1536, 1537, 1686, 1688],
    1947: [1531, 1532, 1687],
    # 墨汐若 — 梅花十三鞭法／落花飛刃／花雨凝甲
    1925: [1473, 1474, 1475, 1477, 1660],
    1926: [1480, 1481, 1482, 1476, 1661, 1663],
    1927: [1478, 1479, 1662],
    # 聶思泠 — 百變身法／鬼手摘星／靈巧避禍
    1917: [1451, 1452, 1453, 1455, 1650],
    1918: [1457, 1458, 1459, 1460, 1651, 1653],
    1919: [1454, 1456, 1652],
    # 無名丐 — 神棍打法／棍掃千軍／神棍擋關
    1913: [1440, 1441, 1442, 1444, 1645],
    1914: [1447, 1448, 1449, 1445, 1646, 1648],
    1915: [1443, 1446, 1647],
    # 郭霆黃 — 霸刀術／藍焰斬天／藍鋼護體
    1921: [1462, 1463, 1464, 1466, 1655],
    1922: [1467, 1468, 1469, 1471, 1656, 1658],
    1923: [1465, 1470, 1657],
    # 藍靜冥 — 萬蠱毒經／冥毒噬魂／幽蠱化盾
    1901: [1407, 1408, 1409, 1410, 1630],
    1902: [1411, 1413, 1414, 1415, 1416, 1631, 1633],
    1903: [1412, 1632],
    # 黃凱竹 — 鐘塔煉藥術／機關暴雨／鐵甲機陣
    1965: [1583, 1584, 1585, 1587, 1710],
    1966: [1588, 1590, 1591, 1592, 1711, 1713],
    1967: [1586, 1589, 1712],
    # 劉靜靜 — 海波暗殺術／霜毒穿脈／含蕊固本
    1969: [1594, 1595, 1596, 1598, 1715],
    1970: [1599, 1601, 1602, 1603, 1716, 1718],
    1971: [1597, 1600, 1717],
    # 七霜 — 陰山醫術／翠針破穴／翡翠回春
    1953: [1550, 1551, 1555, 1557, 1695],
    1954: [1552, 1553, 1554, 1556, 1696],
    1955: [1558, 1559, 1697, 1698],
    # 莫縈懷 — 片羽沾衣／音殺無形／音盾隱身
    1961: [1572, 1573, 1574, 1576, 1705],
    1962: [1577, 1579, 1580, 1581, 1706, 1708],
    1963: [1575, 1578, 1707],
}

CONTAINER_TO_FRAGMENT = {
    # Sword characters
    1881: 1002, 1882: 1002, 1883: 1002,  # 東方啟
    1957: 1003, 1958: 1003, 1959: 1003,  # 瑤琴劍
    1933: 1004, 1934: 1004, 1935: 1004,  # 談笑
    1949: 1005, 1950: 1005, 1951: 1005,  # 龍玉
    1909: 1006, 1910: 1006, 1911: 1006,  # 司徒長生
    1905: 1007, 1906: 1007, 1907: 1007,  # 楊古晨
    1897: 1008, 1898: 1008, 1899: 1008,  # 殷染幽
    # Non-sword characters
    1941: 1010, 1942: 1010, 1943: 1010,  # 青兒
    1885: 1011, 1886: 1011, 1887: 1011,  # 湮菲花
    1889: 1012, 1890: 1012, 1891: 1012,  # 闕崇陽
    1893: 1013, 1894: 1013, 1895: 1013,  # 絲塔娜
    1929: 1014, 1930: 1014, 1931: 1014,  # 沅花
    1937: 1015, 1938: 1015, 1939: 1015,  # 白沫檸
    1945: 1016, 1946: 1016, 1947: 1016,  # 珞堇
    1925: 1017, 1926: 1017, 1927: 1017,  # 墨汐若
    1917: 1018, 1918: 1018, 1919: 1018,  # 聶思泠
    1913: 1019, 1914: 1019, 1915: 1019,  # 無名丐
    1921: 1020, 1922: 1020, 1923: 1020,  # 郭霆黃
    1901: 1021, 1902: 1021, 1903: 1021,  # 藍靜冥
    1965: 1022, 1966: 1022, 1967: 1022,  # 黃凱竹
    1969: 1023, 1970: 1023, 1971: 1023,  # 劉靜靜
    1953: 1024, 1954: 1024, 1955: 1024,  # 七霜
    1961: 1025, 1962: 1025, 1963: 1025,  # 莫縈懷
}

COMMON_SWORD_SKILLS = list(range(1002, 1017))  # 1002-1016

# ═══════════════════════════════════════════════════════════════════════════════
# Elemental Skill Blocks (from 江湖武學 — sword characters only)
# ═══════════════════════════════════════════════════════════════════════════════

ELEM_BLOCKS = {
    "陰": list(range(1174, 1186)),
    "陽": list(range(1187, 1199)),
    "土": list(range(1239, 1251)),
    "金": list(range(1252, 1264)),
    "水": list(range(1265, 1277)),
    "風": list(range(1278, 1290)),
    "雷": list(range(1291, 1303)),
    "電": list(range(1317, 1329)),
    "寒": list(range(1330, 1342)),
}

CHAR_ELEMENTS = {
    "東方啟":   (["金"],         [2, 3, 4]),
    "瑤琴劍":   (["風"],         [22, 23, 24]),
    "談笑":     (["寒", "陰"],   [30, 31, 32]),
    "龍玉":     (["土", "寒"],   [42, 43, 44]),
    "司徒長生": (["電", "陽"],   [46, 47, 48]),
    "楊古晨":   (["雷"],         [50, 51, 52]),
    "殷染幽":   (["水"],         [54, 55, 56]),
}

# ═══════════════════════════════════════════════════════════════════════════════
# Weapon Skill Blocks (12 types × 12 skills — non-sword characters)
# ═══════════════════════════════════════════════════════════════════════════════

WEAPON_BLOCKS = {
    "刀法": list(range(1018, 1030)),   # 12 skills
    "棍法": list(range(1031, 1043)),
    "槍法": list(range(1044, 1056)),
    "拳掌": list(range(1057, 1069)),
    "音律": list(range(1070, 1082)),
    "奇門": list(range(1083, 1095)),
    "弓術": list(range(1096, 1108)),
    "筆法": list(range(1109, 1121)),
    "暗器": list(range(1122, 1134)),
    "短兵": list(range(1135, 1147)),
    "醫術": list(range(1148, 1160)),
    "毒術": list(range(1161, 1173)),
}

# Character → (weapon_types, class_ids)
CHAR_WEAPONS = {
    "青兒":     (["音律"],           [6, 7, 8]),
    "湮菲花":   (["拳掌", "暗器"],   [10, 11, 12]),
    "闕崇陽":   (["短兵"],           [14, 15, 16]),
    "絲塔娜":   (["棍法"],           [18, 19, 20]),
    "沅花":     (["筆法"],           [26, 27, 28]),
    "白沫檸":   (["槍法"],           [34, 35, 36]),
    "珞堇":     (["音律"],           [38, 39, 40]),
    "墨汐若":   (["奇門"],           [58, 59, 60]),
    "聶思泠":   (["拳掌"],           [62, 63, 64]),
    "無名丐":   (["棍法"],           [66, 67, 68]),
    "郭霆黃":   (["刀法"],           [70, 71, 72]),
    "藍靜冥":   (["毒術"],           [74, 75, 76]),
    "黃凱竹":   (["弓術", "毒術"],   [78, 79, 80]),
    "劉靜靜":   (["奇門"],           [82, 83, 84]),
    "七霜":     (["醫術"],           [86, 87, 88]),
    "莫縈懷":   (["奇門"],           [90, 91, 92]),
}

# ═══════════════════════════════════════════════════════════════════════════════
# Class → Personal Skill IDs (from container Known Skills Lists)
# ═══════════════════════════════════════════════════════════════════════════════

CLASS_LEARN_SKILLS = {
    # ── Sword characters (existing) ──
    # 東方啟
    2:  [1352, 1353, 1354, 1356, 1605],
    3:  [1357, 1359, 1360, 1361, 1606, 1608],
    4:  [1355, 1358, 1607],
    # 瑤琴劍
    22: [1561, 1562, 1563, 1565, 1700],
    23: [1566, 1568, 1569, 1570, 1701, 1703],
    24: [1564, 1567, 1702],
    # 談笑 (class 30 already has tags — handled in main but not here)
    31: [1500, 1502, 1503, 1504, 1671, 1673],
    32: [1498, 1501, 1672],
    # 龍玉
    42: [1539, 1540, 1541, 1543, 1690],
    43: [1546, 1547, 1548, 1544, 1691, 1693],
    44: [1542, 1545, 1692],
    # 司徒長生
    46: [1429, 1430, 1431, 1433, 1640],
    47: [1434, 1435, 1436, 1437, 1438, 1641, 1643],
    48: [1432, 1642],
    # 楊古晨
    50: [1418, 1419, 1420, 1423, 1635],
    51: [1424, 1425, 1427, 1426, 1636, 1638],
    52: [1421, 1422, 1637],
    # 殷染幽
    54: [1396, 1397, 1398, 1400, 1625],
    55: [1401, 1403, 1404, 1405, 1626, 1628],
    56: [1399, 1402, 1627],

    # ── Non-sword characters (new) ──
    # 青兒
    6:  [1517, 1518, 1522, 1524, 1680],
    7:  [1525, 1526, 1519, 1520, 1681, 1683],
    8:  [1521, 1523, 1682],
    # 湮菲花
    10: [1363, 1364, 1367, 1368, 1610],
    11: [1371, 1372, 1365, 1366, 1611, 1613],
    12: [1369, 1370, 1612],
    # 闕崇陽
    14: [1374, 1375, 1376, 1378, 1615],
    15: [1379, 1380, 1381, 1382, 1383, 1616, 1618],
    16: [1377, 1617],
    # 絲塔娜
    18: [1385, 1386, 1387, 1389, 1620],
    19: [1390, 1392, 1393, 1394, 1621, 1623],
    20: [1388, 1391, 1622],
    # 沅花
    26: [1484, 1485, 1486, 1487, 1665],
    27: [1488, 1491, 1492, 1493, 1666, 1668],
    28: [1489, 1490, 1667],
    # 白沫檸
    34: [1506, 1507, 1508, 1510, 1675],
    35: [1512, 1513, 1514, 1515, 1676, 1678],
    36: [1509, 1511, 1677],
    # 珞堇
    38: [1528, 1529, 1530, 1533, 1685, 1719],
    39: [1534, 1535, 1536, 1537, 1686, 1688],
    40: [1531, 1532, 1687],
    # 墨汐若
    58: [1473, 1474, 1475, 1477, 1660],
    59: [1480, 1481, 1482, 1476, 1661, 1663],
    60: [1478, 1479, 1662],
    # 聶思泠
    62: [1451, 1452, 1453, 1455, 1650],
    63: [1457, 1458, 1459, 1460, 1651, 1653],
    64: [1454, 1456, 1652],
    # 無名丐
    66: [1440, 1441, 1442, 1444, 1645],
    67: [1447, 1448, 1449, 1445, 1646, 1648],
    68: [1443, 1446, 1647],
    # 郭霆黃
    70: [1462, 1463, 1464, 1466, 1655],
    71: [1467, 1468, 1469, 1471, 1656, 1658],
    72: [1465, 1470, 1657],
    # 藍靜冥
    74: [1407, 1408, 1409, 1410, 1630],
    75: [1411, 1413, 1414, 1415, 1416, 1631, 1633],
    76: [1412, 1632],
    # 黃凱竹
    78: [1583, 1584, 1585, 1587, 1710],
    79: [1588, 1590, 1591, 1592, 1711, 1713],
    80: [1586, 1589, 1712],
    # 劉靜靜
    82: [1594, 1595, 1596, 1598, 1715],
    83: [1599, 1601, 1602, 1603, 1716, 1718],
    84: [1597, 1600, 1717],
    # 七霜
    86: [1550, 1551, 1555, 1557, 1695],
    87: [1552, 1553, 1554, 1556, 1696],
    88: [1558, 1559, 1697, 1698],
    # 莫縈懷
    90: [1572, 1573, 1574, 1576, 1705],
    91: [1577, 1579, 1580, 1581, 1706, 1708],
    92: [1575, 1578, 1707],
}

# Sword class IDs
SWORD_CLASS_IDS = [2, 3, 4, 22, 23, 24, 30, 31, 32, 42, 43, 44,
                   46, 47, 48, 50, 51, 52, 54, 55, 56]

# Non-sword class IDs
NONSWORD_CLASS_IDS = [6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20,
                      26, 27, 28, 34, 35, 36, 38, 39, 40,
                      58, 59, 60, 62, 63, 64, 66, 67, 68,
                      70, 71, 72, 74, 75, 76, 78, 79, 80,
                      82, 83, 84, 86, 87, 88, 90, 91, 92]

# ═══════════════════════════════════════════════════════════════════════════════
# Tier Classification
# ═══════════════════════════════════════════════════════════════════════════════

TIER_COSTS = {
    "入門": {"ap": 10,  "sp": 0,  "frag": 1},
    "初階": {"ap": 20,  "sp": 3,  "frag": 2},
    "中階": {"ap": 35,  "sp": 5,  "frag": 3},
    "進階": {"ap": 55,  "sp": 12, "frag": 5},
    "高階": {"ap": 80,  "sp": 20, "frag": 8},
    "絕學": {"ap": 120, "sp": 35, "frag": 12},
}


def get_tier(mp_cost: int, tp_cost: int) -> str:
    if tp_cost == 100:
        return "絕學"
    if mp_cost <= 8:
        return "入門"
    if mp_cost <= 14:
        return "初階"
    if mp_cost <= 18:
        return "中階"
    if mp_cost <= 28:
        return "進階"
    return "高階"


# ═══════════════════════════════════════════════════════════════════════════════
# Enemy AP/SP Tiers
# ═══════════════════════════════════════════════════════════════════════════════

def get_enemy_rewards(exp: int):
    """Return (ap, sp) tuple based on EXP, or None if exp <= 0."""
    if exp <= 0:
        return None
    if exp <= 50:
        return (3, 0)
    if exp <= 100:
        return (5, 1)
    if exp <= 200:
        return (8, 1)
    if exp <= 400:
        return (12, 2)
    if exp <= 700:
        return (18, 3)
    if exp <= 1200:
        return (25, 5)
    if exp <= 1500:
        return (40, 8)
    return (60, 15)


# ═══════════════════════════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════════════════════════

def load_json(filename: str) -> list:
    path = BASE / "data" / filename
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(filename: str, data: list):
    """Write JSON in RPG Maker MZ format: one element per line, compact."""
    path = BASE / "data" / filename
    lines = ["["]
    for i, item in enumerate(data):
        suffix = "," if i < len(data) - 1 else ""
        lines.append(json.dumps(item, ensure_ascii=False, separators=(',', ':')) + suffix)
    lines.append("]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_to_note(note: str, tags: list[str]) -> str:
    """Append tags to a note field, skipping any that already exist."""
    for tag in tags:
        if tag not in note:
            if note and not note.endswith('\n'):
                note += '\n'
            note += tag + '\n'
    return note


# ═══════════════════════════════════════════════════════════════════════════════
# A: Patch plugins.js — AP/SP display names & gain formulas
# ═══════════════════════════════════════════════════════════════════════════════

def patch_plugins():
    path = BASE / "js" / "plugins.js"
    text = path.read_text(encoding="utf-8")

    replacements = [
        ('\\"AbbrText:str\\":\\"能力\\"', '\\"AbbrText:str\\":\\"修為\\"'),
        ('\\"AbbrText:str\\":\\"經脈\\"', '\\"AbbrText:str\\":\\"悟性\\"'),
        ('\\"PerAction:str\\":\\"10 + Math.randomInt(5)\\"', '\\"PerAction:str\\":\\"0\\"'),
        ('\\"PerEnemy:str\\":\\"50 + Math.randomInt(10)\\"', '\\"PerEnemy:str\\":\\"0\\"'),
    ]

    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
            print(f"  Replaced: ...{old[20:]}...")
        else:
            print(f"  SKIP (already applied): ...{old[20:]}...")

    path.write_text(text, encoding="utf-8")
    print("  => plugins.js patched")


# ═══════════════════════════════════════════════════════════════════════════════
# B: Patch Items.json — create 25 manuscript fragments
# ═══════════════════════════════════════════════════════════════════════════════

def patch_items():
    items = load_json("Items.json")

    for item_id, info in FRAGMENT_ITEMS.items():
        item = items[item_id]
        item["name"] = info["name"]
        item["description"] = info["desc"]
        item["iconIndex"] = FRAGMENT_ICON
        item["itypeId"] = 1
        item["consumable"] = False
        item["occasion"] = 3
        item["scope"] = 0
        item["price"] = 0
        item["note"] = ""
        print(f"  Item {item_id}: {info['name']}")

    save_json("Items.json", items)
    print(f"  => Items.json — {len(FRAGMENT_ITEMS)} fragments created")


# ═══════════════════════════════════════════════════════════════════════════════
# C: Patch Classes.json — add <Learn Skills> tags to 69 battle classes
# ═══════════════════════════════════════════════════════════════════════════════

def _class_to_weapon_blocks(class_id: int) -> list[str]:
    """Return weapon block Learn Skills tags for a class."""
    for _, (weapons, class_ids) in CHAR_WEAPONS.items():
        if class_id in class_ids:
            tags = []
            for weapon in weapons:
                block = WEAPON_BLOCKS[weapon]
                tags.append(f"<Learn Skills: {block[0]} to {block[-1]}>")
            return tags
    return []


def patch_classes():
    classes = load_json("Classes.json")
    count_sword = 0
    count_nonsword = 0

    # ── Non-sword classes: personal + weapon + 輕功 + 六藝 ──
    for class_id in NONSWORD_CLASS_IDS:
        cls = classes[class_id]
        skill_ids = CLASS_LEARN_SKILLS.get(class_id, [])
        if not skill_ids:
            print(f"  WARN: Class {class_id} ({cls['name']}) has no personal skills")
            continue

        skill_list = ", ".join(str(s) for s in skill_ids)
        tags = [f"<Learn Skills: {skill_list}>"]

        # Weapon blocks
        tags.extend(_class_to_weapon_blocks(class_id))

        cls["note"] = append_to_note(cls["note"], tags)
        count_nonsword += 1
        print(f"  Class {class_id:>2} ({cls['name']}): +personal +weapon")

    # ── Sword classes: personal + common + elemental (existing) + 輕功 + 六藝 ──
    for class_id in SWORD_CLASS_IDS:
        cls = classes[class_id]
        tags = []

        # Personal + common sword skills (only for classes in CLASS_LEARN_SKILLS)
        if class_id in CLASS_LEARN_SKILLS:
            skill_ids = CLASS_LEARN_SKILLS[class_id]
            skill_list = ", ".join(str(s) for s in skill_ids)
            tags.append(f"<Learn Skills: {skill_list}>")
            tags.append("<Learn Skills: 1002 to 1016>")

        cls["note"] = append_to_note(cls["note"], tags)
        count_sword += 1
        print(f"  Class {class_id:>2} ({cls['name']}): "
              + ("+personal +common" if class_id in CLASS_LEARN_SKILLS else "elemental only"))

    # ── Elemental blocks for sword characters ──
    for char_name, (elements, class_ids) in CHAR_ELEMENTS.items():
        for cid in class_ids:
            cls = classes[cid]
            tags = []
            for elem in elements:
                block_ids = ELEM_BLOCKS[elem]
                skill_list = ", ".join(str(s) for s in block_ids)
                tags.append(f"<Learn Skills: {skill_list}>")
            cls["note"] = append_to_note(cls["note"], tags)
            print(f"  Class {cid:>2} ({cls['name']}): +{', '.join(elements)}")

    save_json("Classes.json", classes)
    print(f"  => Classes.json — {count_nonsword} non-sword + {count_sword} sword classes patched")


# ═══════════════════════════════════════════════════════════════════════════════
# D: Patch Skills.json — add Learn Cost/Require tags
# ═══════════════════════════════════════════════════════════════════════════════

def patch_skills():
    skills = load_json("Skills.json")

    # Build skill → (fragment_item_id, predecessor_skill_id) mapping
    skill_config: dict[int, tuple[int, int | None]] = {}

    # ── Personal skills from ALL containers ──
    for container_id, chain in CONTAINERS.items():
        frag_id = CONTAINER_TO_FRAGMENT[container_id]
        for idx, skill_id in enumerate(chain):
            predecessor = chain[idx - 1] if idx > 0 else None
            skill_config[skill_id] = (frag_id, predecessor)

    # ── Common sword skills (1002-1016, fragment 1001) ──
    for idx, skill_id in enumerate(COMMON_SWORD_SKILLS):
        predecessor = COMMON_SWORD_SKILLS[idx - 1] if idx > 0 else None
        skill_config[skill_id] = (1001, predecessor)

    # ── Elemental block skills (fragment 1001) ──
    all_elem_ids: set[int] = set()
    for elements, _ in CHAR_ELEMENTS.values():
        for elem in elements:
            all_elem_ids.update(ELEM_BLOCKS[elem])
    for elem_name, block_ids in ELEM_BLOCKS.items():
        if not any(sid in all_elem_ids for sid in block_ids):
            continue
        for idx, skill_id in enumerate(block_ids):
            predecessor = block_ids[idx - 1] if idx > 0 else None
            if skill_id not in skill_config:
                skill_config[skill_id] = (1001, predecessor)

    # ── Weapon block skills (fragment 1009) ──
    # Only tag weapon blocks that are actually used by non-sword characters
    used_weapons: set[str] = set()
    for _, (weapons, _) in CHAR_WEAPONS.items():
        used_weapons.update(weapons)
    for weapon_name in used_weapons:
        block_ids = WEAPON_BLOCKS[weapon_name]
        for idx, skill_id in enumerate(block_ids):
            predecessor = block_ids[idx - 1] if idx > 0 else None
            if skill_id not in skill_config:
                skill_config[skill_id] = (1009, predecessor)

    # ── Apply tags ──
    count = 0
    tier_summary: dict[str, int] = {}

    for skill_id in sorted(skill_config):
        frag_id, predecessor = skill_config[skill_id]
        skill = skills[skill_id]
        if skill is None:
            print(f"  WARN: Skill {skill_id} is null, skipping")
            continue

        tier = get_tier(skill["mpCost"], skill["tpCost"])
        costs = TIER_COSTS[tier]

        tags = [f"<Learn AP Cost: {costs['ap']}>"]
        if costs["sp"] > 0:
            tags.append(f"<Learn SP Cost: {costs['sp']}>")
        tags.append(f"<Learn Item {frag_id} Cost: {costs['frag']}>")
        if predecessor is not None:
            tags.append(f"<Learn Require Skill: {predecessor}>")

        skill["note"] = append_to_note(skill["note"], tags)
        count += 1
        tier_summary[tier] = tier_summary.get(tier, 0) + 1

    save_json("Skills.json", skills)
    print(f"  => Skills.json — {count} skills patched")
    for tier, n in sorted(tier_summary.items(), key=lambda x: list(TIER_COSTS).index(x[0])):
        print(f"     {tier}: {n}")


# ═══════════════════════════════════════════════════════════════════════════════
# E: Patch Enemies.json — add AP/SP rewards based on EXP tiers
# ═══════════════════════════════════════════════════════════════════════════════

def patch_enemies():
    enemies = load_json("Enemies.json")
    count = 0

    for i in range(1, len(enemies)):
        enemy = enemies[i]
        if enemy is None:
            continue
        name = enemy.get("name", "")
        if not name or name.startswith("----") or name.startswith("--BOSS--"):
            continue

        exp = enemy.get("exp", 0)
        rewards = get_enemy_rewards(exp)
        if rewards is None:
            continue

        ap, sp = rewards
        tags = [f"<Enemy AP: {ap}>"]
        if sp > 0:
            tags.append(f"<Enemy SP: {sp}>")

        enemy["note"] = append_to_note(enemy["note"], tags)
        count += 1

    save_json("Enemies.json", enemies)
    print(f"  => Enemies.json — {count} enemies patched")


# ═══════════════════════════════════════════════════════════════════════════════
# F: Verification
# ═══════════════════════════════════════════════════════════════════════════════

def verify():
    """Verify all 69 battle classes have Learn Skills and referenced skills have AP costs."""
    classes = load_json("Classes.json")
    skills = load_json("Skills.json")
    items = load_json("Items.json")

    all_class_ids = SWORD_CLASS_IDS + NONSWORD_CLASS_IDS
    errors = []

    # Check classes
    classes_with_learn = 0
    for cid in all_class_ids:
        cls = classes[cid]
        note = cls.get("note", "")
        if "<Learn Skills:" not in note:
            errors.append(f"Class {cid} ({cls['name']}) missing <Learn Skills> tag")
        else:
            classes_with_learn += 1

    # Check skills referenced by classes have AP cost
    import re
    skills_in_classes: set[int] = set()
    for cid in all_class_ids:
        note = classes[cid].get("note", "")
        # Parse "X to Y" ranges
        for m in re.finditer(r'<Learn Skills:\s*(\d+)\s+to\s+(\d+)\s*>', note):
            start, end = int(m.group(1)), int(m.group(2))
            skills_in_classes.update(range(start, end + 1))
        # Parse comma-separated lists
        for m in re.finditer(r'<Learn Skills:\s*([\d,\s]+)>', note):
            text = m.group(1)
            if 'to' not in text:
                for sid_str in text.split(','):
                    sid_str = sid_str.strip()
                    if sid_str.isdigit():
                        skills_in_classes.add(int(sid_str))

    skills_without_ap = 0
    for sid in sorted(skills_in_classes):
        if sid < len(skills) and skills[sid] is not None:
            note = skills[sid].get("note", "")
            if "<Learn AP Cost:" not in note:
                skills_without_ap += 1
                if skills_without_ap <= 10:
                    errors.append(f"Skill {sid} ({skills[sid]['name']}) referenced but missing <Learn AP Cost>")

    if skills_without_ap > 10:
        errors.append(f"  ... and {skills_without_ap - 10} more skills missing AP cost")

    # Check fragment items
    fragments_ok = 0
    for item_id in range(1001, 1026):
        item = items[item_id]
        if item.get("name") and item.get("iconIndex") == FRAGMENT_ICON:
            fragments_ok += 1
        else:
            errors.append(f"Item {item_id} not properly configured as fragment")

    # Report
    print(f"  Classes with Learn Skills: {classes_with_learn}/{len(all_class_ids)}")
    print(f"  Skills referenced by classes: {len(skills_in_classes)}")
    print(f"  Skills missing AP cost: {skills_without_ap}")
    print(f"  Fragment items OK: {fragments_ok}/25")

    if errors:
        print(f"\n  ERRORS ({len(errors)}):")
        for e in errors:
            print(f"    {e}")
        return False
    else:
        print("  => All verifications passed!")
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  SkillLearnSystem Patch — 全角色學習系統")
    print("=" * 60)
    print(f"  Base: {BASE}")
    print()

    # Verify base path
    if not (BASE / "data").is_dir():
        print(f"ERROR: Data directory not found: {BASE / 'data'}")
        sys.exit(1)

    print("[A] Patching plugins.js (AP/SP names)...")
    patch_plugins()
    print()

    print(f"[B] Patching Items.json ({len(FRAGMENT_ITEMS)} fragments)...")
    patch_items()
    print()

    print("[C] Patching Classes.json (69 classes)...")
    patch_classes()
    print()

    print("[D] Patching Skills.json (all learnable skills)...")
    patch_skills()
    print()

    print("[E] Patching Enemies.json (AP/SP rewards)...")
    patch_enemies()
    print()

    print("[F] Verifying...")
    ok = verify()
    print()

    print("=" * 60)
    if ok:
        print("  All patches applied and verified successfully!")
    else:
        print("  Patches applied with WARNINGS — check errors above")
    print("=" * 60)


if __name__ == "__main__":
    main()
