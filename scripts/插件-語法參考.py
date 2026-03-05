"""
Enhanced VisuStella MZ Reference Compiler
==========================================
Generates an annotated syntax reference with:
  1. Chinese purpose annotations (用途註解)
  2. Database tab / event page locations (資料庫分頁 / 事件頁位置)
  3. Usage situation descriptions (使用時機)

Input:  scripts/plugin_extracts/*.txt
Output: consilience-writer/references/visustella-notetags.md
"""
import os
import re

EXTRACTS_DIR = r"C:\Consilience\scripts\plugin_extracts"
OUTPUT_FILE = r"C:\Consilience\consilience-writer\references\visustella-notetags.md"

# ─── Plugin registry ───────────────────────────────────────────────────────
PLUGIN_INFO = {
    # Tier 0
    'VisuMZ_0_CoreEngine.txt': ('CoreEngine', '核心引擎', '0-core'),
    # Tier 1
    'VisuMZ_1_BattleCore.txt': ('BattleCore', '戰鬥核心', '1-battle'),
    'VisuMZ_1_ElementStatusCore.txt': ('ElementStatusCore', '屬性特質核心', '1-element'),
    'VisuMZ_1_EventsMoveCore.txt': ('EventsMoveCore', '事件移動核心', '1-events'),
    'VisuMZ_1_ItemsEquipsCore.txt': ('ItemsEquipsCore', '物品裝備核心', '1-items'),
    'VisuMZ_1_MainMenuCore.txt': ('MainMenuCore', '主選單核心', '1-menu'),
    'VisuMZ_1_MessageCore.txt': ('MessageCore', '訊息核心', '1-message'),
    'VisuMZ_1_OptionsCore.txt': ('OptionsCore', '選項核心', '1-options'),
    'VisuMZ_1_SaveCore.txt': ('SaveCore', '存檔核心', '1-save'),
    'VisuMZ_1_SkillsStatesCore.txt': ('SkillsStatesCore', '技能狀態核心', '1-skills'),
    # Tier 2 - Battle
    'VisuMZ_2_AggroControlSys.txt': ('AggroControlSystem', '仇恨控制', '2-battle'),
    'VisuMZ_2_AggroControlSystem.txt': ('AggroControlSystem(alt)', '仇恨控制(替代)', '2-battle-skip'),
    'VisuMZ_2_BattleSystemATB.txt': ('BattleSystemATB', 'ATB戰鬥', '2-battle'),
    'VisuMZ_2_BattleSystemBTB.txt': ('BattleSystemBTB', 'BTB戰鬥', '2-battle'),
    'VisuMZ_2_BattleSystemCTB.txt': ('BattleSystemCTB', 'CTB戰鬥', '2-battle'),
    'VisuMZ_2_BattleSystemFTB.txt': ('BattleSystemFTB', 'FTB戰鬥', '2-battle'),
    'VisuMZ_2_BattleSystemOTB.txt': ('BattleSystemOTB', 'OTB戰鬥', '2-battle'),
    'VisuMZ_2_BattleSystemPTB.txt': ('BattleSystemPTB', 'PTB戰鬥', '2-battle'),
    'VisuMZ_2_BattleSystemSTB.txt': ('BattleSystemSTB', 'STB戰鬥', '2-battle'),
    # Tier 2 - Other
    'VisuMZ_2_BrightEffects.txt': ('BrightEffects', '明亮特效', '2-visual'),
    'VisuMZ_2_ClassChangeSystem.txt': ('ClassChangeSystem', '轉職系統', '2-system'),
    'VisuMZ_2_CommonEventMenu.txt': ('CommonEventMenu', '公共事件選單', '2-system'),
    'VisuMZ_2_DoodadsSystem.txt': ('DoodadsSystem', '裝飾物系統', '2-map'),
    'VisuMZ_2_DragonbonesUnion.txt': ('DragonbonesUnion', 'Dragonbones整合', '2-visual'),
    'VisuMZ_2_EnhancedTpSystem.txt': ('EnhancedTpSystem', '增強TP系統', '2-battle'),
    'VisuMZ_2_EquipSetBonuses.txt': ('EquipSetBonuses', '套裝獎勵', '2-items'),
    'VisuMZ_2_ExtMessageFunc.txt': ('ExtMessageFunc', '擴充訊息功能', '2-message'),
    'VisuMZ_2_HorrorEffects.txt': ('HorrorEffects', '恐怖特效', '2-visual'),
    'VisuMZ_2_ItemCraftingSys.txt': ('ItemCraftingSys', '物品合成', '2-items'),
    'VisuMZ_2_PartySystem.txt': ('PartySystem', '隊伍系統', '2-system'),
    'VisuMZ_2_QuestSystem.txt': ('QuestSystem', '任務系統', '2-system'),
    'VisuMZ_2_SkillLearnSystem.txt': ('SkillLearnSystem', '技能學習', '2-system'),
    'VisuMZ_2_VNPictureBusts.txt': ('VNPictureBusts', 'VN立繪', '2-visual'),
    'VisuMZ_2_VisualBattleEnv.txt': ('VisualBattleEnv', '戰鬥背景', '2-visual'),
    'VisuMZ_2_WeaponSwapSystem.txt': ('WeaponSwapSystem', '武器切換', '2-battle'),
    # Tier 3
    'VisuMZ_3_ActSeqCamera.txt': ('ActSeqCamera', '動作序列相機', '3-actseq'),
    'VisuMZ_3_ActSeqImpact.txt': ('ActSeqImpact', '動作序列衝擊', '3-actseq'),
    'VisuMZ_3_ActSeqProjectiles.txt': ('ActSeqProjectiles', '動作序列投射物', '3-actseq'),
    'VisuMZ_3_AntiDmgBarriers.txt': ('AntiDmgBarriers', '護盾系統', '3-battle'),
    'VisuMZ_3_AutoSkillTriggers.txt': ('AutoSkillTriggers', '自動技能觸發', '3-battle'),
    'VisuMZ_3_BattleAI.txt': ('BattleAI', '戰鬥AI', '3-battle'),
    'VisuMZ_3_BattleCmdTalk.txt': ('BattleCmdTalk', '戰鬥對話指令', '3-battle'),
    'VisuMZ_3_BoostAction.txt': ('BoostAction', '增幅行動', '3-battle'),
    'VisuMZ_3_DoodadsEditor.txt': ('DoodadsEditor', '裝飾物編輯器', '3-map'),
    'VisuMZ_3_EnemyLevels.txt': ('EnemyLevels', '敵人等級', '3-battle'),
    'VisuMZ_3_FrontviewBattleUI.txt': ('FrontviewBattleUI', '前視戰鬥UI', '3-ui'),
    'VisuMZ_3_LifeStateEffects.txt': ('LifeStateEffects', '生命狀態特效', '3-battle'),
    'VisuMZ_3_LimitedSkillUses.txt': ('LimitedSkillUses', '技能使用次數限制', '3-battle'),
    'VisuMZ_3_MessageKeywords.txt': ('MessageKeywords', '訊息關鍵字', '3-message'),
    'VisuMZ_3_MessageLog.txt': ('MessageLog', '訊息記錄', '3-message'),
    'VisuMZ_3_MsgLetterSounds.txt': ('MsgLetterSounds', '訊息字母音效', '3-message'),
    'VisuMZ_3_NewGamePlus.txt': ('NewGamePlus', '新遊戲+', '3-system'),
    'VisuMZ_3_SideviewBattleUI.txt': ('SideviewBattleUI', '側視戰鬥UI', '3-ui'),
    'VisuMZ_3_SkillCooldowns.txt': ('SkillCooldowns', '技能冷卻', '3-battle'),
    'VisuMZ_3_StateTooltips.txt': ('StateTooltips', '狀態提示', '3-ui'),
    'VisuMZ_3_StealItems.txt': ('StealItems', '偷取物品', '3-battle'),
    'VisuMZ_3_VictoryAftermath.txt': ('VictoryAftermath', '勝利結算', '3-battle'),
    'VisuMZ_3_VisualStateEffect.txt': ('VisualStateEffect', '視覺狀態特效', '3-visual'),
    'VisuMZ_3_VisualStateEffects.txt': ('VisualStateEffects', '視覺狀態特效(新)', '3-visual'),
    'VisuMZ_3_VisualTextWindows.txt': ('VisualTextWindows', '視覺文字視窗', '3-ui'),
    'VisuMZ_3_WeaknessDisplay.txt': ('WeaknessDisplay', '弱點顯示', '3-battle'),
    'VisuMZ_3_WeaponAnimation.txt': ('WeaponAnimation', '武器動畫', '3-visual'),
    # Tier 4
    'VisuMZ_4_AnimatedMapDest.txt': ('AnimatedMapDest', '動畫地圖目的地', '4-map'),
    'VisuMZ_4_AnimatedPictures.txt': ('AnimatedPictures', '動畫圖片', '4-visual'),
    'VisuMZ_4_AttachedPictures.txt': ('AttachedPictures', '附著圖片', '4-visual'),
    'VisuMZ_4_BattleCursor.txt': ('BattleCursor', '戰鬥游標', '4-ui'),
    'VisuMZ_4_BreakShields.txt': ('BreakShields', '破盾系統', '4-battle'),
    'VisuMZ_4_ButtonCmnEvts.txt': ('ButtonCmnEvts', '按鈕公共事件', '4-system'),
    'VisuMZ_4_CombatLog.txt': ('CombatLog', '戰鬥記錄', '4-battle'),
    'VisuMZ_4_ConsumeDefStates.txt': ('ConsumeDefStates', '消耗防禦狀態', '4-battle'),
    'VisuMZ_4_CreditsPage.txt': ('CreditsPage', '製作名單頁', '4-system'),
    'VisuMZ_4_DatabaseInherit.txt': ('DatabaseInherit', '資料庫繼承', '4-system'),
    'VisuMZ_4_Debugger.txt': ('Debugger', '除錯工具', '4-system'),
    'VisuMZ_4_EncounterEffects.txt': ('EncounterEffects', '遭遇特效', '4-map'),
    'VisuMZ_4_ExtraEnemyDrops.txt': ('ExtraEnemyDrops', '額外敵人掉落', '4-battle'),
    'VisuMZ_4_GabWindow.txt': ('GabWindow', '閒聊視窗', '4-message'),
    'VisuMZ_4_MenuCursor.txt': ('MenuCursor', '選單游標', '4-ui'),
    'VisuMZ_4_MessageVisibility.txt': ('MessageVisibility', '訊息可見性', '4-message'),
    'VisuMZ_4_PatchNotes.txt': ('PatchNotes', '更新日誌', '4-system'),
    'VisuMZ_4_PictureCmnEvts.txt': ('PictureCmnEvts', '圖片公共事件', '4-system'),
    'VisuMZ_4_ProximityCompass.txt': ('ProximityCompass', '近距指南針', '4-map'),
    'VisuMZ_4_SkillContainers.txt': ('SkillContainers', '技能容器', '4-battle'),
    'VisuMZ_4_VisualFogs.txt': ('VisualFogs', '視覺霧氣', '4-map'),
    'VisuMZ_4_VisualItemInv.txt': ('VisualItemInv', '視覺物品欄', '4-ui'),
    'VisuMZ_4_VisualParallaxes.txt': ('VisualParallaxes', '視覺遠景', '4-map'),
    'VisuMZ_4_WeaknessPopups.txt': ('WeaknessPopups', '弱點彈出', '4-visual'),
    'VisuMZ_4_WeaponUnleash.txt': ('WeaponUnleash', '武器連鎖', '4-battle'),
    # Tier 5
    'VisuMZ_5_TileD1.7.x.txt': ('TileD', 'TileD地圖', '5-map'),
    # Non-VisuMZ
    'MOG_Weather_EX.txt': ('MOG_Weather_EX', 'MOG天氣特效', 'mog'),
    'MOG_BattleHud.txt': ('MOG_BattleHud', 'MOG戰鬥HUD', 'mog'),
    'MOG_BattlerMotion.txt': ('MOG_BattlerMotion', 'MOG戰鬥動作', 'mog'),
    'MOG_BattleCursor.txt': ('MOG_BattleCursor', 'MOG戰鬥游標', 'mog'),
    'MOG_ActorPictureCM.txt': ('MOG_ActorPictureCM', 'MOG角色立繪', 'mog'),
    'MOG_HPGauge.txt': ('MOG_HPGauge', 'MOG血量條', 'mog'),
    'MOG_ActionName.txt': ('MOG_ActionName', 'MOG動作名稱', 'mog'),
    'MOG_ATB_Gauge.txt': ('MOG_ATB_Gauge', 'MOG ATB量條', 'mog'),
    'MOG_MenuBackground.txt': ('MOG_MenuBackground', 'MOG選單背景', 'mog'),
    'MOG_SkipWindowLog.txt': ('MOG_SkipWindowLog', 'MOG跳過視窗記錄', 'mog'),
    'Luna_MouseSystem.txt': ('Luna_MouseSystem', 'Luna滑鼠系統', 'other'),
    'DotMoveSystem.txt': ('DotMoveSystem', '點移動系統', 'other'),
    'DotMoveSystem_FunctionEx.txt': ('DotMoveSystem_FunctionEx', '點移動擴充', 'other'),
    'Public_0_Dragonbones.txt': ('Dragonbones', 'Dragonbones', 'other'),
    'TN_SpriteExtender.txt': ('TN_SpriteExtender', 'TN精靈擴充', 'other'),
}

# ─── "Used for:" → Chinese location mapping ────────────────────────────────

# Database object type → Chinese name
DB_OBJECT_ZH = {
    'Actor':          '角色',
    'Class':          '職業',
    'Skill':          '技能',
    'Item':           '物品',
    'Weapon':         '武器',
    'Armor':          '防具',
    'Enemy':          '敵人',
    'State':          '狀態',
    'Map':            '地圖屬性',
    'Tileset':        '圖塊',
    'Animation':      '動畫',
    'Event':          '事件',
    'Troop':          '敵群',
    'Common Event':   '公共事件',
}

# Location type → where in RMMZ editor
LOCATION_TYPE_ZH = {
    'Notetags':            '備註欄',
    'Notetag':             '備註欄',
    'Name Tags':           '名稱欄',
    'Name Tag':            '名稱欄',
    'Comment Tags':        '事件頁>註釋指令',
    'Comment Tag':         '事件頁>註釋指令',
    'Page Comment Tags':   '事件頁>註釋指令',
}

# Section sub-header translations
SECTION_HEADER_ZH = {
    'HP Gauge-Related': 'HP血量條相關',
    'Animation-Related': '動畫相關',
    'Battleback-Related': '戰鬥背景相關',
    'Battle Command-Related': '戰鬥指令相關',
    'JavaScript Notetag: Battle Command-Related': 'JS備註: 戰鬥指令相關',
    'Targeting-Related': '目標選擇相關',
    'JavaScript Notetag: Targeting-Related': 'JS備註: 目標選擇相關',
    'Damage-Related': '傷害相關',
    'Critical-Related': '暴擊相關',
    'JavaScript Notetags: Critical-Related': 'JS備註: 暴擊相關',
    'Life Steal-Related': '吸血相關',
    'Action Sequence-Related': '動作序列相關',
    'Animated Sideview Battler-Related': '側視動畫戰鬥者相關',
    'Enemy-Related': '敵人相關',
    'JavaScript Notetags: Mechanics-Related': 'JS備註: 機制相關',
    'Battle Layout-Related': '戰鬥佈局相關',
    'Troop Size Tags': '敵群大小標籤',
    'Troop Comment Tags': '敵群註釋標籤',
    'Element-Related': '屬性相關',
    'Trait Set-Related': '特質集相關',
    'JavaScript Notetags: Trait Set-Related': 'JS備註: 特質集相關',
    'General': '通用',
    'Equip Type-Related': '裝備類型相關',
    'JavaScript Notetags: Equipment': 'JS備註: 裝備相關',
    'Status Window-Related': '狀態視窗相關',
    'Parameter-Related': '能力值相關',
    'Provoke-Related': '挑釁相關',
    'Taunt-Related': '嘲諷相關',
    'Aggro-Related': '仇恨相關',
    'JavaScript Notetags: Aggro-Related': 'JS備註: 仇恨相關',
    'Skill Cost-Related': '技能消耗相關',
    'Skill Type-Related': '技能類型相關',
    'Skill Access-Related': '技能可用性相關',
    'State-Related': '狀態相關',
    'State Category-Related': '狀態類別相關',
    'State Turn-Related': '狀態回合相關',
    'Passive State-Related': '被動狀態相關',
}

# Stop keywords that end useful content
STOP_KEYWORDS = [
    'Introduction', 'Requirements', 'Terms of Use', 'Changelog',
    'Version History', 'End of Help', 'End of Helpfile',
    'Contact us', 'License', 'Copyright', 'Credits',
    'VisuStella MZ Compatibility', 'Major Changes',
    'Important Changes', 'Slip Damage Popup',
    'Passive State Clarification',
]

# Section type detection
NOTETAG_KW = ['Notetag', 'Note Tag']
COMMAND_KW = ['Plugin Command']
SCRIPT_KW = ['Script Call', 'Lunatic Mode', 'JavaScript']
ACTSEQ_KW = ['Action Sequence']


# ─── Parsing functions ──────────────────────────────────────────────────────

def classify_section(text):
    """Classify a section header line."""
    for kw in STOP_KEYWORDS:
        if kw in text:
            return 'stop'
    for kw in NOTETAG_KW:
        if kw in text:
            return 'notetags'
    for kw in COMMAND_KW:
        if kw in text:
            return 'plugin_commands'
    for kw in ACTSEQ_KW:
        if kw in text:
            return 'action_sequences'
    for kw in SCRIPT_KW:
        if kw in text and 'Notetag' not in text:
            return 'script_calls'
    return None


def is_separator(line):
    """Check if line is a === or --- separator."""
    s = line.strip()
    if len(s) >= 10 and all(c == '=' for c in s):
        return True
    if s.startswith('=') and s.endswith('=') and '=' * 4 in s:
        return True
    return False


def is_subsection_header(line):
    """Check if line is an === Sub-Section === header."""
    s = line.strip()
    return s.startswith('===') and s.endswith('===') and len(s) > 8


def extract_structured_sections(help_text):
    """
    Extract sections with sub-headers preserved.
    Returns dict of section_type -> list of (sub_header, entries_text) tuples.
    """
    lines = help_text.split('\n')
    sections = {
        'notetags': [],
        'plugin_commands': [],
        'script_calls': [],
        'action_sequences': [],
    }

    current_section = None
    current_sub_header = None
    current_content = []

    def flush():
        nonlocal current_content
        if current_section and current_content:
            text = '\n'.join(current_content).strip()
            if text:
                sections[current_section].append((current_sub_header, text))
        current_content = []

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        # Detect === separator line
        if is_separator(stripped):
            # Look at next non-empty line
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines):
                next_s = lines[j].strip()

                # Check if it's a stop section
                section_type = classify_section(next_s)
                if section_type == 'stop':
                    flush()
                    current_section = None
                    current_sub_header = None
                    i = j + 1
                    # Skip trailing separator
                    if i < len(lines) and is_separator(lines[i].strip()):
                        i += 1
                    continue

                # Check if it's a new section type
                if section_type:
                    flush()
                    current_section = section_type
                    current_sub_header = None
                    i = j + 1
                    if i < len(lines) and is_separator(lines[i].strip()):
                        i += 1
                    continue

                # Check if next line is a === sub-header ===
                if is_subsection_header(next_s) and current_section:
                    # This is a sub-section within current section type
                    flush()
                    # Extract sub-header name
                    sub = next_s.strip('= ').strip()
                    sub_type = classify_section(sub)
                    if sub_type and sub_type != 'stop':
                        current_section = sub_type
                    current_sub_header = sub
                    i = j + 1
                    # Skip trailing separator
                    if i < len(lines) and is_separator(lines[i].strip()):
                        i += 1
                    continue

            i += 1
            continue

        # Also detect inline === Sub-Section === headers
        if is_subsection_header(stripped) and current_section:
            sub = stripped.strip('= ').strip()
            sub_type = classify_section(sub)
            if sub_type == 'stop':
                flush()
                current_section = None
                current_sub_header = None
                i += 1
                continue
            flush()
            if sub_type and sub_type != current_section:
                current_section = sub_type
            current_sub_header = sub
            i += 1
            continue

        # Accumulate content
        if current_section:
            current_content.append(lines[i])

        i += 1

    flush()
    return sections


def parse_used_for(text):
    """
    Parse a "Used for:" line into Chinese location string.
    Returns (chinese_location, is_database, detail_str)
    """
    if not text:
        return ('', True, '')

    text = text.strip().rstrip('.')

    # Remove "Notetags" suffix for simplicity in parsing
    parts = []
    locations = []

    # Parse the object types from the "Used for:" text
    # Examples:
    #   "Actor, Class, Weapon, Armor, Enemy, State Notetags"
    #   "Enemy Notetags"
    #   "Event Notetags and Event Page Comment Tags"
    #   "Map Notetags, Troop Name Tags, and Troop Comment Tags"
    #   "Item, Weapon, Armor Notetags"
    #   "Skill, Item Notetags"

    is_database = True
    zh_parts = []

    # Check for Event-related
    if 'Event Page Comment Tag' in text or 'Event Notetag' in text:
        is_database = False

    # Check for Troop comment
    if 'Troop Page Comment' in text or 'Troop Comment' in text:
        is_database = False

    # Check for Common Event
    if 'Common Event' in text:
        is_database = False

    # Check for Map Event Page
    if 'Map Event Page' in text:
        is_database = False

    # Parse individual object types
    normalized = text
    loc_descriptions = []

    # Special case: "Class Skill Learn Notetags" - don't match generic Actor/Class/Skill
    is_class_skill_learn = 'Class Skill Learn' in normalized

    # Pattern 1: Database notetags (Actor, Class, ... Notetags)
    if not is_class_skill_learn:
        db_match = re.findall(r'(Actor|Class|Skill|Item|Weapon|Armor|Enemy|State)', normalized)
        if db_match:
            zh_objs = [DB_OBJECT_ZH.get(obj, obj) for obj in db_match]
            seen = set()
            unique = []
            for z in zh_objs:
                if z not in seen:
                    seen.add(z)
                    unique.append(z)
            loc_descriptions.append('資料庫>' + ','.join(unique) + '>備註欄')

    # Pattern 2: Map Notetags
    if 'Map Notetag' in normalized:
        loc_descriptions.append('資料庫>地圖屬性>備註欄')

    # Pattern 3: Tileset Notetags
    if 'Tileset Notetag' in normalized:
        loc_descriptions.append('資料庫>圖塊>備註欄')

    # Pattern 4: Animation Name Tags
    if 'Animation Name Tag' in normalized:
        loc_descriptions.append('資料庫>動畫>名稱欄')

    # Pattern 5: MV Animation Name Tags
    if 'MV Animation' in normalized:
        loc_descriptions.append('資料庫>動畫(MV)>名稱欄')

    # Pattern 6: Event Notetags
    if 'Event Notetag' in normalized and 'Map Event Page' not in normalized:
        loc_descriptions.append('事件編輯器>事件備註欄')

    # Pattern 7: Event Page Comment Tags
    if 'Event Page Comment' in normalized:
        loc_descriptions.append('事件頁>註釋指令')

    # Pattern 8: Troop Name Tags
    if 'Troop Name' in normalized:
        loc_descriptions.append('資料庫>敵群>名稱欄')

    # Pattern 9: Troop Comment Tags / Troop Page Comment Tags
    if 'Troop Comment' in normalized or 'Troop Page Comment' in normalized or 'Troop Page,' in normalized:
        loc_descriptions.append('敵群事件頁>註釋指令')

    # Pattern 10: Map Event Page
    if 'Map Event Page' in normalized:
        loc_descriptions.append('地圖事件頁>註釋指令')

    # Pattern 11: Common Event Page
    if 'Common Event' in normalized:
        loc_descriptions.append('公共事件>註釋指令')

    # Pattern 12: Class Skill Learn
    if 'Class Skill Learn' in normalized:
        loc_descriptions.append('資料庫>職業(技能學習用)>備註欄')

    if not loc_descriptions:
        # Fallback: just use the raw text
        loc_descriptions.append(normalized)

    # Deduplicate
    seen = set()
    unique_locs = []
    for loc in loc_descriptions:
        if loc not in seen:
            seen.add(loc)
            unique_locs.append(loc)

    return (' ＆ '.join(unique_locs), is_database, text)


def split_entries(text):
    """Split a raw section text into individual entries by --- separators."""
    entries = []
    current = []
    for line in text.split('\n'):
        stripped = line.strip()
        if stripped == '---' or (len(stripped) >= 3 and all(c == '-' for c in stripped) and len(stripped) <= 80):
            if current:
                entry = '\n'.join(current).strip()
                if entry:
                    entries.append(entry)
                current = []
        else:
            current.append(line)
    if current:
        entry = '\n'.join(current).strip()
        if entry:
            entries.append(entry)
    return entries


def extract_tag_syntax(entry_text):
    """Extract tag syntax lines from an entry."""
    tags = []
    for line in entry_text.split('\n'):
        s = line.strip()
        if not s:
            continue
        # Tag syntax lines start with < and aren't description bullets
        if s.startswith('<') and not s.startswith('- '):
            tags.append(s)
        # Some entries show format with opening/closing tags
        elif s.startswith('</') and '>' in s:
            tags.append(s)
        # Stop at description lines
        elif s.startswith('- ') or s.startswith('* '):
            break
        # Lines that are part of multi-line tag blocks
        elif tags and not s.startswith('-') and not s.startswith('*') and not s.startswith('='):
            # Could be continuation of tag area (e.g. "x" or "code" lines between tags)
            if s.startswith('<') or (len(s) < 50 and '<' not in s and '>' not in s and 'Used for' not in s):
                tags.append(s)
    return tags


def extract_used_for_line(entry_text):
    """Extract the 'Used for:' information from an entry."""
    for line in entry_text.split('\n'):
        s = line.strip()
        if s.startswith('- Used for:'):
            return s[len('- Used for:'):].strip()
    return None


def extract_description(entry_text):
    """Extract description text (lines starting with '- ' after 'Used for:')."""
    lines = entry_text.split('\n')
    desc_lines = []
    found_used_for = False
    for line in lines:
        s = line.strip()
        if s.startswith('- Used for:'):
            found_used_for = True
            continue
        if found_used_for and (s.startswith('- ') or s.startswith('  ')):
            desc_lines.append(s)
        elif found_used_for and s == '':
            continue
    return ' '.join(desc_lines).strip() if desc_lines else ''


def clean_trailing_junk(text):
    """Remove trailing license/contact/URL blocks."""
    lines = text.split('\n')
    clean = []
    for line in lines:
        s = line.strip()
        if any(kw in s for kw in [
            '=== Contact', '=== License', '=== Copyright',
            'Permission is hereby granted', 'MIT license',
            'THE SOFTWARE IS PROVIDED', 'Team VisuStella',
            '- Archeia', 'credit the following people',
        ]):
            break
        if re.match(r'^\[?(Website|Twitter|Github|Patreon|Discord)\]?\s*:?\s*https?://', s):
            continue
        clean.append(line)
    return '\n'.join(clean).strip()


# ─── Main compilation ───────────────────────────────────────────────────────

def main():
    files = sorted(os.listdir(EXTRACTS_DIR))
    files = [f for f in files if f.endswith('.txt') and not f.startswith('_')]

    print(f"Processing {len(files)} extracted help files...")

    all_plugins = []
    total_notetags = 0
    total_commands = 0
    total_scripts = 0
    total_actseq = 0

    for fname in files:
        if fname not in PLUGIN_INFO:
            continue
        info = PLUGIN_INFO[fname]
        if info[2].endswith('-skip'):
            continue

        fpath = os.path.join(EXTRACTS_DIR, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove header line
        if content.startswith('==='):
            content = '\n'.join(content.split('\n')[2:])

        sections = extract_structured_sections(content)

        # Process each section type
        processed = {
            'notetags': [],
            'plugin_commands': [],
            'script_calls': [],
            'action_sequences': [],
        }

        for sec_key in processed:
            for sub_header, raw_text in sections[sec_key]:
                cleaned = clean_trailing_junk(raw_text)
                if not cleaned:
                    continue

                entries = split_entries(cleaned)
                for entry in entries:
                    # Skip empty or very short entries
                    if len(entry.strip()) < 5:
                        continue
                    # Skip entries that are just headers or descriptions without tags
                    tag_syntax = extract_tag_syntax(entry)
                    used_for = extract_used_for_line(entry)
                    description = extract_description(entry)

                    processed[sec_key].append({
                        'sub_header': sub_header,
                        'tag_syntax': tag_syntax,
                        'used_for_raw': used_for,
                        'description': description,
                        'raw': entry.strip(),
                    })

        nt_count = len(processed['notetags'])
        cmd_count = len(processed['plugin_commands'])
        js_count = len(processed['script_calls'])
        as_count = len(processed['action_sequences'])
        total_notetags += nt_count
        total_commands += cmd_count
        total_scripts += js_count
        total_actseq += as_count

        has_content = any(processed[k] for k in processed)
        if has_content:
            all_plugins.append({
                'filename': fname,
                'name': info[0],
                'chinese': info[1],
                'category': info[2],
                'sections': processed,
                'counts': {'nt': nt_count, 'cmd': cmd_count, 'js': js_count, 'as': as_count},
            })

    print(f"Plugins with content: {len(all_plugins)}")
    print(f"Total entries - NT:{total_notetags} CMD:{total_commands} JS:{total_scripts} AS:{total_actseq}")

    # ─── Build output document ──────────────────────────────────────────
    out = []

    out.append("# VisuStella MZ 完整語法參考（含位置與用途註解）")
    out.append(f"# 萬法同歸 — {len(all_plugins)} 個插件 | NT:{total_notetags} CMD:{total_commands} JS:{total_scripts} AS:{total_actseq}")
    out.append("")
    out.append("## 使用說明")
    out.append("")
    out.append("- **NT (Notetags/備註標籤)**: 寫在資料庫各分頁的「備註」欄位中")
    out.append("- **CMD (Plugin Commands/插件指令)**: 在事件頁中選擇「插件指令」")
    out.append("- **JS (Script Calls/腳本呼叫)**: 在事件頁「腳本」指令中、或傷害公式欄使用")
    out.append("- **AS (Action Sequences/動作序列)**: 在技能/物品的公共事件中，配合BattleCore使用")
    out.append("")
    out.append("### 位置圖示說明")
    out.append("")
    out.append("| 標記 | 含義 |")
    out.append("|------|------|")
    out.append("| 📌 資料庫>角色>備註欄 | RPG Maker MZ 編輯器 → 資料庫 → 角色分頁 → 備註欄位 |")
    out.append("| 📌 資料庫>技能>備註欄 | RPG Maker MZ 編輯器 → 資料庫 → 技能分頁 → 備註欄位 |")
    out.append("| 📌 事件頁>插件指令 | RPG Maker MZ 編輯器 → 地圖事件/公共事件 → 插件指令 |")
    out.append("| 📌 事件頁>腳本 | RPG Maker MZ 編輯器 → 地圖事件/公共事件 → 腳本指令 |")
    out.append("| 📌 事件頁>註釋指令 | RPG Maker MZ 編輯器 → 事件頁 → 註釋(Comment)指令 |")
    out.append("| 📌 資料庫>敵群>名稱欄 | RPG Maker MZ 編輯器 → 資料庫 → 敵群 → 名稱欄位 |")
    out.append("| 📌 資料庫>動畫>名稱欄 | RPG Maker MZ 編輯器 → 資料庫 → 動畫 → 名稱欄位 |")
    out.append("")
    out.append("---")
    out.append("")

    # ─── Table of contents ──────────────────────────────────────────────
    out.append("## 目錄")
    out.append("")

    chapter = 0
    for plugin in all_plugins:
        chapter += 1
        c = plugin['counts']
        tags = []
        if c['nt']:  tags.append(f"NT:{c['nt']}")
        if c['cmd']: tags.append(f"CMD:{c['cmd']}")
        if c['js']:  tags.append(f"JS:{c['js']}")
        if c['as']:  tags.append(f"AS:{c['as']}")
        tag_str = ' | '.join(tags)

        anchor = plugin['name'].lower().replace('(', '').replace(')', '').replace(' ', '-')
        out.append(f"{chapter}. [{plugin['name']} ({plugin['chinese']})](#{anchor}) [{tag_str}]")

    out.append("")
    out.append("---")
    out.append("")

    # ─── Per-plugin sections ────────────────────────────────────────────
    section_labels = {
        'notetags': ('Notetags（備註標籤）', '📌 寫在資料庫備註欄'),
        'plugin_commands': ('Plugin Commands（插件指令）', '📌 位置: 事件頁 > 插件指令'),
        'script_calls': ('Script Calls（腳本呼叫）', '📌 位置: 事件頁 > 腳本指令 / 傷害公式欄 / 條件分歧腳本'),
        'action_sequences': ('Action Sequences（動作序列）', '📌 位置: 技能公共事件 / 敵群事件頁 > 配合BattleCore'),
    }
    section_order = ['notetags', 'plugin_commands', 'script_calls', 'action_sequences']

    chapter = 0
    for plugin in all_plugins:
        chapter += 1
        out.append(f"## {chapter}. {plugin['name']} ({plugin['chinese']})")
        out.append(f"> 檔案: `{plugin['filename'].replace('.txt', '.js')}`")
        out.append("")

        sub_idx = 0
        for sec_key in section_order:
            entries = plugin['sections'][sec_key]
            if not entries:
                continue

            label, default_location = section_labels[sec_key]
            sub_idx += 1
            out.append(f"### {chapter}.{sub_idx} {label}")
            out.append("")

            if sec_key != 'notetags':
                # Plugin Commands, Script Calls, Action Sequences — single location
                out.append(f"> {default_location}")
                out.append("")

            # Group entries by sub_header
            current_sub = None
            for entry in entries:
                sub = entry.get('sub_header')
                if sub and sub != current_sub:
                    current_sub = sub
                    zh_sub = SECTION_HEADER_ZH.get(sub, sub)
                    out.append(f"#### {zh_sub}")
                    out.append("")

                # For notetags: add location annotation per entry
                if sec_key == 'notetags':
                    used_for = entry.get('used_for_raw')
                    if used_for:
                        zh_loc, _, _ = parse_used_for(used_for)
                        out.append(f"> 📌 {zh_loc}")
                        out.append("")

                # Output the raw entry in a code block for syntax preservation
                out.append("```")
                out.append(entry['raw'])
                out.append("```")
                out.append("")

            out.append("")

        out.append("---")
        out.append("")

    # ─── Statistics ─────────────────────────────────────────────────────
    out.append("## 統計")
    out.append("")
    out.append(f"| 類型 | 總數 |")
    out.append(f"|------|------|")
    out.append(f"| Notetags (備註標籤) | {total_notetags} |")
    out.append(f"| Plugin Commands (插件指令) | {total_commands} |")
    out.append(f"| Script Calls (腳本呼叫) | {total_scripts} |")
    out.append(f"| Action Sequences (動作序列) | {total_actseq} |")
    out.append(f"| **總計** | **{total_notetags + total_commands + total_scripts + total_actseq}** |")
    out.append("")

    # ─── Quick Reference: Database Tab Index ────────────────────────────
    out.append("## 快速索引：依資料庫分頁")
    out.append("")
    out.append("### 角色 (Actors) 備註欄可用的 Notetags")
    out.append("搜尋 `Actor Notetag` 找到所有適用於角色備註欄的標籤。")
    out.append("")
    out.append("### 職業 (Classes) 備註欄可用的 Notetags")
    out.append("搜尋 `Class Notetag` 找到所有適用於職業備註欄的標籤。")
    out.append("")
    out.append("### 技能 (Skills) 備註欄可用的 Notetags")
    out.append("搜尋 `Skill Notetag` 找到所有適用於技能備註欄的標籤。")
    out.append("")
    out.append("### 物品 (Items) 備註欄可用的 Notetags")
    out.append("搜尋 `Item Notetag` 或 `Item,` 找到所有適用於物品備註欄的標籤。")
    out.append("")
    out.append("### 武器 (Weapons) 備註欄可用的 Notetags")
    out.append("搜尋 `Weapon Notetag` 或 `Weapon,` 找到所有適用於武器備註欄的標籤。")
    out.append("")
    out.append("### 防具 (Armors) 備註欄可用的 Notetags")
    out.append("搜尋 `Armor Notetag` 或 `Armor,` 找到所有適用於防具備註欄的標籤。")
    out.append("")
    out.append("### 敵人 (Enemies) 備註欄可用的 Notetags")
    out.append("搜尋 `Enemy Notetag` 或 `Enemy,` 找到所有適用於敵人備註欄的標籤。")
    out.append("")
    out.append("### 狀態 (States) 備註欄可用的 Notetags")
    out.append("搜尋 `State Notetag` 或 `State ` 找到所有適用於狀態備註欄的標籤。")
    out.append("")
    out.append("### 地圖屬性 (Map Properties) 備註欄可用的 Notetags")
    out.append("搜尋 `Map Notetag` 找到所有適用於地圖屬性備註欄的標籤。")
    out.append("")
    out.append("### 圖塊 (Tilesets) 備註欄可用的 Notetags")
    out.append("搜尋 `Tileset Notetag` 找到所有適用於圖塊備註欄的標籤。")
    out.append("")
    out.append("### 事件 (Events) 相關的 Notetags")
    out.append("搜尋 `Event Notetag` 找到所有適用於事件備註/註釋的標籤。")
    out.append("")
    out.append("### 敵群 (Troops) 名稱/註釋可用的 Tags")
    out.append("搜尋 `Troop Name` 或 `Troop Comment` 找到所有適用於敵群的標籤。")
    out.append("")
    out.append("### 動畫 (Animations) 名稱欄可用的 Tags")
    out.append("搜尋 `Animation Name` 找到所有適用於動畫名稱欄的標籤。")
    out.append("")

    # Write output
    final_text = '\n'.join(out)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_text)

    line_count = final_text.count('\n') + 1
    char_count = len(final_text)
    print(f"\nOutput: {OUTPUT_FILE}")
    print(f"  Lines: {line_count:,}")
    print(f"  Characters: {char_count:,}")


if __name__ == '__main__':
    main()
