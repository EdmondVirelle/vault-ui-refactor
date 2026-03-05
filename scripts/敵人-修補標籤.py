"""Add complete notetags to all 91 enemies in Enemies.json.

Adds: Aggro, Aspect (Name/Icon/Description), AI Style/Level, Steal tables.
Preserves: existing Break Shields, Passive States, AI tags.

Element IDs: see System.json elements array.
"""
import json
import os
import re

DATA_DIR = r'C:\Consilience\Consilience\data'

def read_json(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('[\n')
        for i, item in enumerate(data):
            line = json.dumps(item, ensure_ascii=False, separators=(',', ':'))
            if i < len(data) - 1:
                f.write(line + ',\n')
            else:
                f.write(line + '\n')
        f.write(']\n')

# ============================================================
# CONSTANTS
# ============================================================

SEPARATOR_IDS = {3, 17, 26, 35, 44, 53, 62, 71, 80}
SKIP_IDS = {1, 2, 11}  # training dummy + template enemies (already complete)

CHAPTER_RANGES = [
    (0, 1, 16),    # Prologue
    (1, 18, 25),   # Ch1
    (2, 27, 34),   # Ch2
    (3, 36, 43),   # Ch3
    (4, 45, 52),   # Ch4
    (5, 54, 61),   # Ch5
    (6, 63, 70),   # Ch6
    (7, 72, 79),   # Ch7
    (8, 81, 91),   # Ch8
]

# ============================================================
# ENEMY DESCRIPTIONS (one per enemy)
# ============================================================

DESCRIPTIONS = {
    4:  "出沒於荒野的野生狼群，成群結隊時更加危險。",
    5:  "潛伏於草叢中的劇毒之蛇，行動迅捷。",
    6:  "佔據山道的土匪，見人就搶。",
    7:  "帝國正規軍的基層巡邏單位。",
    8:  "統領帝國駐軍的武裝將領，實力不容小覷。",
    9:  "傳說中的靈獸耳鼠，擁有非凡的靈覺與速度。",
    10: "封印於黃裳典籍中的判官意識，以文字為武器。",
    12: "帝國軍中的弓箭手，擅長遠程射擊。",
    13: "遺跡中蘇醒的石製守衛，防禦力極高。",
    14: "被困於遺跡中的不甘冤魂，以怨念為力。",
    15: "帝國哨兵部隊的隊長，統率力與戰鬥力兼備。",
    16: "遺跡深處的機關守衛，以古老技術驅動。",
    18: "埋伏在路旁的劫匪，專挑落單的旅人下手。",
    19: "帝國暗中部署的情報人員，善於隱匿與偷襲。",
    20: "受人雇用的街頭打手，力大而魯莽。",
    21: "背叛師門的武林叛徒，功夫不弱但心術不正。",
    22: "潛伏暗處的職業殺手，出手快狠準。",
    23: "經過嚴格訓練的帝國精銳部隊。",
    24: "帝國重裝騎士，攻防俱佳的精銳戰力。",
    25: "劃月門下的邪道修行者，功力深厚且手段陰狠。",
    27: "棲息於沙漠中的劇毒蠍子，尾針含有致命毒液。",
    28: "黃沙中成群出沒的沙漠狼，適應惡劣環境。",
    29: "駐守西域的帝國沙漠部隊，裝備適應沙漠作戰。",
    30: "由沙暴中凝聚而成的精怪，擅長風沙攻擊。",
    31: "西域商隊雇用的護衛，身經百戰。",
    32: "檮杌留下的殘影，雖非本體但仍具威脅。",
    33: "黑市中活躍的職業殺手，行蹤詭秘。",
    34: "沙漠深處的巨型蟲獸，體型龐大防禦驚人。",
    36: "仙池門下的弟子，修習寒冰劍法。",
    37: "凝聚寒氣而生的冰靈，攻擊帶有寒凍效果。",
    38: "受靈氣污染而變異的水中怪物。",
    39: "被邪術蠱惑的仙池弟子，失去自我意識。",
    40: "棲息於寒冰之地的巨熊，皮糙肉厚。",
    41: "窮奇散發的幻象，能迷惑人心。",
    42: "守護仙池聖地的護法武者，實力強橫。",
    43: "第一代奇美拉實驗體，融合多種生物的恐怖造物。",
    45: "帝國派出的探索部隊，正在搜尋靈脈資源。",
    46: "棲息於深山中的靈體，善用幻術。",
    47: "吸收靈脈能量而生的異獸，力量隨靈氣波動。",
    48: "帝國軍中的工程技術兵，擅長使用機關器械。",
    49: "戴著鬼面的兇猛猿猴，行動敏捷且狡詐。",
    50: "體型巨大的百足蜈蚣，毒性極強。",
    51: "帝國麾下的煉金術士，能以術式輔助作戰。",
    52: "守護靈脈源頭的強大存在，不容許任何人接近。",
    54: "全身重甲的帝國精銳，防禦力極高但行動遲緩。",
    55: "陰間差役的小兵，雖弱但數量眾多。",
    56: "徘徊不去的亡魂，以怨念驅動殘軀。",
    57: "第二代奇美拉改良體，比初代更加兇殘。",
    58: "帝國審判機構的官員，精通法術與審訊。",
    59: "身穿黑袍的邪教教士，以暗黑術式為武器。",
    60: "以機械技術製造的戰鬥傀儡，無痛無懼。",
    61: "守衛甘珠爾聖地的強大護衛者。",
    63: "枯死大樹化為的妖怪，以枝幹纏繞獵物。",
    64: "饕餮驅使的獸僕，凶暴嗜血。",
    65: "毒林中成群的毒蟲，數量龐大。",
    66: "帝國暗部的精銳密探，行動隱秘殺招致命。",
    67: "戾神碎裂的意識碎片，仍殘留強大的邪力。",
    68: "受邪氣侵蝕而變異的門徒，已非人形。",
    69: "陰山中修煉鬼道的邪修，善用陰寒之力。",
    70: "戾神降臨的化身，散發毀滅性的邪氣。",
    72: "守衛鐘塔入口的帝國衛兵，裝備精良。",
    73: "第三代奇美拉完成體，帝國科技的巔峰之作。",
    74: "以理式能量驅動的構裝體，邏輯精準而冷酷。",
    75: "駐守鐘塔的帝國研究員，能以術式遠程攻擊。",
    76: "違反禁忌的實驗產物，力量暴走而不穩定。",
    77: "從虛空裂隙中溢出的怪物，形態扭曲。",
    78: "帝國鐘塔的最高指揮官，身經百戰。",
    79: "初現雛形的不可名狀存在，令人窒息的壓迫感。",
    81: "混沌力量的殘餘影像，虛實不定。",
    82: "饕餮本體的化身，貪噬一切的凶獸。",
    83: "檮杌本體的化身，蠻橫霸道的凶獸。",
    84: "窮奇本體的化身，狡詐多變的凶獸。",
    85: "帝國傾盡國力打造的終極兵器，毀滅之力。",
    86: "四兇之力融合為一的恐怖存在。",
    87: "混沌力量的核心凝聚，散發扭曲世界的能量。",
    88: "虛空中遊蕩的巨大靈體，超越常理的存在。",
    89: "超越認知的混沌本體，萬法同歸的終極試煉。",
    90: "理式秩序崩壞後的產物，邏輯扭曲的異形。",
    91: "被混沌力量侵蝕的生命體，正在失去自我。",
}

# Steal tables: chapter-based common items
CHAPTER_STEAL_ITEMS = {
    0: [("Item 止血草", 50), ("Item 薄荷葉", 30)],
    1: [("Item 金創藥", 45), ("Item 暖香玉", 25)],
    2: [("Item 活血散", 45), ("Item 田七粉", 25)],
    3: [("Item 千錘首烏丸", 40), ("Item 七葉補血草", 25)],
    4: [("Item 續命八丸", 40), ("Item 地脈玉髓", 20)],
    5: [("Item 參茸養血精", 35), ("Item 返氣丹", 25)],
    6: [("Item 生肌續命膏", 35), ("Item 凝神液", 20)],
    7: [("Item 九轉回天丹", 30), ("Item 龜鶴延年丹", 15)],
    8: [("Item 九轉回天丹", 35), ("Item 洗髓液", 15)],
}

# Additional rare steal items for boss enemies
BOSS_STEAL_ITEMS = {
    0: [("Item 活血散", 10)],
    1: [("Item 千錘首烏丸", 10)],
    2: [("Item 七葉補血草", 10)],
    3: [("Item 地脈玉髓", 10)],
    4: [("Item 返氣丹", 10)],
    5: [("Item 七色行氣丹", 8)],
    6: [("Item 九轉回天丹", 8)],
    7: [("Item 天王護心丹", 5)],
    8: [("Item 大還丹(真)", 5)],
}

# Empire-specific additional steal items
EMPIRE_STEAL_EXTRA = {
    0: ("Item 定神香", 20),
    1: ("Item 壯骨粉", 20),
    2: ("Item 避寒犀角散", 20),
    3: ("Item 固氣膠", 18),
    4: ("Item 大力丸", 15),
    5: ("Item 金剛不壞丸", 12),
    6: ("Item 輕身散", 12),
    7: ("Item 閉氣丸", 10),
    8: ("Item 天佑神速香", 10),
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_chapter(eid):
    for ch, start, end in CHAPTER_RANGES:
        if start <= eid <= end:
            return ch
    return -1

def extract_break_shields(note):
    m = re.search(r'<Break Shields:\s*(\d+)>', note)
    return int(m.group(1)) if m else None

def extract_passive_states(note):
    return [int(m.group(1)) for m in re.finditer(r'<Passive State:\s*(\d+)>', note)]

def extract_ai_style(note):
    m = re.search(r'<AI Style:\s*(\w+)>', note)
    return m.group(1) if m else None

def extract_ai_level(note):
    m = re.search(r'<AI Level:\s*(\d+)>', note)
    return int(m.group(1)) if m else None

def is_empire(name):
    return '帝國' in name

def is_boss_type(passive_states):
    return 101 in passive_states or 102 in passive_states

def get_aggro(params):
    """Determine aggro based on stat distribution."""
    atk, defn, mat = params[2], params[3], params[4]
    if defn > atk and defn > mat:
        return 100  # tanky
    elif mat > atk * 1.3:
        return 30   # caster
    else:
        return 50   # standard

def get_ai_settings(chapter, is_boss, existing_style, existing_level):
    """Determine AI style and level."""
    if existing_style:
        return existing_style, existing_level or 100
    if is_boss:
        return "Gambit", min(100, 70 + chapter * 4)
    if chapter >= 5:
        return "Gambit", min(100, 60 + chapter * 5)
    if chapter >= 2:
        return "Classic", 50 + chapter * 8
    return "Classic", 50

def build_steal_block(chapter, gold_reward, is_boss_flag, is_empire_flag):
    """Build the <Steal> block content."""
    lines = []
    # Gold steal (2x reward, 40% chance)
    gold_amount = max(50, gold_reward * 2)
    lines.append(f"Gold {gold_amount}: 40%")
    # Chapter items
    for item_name, chance in CHAPTER_STEAL_ITEMS.get(chapter, []):
        lines.append(f"{item_name}: {chance}%")
    # Empire bonus item
    if is_empire_flag and chapter in EMPIRE_STEAL_EXTRA:
        item_name, chance = EMPIRE_STEAL_EXTRA[chapter]
        lines.append(f"{item_name}: {chance}%")
    # Boss rare items
    if is_boss_flag and chapter in BOSS_STEAL_ITEMS:
        for item_name, chance in BOSS_STEAL_ITEMS[chapter]:
            lines.append(f"{item_name}: {chance}%")
    return lines

def build_note(break_shields, passive_states, aggro, name, icon, desc,
               ai_style, ai_level, steal_lines):
    """Build the complete note string."""
    parts = []
    # Passive states
    for ps in passive_states:
        parts.append(f"<Passive State: {ps}>")
    # Break shields
    if break_shields is not None:
        parts.append(f"<Break Shields: {break_shields}>")
    # Aggro
    parts.append(f"<Aggro: +{aggro}>")
    # Aspect
    parts.append(f"<Aspect Name: {name}>")
    parts.append(f"<Aspect Icon: {icon}>")
    parts.append("<Aspect Description>")
    parts.append(desc)
    parts.append("</Aspect Description>")
    # AI
    if ai_style:
        parts.append(f"<AI Style: {ai_style}>")
        parts.append(f"<AI Level: {ai_level}>")
    # Steal
    if steal_lines:
        parts.append("<Steal>")
        parts.extend(steal_lines)
        parts.append("</Steal>")
    return "\n".join(parts) + "\n"

# ============================================================
# MAIN
# ============================================================

enemies = read_json('Enemies.json')
changes = 0
skipped = 0

for i, enemy in enumerate(enemies):
    if enemy is None:
        continue
    eid = enemy['id']
    name = enemy.get('name', '')

    # Skip separators
    if eid in SEPARATOR_IDS or name.startswith('----'):
        continue

    # Skip training dummy and templates
    if eid in SKIP_IDS:
        skipped += 1
        continue

    # Skip enemies beyond ID 91 (empty placeholders)
    if eid > 91:
        continue

    chapter = get_chapter(eid)
    if chapter < 0:
        continue

    note = enemy.get('note', '')
    params = enemy.get('params', [0]*8)
    gold = enemy.get('gold', 0)

    # Extract existing tags
    bs = extract_break_shields(note)
    ps = extract_passive_states(note)
    existing_ai = extract_ai_style(note)
    existing_ai_lvl = extract_ai_level(note)

    # Determine attributes
    is_boss = is_boss_type(ps)
    is_emp = is_empire(name)
    aggro = get_aggro(params)
    ai_style, ai_level = get_ai_settings(chapter, is_boss, existing_ai, existing_ai_lvl)

    # Get description
    desc = DESCRIPTIONS.get(eid, f"{name}.")

    # Aspect icon
    icon = 3335  # default soldier icon

    # Steal table
    steal = build_steal_block(chapter, gold, is_boss, is_emp)

    # Build new note
    new_note = build_note(bs, ps, aggro, name, icon, desc,
                          ai_style, ai_level, steal)
    enemy['note'] = new_note
    changes += 1

print(f"Updated {changes} enemies (skipped {skipped} templates)")

# Write output
write_json('Enemies.json', enemies)
print(f"Enemies.json written successfully!")

# Verification: print summary of a few enemies
for check_id in [4, 25, 43, 70, 89]:
    e = enemies[check_id]
    if e:
        note_preview = e['note'][:120].replace('\n', ' | ')
        print(f"  ID {check_id} ({e['name']}): {note_preview}...")
