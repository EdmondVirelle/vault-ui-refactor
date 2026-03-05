#!/usr/bin/env python3
"""
Patch Enemies.json:
1. Add 【BOSS】 prefix to boss enemy names
2. Fix HP values for mid-game bosses
3. Add more skills/actions to bosses that need phase-based design
"""
import json
import sys
from pathlib import Path

ENEMIES_PATH = Path(__file__).parent.parent / "Consilience" / "data" / "Enemies.json"

def main():
    with open(ENEMIES_PATH, "r", encoding="utf-8") as f:
        enemies = json.load(f)

    # ── 1. Boss name markers ──
    boss_ids = {
        8:  "【BOSS】武裝兵將領",
        10: "【BOSS】書中判官",
        25: "【BOSS】劃月邪徒",
        34: "【BOSS】沙漠巨蟲",
        43: "【BOSS】初代奇美拉",
        52: "【BOSS】靈脈守護者",
        57: "【BOSS】奇美拉二代",
        61: "【BOSS】甘珠爾守衛",
        70: "【BOSS】戾神化身",
        73: "【BOSS】奇美拉三代",
        79: "【BOSS】不可名狀幼體",
        82: "【BOSS】饕餮化身",
        83: "【BOSS】檮杌化身",
        84: "【BOSS】窮奇化身",
        85: "【BOSS】帝國終極兵器",
        86: "【BOSS】四兇融合體",
        87: "【BOSS】混沌核心",
        88: "【BOSS】虛空巨靈",
        89: "【BOSS】不可名狀之物",
    }

    # ── 2. HP fixes (params[0] = MHP) ──
    hp_fixes = {
        25: 800,    # 劃月邪徒: 500→800 (升格Ch1 Boss)
        34: 1000,   # 沙漠巨蟲: 600→1000 (升格Ch2 Boss)
        52: 1000,   # 靈脈守護者: 700→1000
        57: 1200,   # 奇美拉二代: 600→1200
        61: 1200,   # 甘珠爾守衛: 800→1200
        73: 1800,   # 奇美拉三代: 700→1800
        79: 1500,   # 不可名狀幼體: 1000→1500
    }

    # ── 3. Boss action enhancements ──
    # conditionType: 0=always, 1=turn(A+Bn), 2=HP%(lo,hi), 3=MP%(lo,hi), 4=state, 5=party level, 6=switch
    # For HP%: conditionParam1=threshold%, conditionParam2=0 means "below threshold"
    #          conditionParam1=lo, conditionParam2=hi means "between lo% and hi%"

    def act(skill_id, rating=5, cond_type=0, p1=0, p2=0):
        return {
            "skillId": skill_id, "rating": rating,
            "conditionType": cond_type, "conditionParam1": p1, "conditionParam2": p2
        }

    boss_actions = {
        # ── Ch1 Boss: 劃月邪徒 (ID 25) ── 升格為正式Boss
        # 原有: 攻擊, 斬鉄, 旋風, 金光, 連斬, 蓄力
        # 新增: 強化攻擊(98), 反擊姿態(103), 領域展開(132) HP<40%
        25: [
            act(1),             # 攻擊
            act(12),            # 壹式・斬鉄
            act(13),            # 貳式・旋風
            act(15),            # 肆式・金光
            act(16),            # 伍式・連斬
            act(102, 4),        # 蓄力
            act(98, 3, 1, 1, 3),  # 強化攻擊 (Turn 1+3n)
            act(103, 3, 2, 40, 0),  # 反擊姿態 (HP<40%)
            act(132, 2, 2, 30, 0),  # 領域展開 (HP<30%)
        ],

        # ── Ch2 Boss: 沙漠巨蟲 (ID 34) ── 升格為正式Boss
        # 原有: 攻擊, 猛撲, 暴怒衝撞, 吞噬, 狂暴化
        # 新增: 毒霧彈(40), 蓄力(102), 暴走模式(140) HP<25%
        34: [
            act(1),             # 攻擊
            act(34),            # 猛撲
            act(39),            # 暴怒衝撞
            act(38),            # 吞噬
            act(35, 4),         # 毒牙
            act(40, 3, 2, 60, 0),  # 毒霧彈 (HP<60%)
            act(44, 3, 2, 50, 0),  # 狂暴化 (HP<50%)
            act(102, 3, 1, 1, 3),  # 蓄力 (Turn 1+3n)
            act(140, 2, 2, 25, 0), # 暴走模式 (HP<25%)
        ],

        # ── Ch3 Boss: 初代奇美拉 (ID 43) ── 增加階段感
        # 原有: 攻擊, 石偶拳, 活體撕裂, 氣瑪那融合波, 奇美拉突進, 不穩定爆發, 形態變異
        # 新增: 蓄力(102), 怒意爆發(135) HP<25%
        43: [
            act(1),             # 攻擊
            act(105),           # 石偶拳
            act(106),           # 活體撕裂
            act(107),           # 氣瑪那融合波
            act(108),           # 奇美拉突進
            act(109, 3, 2, 30, 0),  # 不穩定爆發 (HP<30%)
            act(110, 2, 2, 50, 0),  # 形態變異 (HP<50%)
            act(102, 3, 1, 1, 3),   # 蓄力 (Turn 1+3n)
            act(135, 2, 2, 25, 0),  # 怒意爆發 (HP<25%)
        ],

        # ── Ch4 Boss: 靈脈守護者 (ID 52) ── 增加技能
        # 原有: 地脈噴發, 靈壓, 領域展開, 天威降臨, 不死再生
        # 新增: 全屬性壓制(137) HP<40%, 混沌脈動(85) HP<30%
        52: [
            act(1),             # 攻擊
            act(185),           # 地脈噴發
            act(183),           # 靈壓
            act(132, 3, 1, 1, 4),   # 領域展開 (Turn 1+4n)
            act(133, 3, 2, 60, 0),  # 天威降臨 (HP<60%)
            act(138, 2, 2, 30, 0),  # 不死再生 (HP<30%)
            act(137, 2, 2, 40, 0),  # 全屬性壓制 (HP<40%)
            act(85, 2, 2, 25, 0),   # 混沌脈動 (HP<25%)
        ],

        # ── Ch5 Boss: 奇美拉二代 (ID 57) ── 大幅強化
        # 新增: 奇美拉嘶嚎(113), 基因崩壞(114), 暴走模式(140)
        57: [
            act(1),             # 攻擊
            act(106),           # 活體撕裂
            act(107),           # 氣瑪那融合波
            act(108),           # 奇美拉突進
            act(112, 3, 2, 60, 0),  # 異種再生 (HP<60%)
            act(109, 3, 2, 40, 0),  # 不穩定爆發 (HP<40%)
            act(110, 2, 2, 50, 0),  # 形態變異 (HP<50%)
            act(113, 3, 2, 35, 0),  # 奇美拉嘶嚎 (HP<35%)
            act(114, 2, 2, 20, 0),  # 基因崩壞 (HP<20%)
            act(140, 2, 2, 15, 0),  # 暴走模式 (HP<15%)
        ],

        # ── Ch5 Boss: 甘珠爾守衛 (ID 61) ── 增加技能
        # 新增: 帝國終焉(124) HP<25%, 吸收屏障(139) HP<50%
        61: [
            act(1),             # 攻擊
            act(118),           # 鐘塔共振
            act(122),           # 鐵幕防線
            act(121),           # 帝國重砲
            act(123, 4),        # 殲滅指令
            act(128, 3, 1, 1, 3),  # 帝國戰歌 (Turn 1+3n)
            act(139, 3, 2, 50, 0), # 吸收屏障 (HP<50%)
            act(124, 2, 2, 25, 0), # 帝國終焉 (HP<25%)
            act(97, 3, 2, 40, 0),  # 強化防禦 (HP<40%)
        ],

        # ── Ch7 Boss: 不可名狀幼體 (ID 79) ── 增加技能
        # 原有: 不可名狀, 混沌脈動, 虛空侵蝕, 混沌吐息, 封印瓦解
        # 新增: 次元崩塌(88), 法則扭曲(87), 不死再生(138)
        79: [
            act(1),             # 攻擊
            act(83),            # 不可名狀
            act(85),            # 混沌脈動
            act(82),            # 虛空侵蝕
            act(77),            # 混沌吐息
            act(84, 3, 2, 50, 0),  # 封印瓦解 (HP<50%)
            act(88, 3, 2, 40, 0),  # 次元崩塌 (HP<40%)
            act(87, 3, 2, 30, 0),  # 法則扭曲 (HP<30%)
            act(138, 2, 2, 20, 0), # 不死再生 (HP<20%)
        ],
    }

    # ── Apply changes ──
    changes = []
    for enemy in enemies:
        if enemy is None:
            continue
        eid = enemy["id"]

        # Name markers
        if eid in boss_ids:
            old = enemy["name"]
            enemy["name"] = boss_ids[eid]
            changes.append(f"  [NAME] ID {eid}: {old} → {enemy['name']}")

        # HP fixes
        if eid in hp_fixes:
            old_hp = enemy["params"][0]
            enemy["params"][0] = hp_fixes[eid]
            changes.append(f"  [HP]   ID {eid}: {old_hp} → {hp_fixes[eid]}")

        # Action enhancements
        if eid in boss_actions:
            old_count = len(enemy["actions"])
            enemy["actions"] = boss_actions[eid]
            new_count = len(enemy["actions"])
            changes.append(f"  [ACTS] ID {eid}: {old_count} → {new_count} actions")

    # ── Write back ──
    with open(ENEMIES_PATH, "w", encoding="utf-8") as f:
        json.dump(enemies, f, ensure_ascii=False, indent=None, separators=(",", ":"))
        # RPG Maker MZ uses compact JSON with newlines per entry

    # Re-format: one entry per line like RPG Maker expects
    with open(ENEMIES_PATH, "r", encoding="utf-8") as f:
        data = f.read()

    # RPG Maker format: [\nnull,\n{...},\n{...},\n...\n]
    formatted = "[\n"
    items = json.loads(data)
    for i, item in enumerate(items):
        if item is None:
            formatted += "null"
        else:
            formatted += json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        if i < len(items) - 1:
            formatted += ","
        formatted += "\n"
    formatted += "]"

    with open(ENEMIES_PATH, "w", encoding="utf-8") as f:
        f.write(formatted)

    print(f"Patched {len(changes)} changes:")
    for c in changes:
        print(c)

if __name__ == "__main__":
    main()
