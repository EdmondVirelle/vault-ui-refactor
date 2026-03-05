"""
生成敵人技能(32–250)與敵人(3–91)，含分類分隔行。
覆蓋 Skills 32–250、Enemies 3–91，並更新 Enemies 8–10 動作。
修正 Skill #232 名稱 【劉琦】→【東方啟】(移至 ID 31 以外保留)。

使用方式: python scripts/generate_enemies.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'Consilience' / 'data'
SKILLS_PATH = ROOT / 'Skills.json'
ENEMIES_PATH = ROOT / 'Enemies.json'

# ═══════════════════════════════════════════════════════════════════════
# Formula Templates
# ═══════════════════════════════════════════════════════════════════════
_P = ('Math.max(1,((a.atk*2.2-b.def*0.9)+(a.mat*0.4-b.mdf*0.2))'
      '*(1+(a.agi-b.agi)/100)+a.luk/(b.luk+1))*(a.hp/a.mhp+0.5)*{p}')
_M = ('Math.max(1,((a.mat*2.2-b.mdf*0.9)+(a.atk*0.4-b.def*0.2))'
      '*(1+(a.agi-b.agi)/100)+a.luk/(b.luk+1))*(a.hp/a.mhp+0.5)*{p}')
_DH = 'Math.max(1,((a.atk*2.0-b.def*0.8)+(a.mat*0.3-b.mdf*0.2))*(1+(a.agi-b.agi)/100))*{p}'
_DM = 'Math.max(1,((a.mat*2.0-b.mdf*0.8)+(a.atk*0.3-b.def*0.2))*(1+(a.agi-b.agi)/100))*{p}'
PHY = lambda p: _P.format(p=p)
MAG = lambda p: _M.format(p=p)
DRAIN_HP = lambda p: _DH.format(p=p)
DRAIN_MP = lambda p: _DM.format(p=p)

# ═══════════════════════════════════════════════════════════════════════
# Effect / Trait / Action helpers
# ═══════════════════════════════════════════════════════════════════════
def st(sid, ch=1.0):  return {'code':21,'dataId':sid,'value1':ch,'value2':0}
def bf(p, t=3):       return {'code':31,'dataId':p,'value1':t,'value2':0}
def db(p, t=3):       return {'code':32,'dataId':p,'value1':t,'value2':0}

def ew(eid, v=1.5):   return {'code':11,'dataId':eid,'value':v}
def er(eid, v=0.5):   return {'code':11,'dataId':eid,'value':v}
HR  = {'code':22,'dataId':0,'value':0.95}
EV  = {'code':22,'dataId':1,'value':0.05}
EV2 = {'code':22,'dataId':1,'value':0.12}
EV3 = {'code':22,'dataId':1,'value':0.15}
BT  = [HR, EV]                                  # base traits
BEA = BT + [ew(1,1.3)]                          # beast
IMP = BT + [ew(5,1.3)]                          # imperial
YOK = BT + [ew(15,1.5), er(14,0.5)]             # yokai
CHA = BT + [ew(16,1.5)]                         # chaos
CHI = BT + [ew(16,1.3), ew(12,1.2)]             # chimera
CON = BT + [ew(3,1.3), er(10,0.5)]              # construct

def act(sid, r=5, ct=0, p1=0, p2=0):
    return {'skillId':sid,'rating':r,'conditionType':ct,'conditionParam1':p1,'conditionParam2':p2}
A1 = act(1, 5)  # basic attack
ND = {'dataId':1,'denominator':1,'kind':0}

# State IDs (standard RPG Maker MZ):
# 1=death, 4=poison, 5=blind, 6=confusion, 7=silence, 8=sleep, 9=paralyze, 10=stun


# ═══════════════════════════════════════════════════════════════════════
# Skill Builder (compact)
# ═══════════════════════════════════════════════════════════════════════
_SKILL_DEFAULTS = dict(
    animationId=0, damage=dict(critical=False, elementId=0, formula='0', type=0, variance=8),
    description='', effects=[], hitType=0, iconIndex=0, message1='', message2='',
    mpCost=0, name='', note='', occasion=1, repeats=1, requiredWtypeId1=0,
    requiredWtypeId2=0, scope=0, speed=0, stypeId=0, successRate=100,
    tpCost=0, tpGain=0, messageType=1,
)

def S(sid, name, **kw):
    """Build a skill dict. Pass dt/formula/el/var for damage sub-fields."""
    s = {**_SKILL_DEFAULTS, 'id': sid, 'name': name}
    d = dict(s['damage'])
    for k in ('dt','formula','el','var','crit'):
        if k in kw:
            remap = {'dt':'type','el':'elementId','var':'variance','crit':'critical'}
            d[remap.get(k,k)] = kw.pop(k)
    s['damage'] = d
    s.update(kw)
    return s

def SEP(sid, label):
    """Separator skill entry."""
    return S(sid, f'----{label}----', occasion=0, successRate=0)


# ═══════════════════════════════════════════════════════════════════════
# ALL SKILLS  (32–250)
# ═══════════════════════════════════════════════════════════════════════
SKILLS = [
    # ─── 野獸技能 (32–44) ───────────────────────────────────
    SEP(32, '野獸技能'),
    S(33,'撕咬',    dt=1,formula=PHY(1.0),scope=1,hitType=1, iconIndex=3158,message1='%1 張口撕咬！'),
    S(34,'猛撲',    dt=1,formula=PHY(1.2),scope=1,hitType=1, iconIndex=3158,message1='%1 猛撲而來！',effects=[st(10,0.3)]),
    S(35,'毒牙',    dt=1,formula=PHY(0.8),scope=1,hitType=1, iconIndex=3158,message1='%1 露出毒牙！',effects=[st(4,0.5)]),
    S(36,'嚎叫',    scope=11,iconIndex=3158,message1='%1 發出震耳嚎叫！',effects=[bf(2,3)]),
    S(37,'亂爪',    dt=1,formula=PHY(0.6),scope=4,hitType=1, iconIndex=3158,message1='%1 亂爪揮出！'),
    S(38,'吞噬',    dt=5,formula=DRAIN_HP(1.3),scope=1,hitType=1, iconIndex=3158,message1='%1 張口吞噬！'),
    S(39,'暴怒衝撞', dt=1,formula=PHY(1.8),scope=2,hitType=1, iconIndex=3158,message1='%1 暴怒衝撞！',note='<OTB User Next Turn: +3>'),
    S(40,'毒霧彈',   dt=1,formula=MAG(0.7),scope=2,hitType=2, iconIndex=3170,message1='%1 噴出毒霧！',effects=[st(4,0.3)]),
    S(41,'蛛絲纏繞', dt=1,formula=MAG(0.5),scope=1,hitType=2, iconIndex=3170,message1='%1 吐出蛛絲！',effects=[st(9,0.5)]),
    S(42,'石化凝視', dt=1,formula=MAG(0.5),scope=1,hitType=2, iconIndex=3172,message1='%1 睜開石化之眼！',effects=[st(9,0.7)]),
    S(43,'寄生蟲巢', dt=5,formula=DRAIN_HP(1.0),scope=1,hitType=2, iconIndex=3170,message1='%1 放出寄生蟲！',effects=[st(4,0.5)]),
    S(44,'狂暴化',   scope=11,iconIndex=3158,message1='%1 進入狂暴狀態！',effects=[bf(2,5),db(3,5)]),

    # ─── 帝國技能 (45–58) ───────────────────────────────────
    SEP(45, '帝國技能'),
    S(46,'帝國軍刀',   dt=1,formula=PHY(1.0),el=2,scope=1,hitType=1, iconIndex=3155,message1='%1 揮出帝國軍刀！'),
    S(47,'十字斬',     dt=1,formula=PHY(1.3),el=1,scope=1,hitType=1, iconIndex=3154,message1='%1 使出十字斬！'),
    S(48,'聖光療癒',   dt=3,formula='a.mat*2+50',scope=11,iconIndex=3435,message1='%1 施展聖光療癒！'),
    S(49,'盾擊',       dt=1,formula=PHY(0.8),scope=1,hitType=1, iconIndex=3155,message1='%1 以盾猛擊！',effects=[st(10,0.4)]),
    S(50,'帝國連斬',   dt=1,formula=PHY(0.5),scope=5,hitType=1, iconIndex=3155,message1='%1 使出帝國連斬！'),
    S(51,'理式砲擊',   dt=1,formula=MAG(1.5),scope=2,hitType=2, iconIndex=3166,message1='%1 發射理式砲擊！'),
    S(52,'機關弩射',   dt=1,formula=PHY(0.7),el=8,scope=4,hitType=1, iconIndex=3164,message1='%1 機關弩齊射！'),
    S(53,'瑪那聚焦',   dt=1,formula=MAG(2.0),scope=1,hitType=2, iconIndex=3166,message1='%1 將瑪那聚焦！',note='<OTB User Next Turn: +2>'),
    S(54,'理式結界',   scope=11,iconIndex=3166,message1='%1 展開理式結界！',effects=[bf(3,3),bf(5,3)]),
    S(55,'帝國號令',   scope=13,iconIndex=3335,message1='%1 下達帝國號令！',effects=[bf(2,3)]),
    S(56,'帝國軍陣',   scope=13,iconIndex=3335,message1='%1 布下帝國軍陣！',effects=[bf(3,3),bf(5,3)]),
    S(57,'理式分析',   scope=1,iconIndex=3166,message1='%1 啟動理式分析！',effects=[db(2,3),db(3,3),db(4,3),db(5,3)]),
    S(58,'機關砲連射', dt=1,formula=PHY(0.4),scope=6,hitType=1, iconIndex=3164,message1='%1 發動機關砲連射！'),

    # ─── 妖邪技能 (59–75) ───────────────────────────────────
    SEP(59, '妖邪技能'),
    S(60,'陰氣爪擊',  dt=1,formula=MAG(1.0),el=14,scope=1,hitType=2, iconIndex=3172,message1='%1 揮出陰氣之爪！'),
    S(61,'魂吸',      dt=6,formula=DRAIN_MP(1.2),scope=1,hitType=2, iconIndex=3172,message1='%1 吸取魂魄！'),
    S(62,'詛咒之眼',  dt=1,formula=MAG(0.8),scope=1,hitType=2, iconIndex=3172,message1='%1 瞪出詛咒之眼！',effects=[db(2,3),db(4,3)]),
    S(63,'妖霧',      dt=1,formula=MAG(0.7),scope=2,hitType=2, iconIndex=3172,message1='%1 噴出妖霧！',effects=[st(4,0.3)]),
    S(64,'冥火',      dt=1,formula=MAG(1.5),el=14,scope=1,hitType=2, iconIndex=3172,message1='%1 召喚冥火！'),
    S(65,'怨靈附身',  dt=1,formula=MAG(0.6),scope=1,hitType=2, iconIndex=3172,message1='%1 驅使怨靈附身！',effects=[st(6,0.5)]),
    S(66,'萬蠱噬心',  dt=1,formula=MAG(1.8),el=13,scope=1,hitType=2, iconIndex=3170,message1='%1 放出萬蠱噬心！',effects=[st(4,0.6)]),
    S(67,'血海翻騰',  dt=1,formula=MAG(1.5),scope=2,hitType=2, iconIndex=3172,message1='%1 掀起血海翻騰！'),
    S(68,'腐蝕之息',  dt=1,formula=MAG(1.0),scope=2,hitType=2, iconIndex=3172,message1='%1 噴出腐蝕之息！',effects=[db(3,3)]),
    S(69,'亡者之歌',  dt=1,formula=MAG(0.5),scope=2,hitType=2, iconIndex=3172,message1='%1 吟唱亡者之歌！',effects=[st(8,0.4)]),
    S(70,'噬魂幡',    dt=5,formula=DRAIN_HP(1.5),scope=1,hitType=2, iconIndex=3172,message1='%1 揮動噬魂幡！'),
    S(71,'冥界召喚',  scope=11,iconIndex=3172,message1='%1 呼喚冥界之力！',effects=[bf(2,3),bf(4,3)]),
    S(72,'萬鬼夜行',  dt=1,formula=MAG(1.2),scope=2,hitType=2, iconIndex=3172,message1='%1 召喚萬鬼夜行！',effects=[st(4,0.2),st(6,0.2),st(8,0.2)]),
    S(73,'九幽冥咒',  dt=1,formula=MAG(2.0),scope=1,hitType=2, iconIndex=3172,message1='%1 施展九幽冥咒！',effects=[st(4,0.8)]),
    S(74,'業火焚身',  dt=1,formula=MAG(2.0),el=14,scope=2,hitType=2, iconIndex=3172,message1='%1 引動業火焚身！'),
    S(75,'厲鬼纏身',  dt=1,formula=MAG(1.0),scope=1,hitType=2, iconIndex=3172,message1='%1 召來厲鬼纏身！',effects=[db(4,3),db(5,3)]),

    # ─── 混沌技能 (76–88) ───────────────────────────────────
    SEP(76, '混沌技能'),
    S(77,'混沌吐息',  dt=1,formula=MAG(2.5),el=16,scope=2,hitType=2, iconIndex=3022,message1='%1 噴出混沌吐息！'),
    S(78,'四兇共鳴',  scope=11,iconIndex=3022,message1='%1 引發四兇共鳴！',effects=[bf(2,3),bf(4,3),bf(6,3)]),
    S(79,'次元裂隙',  dt=1,formula=MAG(3.0),scope=1,hitType=2, iconIndex=3022,message1='%1 撕裂次元！',note='<OTB User Next Turn: +4>'),
    S(80,'理式崩壞',  dt=1,formula=MAG(1.5),scope=2,hitType=2, iconIndex=3022,message1='%1 引發理式崩壞！',effects=[st(7,0.4)]),
    S(81,'奇美拉融合',dt=3,formula='a.mhp*0.25',scope=11,iconIndex=3022,message1='%1 啟動奇美拉融合！'),
    S(82,'虛空侵蝕',  dt=1,formula=MAG(1.2),scope=2,hitType=2, iconIndex=3022,message1='%1 釋放虛空侵蝕！',effects=[db(2,3),db(3,3),db(6,3)]),
    S(83,'不可名狀',  dt=1,formula=MAG(4.0),scope=1,hitType=2, iconIndex=3022,message1='%1 施展不可名狀之力！',note='<OTB User Next Turn: +6>'),
    S(84,'封印瓦解',  scope=1,iconIndex=3022,message1='%1 使封印瓦解！',effects=[db(2,5),db(3,5),db(4,5),db(5,5)]),
    S(85,'混沌脈動',  dt=1,formula=MAG(1.5),scope=2,hitType=2, iconIndex=3022,message1='%1 引動混沌脈動！',effects=[st(6,0.3)]),
    S(86,'虛空吞噬',  dt=5,formula=DRAIN_HP(1.5),scope=2,hitType=2, iconIndex=3022,message1='%1 發動虛空吞噬！'),
    S(87,'法則扭曲',  scope=2,hitType=2,iconIndex=3022,message1='%1 扭曲法則！',effects=[db(2,3),db(3,3),db(4,3),db(5,3),db(6,3)]),
    S(88,'次元崩塌',  dt=1,formula=MAG(2.0),scope=2,hitType=2, iconIndex=3022,message1='%1 引發次元崩塌！',effects=[st(10,0.3)]),

    # ─── 通用敵技 (89–103) ──────────────────────────────────
    SEP(89, '通用敵技'),
    S(90,'自爆',     dt=1,formula='Math.max(1,(a.hp*0.8+a.atk*2)*2.0)',scope=2,hitType=1, iconIndex=3158,message1='%1 引爆自身！',effects=[st(1,1.0)]),
    S(91,'集結號令', scope=13,iconIndex=3335,message1='%1 發出集結號令！',effects=[bf(3,3)]),
    S(92,'堅守',     scope=11,iconIndex=3344,message1='%1 擺出堅守之態！',effects=[bf(3,5),bf(5,5)]),
    S(93,'治療術',   dt=3,formula='a.mat*2+30',scope=12,iconIndex=3435,message1='%1 施展治療術！'),
    S(94,'全體治療', dt=3,formula='a.mat*1.5+20',scope=13,iconIndex=3435,message1='%1 施展全體治療！'),
    S(95,'挑釁',     scope=1,iconIndex=3158,message1='%1 發出挑釁！',effects=[st(10,0.2)]),
    S(96,'掩護',     scope=11,iconIndex=3344,message1='%1 擺出掩護姿態！',effects=[bf(3,3)]),
    S(97,'強化防禦', scope=13,iconIndex=3344,message1='%1 強化防禦！',effects=[bf(3,3)]),
    S(98,'強化攻擊', scope=13,iconIndex=3405,message1='%1 強化攻擊！',effects=[bf(2,3)]),
    S(99,'破甲術',   dt=1,formula=PHY(0.5),scope=1,hitType=1, iconIndex=3155,message1='%1 使出破甲術！',effects=[db(3,5)]),
    S(100,'封技術',  dt=1,formula=MAG(0.5),scope=1,hitType=2, iconIndex=3166,message1='%1 施展封技術！',effects=[st(7,0.6)]),
    S(101,'散功術',  dt=6,formula=DRAIN_MP(2.0),scope=1,hitType=2, iconIndex=3166,message1='%1 施展散功術！'),
    S(102,'蓄力',    scope=11,iconIndex=3158,message1='%1 開始蓄力！',effects=[bf(2,2)],note='<OTB User Next Turn: +3>'),
    S(103,'反擊姿態',scope=11,iconIndex=3344,message1='%1 擺出反擊姿態！',effects=[bf(3,2),bf(6,2)]),

    # ─── 奇美拉技能 (104–116) ───────────────────────────────
    SEP(104, '奇美拉技能'),
    S(105,'石偶拳',     dt=1,formula=PHY(1.5),scope=1,hitType=1, iconIndex=3158,message1='%1 揮出石偶拳！'),
    S(106,'活體撕裂',   dt=1,formula=PHY(2.0),scope=1,hitType=1, iconIndex=3158,message1='%1 撕裂活體！'),
    S(107,'氣瑪那融合波',dt=1,formula=MAG(2.0),el=16,scope=2,hitType=2, iconIndex=3022,message1='%1 釋放氣瑪那融合波！'),
    S(108,'奇美拉突進', dt=1,formula=PHY(2.5),scope=1,hitType=1, iconIndex=3158,message1='%1 發動奇美拉突進！',note='<OTB User Next Turn: +2>'),
    S(109,'不穩定爆發', dt=1,formula=MAG(1.5),scope=2,hitType=2, iconIndex=3022,message1='%1 產生不穩定爆發！',effects=[st(6,0.2)]),
    S(110,'形態變異',   dt=3,formula='a.mhp*0.15',scope=11,iconIndex=3022,message1='%1 發生形態變異！',effects=[bf(2,3),bf(6,3)]),
    S(111,'融合吸收',   dt=5,formula=DRAIN_HP(2.0),scope=1,hitType=1, iconIndex=3158,message1='%1 發動融合吸收！'),
    S(112,'異種再生',   dt=3,formula='a.mhp*0.30',scope=11,iconIndex=3022,message1='%1 啟動異種再生！'),
    S(113,'奇美拉嘶嚎', scope=2,hitType=2,iconIndex=3022,message1='%1 發出奇美拉嘶嚎！',effects=[db(2,3),db(6,3)]),
    S(114,'基因崩壞',   dt=1,formula=PHY(2.0),scope=2,hitType=1, iconIndex=3022,message1='%1 引發基因崩壞！',effects=[db(3,3)]),
    S(115,'奇美拉覺醒', scope=11,iconIndex=3022,message1='%1 啟動奇美拉覺醒！',effects=[bf(2,3),bf(4,3),bf(6,3)]),
    S(116,'終極融合體', dt=1,formula=MAG(3.5),scope=1,hitType=2, iconIndex=3022,message1='%1 化為終極融合體攻擊！'),

    # ─── 帝國精銳技 (117–130) ───────────────────────────────
    SEP(117, '帝國精銳技'),
    S(118,'鐘塔共振',   dt=1,formula=MAG(1.5),scope=2,hitType=2, iconIndex=3166,message1='%1 引發鐘塔共振！',effects=[st(7,0.3)]),
    S(119,'理式解構',   dt=1,formula=MAG(1.5),scope=1,hitType=2, iconIndex=3166,message1='%1 啟動理式解構！',effects=[db(3,5),db(5,5)]),
    S(120,'光柱制裁',   dt=1,formula=MAG(2.0),el=15,scope=2,hitType=2, iconIndex=3166,message1='%1 降下光柱制裁！'),
    S(121,'帝國重砲',   dt=1,formula=PHY(3.0),scope=1,hitType=1, iconIndex=3164,message1='%1 發射帝國重砲！',note='<OTB User Next Turn: +4>'),
    S(122,'鐵幕防線',   scope=11,iconIndex=3344,message1='%1 展開鐵幕防線！',effects=[bf(3,5),bf(5,5)]),
    S(123,'殲滅指令',   dt=1,formula=PHY(2.5),scope=2,hitType=1, iconIndex=3335,message1='%1 下達殲滅指令！'),
    S(124,'帝國終焉',   dt=1,formula=MAG(4.0),scope=1,hitType=2, iconIndex=3166,message1='%1 施展帝國終焉！',note='<OTB User Next Turn: +6>'),
    S(125,'瑪那轉譯',   dt=1,formula=MAG(2.0),scope=2,hitType=2, iconIndex=3166,message1='%1 啟動瑪那轉譯！',effects=[db(5,3)]),
    S(126,'理式牢籠',   dt=1,formula=MAG(0.8),scope=1,hitType=2, iconIndex=3166,message1='%1 構築理式牢籠！',effects=[st(9,0.6)]),
    S(127,'機關要塞',   scope=13,iconIndex=3344,message1='%1 啟動機關要塞！',effects=[bf(3,5),bf(5,5)]),
    S(128,'帝國戰歌',   scope=13,iconIndex=3335,message1='%1 高唱帝國戰歌！',effects=[bf(2,3),bf(6,3)]),
    S(129,'理式滅殺',   dt=1,formula=MAG(3.0),scope=2,hitType=2, iconIndex=3166,message1='%1 發動理式滅殺！'),
    S(130,'帝國禁術',   dt=1,formula=MAG(5.0),scope=1,hitType=2, iconIndex=3166,message1='%1 動用帝國禁術！',note='<OTB User Next Turn: +8>'),

    # ─── Boss特殊技 (131–146) ───────────────────────────────
    SEP(131, 'Boss特殊技'),
    S(132,'領域展開',   scope=11,iconIndex=3022,message1='%1 展開領域！',effects=[bf(2,5),bf(3,5),bf(4,5),bf(5,5),bf(6,5)]),
    S(133,'天威降臨',   dt=1,formula=MAG(3.0),scope=2,hitType=2, iconIndex=3022,message1='%1 降下天威！',effects=[db(2,3),db(3,3)]),
    S(134,'殺意凝聚',   scope=11,iconIndex=3158,message1='%1 凝聚殺意！',effects=[bf(2,5)]),
    S(135,'怒意爆發',   dt=1,formula=PHY(2.5),scope=2,hitType=1, iconIndex=3158,message1='%1 爆發怒意！'),
    S(136,'致命連擊',   dt=1,formula=PHY(1.5),scope=5,hitType=1, iconIndex=3158,message1='%1 發動致命連擊！'),
    S(137,'全屬性壓制', scope=2,hitType=2,iconIndex=3022,message1='%1 釋放全屬性壓制！',effects=[db(2,3),db(3,3),db(4,3),db(5,3),db(6,3)]),
    S(138,'不死再生',   dt=3,formula='a.mhp*0.50',scope=11,iconIndex=3022,message1='%1 啟動不死再生！'),
    S(139,'吸收屏障',   scope=11,iconIndex=3022,message1='%1 展開吸收屏障！',effects=[bf(3,5),bf(5,5)]),
    S(140,'暴走模式',   scope=11,iconIndex=3158,message1='%1 進入暴走模式！',effects=[bf(2,5),bf(6,5),db(3,5)]),
    S(141,'滅世宣言',   dt=1,formula=MAG(3.5),scope=2,hitType=2, iconIndex=3022,message1='%1 發出滅世宣言！'),
    S(142,'弱點看破',   scope=1,hitType=2,iconIndex=3166,message1='%1 看破弱點！',effects=[db(3,5),db(5,5)]),
    S(143,'最終形態',   scope=11,iconIndex=3022,message1='%1 進入最終形態！',effects=[bf(2,5),bf(3,5),bf(4,5),bf(5,5),bf(6,5),bf(7,5)]),
    S(144,'極限突破',   dt=1,formula=PHY(5.0),scope=1,hitType=1, iconIndex=3158,message1='%1 發動極限突破！',note='<OTB User Next Turn: +8>'),
    S(145,'瀕死反擊',   dt=1,formula=PHY(3.0),scope=2,hitType=1, iconIndex=3158,message1='%1 瀕死反擊！'),
    S(146,'狂氣釋放',   dt=1,formula=MAG(2.5),scope=2,hitType=2, iconIndex=3022,message1='%1 釋放狂氣！',effects=[st(6,0.3)]),

    # ─── 四兇技能 (147–163) ─────────────────────────────────
    SEP(147, '四兇技能'),
    S(148,'饕餮吞天',   dt=5,formula=DRAIN_HP(2.0),scope=2,hitType=2, iconIndex=3022,message1='%1 發動饕餮吞天！'),
    S(149,'饕餮虹吸',   dt=6,formula=DRAIN_MP(2.0),scope=2,hitType=2, iconIndex=3022,message1='%1 發動饕餮虹吸！'),
    S(150,'饕餮飢餓波', dt=1,formula=MAG(2.5),scope=2,hitType=2, iconIndex=3022,message1='%1 釋放饕餮飢餓波！',effects=[db(2,3)]),
    S(151,'饕餮永食',   dt=5,formula=DRAIN_HP(4.0),scope=1,hitType=2, iconIndex=3022,message1='%1 施展饕餮永食！',note='<OTB User Next Turn: +5>'),
    S(152,'檮杌暴嵐',   dt=1,formula=PHY(3.0),scope=2,hitType=1, iconIndex=3022,message1='%1 掀起檮杌暴嵐！'),
    S(153,'檮杌狂嘯',   dt=1,formula=MAG(2.0),scope=2,hitType=2, iconIndex=3022,message1='%1 發出檮杌狂嘯！',effects=[st(10,0.4),st(6,0.3)]),
    S(154,'檮杌滅世爪', dt=1,formula=PHY(4.0),scope=1,hitType=1, iconIndex=3022,message1='%1 揮出檮杌滅世爪！',note='<OTB User Next Turn: +5>'),
    S(155,'檮杌怒焰',   dt=1,formula=MAG(2.5),scope=2,hitType=2, iconIndex=3022,message1='%1 噴出檮杌怒焰！'),
    S(156,'窮奇惑心',   dt=1,formula=MAG(1.5),scope=2,hitType=2, iconIndex=3022,message1='%1 施展窮奇惑心！',effects=[st(6,0.5)]),
    S(157,'窮奇逆命',   scope=1,hitType=2,iconIndex=3022,message1='%1 施展窮奇逆命！',effects=[db(2,5),db(3,5),db(4,5),db(5,5),db(6,5),db(7,5)]),
    S(158,'窮奇善惡顛', dt=1,formula=MAG(2.5),scope=2,hitType=2, iconIndex=3022,message1='%1 顛倒善惡！',effects=[st(6,0.4)]),
    S(159,'窮奇混淆',   dt=1,formula=MAG(1.0),scope=2,hitType=2, iconIndex=3022,message1='%1 施展窮奇混淆！',effects=[st(5,0.3),st(6,0.3),st(8,0.3)]),
    S(160,'混沌初始',   dt=3,formula='a.mhp*0.30',scope=11,iconIndex=3022,message1='%1 回歸混沌初始！',effects=[bf(2,3),bf(4,3)]),
    S(161,'混沌歸零',   scope=2,hitType=2,iconIndex=3022,message1='%1 令萬物歸零！',effects=[db(2,5),db(3,5),db(4,5),db(5,5)]),
    S(162,'混沌終局',   dt=1,formula=MAG(4.0),el=16,scope=2,hitType=2, iconIndex=3022,message1='%1 引發混沌終局！'),

    # ─── 終極技能 (163–174) ─────────────────────────────────
    SEP(163, '終極技能'),
    S(164,'四兇怒嘯',   dt=1,formula=MAG(3.0),scope=2,hitType=2, iconIndex=3022,message1='%1 發出四兇怒嘯！',effects=[db(2,3),db(6,3)]),
    S(165,'四兇合鳴',   scope=11,iconIndex=3022,message1='%1 引動四兇合鳴！',effects=[bf(2,5),bf(3,5),bf(4,5),bf(6,5)]),
    S(166,'封印侵蝕',   dt=1,formula=MAG(2.5),scope=2,hitType=2, iconIndex=3022,message1='%1 侵蝕封印！',effects=[st(7,0.4)]),
    S(167,'靈脈崩潰',   dt=1,formula=MAG(3.5),scope=2,hitType=2, iconIndex=3022,message1='%1 引發靈脈崩潰！'),
    S(168,'萬法歸寂',   dt=1,formula=MAG(3.0),el=16,scope=2,hitType=2, iconIndex=3022,message1='%1 施展萬法歸寂！',effects=[db(2,3),db(4,3)]),
    S(169,'一念之滅',   dt=1,formula=MAG(5.0),scope=1,hitType=2, iconIndex=3022,message1='%1 以一念滅之！',note='<OTB User Next Turn: +8>'),
    S(170,'天地同歸',   dt=1,formula=MAG(4.0),scope=2,hitType=2, iconIndex=3022,message1='%1 施展天地同歸！',effects=[st(1,0.5)]),
    S(171,'世界終焉',   dt=1,formula=MAG(5.0),scope=2,hitType=2, iconIndex=3022,message1='%1 帶來世界終焉！'),
    S(172,'虛空終焉',   dt=1,formula=MAG(6.0),scope=1,hitType=2, iconIndex=3022,message1='%1 施展虛空終焉！',note='<OTB User Next Turn: +10>'),
    S(173,'不可名狀・真',dt=1,formula=MAG(5.0),el=16,scope=2,hitType=2, iconIndex=3022,message1='%1 展現不可名狀的真實！',effects=[st(6,0.3),st(7,0.3)]),
    S(174,'存在抹消',   dt=1,formula=MAG(6.0),scope=1,hitType=2, iconIndex=3022,message1='%1 抹消存在！'),

    # ─── 環境陷阱技 (175–189) ───────────────────────────────
    SEP(175, '環境陷阱技'),
    S(176,'落石',       dt=1,formula=PHY(1.0),scope=2,hitType=1, iconIndex=3156,message1='岩石崩落！'),
    S(177,'毒沼',       dt=1,formula=MAG(0.5),scope=2,hitType=2, iconIndex=3170,message1='毒沼噴發！',effects=[st(4,0.5)]),
    S(178,'沙暴',       dt=1,formula=MAG(1.0),scope=2,hitType=2, iconIndex=3165,message1='沙暴席捲！',effects=[st(5,0.3)]),
    S(179,'雷擊',       dt=1,formula=MAG(2.5),scope=3,hitType=2, iconIndex=3166,message1='雷電劈下！'),
    S(180,'冰封',       dt=1,formula=MAG(1.0),scope=1,hitType=2, iconIndex=3166,message1='寒冰封鎖！',effects=[st(9,0.5)]),
    S(181,'地裂',       dt=1,formula=PHY(1.5),scope=2,hitType=1, iconIndex=3156,message1='大地裂開！'),
    S(182,'火牆',       dt=1,formula=MAG(1.5),scope=2,hitType=2, iconIndex=3166,message1='火牆升起！'),
    S(183,'靈壓',       dt=1,formula=MAG(1.0),scope=2,hitType=2, iconIndex=3172,message1='強大靈壓降臨！',effects=[db(5,3)]),
    S(184,'瘴氣',       dt=1,formula=MAG(0.8),scope=2,hitType=2, iconIndex=3170,message1='瘴氣瀰漫！',effects=[st(4,0.2),st(5,0.2)]),
    S(185,'地脈噴發',   dt=1,formula=MAG(2.5),scope=2,hitType=2, iconIndex=3166,message1='地脈噴發！'),
    S(186,'封印反噬',   dt=1,formula=MAG(2.0),scope=2,hitType=2, iconIndex=3022,message1='封印反噬！',effects=[st(7,0.3)]),
    S(187,'結界崩壞',   dt=1,formula=MAG(1.5),scope=2,hitType=2, iconIndex=3022,message1='結界崩壞！',effects=[db(3,3),db(5,3)]),
    S(188,'天劫降臨',   dt=1,formula=MAG(4.0),scope=3,hitType=2, iconIndex=3022,message1='天劫降臨！'),
    S(189,'靈脈枯竭',   dt=6,formula=DRAIN_MP(1.5),scope=2,hitType=2, iconIndex=3022,message1='靈脈枯竭！'),

    # ─── 地域技能 (190–207) ─────────────────────────────────
    SEP(190, '地域技能'),
    S(191,'黃沙斬',     dt=1,formula=PHY(1.2),scope=1,hitType=1, iconIndex=3155,message1='%1 使出黃沙斬！'),
    S(192,'沙暴掩襲',   dt=1,formula=PHY(1.0),scope=2,hitType=1, iconIndex=3165,message1='%1 發動沙暴掩襲！',effects=[st(5,0.3)]),
    S(193,'黃沙護體',   scope=11,iconIndex=3344,message1='%1 以黃沙護體！',effects=[bf(3,3)]),
    S(194,'烈日灼燒',   dt=1,formula=MAG(1.5),scope=2,hitType=2, iconIndex=3166,message1='%1 引動烈日灼燒！'),
    S(195,'沙漠葬禮',   dt=1,formula=MAG(2.5),scope=1,hitType=2, iconIndex=3165,message1='%1 發動沙漠葬禮！',effects=[st(10,0.4)]),
    S(196,'寒冰劍氣',   dt=1,formula=MAG(1.5),scope=1,hitType=2, iconIndex=3154,message1='%1 揮出寒冰劍氣！'),
    S(197,'仙池凍結',   dt=1,formula=MAG(1.0),scope=2,hitType=2, iconIndex=3166,message1='%1 施展仙池凍結！',effects=[st(9,0.3)]),
    S(198,'寒霜護體',   scope=11,iconIndex=3344,message1='%1 以寒霜護體！',effects=[bf(3,3),bf(5,3)]),
    S(199,'冰刃連斬',   dt=1,formula=PHY(0.7),scope=5,hitType=1, iconIndex=3154,message1='%1 施展冰刃連斬！'),
    S(200,'陰山毒霧',   dt=1,formula=MAG(1.0),scope=2,hitType=2, iconIndex=3170,message1='%1 噴出陰山毒霧！',effects=[st(4,0.5)]),
    S(201,'饕餮之息',   dt=1,formula=MAG(1.5),scope=2,hitType=2, iconIndex=3022,message1='%1 噴出饕餮之息！',effects=[db(2,3)]),
    S(202,'枯木纏繞',   dt=1,formula=MAG(0.5),scope=1,hitType=2, iconIndex=3170,message1='%1 以枯木纏繞！',effects=[st(9,0.5)]),
    S(203,'鬼修邪功',   dt=1,formula=MAG(2.0),el=14,scope=1,hitType=2, iconIndex=3172,message1='%1 施展鬼修邪功！'),
    S(204,'鐘塔結界',   scope=11,iconIndex=3166,message1='%1 展開鐘塔結界！',effects=[bf(3,5),bf(5,5)]),
    S(205,'理式掃描',   scope=1,hitType=2,iconIndex=3166,message1='%1 啟動理式掃描！',effects=[db(3,3),db(5,3)]),
    S(206,'禁忌注入',   dt=1,formula=MAG(2.5),scope=1,hitType=2, iconIndex=3022,message1='%1 進行禁忌注入！',effects=[st(4,0.3),st(6,0.3)]),
    S(207,'鐘塔轟鳴',   dt=1,formula=MAG(2.0),scope=2,hitType=2, iconIndex=3166,message1='鐘塔轟鳴響徹！',effects=[st(10,0.3)]),

    # ─── 預留空間 (208–250) ─────────────────────────────────
    SEP(208, '預留空間'),
]


# ═══════════════════════════════════════════════════════════════════════
# ENEMIES  (3–91, with chapter separators)
# ═══════════════════════════════════════════════════════════════════════

def E(eid, name, *, hp, mp=0, atk, df, mat, mdf, agi, luk,
      exp, gold, battler, actions, traits, shields=2,
      drops=None, note_extra='', ps=None):
    note_parts = []
    if ps:
        for p in ps: note_parts.append(f'<Passive State: {p}>')
    note_parts.append(f'<Break Shields: {shields}>')
    if note_extra: note_parts.append(note_extra)
    return {
        'id':eid,'actions':actions,'battlerHue':0,'battlerName':battler,
        'dropItems':drops or [ND,ND,ND],'exp':exp,'traits':traits,
        'gold':gold,'name':name,'note':'\n'.join(note_parts),
        'params':[hp,mp,atk,df,mat,mdf,agi,luk],
    }

def ESEP(eid, label):
    return {
        'id':eid,'actions':[],'battlerHue':0,'battlerName':'',
        'dropItems':[ND,ND,ND],'exp':0,'traits':[],'gold':0,
        'name':f'----{label}----','note':'','params':[1,0,1,1,1,1,1,1],
    }

ENEMIES = [
    # ═══ 序章・黃裳典籍 ═══
    ESEP(3, '序章・黃裳典籍'),
    E(4,'野狼',hp=120,atk=14,df=8,mat=5,mdf=5,agi=12,luk=6,
      exp=25,gold=30,battler='Werewolf',shields=1,
      actions=[A1,act(33,5),act(34,3)],traits=BEA),
    E(5,'毒蛇',hp=80,atk=12,df=5,mat=8,mdf=6,agi=16,luk=8,
      exp=22,gold=25,battler='敵人_蛇',shields=1,
      actions=[A1,act(35,5)],traits=BEA+[ew(3,1.3)]),
    E(6,'山賊',hp=150,mp=20,atk=16,df=10,mat=6,mdf=6,agi=10,luk=8,
      exp=30,gold=50,battler='Rogue',shields=2,
      actions=[A1,act(46,4)],traits=BT+[ew(1,1.2)]),
    E(7,'帝國巡邏兵',hp=180,mp=30,atk=15,df=14,mat=8,mdf=8,agi=10,luk=5,
      exp=35,gold=45,battler='Soldier',shields=2,
      actions=[A1,act(46,5),act(49,2,1,2,2)],traits=IMP,ps=[502,503]),
    # 8-11 existing (updated actions below)
    E(12,'帝國弓手',hp=130,mp=25,atk=18,df=8,mat=10,mdf=6,agi=14,luk=7,
      exp=32,gold=40,battler='Rogue',shields=2,
      actions=[A1,act(52,5)],traits=IMP+[ew(5,1.5)]),
    E(13,'遺跡石偶',hp=250,atk=18,df=22,mat=5,mdf=12,agi=5,luk=3,
      exp=50,gold=35,battler='Stoneknight',shields=3,
      actions=[A1,act(33,5),act(39,2,2,50,100)],traits=CON),
    E(14,'黃裳冤魂',hp=200,mp=50,atk=8,df=6,mat=18,mdf=14,agi=12,luk=10,
      exp=45,gold=40,battler='Ghost',shields=2,
      actions=[act(60,5),act(63,3),act(65,2,2,50,100)],traits=YOK),
    E(15,'帝國哨兵隊長',hp=350,mp=60,atk=20,df=18,mat=12,mdf=10,agi=14,luk=8,
      exp=80,gold=80,battler='Captain',shields=3,
      actions=[A1,act(46,5),act(47,3),act(55,2,1,1,3)],traits=IMP,ps=[502,503]),
    E(16,'遺跡守衛機關',hp=300,atk=22,df=25,mat=8,mdf=10,agi=6,luk=3,
      exp=65,gold=50,battler='Puppet',shields=3,
      actions=[A1,act(39,4),act(90,1,2,25,0)],traits=CON),

    # ═══ 第一章・劃月風雲 ═══
    ESEP(17, '第一章・劃月風雲'),
    E(18,'劫道匪',hp=180,mp=20,atk=18,df=12,mat=6,mdf=6,agi=14,luk=10,
      exp=55,gold=65,battler='Orc',shields=2,
      actions=[A1,act(46,4),act(44,2,2,40,0)],traits=BT+[ew(1,1.2)]),
    E(19,'帝國密探',hp=200,mp=40,atk=16,df=10,mat=14,mdf=10,agi=22,luk=12,
      exp=65,gold=70,battler='Assassin',shields=2,
      actions=[A1,act(52,5),act(49,3)],traits=IMP+[EV2]),
    E(20,'打手',hp=220,mp=15,atk=22,df=14,mat=6,mdf=6,agi=12,luk=6,
      exp=60,gold=55,battler='Orc',shields=2,
      actions=[A1,act(33,5),act(39,2,2,40,0)],traits=BT+[ew(5,1.3)]),
    E(21,'門派叛徒',hp=250,mp=50,atk=20,df=15,mat=18,mdf=12,agi=16,luk=10,
      exp=80,gold=80,battler='Swordsman',shields=2,
      actions=[A1,act(47,5),act(60,3),act(54,2,2,60,0)],traits=BT+[ew(15,1.2)]),
    E(22,'暗殺者',hp=170,mp=30,atk=24,df=8,mat=10,mdf=8,agi=28,luk=15,
      exp=75,gold=75,battler='黑空洞_刺客',shields=2,
      actions=[A1,act(52,5),act(34,3)],traits=BT+[EV3,ew(3,1.3)]),
    E(23,'帝國精銳兵',hp=300,mp=50,atk=22,df=20,mat=12,mdf=12,agi=14,luk=8,
      exp=100,gold=100,battler='General_m',shields=3,
      actions=[A1,act(46,5),act(47,3),act(50,2)],traits=IMP,ps=[502,503]),
    E(24,'帝國騎士',hp=400,mp=40,atk=24,df=28,mat=10,mdf=14,agi=10,luk=6,
      exp=120,gold=120,battler='Irongiant',shields=3,
      actions=[A1,act(47,5),act(49,4),act(92,2,2,40,0)],traits=IMP+[ew(3,1.4)],ps=[502]),
    E(25,'劃月邪徒',hp=500,mp=80,atk=25,df=18,mat=22,mdf=16,agi=20,luk=12,
      exp=150,gold=150,battler='Swordsman',shields=3,
      actions=[A1,act(47,5),act(64,4),act(67,2,2,50,0)],traits=BT+[ew(15,1.3),ew(1,1.2)]),

    # ═══ 第二章・西域來風 ═══
    ESEP(26, '第二章・西域來風'),
    E(27,'沙漠毒蠍',hp=250,mp=10,atk=24,df=22,mat=12,mdf=10,agi=18,luk=10,
      exp=110,gold=90,battler='Scorpion',shields=2,
      actions=[A1,act(35,5),act(34,3)],traits=BEA+[ew(3,1.3)]),
    E(28,'黃沙狼群',hp=200,atk=22,df=14,mat=8,mdf=8,agi=24,luk=12,
      exp=105,gold=80,battler='Werewolf',shields=2,
      actions=[A1,act(33,5),act(37,3),act(36,2)],traits=BEA),
    E(29,'帝國沙漠兵',hp=300,mp=40,atk=24,df=20,mat=14,mdf=12,agi=14,luk=8,
      exp=130,gold=110,battler='Soldier',shields=2,
      actions=[A1,act(46,5),act(50,3),act(55,2,1,1,3)],traits=IMP,ps=[502,503]),
    E(30,'沙暴精',hp=350,mp=80,atk=10,df=12,mat=28,mdf=20,agi=20,luk=14,
      exp=150,gold=100,battler='敵人_風精',shields=2,
      actions=[act(63,5),act(60,4),act(68,2)],traits=YOK+[ew(3,1.2)]),
    E(31,'西域商隊護衛',hp=320,mp=30,atk=26,df=22,mat=10,mdf=12,agi=16,luk=10,
      exp=140,gold=130,battler='Sailor',shields=2,
      actions=[A1,act(47,5),act(92,2,2,50,0)],traits=BT+[ew(10,1.3)]),
    E(32,'檮杌獸影',hp=280,mp=50,atk=20,df=14,mat=26,mdf=18,agi=22,luk=16,
      exp=180,gold=120,battler='Demon_metamorphosis',shields=3,
      actions=[act(60,5),act(77,2,2,40,0),act(62,3)],traits=CHA+[ew(15,1.3)]),
    E(33,'黑市殺手',hp=250,mp=35,atk=28,df=14,mat=12,mdf=10,agi=28,luk=18,
      exp=160,gold=150,battler='Assassin',shields=2,
      actions=[A1,act(52,5),act(34,3)],traits=BT+[EV3,ew(3,1.3)]),
    E(34,'沙漠巨蟲',hp=600,atk=30,df=28,mat=10,mdf=14,agi=8,luk=6,
      exp=250,gold=200,battler='Hydra',shields=4,
      actions=[A1,act(38,5),act(39,4),act(35,3)],traits=BEA+[ew(1,1.4)]),

    # ═══ 第三章・仙池寒劍 ═══
    ESEP(35, '第三章・仙池寒劍'),
    E(36,'仙池弟子',hp=300,mp=60,atk=28,df=20,mat=22,mdf=18,agi=22,luk=12,
      exp=200,gold=160,battler='敵人_仙池劍派_女弟子',shields=2,
      actions=[A1,act(47,5),act(54,2,2,50,0)],traits=BT+[ew(5,1.2)]),
    E(37,'寒冰精',hp=280,mp=90,atk=8,df=14,mat=32,mdf=28,agi=18,luk=14,
      exp=210,gold=150,battler='Waterspirit',shields=2,
      actions=[act(196,5),act(197,4),act(67,2,1,1,3)],traits=YOK+[er(14,0.3)]),
    E(38,'變異水獸',hp=350,mp=20,atk=30,df=24,mat=18,mdf=14,agi=16,luk=10,
      exp=220,gold=170,battler='Sahuagin',shields=2,
      actions=[A1,act(33,5),act(38,3),act(36,2)],traits=BEA+[ew(8,1.3)]),
    E(39,'受蠱弟子',hp=320,mp=55,atk=26,df=18,mat=24,mdf=16,agi=20,luk=10,
      exp=230,gold=180,battler='Fanatic',shields=2,
      actions=[A1,act(47,4),act(65,3),act(44,2,2,40,0)],traits=BT+[ew(12,1.3)]),
    E(40,'冰霜巨熊',hp=450,atk=35,df=30,mat=10,mdf=16,agi=10,luk=8,
      exp=280,gold=200,battler='Ogre',shields=3,
      actions=[A1,act(34,5),act(39,3),act(36,2,2,50,0)],traits=BEA+[ew(5,1.4)]),
    E(41,'窮奇幻象',hp=400,mp=100,atk=12,df=16,mat=34,mdf=28,agi=24,luk=18,
      exp=320,gold=220,battler='Gazer',shields=3,
      actions=[act(62,5),act(65,4),act(82,2,2,40,0)],traits=CHA+[ew(15,1.4)]),
    E(42,'仙池護法',hp=500,mp=80,atk=32,df=28,mat=28,mdf=24,agi=22,luk=14,
      exp=400,gold=300,battler='General_f',shields=3,
      actions=[A1,act(47,5),act(54,3),act(51,2,1,1,3)],traits=BT+[ew(5,1.2),ew(15,1.2)]),
    E(43,'初代奇美拉',hp=800,mp=50,atk=36,df=30,mat=32,mdf=22,agi=18,luk=12,
      exp=500,gold=400,battler='Chimera',shields=4,
      actions=[A1,act(105,5),act(108,4),act(81,2,2,30,0),act(109,1,2,25,0)],traits=CHI,ps=[102]),

    # ═══ 第四章・逍遙雲霧 ═══
    ESEP(44, '第四章・逍遙雲霧'),
    E(45,'帝國掘探隊',hp=350,mp=40,atk=30,df=24,mat=16,mdf=14,agi=16,luk=8,
      exp=280,gold=220,battler='SF_Specialforces',shields=2,
      actions=[A1,act(46,5),act(50,3),act(52,2)],traits=IMP,ps=[502]),
    E(46,'山中妖靈',hp=300,mp=100,atk=10,df=12,mat=36,mdf=28,agi=22,luk=16,
      exp=300,gold=200,battler='Fairy',shields=2,
      actions=[act(60,5),act(63,4),act(69,2)],traits=YOK),
    E(47,'靈脈獸',hp=380,mp=30,atk=34,df=26,mat=22,mdf=18,agi=20,luk=12,
      exp=310,gold=230,battler='Cerberus',shields=3,
      actions=[A1,act(34,5),act(38,3),act(36,2,1,1,3)],traits=BEA+[ew(16,1.3)]),
    E(48,'帝國工程兵',hp=320,mp=50,atk=26,df=28,mat=20,mdf=18,agi=12,luk=8,
      exp=270,gold=250,battler='SF_Workrobot',shields=3,
      actions=[A1,act(51,5),act(54,3),act(92,2,2,50,0)],traits=IMP+[ew(3,1.3)]),
    E(49,'鬼面猿',hp=280,mp=10,atk=32,df=16,mat=14,mdf=10,agi=32,luk=18,
      exp=260,gold=200,battler='Imp',shields=2,
      actions=[A1,act(37,5),act(34,4),act(36,2)],traits=BEA+[EV2]),
    E(50,'巨型蜈蚣',hp=420,mp=20,atk=34,df=30,mat=16,mdf=12,agi=14,luk=8,
      exp=320,gold=240,battler='Lamia',shields=3,
      actions=[A1,act(35,5),act(66,3),act(39,2,2,40,0)],traits=BEA+[ew(8,1.3)]),
    E(51,'帝國煉金術士',hp=400,mp=120,atk=14,df=18,mat=38,mdf=30,agi=16,luk=14,
      exp=350,gold=300,battler='Mage',shields=2,
      actions=[act(51,5),act(53,4),act(48,3,2,50,0)],traits=IMP+[ew(5,1.4)]),
    E(52,'靈脈守護者',hp=700,mp=120,atk=28,df=26,mat=40,mdf=32,agi=24,luk=18,
      exp=500,gold=400,battler='Earthspirit',shields=4,
      actions=[act(67,5),act(64,4),act(78,2,2,40,0),act(68,3)],traits=YOK+[ew(16,1.3)],ps=[102]),

    # ═══ 第五章・梅莊庇護 ═══
    ESEP(53, '第五章・梅莊庇護'),
    E(54,'帝國重甲兵',hp=500,mp=30,atk=36,df=42,mat=10,mdf=20,agi=8,luk=6,
      exp=380,gold=300,battler='Irongiant',shields=4,
      actions=[A1,act(47,5),act(49,4),act(92,3,2,50,0)],traits=IMP+[ew(3,1.5)],ps=[502]),
    E(55,'陰帥小卒',hp=400,mp=100,atk=18,df=20,mat=40,mdf=32,agi=24,luk=16,
      exp=400,gold=280,battler='Death',shields=3,
      actions=[act(60,5),act(64,4),act(61,3),act(69,2,1,1,3)],traits=YOK+[er(14,0.3)]),
    E(56,'亡魂',hp=300,mp=60,atk=12,df=10,mat=36,mdf=24,agi=20,luk=18,
      exp=350,gold=250,battler='Ghost',shields=2,
      actions=[act(61,5),act(65,4),act(63,3)],traits=YOK),
    E(57,'奇美拉二代',hp=600,mp=80,atk=40,df=32,mat=38,mdf=26,agi=22,luk=14,
      exp=500,gold=400,battler='Chimera',shields=4,
      actions=[A1,act(106,5),act(107,4),act(112,3,2,35,0),act(109,2,2,25,0)],traits=CHI,ps=[102]),
    E(58,'帝國審判官',hp=450,mp=80,atk=22,df=24,mat=42,mdf=34,agi=18,luk=14,
      exp=420,gold=350,battler='Fanatic',shields=3,
      actions=[act(51,5),act(53,4),act(80,3,1,1,3),act(48,2,2,40,0)],traits=IMP+[ew(14,1.3)]),
    E(59,'黑袍教士',hp=380,mp=110,atk=14,df=16,mat=44,mdf=36,agi=16,luk=16,
      exp=400,gold=320,battler='Mage',shields=2,
      actions=[act(64,5),act(48,4),act(67,2,1,1,3)],traits=IMP+[ew(5,1.4),ew(14,1.2)]),
    E(60,'機械傀儡',hp=500,atk=42,df=38,mat=20,mdf=16,agi=14,luk=4,
      exp=380,gold=350,battler='Puppet',shields=4,
      actions=[A1,act(39,5),act(50,4),act(90,1,2,20,0)],traits=CON),
    E(61,'甘珠爾守衛',hp=800,mp=150,atk=30,df=28,mat=48,mdf=38,agi=24,luk=20,
      exp=650,gold=500,battler='Angel',shields=4,
      actions=[act(67,5),act(64,4),act(78,3,2,40,0),act(48,2,2,30,0)],traits=YOK+[er(14,0.3),ew(16,1.4)],ps=[102]),

    # ═══ 第六章・陰山暗影 ═══
    ESEP(62, '第六章・陰山暗影'),
    E(63,'枯木妖',hp=400,mp=60,atk=20,df=22,mat=42,mdf=30,agi=14,luk=12,
      exp=480,gold=350,battler='Plant',shields=3,
      actions=[act(63,5),act(66,4),act(202,3)],traits=YOK+[ew(2,1.3)]),
    E(64,'饕餮獸僕',hp=500,mp=40,atk=48,df=34,mat=22,mdf=18,agi=20,luk=10,
      exp=520,gold=380,battler='Behemoth',shields=3,
      actions=[A1,act(38,5),act(34,4),act(44,2,2,40,0)],traits=CHA+[ew(1,1.3)]),
    E(65,'毒林蟲群',hp=350,mp=20,atk=28,df=18,mat=32,mdf=16,agi=26,luk=14,
      exp=460,gold=300,battler='Hornet',shields=2,
      actions=[act(35,5),act(66,4),act(37,3)],traits=BEA+[ew(6,1.3)]),
    E(66,'帝國暗部',hp=450,mp=50,atk=44,df=28,mat=20,mdf=18,agi=36,luk=22,
      exp=550,gold=450,battler='黑空洞_刺客',shields=3,
      actions=[A1,act(52,5),act(50,4),act(49,3)],traits=IMP+[EV3]),
    E(67,'戾神碎片',hp=550,mp=120,atk=18,df=24,mat=50,mdf=38,agi=28,luk=22,
      exp=600,gold=400,battler='Plasma',shields=3,
      actions=[act(77,5),act(82,4),act(80,3),act(62,2)],traits=CHA+[er(14,0.5),er(15,0.8)]),
    E(68,'變異門徒',hp=480,mp=70,atk=40,df=26,mat=36,mdf=22,agi=22,luk=12,
      exp=500,gold=380,battler='Skeleton',shields=3,
      actions=[A1,act(66,5),act(44,3),act(67,2,2,40,0)],traits=BT+[ew(12,1.4),ew(15,1.2)]),
    E(69,'陰山鬼修',hp=520,mp=100,atk=22,df=24,mat=48,mdf=36,agi=24,luk=18,
      exp=560,gold=420,battler='Vampire',shields=3,
      actions=[act(203,5),act(61,4),act(65,3),act(69,2,1,1,3)],traits=YOK+[er(14,0.3)]),
    E(70,'戾神化身',hp=1200,mp=200,atk=32,df=32,mat=55,mdf=42,agi=30,luk=24,
      exp=800,gold=600,battler='Darklord',shields=5,
      actions=[act(77,5),act(82,4),act(67,4),act(78,3,2,50,0),act(80,2,2,30,0)],
      traits=CHA+[er(14,0.5)],ps=[102]),

    # ═══ 第七章・鐘塔審判 ═══
    ESEP(71, '第七章・鐘塔審判'),
    E(72,'鐘塔守衛',hp=550,mp=60,atk=46,df=38,mat=28,mdf=26,agi=22,luk=14,
      exp=600,gold=480,battler='SF_Specialforces',shields=3,
      actions=[A1,act(46,5),act(50,4),act(49,3),act(55,2,1,1,3)],traits=IMP,ps=[502,503]),
    E(73,'奇美拉三代',hp=700,mp=100,atk=50,df=36,mat=48,mdf=32,agi=28,luk=16,
      exp=700,gold=550,battler='Chimera',shields=4,
      actions=[A1,act(108,5),act(107,4),act(112,3,2,35,0),act(111,3)],traits=CHI+[er(14,0.5)],ps=[102]),
    E(74,'理式構裝體',hp=600,mp=80,atk=44,df=48,mat=36,mdf=30,agi=16,luk=8,
      exp=620,gold=500,battler='SF_Workrobot',shields=4,
      actions=[A1,act(51,5),act(54,3),act(90,1,2,15,0)],traits=CON+[ew(5,1.4)]),
    E(75,'帝國鐘塔研究員',hp=400,mp=150,atk=18,df=20,mat=52,mdf=40,agi=18,luk=18,
      exp=580,gold=500,battler='SF_Madscientist',shields=2,
      actions=[act(51,5),act(53,4),act(118,3),act(48,2,2,40,0)],traits=IMP+[ew(5,1.5)]),
    E(76,'禁忌實驗體',hp=650,mp=60,atk=52,df=34,mat=44,mdf=28,agi=24,luk=12,
      exp=650,gold=520,battler='Hi_monster',shields=4,
      actions=[A1,act(111,5),act(109,4),act(112,3,2,30,0),act(115,2,2,30,0)],traits=CHI+[ew(12,1.3)]),
    E(77,'虛空裂隙獸',hp=750,mp=100,atk=30,df=28,mat=54,mdf=38,agi=30,luk=20,
      exp=700,gold=550,battler='SF_Demon_of_universe',shields=4,
      actions=[act(77,5),act(79,4),act(82,3),act(88,2,1,1,3)],traits=CHA+[er(14,0.5),er(15,0.8)]),
    E(78,'帝國司令官',hp=800,mp=100,atk=52,df=42,mat=36,mdf=32,agi=26,luk=18,
      exp=800,gold=650,battler='General_m',shields=4,
      actions=[A1,act(47,5),act(55,4),act(123,3),act(122,2,2,40,0)],traits=IMP+[ew(5,1.2)],ps=[502,503]),
    E(79,'不可名狀幼體',hp=1000,mp=150,atk=36,df=30,mat=56,mdf=42,agi=32,luk=24,
      exp=1000,gold=700,battler='Gazer',shields=5,
      actions=[act(83,5),act(82,4),act(77,4),act(78,3,2,40,0),act(84,2,2,25,0)],
      traits=CHA+[er(14,0.3),er(15,0.5)],ps=[102]),

    # ═══ 第八章・萬法同歸 ═══
    ESEP(80, '第八章・萬法同歸'),
    E(81,'混沌殘影',hp=600,mp=80,atk=40,df=30,mat=50,mdf=36,agi=30,luk=20,
      exp=750,gold=550,battler='Plasma',shields=3,
      actions=[act(77,5),act(82,4),act(88,3)],traits=CHA),
    E(82,'饕餮化身',hp=2000,mp=200,atk=60,df=48,mat=50,mdf=40,agi=28,luk=22,
      exp=1500,gold=1000,battler='Behemoth',shields=5,
      actions=[A1,act(148,5),act(150,4),act(151,3,2,40,0),act(78,2,2,30,0),act(140,1,2,25,0)],
      traits=CHA+[ew(1,1.3),er(13,0.5)],ps=[102],
      note_extra='<AI Style: Gambit>\n<AI Level: 100>'),
    E(83,'檮杌化身',hp=2000,mp=180,atk=68,df=42,mat=40,mdf=34,agi=36,luk=20,
      exp=1500,gold=1000,battler='Minotaur',shields=5,
      actions=[A1,act(152,5),act(154,4),act(153,3),act(78,2,2,40,0)],
      traits=CHA+[ew(6,1.3),er(5,0.5)],ps=[102],
      note_extra='<AI Style: Gambit>\n<AI Level: 100>'),
    E(84,'窮奇化身',hp=2000,mp=250,atk=34,df=38,mat=65,mdf=48,agi=32,luk=28,
      exp=1500,gold=1000,battler='Cerberus',shields=5,
      actions=[act(156,5),act(158,4),act(157,3),act(159,3),act(78,2,2,40,0)],
      traits=CHA+[ew(15,1.4),er(14,0.3)],ps=[102],
      note_extra='<AI Style: Gambit>\n<AI Level: 100>'),
    E(85,'帝國終極兵器',hp=1500,mp=100,atk=65,df=60,mat=55,mdf=45,agi=20,luk=10,
      exp=1200,gold=800,battler='SF_Workrobot',shields=5,
      actions=[A1,act(123,5),act(124,4),act(122,3,2,30,0),act(127,2,2,40,0),act(90,1,2,15,0)],
      traits=CON+[ew(5,1.4)],ps=[102]),
    E(86,'四兇融合體',hp=3000,mp=300,atk=62,df=52,mat=68,mdf=50,agi=34,luk=28,
      exp=2000,gold=1500,battler='Darklord_Final',shields=6,
      actions=[act(162,5),act(164,4),act(79,4),act(165,3,2,35,0),act(160,1,2,20,0)],
      traits=CHA+[er(14,0.5),er(15,0.5)],ps=[102],
      note_extra='<AI Style: Gambit>\n<AI Level: 100>'),
    E(87,'混沌核心',hp=1000,mp=200,atk=20,df=55,mat=45,mdf=55,agi=10,luk=30,
      exp=900,gold=600,battler='Firespirit',shields=5,
      actions=[act(92,5),act(67,4),act(88,3),act(78,2,2,50,0)],traits=CHA+[er(14,0.3),er(15,0.3)]),
    E(88,'虛空巨靈',hp=800,mp=120,atk=48,df=36,mat=55,mdf=40,agi=32,luk=22,
      exp=850,gold=650,battler='Dragon',shields=4,
      actions=[act(77,5),act(79,4),act(67,3),act(84,2)],traits=CHA),
    E(89,'不可名狀之物',hp=5000,mp=500,atk=55,df=55,mat=80,mdf=65,agi=38,luk=50,
      exp=3000,gold=2000,battler='God',shields=6,
      actions=[
          act(173,5),act(172,5),act(171,4),act(174,4),
          act(168,3),act(161,3),act(143,2,2,30,0),act(138,1,2,20,0)],
      traits=CHA+[er(1,0.5),er(2,0.5),er(3,0.5),er(14,0.3),er(15,0.3)],ps=[102],
      note_extra='<AI Style: Gambit>\n<AI Level: 100>'),
    E(90,'理式崩壞體',hp=700,mp=100,atk=46,df=36,mat=52,mdf=38,agi=26,luk=18,
      exp=800,gold=580,battler='Lich',shields=3,
      actions=[act(80,5),act(51,4),act(68,3),act(84,2)],traits=BT+[ew(16,1.5),ew(5,1.3)]),
    E(91,'混沌侵蝕者',hp=650,mp=90,atk=42,df=30,mat=48,mdf=34,agi=28,luk=20,
      exp=780,gold=560,battler='Succubus',shields=3,
      actions=[act(77,5),act(61,4),act(66,3),act(82,2)],traits=CHA+[ew(15,1.3)]),
]


# ═══════════════════════════════════════════════════════════════════════
# Existing enemy action updates (8, 9, 10)
# ═══════════════════════════════════════════════════════════════════════
ENEMY_ACTION_UPDATES = {
    8: [A1, act(47, 5), act(121, 3, 2, 50, 0)],    # 武裝兵將領 → 十字斬 + 帝國重砲
    9: [A1, act(33, 5), act(35, 3)],                 # 耳鼠 → 撕咬 + 毒牙
    10: [act(73, 5), act(74, 4), act(67, 3), act(70, 2, 2, 40, 0)],  # 書中判官 → 九幽冥咒 + 業火
}


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════
def main():
    with open(SKILLS_PATH, 'r', encoding='utf-8') as f:
        skills = json.load(f)
    with open(ENEMIES_PATH, 'r', encoding='utf-8') as f:
        enemies = json.load(f)

    print(f'Loaded {len(skills)} skills, {len(enemies)} enemies')

    # ── Patch skills 32–250 ──
    patched_skills = 0
    skill_map = {s['id']: s for s in SKILLS}
    for sid in range(32, 251):
        if sid in skill_map:
            skills[sid] = skill_map[sid]
            patched_skills += 1
        else:
            # Fill remaining with empty reserved slots
            skills[sid] = S(sid, '', occasion=0, successRate=0)
    print(f'[OK] Patched {patched_skills} skills (32–250, incl. separators + reserved)')

    # ── Restore original player skills in reserved 208–250 range ──
    import subprocess
    git_result = subprocess.run(
        ['git', 'show', 'HEAD:Consilience/data/Skills.json'],
        capture_output=True, check=True, cwd=str(ROOT.parent.parent))
    original_skills = json.loads(git_result.stdout.decode('utf-8'))
    restored = 0
    for sid in range(208, 251):
        orig = original_skills[sid] if sid < len(original_skills) else None
        if orig and orig.get('name', ''):
            skills[sid] = orig
            restored += 1
    # Fix Skill #232 name 【劉琦】→【東方啟】
    if skills[232] and skills[232].get('name'):
        skills[232]['name'] = '\u3010\u6771\u65b9\u555f\u3011'
    print(f'[OK] Restored {restored} original skills in 208\u2013250, fixed skill 232 name')

    # ── Patch enemies 3–91 ──
    patched_enemies = 0
    enemy_map = {e['id']: e for e in ENEMIES}
    for eid in range(3, 92):
        if eid in enemy_map:
            while len(enemies) <= eid:
                enemies.append(None)
            enemies[eid] = enemy_map[eid]
            patched_enemies += 1
        elif eid not in (8, 9, 10, 11):
            # Only clear non-existing-enemy slots
            while len(enemies) <= eid:
                enemies.append(None)
            if enemies[eid] is None or enemies[eid].get('name', '') == '':
                pass  # already empty
    print(f'[OK] Patched {patched_enemies} enemies (3–91, incl. separators)')

    # ── Update existing enemies 8, 9, 10 actions ──
    for eid, new_actions in ENEMY_ACTION_UPDATES.items():
        if enemies[eid]:
            enemies[eid]['actions'] = new_actions
            print(f'[OK] Updated enemy {eid} ({enemies[eid]["name"]}) actions')

    # ── Write back ──
    with open(SKILLS_PATH, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(skills, f, ensure_ascii=False, indent=None, separators=(',', ':'))
    print(f'[OK] Written {SKILLS_PATH.name}')

    with open(ENEMIES_PATH, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(enemies, f, ensure_ascii=False, indent=None, separators=(',', ':'))
    print(f'[OK] Written {ENEMIES_PATH.name}')

    # Summary
    seps_s = sum(1 for s in SKILLS if '----' in s['name'])
    real_s = len(SKILLS) - seps_s
    seps_e = sum(1 for e in ENEMIES if '----' in e['name'])
    real_e = len(ENEMIES) - seps_e
    print(f'\n=== Summary ===')
    print(f'Skills: {real_s} real + {seps_s} separators = {len(SKILLS)} entries (IDs 32–207)')
    print(f'Reserved empty: IDs 209–250')
    print(f'Enemies: {real_e} real + {seps_e} separators = {len(ENEMIES)} entries (IDs 3–91)')
    print(f'Existing enemies updated: {list(ENEMY_ACTION_UPDATES.keys())}')
    print('Done!')


if __name__ == '__main__':
    main()
