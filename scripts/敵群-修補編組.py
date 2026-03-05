#!/usr/bin/env python3
"""
Patch Troops.json: fill in enemy group compositions for all chapters.
Troops ID 1-2 reserved (empty/test), ID 3 already has boss fight.
We fill ID 4-25 with standard encounters + boss battles.
"""
import json
from pathlib import Path

TROOPS_PATH = Path(__file__).parent.parent / "Consilience" / "data" / "Troops.json"

# Screen positions for SV battle (RPG Maker MZ default positions)
# x: 600-1000 range, y: 500-900 range
POS = {
    "solo":    [(800, 712)],
    "duo":     [(700, 612), (900, 812)],
    "trio":    [(650, 562), (800, 712), (950, 862)],
    "quad":    [(600, 512), (733, 646), (866, 780), (1000, 912)],
    "boss_1":  [(800, 712)],
    "boss_2":  [(700, 612), (900, 812)],   # boss + 1 add
    "boss_3":  [(650, 562), (800, 712), (950, 862)],  # boss + 2 adds
}

def member(enemy_id, x, y, hidden=False):
    return {"enemyId": enemy_id, "x": x, "y": y, "hidden": hidden}

def empty_page():
    return {
        "conditions": {
            "actorHp": 50, "actorId": 1, "actorValid": False,
            "enemyHp": 50, "enemyIndex": 0, "enemyValid": False,
            "switchId": 1, "switchValid": False,
            "turnA": 0, "turnB": 0, "turnEnding": False, "turnValid": False
        },
        "list": [{"code": 0, "indent": 0, "parameters": []}],
        "span": 0
    }

def make_troop(tid, name, enemy_ids, layout="auto"):
    """Create a troop entry."""
    if layout == "auto":
        n = len(enemy_ids)
        if n == 1: layout = "solo"
        elif n == 2: layout = "duo"
        elif n == 3: layout = "trio"
        else: layout = "quad"

    positions = POS[layout]
    members = []
    for i, eid in enumerate(enemy_ids):
        pos = positions[i % len(positions)]
        members.append(member(eid, pos[0], pos[1]))

    return {
        "id": tid,
        "members": members,
        "name": name,
        "pages": [empty_page()]
    }


# ═══════════════════════════════════════════
# Troop Definitions per Chapter
# ═══════════════════════════════════════════
TROOP_DEFS = [
    # ── 序章：黃裳典籍 (Prologue) ──
    # ID 4-8
    (4,  "野狼x2",              [4, 4]),
    (5,  "毒蛇x2 野狼x1",       [5, 5, 4]),
    (6,  "山賊x2",              [6, 6]),
    (7,  "帝國巡邏兵x2 帝國弓手x1", [7, 7, 12]),
    (8,  "帝國哨兵隊長x1 帝國巡邏兵x2", [15, 7, 7]),
    (9,  "遺跡石偶x2",          [13, 13]),
    (10, "黃裳冤魂x2 遺跡石偶x1", [14, 14, 13]),
    (11, "遺跡守衛機關x1 遺跡石偶x2", [16, 13, 13]),
    (12, "【BOSS】武裝兵將領x1 帝國武民x2", [8, 2, 11]),
    (13, "【BOSS】書中判官",      [10]),

    # ── 第一章：劃月風雲 (Ch1) ──
    # ID 14-20
    (14, "劫道匪x3",            [18, 18, 18]),
    (15, "帝國密探x2",          [19, 19]),
    (16, "打手x2 暗殺者x1",     [20, 20, 22]),
    (17, "門派叛徒x2",          [21, 21]),
    (18, "帝國精銳兵x2 帝國騎士x1", [23, 23, 24]),
    (19, "劃月邪徒x1 門派叛徒x2", [25, 21, 21]),
    (20, "【BOSS】劃月邪徒",      [25]),

    # ── 第二章：西域來風 (Ch2) ──
    # ID 21-27
    (21, "沙漠毒蠍x2 毒蛇x1",   [27, 27, 5]),
    (22, "黃沙狼群x3",          [28, 28, 28]),
    (23, "帝國沙漠兵x2 帝國弓手x1", [29, 29, 12]),
    (24, "沙暴精x1 黃沙狼群x2",  [30, 28, 28]),
    (25, "西域商隊護衛x2",       [31, 31]),
    (26, "檮杌獸影x1 黑市殺手x1", [32, 33]),
    (27, "【BOSS】沙漠巨蟲x1 沙漠毒蠍x2", [34, 27, 27]),

    # ── 第三章：仙池寒劍 (Ch3) ──
    # ID 28-34
    (28, "仙池弟子x2",          [36, 36]),
    (29, "寒冰精x2 變異水獸x1",  [37, 37, 38]),
    (30, "受蠱弟子x2",          [39, 39]),
    (31, "冰霜巨熊x1 寒冰精x1", [40, 37]),
    (32, "窮奇幻象x1 受蠱弟子x2", [41, 39, 39]),
    (33, "仙池護法x1 仙池弟子x2", [42, 36, 36]),
    (34, "【BOSS】初代奇美拉",    [43]),

    # ── 第四章：逍遙雲霧 (Ch4) ──
    # ID 35-41
    (35, "帝國掘探隊x2 帝國工程兵x1", [45, 45, 48]),
    (36, "山中妖靈x2",          [46, 46]),
    (37, "靈脈獸x1 山中妖靈x1", [47, 46]),
    (38, "鬼面猿x2",            [49, 49]),
    (39, "巨型蜈蚣x1 鬼面猿x1", [50, 49]),
    (40, "帝國煉金術士x1 帝國工程兵x2", [51, 48, 48]),
    (41, "【BOSS】靈脈守護者",    [52]),

    # ── 第五章：梅莊庇護 (Ch5) ──
    # ID 42-49
    (42, "帝國重甲兵x1 帝國精銳兵x2", [54, 23, 23]),
    (43, "陰帥小卒x2 亡魂x1",   [55, 55, 56]),
    (44, "亡魂x3",              [56, 56, 56]),
    (45, "帝國審判官x1 黑袍教士x1", [58, 59]),
    (46, "機械傀儡x2",          [60, 60]),
    (47, "黑袍教士x1 帝國重甲兵x1 陰帥小卒x1", [59, 54, 55]),
    (48, "【BOSS】奇美拉二代",    [57]),
    (49, "【BOSS】甘珠爾守衛x1 帝國重甲兵x2", [61, 54, 54]),

    # ── 第六章：陰山暗影 (Ch6) ──
    # ID 50-57
    (50, "枯木妖x2 毒林蟲群x1", [63, 63, 65]),
    (51, "饕餮獸僕x1 毒林蟲群x1", [64, 65]),
    (52, "帝國暗部x2",          [66, 66]),
    (53, "戾神碎片x1 變異門徒x1", [67, 68]),
    (54, "陰山鬼修x1 枯木妖x2", [69, 63, 63]),
    (55, "變異門徒x2 饕餮獸僕x1", [68, 68, 64]),
    (56, "帝國暗部x1 陰山鬼修x1 戾神碎片x1", [66, 69, 67]),
    (57, "【BOSS】戾神化身",      [70]),

    # ── 第七章：鐘塔審判 (Ch7) ──
    # ID 58-65
    (58, "鐘塔守衛x2",          [72, 72]),
    (59, "理式構裝體x1 鐘塔守衛x1", [74, 72]),
    (60, "帝國鐘塔研究員x1 理式構裝體x1", [75, 74]),
    (61, "禁忌實驗體x1 帝國鐘塔研究員x1", [76, 75]),
    (62, "虛空裂隙獸x1 禁忌實驗體x1", [77, 76]),
    (63, "帝國司令官x1 鐘塔守衛x2", [78, 72, 72]),
    (64, "【BOSS】奇美拉三代",    [73]),
    (65, "【BOSS】不可名狀幼體",  [79]),

    # ── 第八章：萬法同歸 (Ch8) ──
    # ID 66-78
    (66, "混沌殘影x2",          [81, 81]),
    (67, "混沌殘影x1 理式崩壞體x1", [81, 90]),
    (68, "混沌侵蝕者x2 混沌殘影x1", [91, 91, 81]),
    (69, "虛空巨靈x1 混沌殘影x2", [88, 81, 81]),
    (70, "【BOSS】饕餮化身",      [82]),
    (71, "【BOSS】檮杌化身",      [83]),
    (72, "【BOSS】窮奇化身",      [84]),
    (73, "【BOSS】帝國終極兵器x1 理式構裝體x2", [85, 74, 74]),
    (74, "混沌核心x1 混沌殘影x2", [87, 81, 81]),
    (75, "【BOSS】四兇融合體",    [86]),
    (76, "虛空巨靈x1 理式崩壞體x2", [88, 90, 90]),
    (77, "混沌核心x1 混沌侵蝕者x2", [87, 91, 91]),
    (78, "【BOSS】不可名狀之物",  [89]),
]


def main():
    with open(TROOPS_PATH, "r", encoding="utf-8") as f:
        troops = json.load(f)

    # Extend array if needed (current length is 26, we need up to ID 78)
    while len(troops) <= 78:
        next_id = len(troops)
        troops.append({
            "id": next_id,
            "members": [],
            "name": "",
            "pages": [empty_page()]
        })

    # Apply troop definitions
    for tid, name, enemy_ids in TROOP_DEFS:
        troop = make_troop(tid, name, enemy_ids)
        # Preserve existing pages if troop already has events (like ID 3)
        if tid < len(troops) and troops[tid] and troops[tid].get("pages") and len(troops[tid]["pages"]) > 1:
            troop["pages"] = troops[tid]["pages"]
        troops[tid] = troop

    # Write back
    formatted = "[\n"
    for i, item in enumerate(troops):
        if item is None:
            formatted += "null"
        else:
            formatted += json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        if i < len(troops) - 1:
            formatted += ","
        formatted += "\n"
    formatted += "]"

    with open(TROOPS_PATH, "w", encoding="utf-8") as f:
        f.write(formatted)

    print(f"Done: wrote {len(TROOP_DEFS)} troop definitions (ID 4-78)")
    for tid, name, eids in TROOP_DEFS:
        print(f"  T{tid:2d}: {name}")

if __name__ == "__main__":
    main()
