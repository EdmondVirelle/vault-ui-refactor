#!/usr/bin/env python3
"""
patch_defensive_skills.py

Patches Skills.json to add 3 unique defensive skills per character (23 chars),
starting from ID 2000. Each character gets a separator + 3 skills = 4 entries.

Total: 23 separators + 69 skills = 92 entries (IDs 2000-2091)

Usage:
    python scripts/patch_defensive_skills.py
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"

# ═══════════════════════════════════════════════════════════════════════════════
# State IDs (from States.json — existing states)
# ═══════════════════════════════════════════════════════════════════════════════

ST_HP_REGEN      = 15   # 聚氣 — HP 4.2%/回合，4回合
ST_MP_REGEN      = 16   # 歸元 — MP 4.2%/回合，4回合
ST_EVASION       = 17   # 閃避 — +30% 閃避，2回合
ST_TAUNT         = 21   # 嘲諷 — 全體嘲諷，2回合
ST_COUNTER       = 22   # 反擊 — +50% 反擊，2回合
ST_LIFESTEAL     = 23   # 飲血 — 25% 吸血，3回合
ST_ANTI_STEAL    = 24   # 飲血反制 — 反吸血，3回合
ST_REGEN_STRONG  = 26   # 針灸 — HP 15%/回合，3回合
ST_INVISIBLE     = 27   # 隱身 — 近乎無敵，2回合
ST_BARRIER       = 28   # 護盾 — 吸收 MDF*2 傷害，3回合
ST_DEF_MICRO     = 48   # 外防微幅上升 — DEF +10%
ST_DEF_MID       = 49   # 外防中幅上升 — DEF +25%
ST_DEF_MAJOR     = 50   # 外防大幅上升 — DEF +55%
ST_MDF_MICRO     = 51   # 內防微幅上升 — MDF +10%
ST_MDF_MID       = 52   # 內防中幅上升 — MDF +25%
ST_MDF_MAJOR     = 53   # 內防大幅上升 — MDF +55%

# Icon indices (matching existing states)
ICON_BARRIER  = 3129
ICON_DEF      = 3117
ICON_EVASION  = 3127
ICON_COUNTER  = 3148
ICON_TAUNT    = 3147
ICON_REGEN    = 3130
ICON_MP_REGEN = 3121
ICON_INVIS    = 3129
ICON_LIFESTL  = 3116
ICON_TEAM     = 3344
ICON_HP_REGEN = 3120

# ═══════════════════════════════════════════════════════════════════════════════
# Skill Definitions — 23 characters × (1 separator + 3 skills)
# ═══════════════════════════════════════════════════════════════════════════════

# Helper: add_state effect
def eff(state_id):
    return {"code": 21, "dataId": state_id, "value1": 1.0, "value2": 0}

# Color tags for notes
C_BLUE   = "<Color: #4FC3F7>"    # Self defense
C_GREEN  = "<Color: #81C784>"    # Team buff
C_GOLD   = "<Color: #FFD54F>"    # Barrier
C_PURPLE = "<Color: #CE93D8>"    # Evasion/stealth
C_CORAL  = "<Color: #FF8A65>"    # Counter/aggro

# Scope constants
SELF = 11
ALLY = 7
TEAM = 8

SKILLS = [
    # ── 東方啟 ──────────────────────────────────────────────────────────────
    {"id": 2000, "sep": "東方啟・護身武學"},
    {"id": 2001, "name": "月華流轉", "icon": ICON_EVASION, "mp": 18, "scope": SELF, "cd": 3,
     "color": C_PURPLE, "effects": [eff(ST_EVASION), eff(ST_DEF_MICRO)],
     "desc": "月光下身影飄渺，\\n閃避率提升30%、外防微幅上升。"},
    {"id": 2002, "name": "劍意凝盾", "icon": ICON_BARRIER, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "以劍意凝聚月華護盾，\\n吸收一定量傷害。"},
    {"id": 2003, "name": "明月照人", "icon": ICON_TEAM, "mp": 25, "scope": TEAM, "cd": 4,
     "color": C_GREEN, "effects": [eff(ST_MDF_MID)],
     "desc": "月光灑落全場，\\n全體同伴內防中幅上升。"},

    # ── 青兒 ────────────────────────────────────────────────────────────────
    {"id": 2004, "sep": "青兒・護身武學"},
    {"id": 2005, "name": "天籟回春", "icon": ICON_HP_REGEN, "mp": 22, "scope": TEAM, "cd": 4,
     "color": C_GREEN, "effects": [eff(ST_HP_REGEN)],
     "desc": "琴音如泉，撫慰傷痛。\\n全體同伴每回合回復氣血。"},
    {"id": 2006, "name": "琴音結界", "icon": ICON_BARRIER, "mp": 20, "scope": SELF, "cd": 3,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "音波層疊凝為壁障，\\n吸收一定量傷害。"},
    {"id": 2007, "name": "霞光護陣", "icon": ICON_TEAM, "mp": 20, "scope": TEAM, "cd": 3,
     "color": C_GREEN, "effects": [eff(ST_DEF_MICRO)],
     "desc": "霞光籠罩戰場，\\n全體同伴外防微幅上升。"},

    # ── 湮菲花 ──────────────────────────────────────────────────────────────
    {"id": 2008, "sep": "湮菲花・護身武學"},
    {"id": 2009, "name": "蘭心續脈", "icon": ICON_REGEN, "mp": 18, "scope": ALLY, "cd": 3,
     "color": C_GREEN, "effects": [eff(ST_REGEN_STRONG)],
     "desc": "點穴通經，令氣血奔流。\\n單體同伴每回合大幅回復氣血。"},
    {"id": 2010, "name": "百花護心", "icon": ICON_TEAM, "mp": 22, "scope": TEAM, "cd": 3,
     "color": C_GREEN, "effects": [eff(ST_MDF_MICRO)],
     "desc": "花瓣如屏，護住心脈。\\n全體同伴內防微幅上升。"},
    {"id": 2011, "name": "木靈堅甲", "icon": ICON_DEF, "mp": 20, "scope": SELF, "cd": 4,
     "color": C_BLUE, "effects": [eff(ST_DEF_MAJOR)],
     "desc": "木靈真氣凝聚體表，\\n自身外防大幅上升。"},

    # ── 闕崇陽 ──────────────────────────────────────────────────────────────
    {"id": 2012, "sep": "闕崇陽・護身武學"},
    {"id": 2013, "name": "疾風閃身", "icon": ICON_EVASION, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_PURPLE, "effects": [eff(ST_EVASION)],
     "desc": "風行疾步，身影如電。\\n閃避率大幅提升。"},
    {"id": 2014, "name": "雷霆反擊", "icon": ICON_COUNTER, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_CORAL, "effects": [eff(ST_COUNTER)],
     "desc": "以雷電蓄勢，觸之即發。\\n反擊率大幅提升。"},
    {"id": 2015, "name": "風壁禦襲", "icon": ICON_BARRIER, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "旋風凝聚成壁，擋住來襲。\\n吸收一定量傷害。"},

    # ── 絲塔娜 ──────────────────────────────────────────────────────────────
    {"id": 2016, "sep": "絲塔娜・護身武學"},
    {"id": 2017, "name": "金剛守勢", "icon": ICON_DEF, "mp": 20, "scope": SELF, "cd": 4,
     "color": C_BLUE, "effects": [eff(ST_DEF_MAJOR)],
     "desc": "棍法鐵壁，固若金湯。\\n自身外防大幅上升。"},
    {"id": 2018, "name": "黃沙壁壘", "icon": ICON_TEAM, "mp": 35, "scope": TEAM, "cd": 5,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "漫天黃沙凝為堅壁，\\n全體同伴獲得護盾。"},
    {"id": 2019, "name": "沙甲鑄身", "icon": ICON_DEF, "mp": 25, "scope": SELF, "cd": 4,
     "color": C_BLUE, "effects": [eff(ST_DEF_MID), eff(ST_MDF_MID)],
     "desc": "細沙覆甲，內外兼護。\\n自身外防、內防中幅上升。"},

    # ── 瑤琴劍 ──────────────────────────────────────────────────────────────
    {"id": 2020, "sep": "瑤琴劍・護身武學"},
    {"id": 2021, "name": "九霄劍幕", "icon": ICON_BARRIER, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "劍氣如幕，萬物莫侵。\\n吸收一定量傷害。"},
    {"id": 2022, "name": "碧雲內護", "icon": ICON_TEAM, "mp": 22, "scope": TEAM, "cd": 3,
     "color": C_GREEN, "effects": [eff(ST_MDF_MICRO)],
     "desc": "碧雲真氣擴散護場。\\n全體同伴內防微幅上升。"},
    {"id": 2023, "name": "御風身法", "icon": ICON_EVASION, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_PURPLE, "effects": [eff(ST_EVASION)],
     "desc": "乘風而動，飄然若仙。\\n閃避率大幅提升。"},

    # ── 沅花 ────────────────────────────────────────────────────────────────
    {"id": 2024, "sep": "沅花・護身武學"},
    {"id": 2025, "name": "墨海結界", "icon": ICON_TEAM, "mp": 28, "scope": TEAM, "cd": 4,
     "color": C_GREEN, "effects": [eff(ST_MDF_MID)],
     "desc": "墨意流轉，織成內護結界。\\n全體同伴內防中幅上升。"},
    {"id": 2026, "name": "遁入畫中", "icon": ICON_INVIS, "mp": 25, "scope": SELF, "cd": 5,
     "color": C_PURPLE, "effects": [eff(ST_INVISIBLE)],
     "desc": "身形融入筆墨之間，\\n近乎完全隱匿存在。"},
    {"id": 2027, "name": "筆意凝盾", "icon": ICON_BARRIER, "mp": 20, "scope": SELF, "cd": 3,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "筆鋒一揮，墨氣凝盾。\\n吸收一定量傷害。"},

    # ── 談笑 ────────────────────────────────────────────────────────────────
    {"id": 2028, "sep": "談笑・護身武學"},
    {"id": 2029, "name": "凝霜守勢", "icon": ICON_DEF, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_BLUE, "effects": [eff(ST_DEF_MID)],
     "desc": "寒霜凝甲，冷意沁骨。\\n自身外防中幅上升。"},
    {"id": 2030, "name": "冰壁千重", "icon": ICON_BARRIER, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "凝冰為壁，千重不破。\\n吸收一定量傷害。"},
    {"id": 2031, "name": "霜寒凌身", "icon": ICON_COUNTER, "mp": 20, "scope": SELF, "cd": 3,
     "color": C_CORAL, "effects": [eff(ST_COUNTER), eff(ST_DEF_MICRO)],
     "desc": "寒氣纏身，碰者自傷。\\n反擊率提升、外防微幅上升。"},

    # ── 白沫檸 ──────────────────────────────────────────────────────────────
    {"id": 2032, "sep": "白沫檸・護身武學"},
    {"id": 2033, "name": "水流護體", "icon": ICON_HP_REGEN, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_BLUE, "effects": [eff(ST_HP_REGEN)],
     "desc": "水流環身，溫養傷口。\\n每回合回復少量氣血。"},
    {"id": 2034, "name": "怒海築牆", "icon": ICON_DEF, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_BLUE, "effects": [eff(ST_DEF_MAJOR)],
     "desc": "怒濤化為屏障，堅不可摧。\\n自身外防大幅上升。"},
    {"id": 2035, "name": "水遁閃身", "icon": ICON_EVASION, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_PURPLE, "effects": [eff(ST_EVASION)],
     "desc": "化身流水，無從捉摸。\\n閃避率大幅提升。"},

    # ── 珞堇 ────────────────────────────────────────────────────────────────
    {"id": 2036, "sep": "珞堇・護身武學"},
    {"id": 2037, "name": "古韻歸元", "icon": ICON_MP_REGEN, "mp": 22, "scope": TEAM, "cd": 4,
     "color": C_GREEN, "effects": [eff(ST_MP_REGEN)],
     "desc": "琴韻悠長，引氣歸元。\\n全體同伴每回合回復內力。"},
    {"id": 2038, "name": "弦音護陣", "icon": ICON_TEAM, "mp": 20, "scope": TEAM, "cd": 3,
     "color": C_GREEN, "effects": [eff(ST_DEF_MICRO)],
     "desc": "弦音共振，凝聚護場。\\n全體同伴外防微幅上升。"},
    {"id": 2039, "name": "和弦結壁", "icon": ICON_BARRIER, "mp": 20, "scope": SELF, "cd": 3,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "和弦交織成壁，音障護身。\\n吸收一定量傷害。"},

    # ── 龍玉 ────────────────────────────────────────────────────────────────
    {"id": 2040, "sep": "龍玉・護身武學"},
    {"id": 2041, "name": "龍鱗護甲", "icon": ICON_DEF, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_BLUE, "effects": [eff(ST_DEF_MAJOR)],
     "desc": "龍鱗顯現，刀槍不入。\\n自身外防大幅上升。"},
    {"id": 2042, "name": "玄冰屏障", "icon": ICON_BARRIER, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "玄冰凝聚成屏，寒意拒敵。\\n吸收一定量傷害。"},
    {"id": 2043, "name": "龍氣內護", "icon": ICON_DEF, "mp": 18, "scope": SELF, "cd": 3,
     "color": C_BLUE, "effects": [eff(ST_MDF_MID)],
     "desc": "龍氣貫通經脈，護住內息。\\n自身內防中幅上升。"},

    # ── 司徒長生 ────────────────────────────────────────────────────────────
    {"id": 2044, "sep": "司徒長生・護身武學"},
    {"id": 2045, "name": "天機幻影", "icon": ICON_EVASION, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_PURPLE, "effects": [eff(ST_EVASION)],
     "desc": "身化幻影，虛實莫辨。\\n閃避率大幅提升。"},
    {"id": 2046, "name": "虛縷護陣", "icon": ICON_TEAM, "mp": 35, "scope": TEAM, "cd": 5,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "虛縷結界擴展至全場。\\n全體同伴獲得護盾。"},
    {"id": 2047, "name": "天機護心", "icon": ICON_DEF, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_BLUE, "effects": [eff(ST_MDF_MAJOR)],
     "desc": "天機心法運轉至極，\\n自身內防大幅上升。"},

    # ── 楊古晨 ──────────────────────────────────────────────────────────────
    {"id": 2048, "sep": "楊古晨・護身武學"},
    {"id": 2049, "name": "醉步迷蹤", "icon": ICON_EVASION, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_PURPLE, "effects": [eff(ST_EVASION), eff(ST_COUNTER)],
     "desc": "醉態飄搖，卻暗藏殺機。\\n閃避率與反擊率同時提升。"},
    {"id": 2050, "name": "酒氣凝甲", "icon": ICON_DEF, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_BLUE, "effects": [eff(ST_DEF_MID)],
     "desc": "酒氣蒸騰，凝於體表成甲。\\n自身外防中幅上升。"},
    {"id": 2051, "name": "雷鎧護體", "icon": ICON_BARRIER, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "雷光交織成鎧，電芒護身。\\n吸收一定量傷害。"},

    # ── 殷染幽 ──────────────────────────────────────────────────────────────
    {"id": 2052, "sep": "殷染幽・護身武學"},
    {"id": 2053, "name": "血霧障目", "icon": ICON_EVASION, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_PURPLE, "effects": [eff(ST_EVASION)],
     "desc": "血霧瀰漫，遮蔽身形。\\n閃避率大幅提升。"},
    {"id": 2054, "name": "血海歸源", "icon": ICON_LIFESTL, "mp": 20, "scope": SELF, "cd": 4,
     "color": C_CORAL, "effects": [eff(ST_LIFESTEAL)],
     "desc": "血海之力灌注兵刃。\\n攻擊時吸收對方氣血。"},
    {"id": 2055, "name": "血刃反噬", "icon": ICON_COUNTER, "mp": 18, "scope": SELF, "cd": 3,
     "color": C_CORAL, "effects": [eff(ST_ANTI_STEAL), eff(ST_DEF_MICRO)],
     "desc": "血氣如毒，吸我者反受其害。\\n反制吸血、外防微幅上升。"},

    # ── 墨汐若 ──────────────────────────────────────────────────────────────
    {"id": 2056, "sep": "墨汐若・護身武學"},
    {"id": 2057, "name": "梅影護陣", "icon": ICON_TEAM, "mp": 20, "scope": TEAM, "cd": 3,
     "color": C_GREEN, "effects": [eff(ST_DEF_MICRO)],
     "desc": "鞭影如梅枝交錯，護住全場。\\n全體同伴外防微幅上升。"},
    {"id": 2058, "name": "梅花凝盾", "icon": ICON_BARRIER, "mp": 20, "scope": SELF, "cd": 3,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "梅花瓣瓣凝聚成盾。\\n吸收一定量傷害。"},
    {"id": 2059, "name": "暗香浮動", "icon": ICON_REGEN, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_BLUE, "effects": [eff(ST_MDF_MID), eff(ST_HP_REGEN)],
     "desc": "暗香縈繞，靜養傷痛。\\n內防中幅上升、每回合回復氣血。"},

    # ── 聶思泠 ──────────────────────────────────────────────────────────────
    {"id": 2060, "sep": "聶思泠・護身武學"},
    {"id": 2061, "name": "鬼影匿蹤", "icon": ICON_INVIS, "mp": 25, "scope": SELF, "cd": 5,
     "color": C_PURPLE, "effects": [eff(ST_INVISIBLE)],
     "desc": "身影消散，無人可尋。\\n進入近乎完全隱匿狀態。"},
    {"id": 2062, "name": "百變閃身", "icon": ICON_EVASION, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_PURPLE, "effects": [eff(ST_EVASION)],
     "desc": "百變身法，招招閃避。\\n閃避率大幅提升。"},
    {"id": 2063, "name": "機靈護體", "icon": ICON_COUNTER, "mp": 18, "scope": SELF, "cd": 3,
     "color": C_CORAL, "effects": [eff(ST_COUNTER), eff(ST_DEF_MICRO)],
     "desc": "看似大意，實則暗藏反擊。\\n反擊率提升、外防微幅上升。"},

    # ── 無名丐 ──────────────────────────────────────────────────────────────
    {"id": 2064, "sep": "無名丐・護身武學"},
    {"id": 2065, "name": "裝死遁法", "icon": ICON_INVIS, "mp": 22, "scope": SELF, "cd": 5,
     "color": C_PURPLE, "effects": [eff(ST_INVISIBLE)],
     "desc": "乞丐最強秘技——裝死。\\n敵人暫時失去目標。"},
    {"id": 2066, "name": "鐵棍橫擋", "icon": ICON_DEF, "mp": 20, "scope": SELF, "cd": 4,
     "color": C_BLUE, "effects": [eff(ST_DEF_MAJOR)],
     "desc": "橫棍當胸，硬扛萬鈞。\\n自身外防大幅上升。"},
    {"id": 2067, "name": "水遁護盾", "icon": ICON_BARRIER, "mp": 20, "scope": SELF, "cd": 3,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "水氣凝結成盾，擋在身前。\\n吸收一定量傷害。"},

    # ── 郭霆黃 ──────────────────────────────────────────────────────────────
    {"id": 2068, "sep": "郭霆黃・護身武學"},
    {"id": 2069, "name": "霸氣迫人", "icon": ICON_TAUNT, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_CORAL, "effects": [eff(ST_TAUNT), eff(ST_DEF_MID)],
     "desc": "霸氣外放，敵人只能盯著你。\\n嘲諷全體、外防中幅上升。"},
    {"id": 2070, "name": "藍鋼鑄壁", "icon": ICON_BARRIER, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "藍鋼之力凝為鐵壁。\\n吸收一定量傷害。"},
    {"id": 2071, "name": "刀壁反斬", "icon": ICON_COUNTER, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_CORAL, "effects": [eff(ST_COUNTER)],
     "desc": "以攻代守，刀鋒迎敵。\\n反擊率大幅提升。"},

    # ── 藍靜冥 ──────────────────────────────────────────────────────────────
    {"id": 2072, "sep": "藍靜冥・護身武學"},
    {"id": 2073, "name": "蠱甲凝毒", "icon": ICON_BARRIER, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "蠱蟲編織成甲，觸之即毒。\\n吸收一定量傷害。"},
    {"id": 2074, "name": "寒冰結甲", "icon": ICON_DEF, "mp": 20, "scope": SELF, "cd": 3,
     "color": C_BLUE, "effects": [eff(ST_DEF_MID), eff(ST_MDF_MICRO)],
     "desc": "冰甲覆體，內外皆固。\\n外防中幅上升、內防微幅上升。"},
    {"id": 2075, "name": "瘴氣迷障", "icon": ICON_TEAM, "mp": 28, "scope": TEAM, "cd": 5,
     "color": C_GREEN, "effects": [eff(ST_EVASION)],
     "desc": "毒霧擴散，敵人難以瞄準。\\n全體同伴閃避率提升。"},

    # ── 黃凱竹 ──────────────────────────────────────────────────────────────
    {"id": 2076, "sep": "黃凱竹・護身武學"},
    {"id": 2077, "name": "機關鐵盾", "icon": ICON_BARRIER, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "展開機關鐵盾，抵擋衝擊。\\n吸收一定量傷害。"},
    {"id": 2078, "name": "鐵甲強化", "icon": ICON_DEF, "mp": 20, "scope": SELF, "cd": 4,
     "color": C_BLUE, "effects": [eff(ST_DEF_MAJOR)],
     "desc": "加裝額外甲片，防禦倍增。\\n自身外防大幅上升。"},
    {"id": 2079, "name": "煙霧彈幕", "icon": ICON_TEAM, "mp": 28, "scope": TEAM, "cd": 5,
     "color": C_GREEN, "effects": [eff(ST_EVASION)],
     "desc": "拋出煙霧彈，遮蔽全場。\\n全體同伴閃避率提升。"},

    # ── 劉靜靜 ──────────────────────────────────────────────────────────────
    {"id": 2080, "sep": "劉靜靜・護身武學"},
    {"id": 2081, "name": "暗影匿殺", "icon": ICON_INVIS, "mp": 25, "scope": SELF, "cd": 5,
     "color": C_PURPLE, "effects": [eff(ST_INVISIBLE)],
     "desc": "沒入暗影之中，伺機而動。\\n進入近乎完全隱匿狀態。"},
    {"id": 2082, "name": "毒蕊反噬", "icon": ICON_COUNTER, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_CORAL, "effects": [eff(ST_COUNTER)],
     "desc": "毒刺暗藏，碰者中毒。\\n反擊率大幅提升。"},
    {"id": 2083, "name": "霜毒護體", "icon": ICON_DEF, "mp": 18, "scope": SELF, "cd": 3,
     "color": C_BLUE, "effects": [eff(ST_MDF_MID)],
     "desc": "霜毒之氣護住經脈。\\n自身內防中幅上升。"},

    # ── 七霜 ────────────────────────────────────────────────────────────────
    {"id": 2084, "sep": "七霜・護身武學"},
    {"id": 2085, "name": "回春養息", "icon": ICON_REGEN, "mp": 25, "scope": TEAM, "cd": 4,
     "color": C_GREEN, "effects": [eff(ST_REGEN_STRONG)],
     "desc": "醫者仁心，令氣血奔流不息。\\n全體同伴每回合大幅回復氣血。"},
    {"id": 2086, "name": "翡翠護盾", "icon": ICON_BARRIER, "mp": 20, "scope": SELF, "cd": 3,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "翡翠靈光凝為護盾。\\n吸收一定量傷害。"},
    {"id": 2087, "name": "銀針封穴", "icon": ICON_DEF, "mp": 18, "scope": SELF, "cd": 3,
     "color": C_BLUE, "effects": [eff(ST_DEF_MID), eff(ST_MDF_MICRO)],
     "desc": "以針封穴，強化經脈防禦。\\n外防中幅上升、內防微幅上升。"},

    # ── 莫縈懷 ──────────────────────────────────────────────────────────────
    {"id": 2088, "sep": "莫縈懷・護身武學"},
    {"id": 2089, "name": "風羽飄渺", "icon": ICON_EVASION, "mp": 15, "scope": SELF, "cd": 3,
     "color": C_PURPLE, "effects": [eff(ST_EVASION)],
     "desc": "羽衣飄動，身影如風。\\n閃避率大幅提升。"},
    {"id": 2090, "name": "音壁迴盪", "icon": ICON_BARRIER, "mp": 22, "scope": SELF, "cd": 4,
     "color": C_GOLD, "effects": [eff(ST_BARRIER)],
     "desc": "音波層疊迴盪，凝為壁障。\\n吸收一定量傷害。"},
    {"id": 2091, "name": "兩儀護天", "icon": ICON_TEAM, "mp": 28, "scope": TEAM, "cd": 4,
     "color": C_GREEN, "effects": [eff(ST_DEF_MICRO), eff(ST_MDF_MICRO)],
     "desc": "兩儀之力護佑全場。\\n全體同伴外防、內防微幅上升。"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# Build JSON entries
# ═══════════════════════════════════════════════════════════════════════════════

EMPTY_DAMAGE = {"type": 0, "formula": "0", "critical": False, "elementId": 0, "variance": 0}

def make_separator(sid: int, label: str) -> dict:
    return {
        "id": sid,
        "name": f"----{label}----",
        "iconIndex": 0,
        "description": "",
        "stypeId": 0,
        "scope": 0,
        "mpCost": 0,
        "tpCost": 0,
        "tpGain": 0,
        "hitType": 0,
        "occasion": 0,
        "speed": 0,
        "successRate": 100,
        "repeats": 1,
        "animationId": 0,
        "messageType": 1,
        "message1": "",
        "message2": "",
        "requiredWtypeId1": 0,
        "requiredWtypeId2": 0,
        "damage": EMPTY_DAMAGE.copy(),
        "effects": [],
        "note": "",
    }


def make_skill(entry: dict) -> dict:
    note_parts = [entry["color"]]
    note_parts.append(f"<Cooldown: {entry['cd']}>")
    note_parts.append("<Boost Turns>")
    note = "\n".join(note_parts)

    return {
        "id": entry["id"],
        "name": entry["name"],
        "iconIndex": entry["icon"],
        "description": entry["desc"],
        "stypeId": 0,
        "scope": entry["scope"],
        "mpCost": entry["mp"],
        "tpCost": 0,
        "tpGain": 5,
        "hitType": 0,
        "occasion": 1,
        "speed": 0,
        "successRate": 100,
        "repeats": 1,
        "animationId": 0,
        "messageType": 1,
        "message1": "",
        "message2": "",
        "requiredWtypeId1": 0,
        "requiredWtypeId2": 0,
        "damage": EMPTY_DAMAGE.copy(),
        "effects": entry["effects"],
        "note": note,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Patch
# ═══════════════════════════════════════════════════════════════════════════════

def save_json(path, data):
    lines = ["["]
    for i, item in enumerate(data):
        suffix = "," if i < len(data) - 1 else ""
        lines.append(json.dumps(item, ensure_ascii=False, separators=(',', ':')) + suffix)
    lines.append("]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    path = BASE / "Skills.json"
    skills = json.loads(path.read_text(encoding="utf-8"))

    # Extend array if needed
    max_id = max(s["id"] for s in SKILLS if "id" in s)
    while len(skills) <= max_id:
        skills.append(None)

    count_sep = 0
    count_skill = 0

    for entry in SKILLS:
        sid = entry["id"]
        if "sep" in entry:
            skills[sid] = make_separator(sid, entry["sep"])
            count_sep += 1
            print(f"  [{sid}] ----{entry['sep']}----")
        else:
            skills[sid] = make_skill(entry)
            count_skill += 1
            scope_label = {11: "自身", 7: "單體", 8: "全體"}[entry["scope"]]
            effects_str = " + ".join(
                f"State{e['dataId']}" for e in entry["effects"]
            )
            print(f"  [{sid}] {entry['name']} ({scope_label}, MP{entry['mp']}, CD{entry['cd']}) → {effects_str}")

    save_json(path, skills)
    print()
    print(f"  => {count_sep} separators + {count_skill} skills written (IDs 2000-{max_id})")
    print(f"  => Skills.json total entries: {len(skills)}")


if __name__ == "__main__":
    main()
