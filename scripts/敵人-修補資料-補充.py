#!/usr/bin/env python3
"""
Patch Enemies.json round 2: fill in boss actions per design doc (敵人設計.md)
"""
import json
from pathlib import Path

ENEMIES_PATH = Path(__file__).parent.parent / "Consilience" / "data" / "Enemies.json"

def act(skill_id, rating=5, cond_type=0, p1=0, p2=0):
    return {
        "skillId": skill_id, "rating": rating,
        "conditionType": cond_type, "conditionParam1": p1, "conditionParam2": p2
    }

BOSS_ACTIONS = {
    # ── Ch6 Boss: 戾神化身 (ID 70) ── design doc has 8 skills
    70: [
        act(1),                         # 攻擊
        act(77),                        # 混沌吐息
        act(79),                        # 次元裂隙
        act(80),                        # 理式崩壞
        act(132, 3, 1, 1, 4),           # 領域展開 (Turn 1+4n)
        act(133, 3, 2, 60, 0),          # 天威降臨 (HP<60%)
        act(135, 3, 2, 40, 0),          # 怒意爆發 (HP<40%)
        act(138, 2, 2, 25, 0),          # 不死再生 (HP<25%)
    ],

    # ── Ch7 Boss: 奇美拉三代 (ID 73) ── design doc has 11 skills
    73: [
        act(1),                         # 攻擊
        act(106),                       # 活體撕裂
        act(107),                       # 氣瑪那融合波
        act(108),                       # 奇美拉突進
        act(109, 3, 2, 35, 0),          # 不穩定爆發 (HP<35%)
        act(110, 3, 2, 50, 0),          # 形態變異 (HP<50%)
        act(111),                       # 融合吸收
        act(112, 3, 2, 60, 0),          # 異種再生 (HP<60%)
        act(113, 3, 2, 40, 0),          # 奇美拉嘶嚎 (HP<40%)
        act(114, 2, 2, 25, 0),          # 基因崩壞 (HP<25%)
        act(115, 2, 2, 20, 0),          # 奇美拉覺醒 (HP<20%)
    ],

    # ── Ch8 Boss: 饕餮化身 (ID 82) ── design doc has 7 skills
    82: [
        act(1),                         # 攻擊
        act(148),                       # 饕餮吞天
        act(149),                       # 饕餮虹吸
        act(150),                       # 饕餮飢餓波
        act(151, 3, 2, 40, 0),          # 饕餮永食 (HP<40%)
        act(44, 3, 2, 50, 0),           # 狂暴化 (HP<50%)
        act(138, 2, 2, 25, 0),          # 不死再生 (HP<25%)
        act(78, 2, 2, 30, 0),           # 四兇共鳴 (HP<30%)
    ],

    # ── Ch8 Boss: 檮杌化身 (ID 83) ── design doc has 7 skills
    83: [
        act(1),                         # 攻擊
        act(152),                       # 檮杌暴嵐
        act(153),                       # 檮杌狂嘯
        act(154),                       # 檮杌滅世爪
        act(155, 3, 2, 50, 0),          # 檮杌怒焰 (HP<50%)
        act(44, 3, 2, 40, 0),           # 狂暴化 (HP<40%)
        act(135, 2, 2, 30, 0),          # 怒意爆發 (HP<30%)
        act(78, 2, 2, 25, 0),           # 四兇共鳴 (HP<25%)
    ],

    # ── Ch8 Boss: 窮奇化身 (ID 84) ── design doc has 7 skills
    84: [
        act(1),                         # 攻擊
        act(156),                       # 窮奇惑心
        act(157),                       # 窮奇逆命
        act(158),                       # 窮奇善惡顛
        act(159, 3, 2, 50, 0),          # 窮奇混淆 (HP<50%)
        act(132, 3, 2, 40, 0),          # 領域展開 (HP<40%)
        act(137, 2, 2, 30, 0),          # 全屬性壓制 (HP<30%)
        act(78, 2, 2, 25, 0),           # 四兇共鳴 (HP<25%)
    ],

    # ── Ch8 Boss: 帝國終極兵器 (ID 85) ── design doc has 8 skills
    85: [
        act(1),                         # 攻擊
        act(121),                       # 帝國重砲
        act(123),                       # 殲滅指令
        act(129),                       # 理式滅殺
        act(130, 3, 2, 50, 0),          # 帝國禁術 (HP<50%)
        act(124, 3, 2, 40, 0),          # 帝國終焉 (HP<40%)
        act(140, 2, 2, 30, 0),          # 暴走模式 (HP<30%)
        act(139, 3, 2, 50, 0),          # 吸收屏障 (HP<50%)
        act(122, 3, 1, 1, 3),           # 鐵幕防線 (Turn 1+3n)
    ],

    # ── Ch8 Boss: 四兇融合體 (ID 86) ── design doc has 7+ skills
    86: [
        act(1),                         # 攻擊
        act(164),                       # 四兇怒嘯
        act(165),                       # 四兇合鳴
        act(166, 3, 2, 60, 0),          # 封印侵蝕 (HP<60%)
        act(167, 3, 2, 50, 0),          # 靈脈崩潰 (HP<50%)
        act(160, 2, 2, 30, 0),          # 混沌初始 (HP<30%)
        act(138, 2, 2, 40, 0),          # 不死再生 (HP<40%)
        act(143, 2, 2, 20, 0),          # 最終形態 (HP<20%)
        act(79, 3),                     # 次元裂隙
    ],

    # ── Ch8: 混沌核心 (ID 87) ── design doc has 8 skills
    87: [
        act(1),                         # 攻擊
        act(77),                        # 混沌吐息
        act(79),                        # 次元裂隙
        act(80),                        # 理式崩壞
        act(85),                        # 混沌脈動
        act(88, 3, 2, 50, 0),           # 次元崩塌 (HP<50%)
        act(161, 2, 2, 30, 0),          # 混沌歸零 (HP<30%)
        act(162, 2, 2, 20, 0),          # 混沌終局 (HP<20%)
        act(92, 3, 1, 1, 3),            # 堅守 (Turn 1+3n)
    ],

    # ── Ch8: 虛空巨靈 (ID 88) ── design doc has 7 skills
    88: [
        act(1),                         # 攻擊
        act(82),                        # 虛空侵蝕
        act(86),                        # 虛空吞噬
        act(87),                        # 法則扭曲
        act(88, 3, 2, 50, 0),           # 次元崩塌 (HP<50%)
        act(167, 3, 2, 40, 0),          # 靈脈崩潰 (HP<40%)
        act(141, 2, 2, 25, 0),          # 滅世宣言 (HP<25%)
        act(77),                        # 混沌吐息
    ],

    # ── FINAL BOSS: 不可名狀之物 (ID 89) ── design doc has 13 skills
    89: [
        act(1),                         # 攻擊
        act(83),                        # 不可名狀
        act(173),                       # 不可名狀・真
        act(162),                       # 混沌終局
        act(168),                       # 萬法歸寂
        act(169, 4),                    # 一念之滅
        act(170, 4),                    # 天地同歸
        act(171, 3, 2, 50, 0),          # 世界終焉 (HP<50%)
        act(172, 3, 2, 40, 0),          # 虛空終焉 (HP<40%)
        act(174, 2, 2, 30, 0),          # 存在抹消 (HP<30%)
        act(160, 3, 2, 35, 0),          # 混沌初始 (HP<35%)
        act(143, 2, 2, 25, 0),          # 最終形態 (HP<25%)
        act(144, 2, 2, 15, 0),          # 極限突破 (HP<15%)
        act(145, 2, 2, 10, 0),          # 瀕死反擊 (HP<10%)
    ],
}

def main():
    with open(ENEMIES_PATH, "r", encoding="utf-8") as f:
        enemies = json.load(f)

    changes = []
    for enemy in enemies:
        if enemy is None:
            continue
        eid = enemy["id"]
        if eid in BOSS_ACTIONS:
            old_count = len(enemy["actions"])
            enemy["actions"] = BOSS_ACTIONS[eid]
            new_count = len(enemy["actions"])
            changes.append(f"  ID {eid} {enemy['name']}: {old_count} -> {new_count} actions")

    # Write back in RPG Maker format
    formatted = "[\n"
    for i, item in enumerate(enemies):
        if item is None:
            formatted += "null"
        else:
            formatted += json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        if i < len(enemies) - 1:
            formatted += ","
        formatted += "\n"
    formatted += "]"

    with open(ENEMIES_PATH, "w", encoding="utf-8") as f:
        f.write(formatted)

    for c in changes:
        print(c)
    print(f"Done: {len(changes)} bosses updated")

if __name__ == "__main__":
    main()
