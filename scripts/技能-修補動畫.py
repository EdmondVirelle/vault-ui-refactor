#!/usr/bin/env python3
"""
為 Skills.json 中 ID 12~211 的敵軍技能加上動畫。
依照技能名稱、屬性、範圍、傷害類型做比對。
已有動畫 (animationId != 0) 的技能不覆蓋。
分隔符 (名稱以 ---- 開頭) 跳過。
"""
import json
import sys
from pathlib import Path

SKILLS_PATH = Path(__file__).resolve().parent.parent / "Consilience" / "data" / "Skills.json"

# ── 手動映射表：skill_id → animationId ──
# 根據技能名稱、屬性(elementId)、範圍(scope)、傷害類型逐一比對
ANIMATION_MAP = {
    # ═══ 廿式軍刀術 (12~31) ═══
    # 12: 壹式・斬鉄 → 346 (already set)
    # 13: 貳式・旋風 → 189 (already set)
    # 14: 參式・凝氣 → 381 (already set)
    15: 380,   # 肆式・金光 (金/陽 single attack) → EVFXForge15_01 光
    16: 345,   # 伍式・連斬 (random 3 slash) → EVFXParagon_01_01 神劍
    17: 382,   # 陸式・堅壁 (金/self buff) → EVFXForge15_03 光
    18: 348,   # 柒式・一閃 (金/single slash) → EVFXParagon_01_04 神劍
    19: 52,    # 捌式・鷹揚 (taunt/self buff) → 強化2
    20: 41,    # 玖式・歸元 (self heal) → 治癒單體1
    21: 349,   # 拾式・十字斬 (陽/金 single slash) → EVFXParagon_01_05
    22: 53,    # 拾壹式・昂揚 (all ally buff) → 強化3
    23: 44,    # 拾貳式・金蓮 (all heal) → 治癒全體2
    24: 91,    # 拾參式・絕影 (stealth/self) → 疾風單體1
    25: 98,    # 拾肆式・聖盾 (all shield) → 聖光全體1
    26: 385,   # 拾伍式・劍氣 (陽 magic all) → EVFXForge15_06 光
    27: 231,   # 拾陸式・血刃 (self buff absorb) → EVFX02_01_SanguineEdge
    28: 350,   # 拾柒式・鳳翔 (陽 slash all) → EVFXParagon_01_06
    29: 354,   # 拾捌式・覇王斬 (金陽 single, powerful) → EVFXParagon_01_10
    30: 389,   # 拾玖式・天照 (陽金 magic all) → EVFXForge15_10 光
    31: 356,   # 終式・天地一刀 (ultimate slash single) → EVFXParagon_01_12

    # ═══ 野獸技能 (33~44) ═══
    33: 16,    # 撕咬 (bite single) → 爪擊物理
    34: 39,    # 猛撲 (pounce single) → 衝撞
    35: 59,    # 毒牙 (poison fang single) → 中毒
    36: 37,    # 嚎叫 (howl self) → 咆嘯
    37: 28,    # 亂爪 (wild claw random 2) → 爪擊特殊
    38: 58,    # 吞噬 (devour HP drain) → 吸收
    39: 39,    # 暴怒衝撞 (rage charge all) → 衝撞
    40: 33,    # 毒霧彈 (poison fog all) → 花粉
    41: 57,    # 蛛絲纏繞 (spider web single) → 束縛
    42: 64,    # 石化凝視 (petrify single) → 麻痺
    43: 59,    # 寄生蟲巢 (parasite HP drain) → 中毒
    44: 37,    # 狂暴化 (berserk self) → 咆嘯

    # ═══ 帝國技能 (46~58) ═══
    46: 6,     # 帝國軍刀 (saber single phys) → 斬擊物理
    47: 23,    # 十字斬 (cross slash single) → 斬擊特殊1
    48: 96,    # 聖光療癒 (holy heal self) → 聖光單體1
    49: 1,     # 盾擊 (shield bash single) → 打擊物理
    50: 25,    # 帝國連斬 (combo slash random 3) → 斬擊特殊3
    51: 116,   # 理式砲擊 (formula cannon all) → 雷射全體
    52: 29,    # 機關弩射 (crossbow random 2) → 箭矢特殊
    53: 119,   # 瑪那聚焦 (mana focus single) → 光彈
    54: 229,   # 理式結界 (formula barrier self) → プロテクション
    55: 51,    # 帝國號令 (empire command all ally) → 強化1
    56: 52,    # 帝國軍陣 (formation all ally) → 強化2
    57: 54,    # 理式分析 (analysis debuff single) → 弱化1
    58: 112,   # 機關砲連射 (machine gun random 4) → 槍擊連擊

    # ═══ 妖邪技能 (60~75) ═══
    60: 101,   # 陰氣爪擊 (yin claw single, elem=14 陰) → 黑暗單體1
    61: 58,    # 魂吸 (soul absorb MP drain) → 吸收
    62: 60,    # 詛咒之眼 (curse eye single debuff) → 黑暗
    63: 103,   # 妖霧 (demon fog all) → 黑暗全體1
    64: 469,   # 冥火 (netherfire single, elem=14) → EVFXForge11_01 火焰
    65: 101,   # 怨靈附身 (spirit possession single) → 黑暗單體1
    66: 59,    # 萬蠱噬心 (gu single, elem=13) → 中毒
    67: 104,   # 血海翻騰 (blood sea all) → 黑暗全體2
    68: 32,    # 腐蝕之息 (corrosive breath all) → 吹息
    69: 36,    # 亡者之歌 (song of the dead all) → 歌
    70: 58,    # 噬魂幡 (soul banner HP drain) → 吸收
    71: 103,   # 冥界召喚 (underworld summon self buff) → 黑暗全體1
    72: 105,   # 萬鬼夜行 (ghost parade all) → 黑暗全體3
    73: 102,   # 九幽冥咒 (nine hells curse single) → 黑暗單體2
    74: 70,    # 業火焚身 (karmic fire all, elem=14) → 火炎全體3
    75: 102,   # 厲鬼纏身 (fierce ghost single) → 黑暗單體2

    # ═══ 混沌技能 (77~88) ═══
    77: 32,    # 混沌吐息 (chaos breath all, elem=16) → 吹息
    78: 53,    # 四兇共鳴 (four fiends self buff) → 強化3
    79: 110,   # 次元裂隙 (dimensional rift single) → 無屬全體3
    80: 109,   # 理式崩壞 (formula collapse all) → 無屬全體2
    81: 42,    # 奇美拉融合 (chimera fusion self heal) → 治癒單體2
    82: 104,   # 虛空侵蝕 (void erosion all) → 黑暗全體2
    83: 110,   # 不可名狀 (unspeakable single) → 無屬全體3
    84: 55,    # 封印瓦解 (seal collapse debuff) → 弱化2
    85: 108,   # 混沌脈動 (chaos pulse all) → 無屬全體1
    86: 58,    # 虛空吞噬 (void devour all HP drain) → 吸收
    87: 56,    # 法則扭曲 (law distortion all debuff) → 弱化3
    88: 110,   # 次元崩塌 (dimension collapse all) → 無屬全體3

    # ═══ 通用敵技 (90~103) ═══
    90: 202,   # 自爆 (self-destruct all) → 爆発1
    91: 51,    # 集結號令 (rally all ally) → 強化1
    92: 229,   # 堅守 (hold firm self) → プロテクション
    93: 41,    # 治療術 (heal single ally) → 治癒單體1
    94: 43,    # 全體治療 (heal all) → 治癒全體1
    95: 37,    # 挑釁 (provoke single) → 咆嘯
    96: 229,   # 掩護 (cover self) → プロテクション
    97: 51,    # 強化防禦 (buff defense all ally) → 強化1
    98: 52,    # 強化攻擊 (buff attack all ally) → 強化2
    99: 54,    # 破甲術 (armor break single) → 弱化1
    100: 61,   # 封技術 (seal skill single) → 沉默
    101: 55,   # 散功術 (dispel MP drain single) → 弱化2
    102: 53,   # 蓄力 (charge self buff) → 強化3
    103: 52,   # 反擊姿態 (counter stance self) → 強化2

    # ═══ 奇美拉技能 (105~116) ═══
    105: 86,   # 石偶拳 (stone fist single phys) → 大地單體1
    106: 28,   # 活體撕裂 (tear single phys) → 爪擊特殊
    107: 109,  # 氣瑪那融合波 (fusion wave all, elem=16) → 無屬全體2
    108: 39,   # 奇美拉突進 (charge single) → 衝撞
    109: 202,  # 不穩定爆發 (unstable explosion all) → 爆発1
    110: 42,   # 形態變異 (mutation self heal) → 治癒單體2
    111: 58,   # 融合吸收 (fusion absorb HP drain) → 吸收
    112: 45,   # 異種再生 (alien regen self heal) → 療癒單體1
    113: 34,   # 奇美拉嘶嚎 (screech all debuff) → 超音波
    114: 55,   # 基因崩壞 (gene collapse all phys) → 弱化2
    115: 53,   # 奇美拉覺醒 (awakening self buff) → 強化3
    116: 107,  # 終極融合體 (ultimate fusion single magic) → 無屬單體2

    # ═══ 帝國精銳技 (118~130) ═══
    118: 34,   # 鐘塔共振 (bell tower all magic) → 超音波
    119: 55,   # 理式解構 (deconstruct single magic) → 弱化2
    120: 117,  # 光柱制裁 (light pillar all, elem=15) → 光柱1
    121: 115,  # 帝國重砲 (heavy cannon single phys) → 雷射單體
    122: 229,  # 鐵幕防線 (iron curtain self) → プロテクション
    123: 116,  # 殲滅指令 (annihilate all phys) → 雷射全體
    124: 107,  # 帝國終焉 (empire end single magic) → 無屬單體2
    125: 108,  # 瑪那轉譯 (mana translate all magic) → 無屬全體1
    126: 57,   # 理式牢籠 (formula cage single magic) → 束縛
    127: 53,   # 機關要塞 (fortress all ally buff) → 強化3
    128: 36,   # 帝國戰歌 (war song all ally buff) → 歌
    129: 110,  # 理式滅殺 (formula annihilate all magic) → 無屬全體3
    130: 109,  # 帝國禁術 (forbidden art single magic) → 無屬全體2

    # ═══ Boss特殊技 (132~146) ═══
    132: 53,   # 領域展開 (domain expansion self buff) → 強化3
    133: 100,  # 天威降臨 (divine might all magic) → 聖光全體3
    134: 52,   # 殺意凝聚 (killing intent self buff) → 強化2
    135: 202,  # 怒意爆發 (rage explosion all phys) → 爆発1
    136: 22,   # 致命連擊 (lethal combo random 3 phys) → 打擊特殊2
    137: 56,   # 全屬性壓制 (all suppress all debuff) → 弱化3
    138: 42,   # 不死再生 (undead regen self heal) → 治癒單體2
    139: 228,  # 吸收屏障 (absorb barrier self) → リフレクション
    140: 53,   # 暴走模式 (rampage mode self buff) → 強化3
    141: 110,  # 滅世宣言 (world destruction all magic) → 無屬全體3
    142: 54,   # 弱點看破 (weakness expose single debuff) → 弱化1
    143: 53,   # 最終形態 (final form self buff) → 強化3
    144: 30,   # 極限突破 (limit break single phys) → 通用特殊1
    145: 30,   # 瀕死反擊 (near-death counter all phys) → 通用特殊1
    146: 37,   # 狂氣釋放 (madness release all magic) → 咆嘯

    # ═══ 四兇技能 (148~162) ═══
    148: 58,   # 饕餮吞天 (taotie swallow all HP drain) → 吸收
    149: 58,   # 饕餮虹吸 (taotie absorb all MP drain) → 吸收
    150: 108,  # 饕餮飢餓波 (hunger wave all magic) → 無屬全體1
    151: 58,   # 饕餮永食 (eternal feast single HP drain) → 吸收
    152: 94,   # 檮杌暴嵐 (taowu storm all phys) → 疾風全體2
    153: 37,   # 檮杌狂嘯 (wild howl all magic) → 咆嘯
    154: 28,   # 檮杌滅世爪 (world-end claw single phys) → 爪擊特殊
    155: 70,   # 檮杌怒焰 (rage flame all magic) → 火炎全體3
    156: 63,   # 窮奇惑心 (bewitch all magic) → 混亂
    157: 56,   # 窮奇逆命 (reverse fate single debuff) → 弱化3
    158: 63,   # 窮奇善惡顛 (good/evil flip all magic) → 混亂
    159: 35,   # 窮奇混淆 (confusion all magic) → 霧
    160: 53,   # 混沌初始 (chaos beginning self heal) → 強化3
    161: 56,   # 混沌歸零 (chaos reset all debuff) → 弱化3
    162: 110,  # 混沌終局 (chaos end all, elem=16) → 無屬全體3

    # ═══ 終極技能 (164~174) ═══
    164: 37,   # 四兇怒嘯 (four fiends roar all magic) → 咆嘯
    165: 53,   # 四兇合鳴 (four fiends chorus self buff) → 強化3
    166: 104,  # 封印侵蝕 (seal erosion all magic) → 黑暗全體2
    167: 90,   # 靈脈崩潰 (spirit vein collapse all magic) → 大地全體3
    168: 110,  # 萬法歸寂 (all dharma silence all, elem=16) → 無屬全體3
    169: 65,   # 一念之滅 (one thought destruction single) → 即死
    170: 203,  # 天地同歸 (heaven earth return all magic) → 爆発2
    171: 110,  # 世界終焉 (world end all magic) → 無屬全體3
    172: 105,  # 虛空終焉 (void end single magic) → 黑暗全體3
    173: 110,  # 不可名狀・真 (unspeakable true all, elem=16) → 無屬全體3
    174: 65,   # 存在抹消 (existence erasure single magic) → 即死

    # ═══ 環境陷阱技 (176~189) ═══
    176: 88,   # 落石 (falling rocks all phys) → 大地全體1
    177: 59,   # 毒沼 (poison swamp all magic) → 中毒
    178: 93,   # 沙暴 (sandstorm all magic) → 疾風全體1
    179: 76,   # 雷擊 (lightning random 2 magic) → 雷電單體1
    180: 71,   # 冰封 (ice seal single magic) → 寒冰單體1
    181: 89,   # 地裂 (earth crack all phys) → 大地全體2
    182: 68,   # 火牆 (fire wall all magic) → 火炎全體1
    183: 108,  # 靈壓 (spirit pressure all magic) → 無屬全體1
    184: 33,   # 瘴氣 (miasma all magic) → 花粉
    185: 90,   # 地脈噴發 (ley line eruption all magic) → 大地全體3
    186: 104,  # 封印反噬 (seal backlash all magic) → 黑暗全體2
    187: 109,  # 結界崩壞 (barrier collapse all magic) → 無屬全體2
    188: 80,   # 天劫降臨 (heaven calamity random 2 magic) → 雷電全體3
    189: 55,   # 靈脈枯竭 (exhaustion all MP drain) → 弱化2

    # ═══ 地域技能 (191~211) ═══
    191: 328,  # 黃沙斬 (yellow sand slash single phys) → EVFXForge07_01 沙子
    192: 330,  # 沙暴掩襲 (sandstorm ambush all phys) → EVFXForge07_03 沙子
    193: 329,  # 黃沙護體 (sand shield self) → EVFXForge07_02 沙子
    194: 469,  # 烈日灼燒 (scorching sun all magic) → EVFXForge11_01 火焰
    195: 332,  # 沙漠葬禮 (desert funeral single magic) → EVFXForge07_05 沙子
    196: 71,   # 寒冰劍氣 (ice sword qi single magic) → 寒冰單體1
    197: 75,   # 仙池凍結 (pool freeze all magic) → 寒冰全體3
    198: 73,   # 寒霜護體 (frost shield self) → 寒冰全體1
    199: 9,    # 冰刃連斬 (ice blade combo random 3) → 斬擊寒冰
    200: 35,   # 陰山毒霧 (dark mountain fog all magic) → 霧
    201: 32,   # 饕餮之息 (taotie breath all magic) → 吹息
    202: 57,   # 枯木纏繞 (dead wood entangle single magic) → 束縛
    203: 397,  # 鬼修邪功 (ghost evil art single, elem=14) → EVFXForge13_01 暗
    204: 229,  # 鐘塔結界 (bell tower barrier self) → プロテクション
    205: 54,   # 理式掃描 (formula scan single debuff) → 弱化1
    206: 107,  # 禁忌注入 (forbidden injection single magic) → 無屬單體2
    207: 34,   # 鐘塔轟鳴 (bell tower rumble all magic) → 超音波
    # 208: 閃光彈 → 40 (already set)
    209: 54,   # 觀察破綻 (observe weakness self) → 弱化1
    # 210: 烈風呼喚 → 93 (already set)
    211: 35,   # 躲藏 (hide self) → 霧
}


def main():
    with open(SKILLS_PATH, "r", encoding="utf-8") as f:
        skills = json.load(f)

    changed = 0
    skipped_separator = 0
    skipped_existing = 0
    skipped_unmapped = 0

    for skill in skills:
        if skill is None:
            continue
        sid = skill["id"]
        if sid < 12 or sid > 211:
            continue

        name = skill["name"]

        # skip separators
        if name.startswith("----"):
            skipped_separator += 1
            continue

        # skip already animated
        if skill["animationId"] != 0:
            skipped_existing += 1
            continue

        if sid in ANIMATION_MAP:
            old = skill["animationId"]
            skill["animationId"] = ANIMATION_MAP[sid]
            changed += 1
            print(f"  #{sid:3d} {name} → animationId={ANIMATION_MAP[sid]}")
        else:
            skipped_unmapped += 1
            print(f"  #{sid:3d} {name} → [UNMAPPED]")

    print(f"\n=== 完成 ===")
    print(f"  修改: {changed}")
    print(f"  已有動畫: {skipped_existing}")
    print(f"  分隔符: {skipped_separator}")
    print(f"  未映射: {skipped_unmapped}")

    with open(SKILLS_PATH, "w", encoding="utf-8") as f:
        json.dump(skills, f, ensure_ascii=False, indent=None, separators=(",", ":"))
        f.write("\n")

    print(f"\n已寫入 {SKILLS_PATH}")


if __name__ == "__main__":
    main()
