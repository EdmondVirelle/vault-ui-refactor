"""
萬法同歸 — 職業生成器
Generates 23×3 = 69 class variants for Classes.json.

Each character gets three job variants:
  A (均衡): Original balanced stats
  B (攻擊特化): ATK/MAT ×1.18, DEF/MDF ×0.82, HP ×0.95  (normalized)
  C (防禦特化): DEF/MDF ×1.18, HP ×1.10, ATK/MAT ×0.82  (normalized)
"""
import json, copy, math
from pathlib import Path

DATA_DIR = Path("C:/Consilience/Consilience/data")
CLASSES_PATH = DATA_DIR / "Classes.json"
ACTORS_PATH = DATA_DIR / "Actors.json"

# ── Stat indices ──────────────────────────────────────────────────
MHP, MMP, ATK, DEF, MAT, MDF, AGI, LUK = range(8)

# ── Variant multipliers (directional, will be normalized) ────────
#           MHP   MMP   ATK   DEF   MAT   MDF   AGI   LUK
MULT_B = [0.95, 1.00, 1.18, 0.82, 1.18, 0.82, 1.00, 1.00]  # 攻擊特化
MULT_C = [1.10, 1.00, 0.82, 1.18, 0.82, 1.18, 1.00, 1.00]  # 防禦特化

# ── Actor → Class mapping (from current Actors.json) ─────────────
# Actors 24/25/26 have empty names — excluded (not playable)
# actor_id: (actor_name, current_class_id)
ACTOR_CLASS_MAP = {
    # ---東方啟---
    1:  ("東方啟", 1),
    # ---青兒---
    2:  ("青兒", 17),
    # ---湮菲花---
    3:  ("湮菲花", 2),
    # ---闕崇陽---
    4:  ("闕崇陽", 3),
    # ---絲塔娜---
    5:  ("絲塔娜", 4),
    # ---瑤琴劍---
    6:  ("瑤琴劍", 23),
    # ---沅花---
    7:  ("沅花", 13),
    # ---談笑---
    8:  ("談笑", 14),
    # ---白沫檸---
    9:  ("白沫檸", 15),
    # ---珞堇---
    10: ("珞堇", 17),
    # ---龍玉---
    11: ("龍玉", 1),
    # ---司徒長生---
    12: ("司徒長生", 8),
    # ---楊古晨---
    13: ("楊古晨", 7),
    # ---殷染幽---
    14: ("殷染幽", 5),
    # ---墨汐若---
    15: ("墨汐若", 12),
    # ---聶思泠---
    16: ("聶思泠", 10),
    # ---無名丐---
    17: ("無名丐", 9),
    # ---郭霆黃---
    18: ("郭霆黃", 11),
    # ---藍靜冥---
    19: ("藍靜冥", 6),
    # ---黃凱竹---
    20: ("黃凱竹", 1),
    # ---劉靜靜---
    21: ("劉靜靜", 25),
    # ---七霜---
    22: ("七霜", 21),
    # ---莫縈懷---
    23: ("莫縈懷", 24),
}

# ── Job names: actor_id → (職業A, 職業B, 職業C) ──────────────────
# 職業A = existing class name (preserved)
# 職業B = 攻擊特化 variant
# 職業C = 防禦特化 variant
JOB_NAMES = {
    # ---東方啟--- 劃月莊少主，劍法為主
    1:  ("劃月少主", "烈焰斬月", "明月護身"),
    # ---青兒--- 劃月山莊侍女，暗器/輕功
    2:  ("斷霞千縷", "霞影裂空", "霞光凝盾"),
    # ---湮菲花--- 醫術/點穴，內功型
    3:  ("蕙質蘭心", "蘭刺穿心", "蘭盾芳華"),
    # ---闕崇陽--- 武學宗師，速度型
    4:  ("追風逐電", "雷電破空", "風壁禦雷"),
    # ---絲塔娜--- 西域黃沙族，剛猛外功
    5:  ("黃沙天罡", "沙暴裂地", "金甲沙城"),
    # ---瑤琴劍--- 逍遙山門宗主，劍/琴
    6:  ("碧縷九霄", "九霄劍嘯", "碧雲護天"),
    # ---沅花--- 逍遙山門大師姐，筆法/花
    7:  ("百花為墨", "落花殺筆", "花甲護身"),
    # ---談笑--- 逍遙山門二弟子，劍術
    8:  ("凝霜劍癡", "霜刃穿骨", "冰魄守心"),
    # ---白沫檸--- 逍遙山門三弟子，水系
    9:  ("水木清華", "清流破浪", "華木成林"),
    # ---珞堇--- 古弦琴莊，音律
    10: ("斷霞遺韻", "弦震八方", "古韻護魂"),
    # ---龍玉--- 仙池劍派掌門，冰劍
    11: ("霜天冷徹", "冰劍寒鋒", "玄冰鐵壁"),
    # ---司徒長生--- 仙池劍派，控制/速度
    12: ("男以控制", "幻影殺機", "虛縷結界"),
    # ---楊古晨--- 仙池劍派二弟子，雷/酒
    13: ("酒吞雷震", "天雷裂岳", "雷鎧金身"),
    # ---殷染幽--- 仙池叛徒，暗殺/速度
    14: ("血海飄香", "血刃無情", "血海歸潮"),
    # ---墨汐若--- 梅莊莊主，筆墨
    15: ("花開花落", "落花飛刃", "花雨凝甲"),
    # ---聶思泠--- 南蠻族，竊盜/敏捷
    16: ("鬼靈精怪", "鬼手摘星", "靈巧避禍"),
    # ---無名丐--- 招搖撞騙，棍法
    17: ("滔天神棍", "棍掃千軍", "神棍擋關"),
    # ---郭霆黃--- 江湖豪客，霸道刀法
    18: ("霸道藍刀", "藍焰斬天", "藍鋼護體"),
    # ---藍靜冥--- 五仙教遺孤，毒/蠱
    19: ("冥音萬蠱", "冥毒噬魂", "幽蠱化盾"),
    # ---黃凱竹--- 機關/發明
    20: ("萬機編碼", "機關暴雨", "鐵甲機陣"),
    # ---劉靜靜--- 江陵名醫之女，毒/醫
    21: ("毒蕊含霜", "霜毒穿脈", "含蕊固本"),
    # ---七霜--- 陰山草堂，醫術
    22: ("翡翠生機", "翠針破穴", "翡翠回春"),
    # ---莫縈懷--- 白綾，兩儀
    23: ("影隨音鳴", "音殺無形", "音盾隱身"),
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_lv50_total(params):
    """Sum of all 8 stats at Lv50 (index 49)."""
    return sum(params[i][49] for i in range(8))


def scale_params(params, multipliers):
    """Scale param curves by directional multipliers, then normalize
    so Lv50 total matches the original (keeps variants within ±3%)."""
    # First pass: apply directional multipliers
    raw = []
    for si in range(8):
        raw.append([max(1, round(v * multipliers[si])) for v in params[si]])

    # Normalize to match original Lv50 total
    base_total = compute_lv50_total(params)
    raw_total = compute_lv50_total(raw)
    if raw_total > 0 and base_total > 0:
        norm = base_total / raw_total
        scaled = []
        for si in range(8):
            scaled.append([max(1, round(v * multipliers[si] * norm))
                           for v in params[si]])
        return scaled
    return raw


def fix_broken_class_params(params, target_total=4500):
    """Scale up anomalously low class params to reach target Lv50 total."""
    current = compute_lv50_total(params)
    if current <= 0:
        return params
    ratio = target_total / current
    return [[max(1, round(v * ratio)) for v in params[si]] for si in range(8)]


def design_placeholder_params(actor_id):
    """Design unique base stats for placeholder classes.
    Curves use diminishing returns: stat(lv) = 1 + (max-1) * sqrt((lv-1)/98).
    """
    # Lv99 stat profiles per character:
    #          MHP   MMP   ATK   DEF   MAT   MDF   AGI   LUK
    PROFILES = {
        # ---青兒--- 侍女，暗器靈巧型
        2:  [4800, 1100, 110, 100, 160, 150, 260, 230],
        # ---沅花--- 筆法/花術，內功型
        7:  [5800, 1300, 140, 130, 195, 170, 280, 250],
        # ---白沫檸--- 水系，均衡偏防
        9:  [6000, 1200, 145, 150, 160, 165, 270, 250],
        # ---珞堇--- 琴師，高內功/內防
        10: [5500, 1400, 125, 120, 200, 190, 290, 260],
        # ---聶思泠--- 盜賊，高敏/幸運
        16: [5200, 1100, 170, 110, 155, 130, 380, 370],
        # ---無名丐--- 棍法，高攻高血
        17: [6800, 900,  185, 160, 120, 135, 300, 310],
        # ---郭霆黃--- 重刀型，高攻防
        18: [7200, 850,  195, 185, 130, 145, 270, 240],
        # ---黃凱竹--- 機關師，偏內功
        20: [5600, 1200, 155, 140, 185, 165, 310, 290],
        # ---七霜--- 醫師，高內防/內力
        22: [6000, 1500, 120, 135, 190, 200, 270, 280],
    }
    profile = PROFILES.get(actor_id, [5300, 1060, 137, 137, 137, 137, 275, 275])

    params = []
    for si in range(8):
        max_val = profile[si]
        curve = []
        for lv in range(1, 101):
            if lv == 1:
                curve.append(1)
            else:
                val = 1 + (max_val - 1) * math.sqrt((lv - 1) / 98)
                curve.append(max(1, round(val)))
        params.append(curve)
    return params


def make_class_entry(name, params, traits=None, learnings=None,
                     exp_params=None, note=""):
    """Create a standard RPG Maker MZ class entry."""
    return {
        "id": 0,  # Set later
        "expParams": exp_params or [30, 20, 30, 30],
        "traits": traits or [
            {"code": 23, "dataId": 0, "value": 0}
        ],
        "learnings": learnings or [],
        "name": name,
        "note": note,
        "params": params,
    }


def main():
    classes_data = load_json(CLASSES_PATH)
    actors_data = load_json(ACTORS_PATH)

    print(f"Loaded {len(classes_data)} classes, {len(actors_data)} actors")

    # ── Categorize classes ───────────────────────────────────────
    PLACEHOLDER_IDS = {9, 10, 11, 13, 15, 16, 17, 18, 19, 20, 21}
    BROKEN_IDS = {12, 14}

    # Track shared classes
    class_users = {}
    for aid, (aname, cid) in ACTOR_CLASS_MAP.items():
        class_users.setdefault(cid, []).append(aid)
    shared_classes = {cid: aids for cid, aids in class_users.items()
                      if len(aids) > 1}
    print(f"Shared classes: { {cid: [ACTOR_CLASS_MAP[a][0] for a in aids] for cid, aids in shared_classes.items()} }")

    # ── Build variant-A base params per actor ────────────────────
    actor_base_params = {}
    actor_base_meta = {}

    for aid in sorted(ACTOR_CLASS_MAP):
        aname, cid = ACTOR_CLASS_MAP[aid]
        orig = classes_data[cid]
        orig_params = orig["params"]

        if cid in BROKEN_IDS:
            base = fix_broken_class_params(orig_params, 4500)
            tag = f"FIXED {compute_lv50_total(orig_params)}→{compute_lv50_total(base)}"
        elif cid in PLACEHOLDER_IDS:
            base = design_placeholder_params(aid)
            tag = f"DESIGNED Lv50={compute_lv50_total(base)}"
        elif cid in shared_classes:
            users = shared_classes[cid]
            if aid == users[0]:
                base = copy.deepcopy(orig_params)
                tag = f"ORIGINAL Lv50={compute_lv50_total(base)}"
            else:
                # Differentiate shared classes
                VAR = {
                    # ---龍玉--- shared classId=1 with 東方啟: more ATK/DEF, less MAT
                    11: [1.02, 0.98, 1.05, 1.03, 0.95, 1.00, 0.98, 0.99],
                    # ---黃凱竹--- shared classId=1: more MAT/MMP, less ATK
                    20: [0.95, 1.05, 0.92, 0.90, 1.10, 1.05, 1.02, 1.01],
                    # ---珞堇--- shared classId=17 with 青兒: use designed stats
                    10: None,
                }
                v = VAR.get(aid)
                if v is None:
                    # Use designed placeholder stats instead
                    base = design_placeholder_params(aid)
                    tag = f"DESIGNED (shared) Lv50={compute_lv50_total(base)}"
                else:
                    base = scale_params(orig_params, v)
                    tag = f"VARIED Lv50={compute_lv50_total(base)}"
        else:
            base = copy.deepcopy(orig_params)
            tag = f"ORIGINAL Lv50={compute_lv50_total(base)}"

        actor_base_params[aid] = base
        actor_base_meta[aid] = {
            "traits": copy.deepcopy(orig.get("traits", [])),
            "learnings": copy.deepcopy(orig.get("learnings", [])),
            "expParams": copy.deepcopy(orig.get("expParams", [30, 20, 30, 30])),
        }
        print(f"  [{aid:2d}] {aname:6s} classId={cid:2d}  {tag}")

    # ── Generate 3 variants per actor ────────────────────────────
    new_classes = [None]  # index 0 = null
    for i in range(1, len(classes_data)):
        new_classes.append(copy.deepcopy(classes_data[i]))

    next_id = len(new_classes)
    actor_class_ids = {}  # aid → [classA_id, classB_id, classC_id]

    for aid in sorted(ACTOR_CLASS_MAP):
        aname, orig_cid = ACTOR_CLASS_MAP[aid]
        base = actor_base_params[aid]
        meta = actor_base_meta[aid]
        job_a, job_b, job_c = JOB_NAMES[aid]

        # ── Variant A ────────────────────────────────────────────
        users = class_users.get(orig_cid, [])
        if len(users) > 1 and aid != users[0]:
            # Shared class — create new entry for this actor's A
            class_a_id = next_id
            entry_a = make_class_entry(
                job_a, base, meta["traits"], meta["learnings"],
                meta["expParams"])
            entry_a["id"] = class_a_id
            new_classes.append(entry_a)
            next_id += 1
        else:
            class_a_id = orig_cid
            new_classes[class_a_id]["params"] = base
            new_classes[class_a_id]["name"] = job_a
            new_classes[class_a_id]["id"] = class_a_id

        # ── Variant B (攻擊特化) ─────────────────────────────────
        class_b_id = next_id
        entry_b = make_class_entry(
            job_b, scale_params(base, MULT_B),
            meta["traits"], [], meta["expParams"])
        entry_b["id"] = class_b_id
        new_classes.append(entry_b)
        next_id += 1

        # ── Variant C (防禦特化) ─────────────────────────────────
        class_c_id = next_id
        entry_c = make_class_entry(
            job_c, scale_params(base, MULT_C),
            meta["traits"], [], meta["expParams"])
        entry_c["id"] = class_c_id
        new_classes.append(entry_c)
        next_id += 1

        actor_class_ids[aid] = [class_a_id, class_b_id, class_c_id]

    # ── Ensure all IDs correct ───────────────────────────────────
    for i in range(1, len(new_classes)):
        if new_classes[i]:
            new_classes[i]["id"] = i

    # ── Validate ─────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Generated {len(new_classes)-1} classes")
    print(f"{'='*60}")

    errors = 0
    for aid in sorted(actor_class_ids):
        aname = ACTOR_CLASS_MAP[aid][0]
        ids = actor_class_ids[aid]
        names = [new_classes[cid]["name"] for cid in ids]
        totals = [compute_lv50_total(new_classes[cid]["params"]) for cid in ids]
        avg = sum(totals) / 3
        max_dev = max(abs(t - avg) / avg * 100 for t in totals) if avg > 0 else 0
        ok = "OK" if max_dev <= 3.0 else "WARN"
        if max_dev > 3.0:
            errors += 1
        print(f"  ---{aname}---  "
              f"A={ids[0]:2d}({names[0]}) B={ids[1]:2d}({names[1]}) C={ids[2]:2d}({names[2]})")
        print(f"    Lv50: A={totals[0]} B={totals[1]} C={totals[2]}  "
              f"dev={max_dev:.2f}%  [{ok}]")

    if errors:
        print(f"\n  WARNING: {errors} actors exceed ±3%!")
    else:
        print(f"\n  All 23 actors within ±3%.")

    # ── Write mapping JSON ───────────────────────────────────────
    mapping = {}
    for aid in sorted(actor_class_ids):
        aname = ACTOR_CLASS_MAP[aid][0]
        ids = actor_class_ids[aid]
        mapping[aid] = {
            "name": aname,
            "classes": ids,
            "job_names": list(JOB_NAMES[aid]),
        }

    mapping_path = DATA_DIR / "actor_class_mapping.json"
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"\nMapping → {mapping_path}")

    # ── Write Classes.json ───────────────────────────────────────
    with open(CLASSES_PATH, "w", encoding="utf-8") as f:
        json.dump(new_classes, f, ensure_ascii=False, indent=None,
                  separators=(",", ":"))
    print(f"Classes.json → {len(new_classes)} entries")

    # ── Update Actors.json classIds ──────────────────────────────
    actors = load_json(ACTORS_PATH)
    for a in actors:
        if not a:
            continue
        aid = a["id"]
        if aid in actor_class_ids:
            a["classId"] = actor_class_ids[aid][0]
    with open(ACTORS_PATH, "w", encoding="utf-8") as f:
        json.dump(actors, f, ensure_ascii=False, indent=None,
                  separators=(",", ":"))
    print(f"Actors.json updated")

    print("\nDone!")


if __name__ == "__main__":
    main()
