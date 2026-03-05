"""
萬法同歸 — SDD 1000/100 職業生成器 (v2)
Generates 23×3 = 69 class variants for Classes.json,
conforming to SDD low-number system (HP~1000, attributes~100).

Calibration anchor:
  Lv.1 談笑 (ATK=17) vs 帝國武民 (DEF=22), power=1.0 → ~35 damage

Each character gets three job variants:
  A (均衡): Balanced base stats
  B (攻擊特化): ATK/MAT ×1.18, DEF/MDF ×0.82, HP ×0.95  (normalized)
  C (防禦特化): DEF/MDF ×1.18, HP ×1.10, ATK/MAT ×0.82  (normalized)
"""
import json, copy, math
from pathlib import Path

DATA_DIR = Path("C:/Consilience/Consilience/data")
CLASSES_PATH = DATA_DIR / "Classes.json"
ACTORS_PATH = DATA_DIR / "Actors.json"
MAPPING_PATH = DATA_DIR / "actor_class_mapping.json"

# ── Stat indices ──────────────────────────────────────────────────
MHP, MMP, ATK, DEF, MAT, MDF, AGI, LUK = range(8)
STAT_NAMES = ["MHP", "MMP", "ATK", "DEF", "MAT", "MDF", "AGI", "LUK"]

# ── Variant multipliers (directional, will be normalized) ────────
#           MHP   MMP   ATK   DEF   MAT   MDF   AGI   LUK
MULT_B = [0.95, 1.00, 1.18, 0.82, 1.18, 0.82, 1.00, 1.00]  # 攻擊特化
MULT_C = [1.10, 1.00, 0.82, 1.18, 0.82, 1.18, 1.00, 1.00]  # 防禦特化

# ── Lv1 stat ratio (fraction of Lv99) ────────────────────────────
# HP/MP use 0.17, combat stats use 0.22
LV1_RATIO = [0.17, 0.17, 0.22, 0.22, 0.22, 0.22, 0.22, 0.22]

# ── Actor data ────────────────────────────────────────────────────
ACTOR_NAMES = {
    1: "東方啟", 2: "青兒", 3: "湮菲花", 4: "闕崇陽", 5: "絲塔娜",
    6: "瑤琴劍", 7: "沅花", 8: "談笑", 9: "白沫檸", 10: "珞堇",
    11: "龍玉", 12: "司徒長生", 13: "楊古晨", 14: "殷染幽", 15: "墨汐若",
    16: "聶思泠", 17: "無名丐", 18: "郭霆黃", 19: "藍靜冥", 20: "黃凱竹",
    21: "劉靜靜", 22: "七霜", 23: "莫縈懷",
}

# Original class IDs from Actors.json (before reassignment for shared classes)
ACTOR_ORIG_CLASS = {
    1: 1, 2: 17, 3: 2, 4: 3, 5: 4, 6: 23, 7: 13, 8: 14,
    9: 15, 10: 17, 11: 1, 12: 8, 13: 7, 14: 5, 15: 12,
    16: 10, 17: 9, 18: 11, 19: 6, 20: 1, 21: 25, 22: 21, 23: 24,
}

# Class ID assignment: actor_id → [A_id, B_id, C_id]
ACTOR_CLASS_IDS = {
    1:  [1, 26, 27],   2:  [17, 28, 29],  3:  [2, 30, 31],
    4:  [3, 32, 33],   5:  [4, 34, 35],   6:  [23, 36, 37],
    7:  [13, 38, 39],  8:  [14, 40, 41],  9:  [15, 42, 43],
    10: [44, 45, 46],  11: [47, 48, 49],  12: [8, 50, 51],
    13: [7, 52, 53],   14: [5, 54, 55],   15: [12, 56, 57],
    16: [10, 58, 59],  17: [9, 60, 61],   18: [11, 62, 63],
    19: [6, 64, 65],   20: [66, 67, 68],  21: [25, 69, 70],
    22: [21, 71, 72],  23: [24, 73, 74],
}

JOB_NAMES = {
    1:  ("劃月少主", "烈焰斬月", "明月護身"),
    2:  ("斷霞千縷", "霞影裂空", "霞光凝盾"),
    3:  ("蕙質蘭心", "蘭刺穿心", "蘭盾芳華"),
    4:  ("追風逐電", "雷電破空", "風壁禦雷"),
    5:  ("黃沙天罡", "沙暴裂地", "金甲沙城"),
    6:  ("碧縷九霄", "九霄劍嘯", "碧雲護天"),
    7:  ("百花為墨", "落花殺筆", "花甲護身"),
    8:  ("凝霜劍癡", "霜刃穿骨", "冰魄守心"),
    9:  ("水木清華", "清流破浪", "華木成林"),
    10: ("斷霞遺韻", "弦震八方", "古韻護魂"),
    11: ("霜天冷徹", "冰劍寒鋒", "玄冰鐵壁"),
    12: ("男以控制", "幻影殺機", "虛縷結界"),
    13: ("酒吞雷震", "天雷裂岳", "雷鎧金身"),
    14: ("血海飄香", "血刃無情", "血海歸潮"),
    15: ("花開花落", "落花飛刃", "花雨凝甲"),
    16: ("鬼靈精怪", "鬼手摘星", "靈巧避禍"),
    17: ("滔天神棍", "棍掃千軍", "神棍擋關"),
    18: ("霸道藍刀", "藍焰斬天", "藍鋼護體"),
    19: ("冥音萬蠱", "冥毒噬魂", "幽蠱化盾"),
    20: ("萬機編碼", "機關暴雨", "鐵甲機陣"),
    21: ("毒蕊含霜", "霜毒穿脈", "含蕊固本"),
    22: ("翡翠生機", "翠針破穴", "翡翠回春"),
    23: ("影隨音鳴", "音殺無形", "音盾隱身"),
}

# ── SDD 1000/100 Stat Profiles (Lv99 targets) ────────────────────
# HP ceiling ~1000, attribute ceiling ~100
# Lv1 auto-computed from Lv99 × LV1_RATIO
# Format: [MHP, MMP, ATK, DEF, MAT, MDF, AGI, LUK]
LV99_PROFILES = {
    # ----東方啟---- 劍法+金，均衡型主角
    1:  [750, 95, 70, 52, 48, 48, 62, 55],
    # ----青兒---- 暗器/音律+風，敏捷型支援
    2:  [550, 80, 50, 38, 55, 42, 80, 75],
    # ----湮菲花---- 拳掌/醫術+木，高內功型
    3:  [580, 150, 40, 36, 76, 70, 50, 48],
    # ----闕崇陽---- 短兵+雷，武學宗師均衡偏高
    4:  [720, 120, 60, 50, 55, 52, 68, 75],
    # ----絲塔娜---- 棍法+土，剛猛物理坦克
    5:  [900, 55, 82, 68, 32, 40, 45, 38],
    # ----瑤琴劍---- 劍法+風，劍琴雙修（ATK+MAT雙高）
    6:  [700, 115, 72, 52, 70, 58, 62, 51],
    # ----沅花---- 筆法+木，高內功型
    7:  [600, 130, 48, 40, 75, 55, 60, 52],
    # ----談笑---- 劍法+寒，劍術高手（校準基準）
    8:  [650, 85, 78, 42, 55, 45, 70, 55],
    # ----白沫檸---- 槍法+水，均衡偏防
    9:  [740, 95, 56, 55, 50, 52, 56, 46],
    # ----珞堇---- 音律+木，琴師高內功
    10: [520, 140, 38, 36, 78, 70, 55, 43],
    # ----龍玉---- 劍法+土，鐵壁掌門（最高HP+DEF）
    11: [950, 75, 68, 70, 40, 55, 48, 34],
    # ----司徒長生---- 劍法+電，控制速度型（高AGI）
    12: [600, 105, 52, 40, 56, 50, 85, 72],
    # ----楊古晨---- 劍法+雷，物理偏重
    13: [700, 85, 68, 50, 52, 45, 58, 42],
    # ----殷染幽---- 劍法+水，暗殺速度型（高AGI+ATK，低防）
    14: [550, 90, 75, 34, 50, 36, 85, 60],
    # ----墨汐若---- 奇門+風，均衡支援
    15: [620, 115, 50, 42, 65, 52, 58, 48],
    # ----聶思泠---- 短兵+火，盜賊型（最高AGI+LUK，最低HP）
    16: [480, 70, 52, 30, 40, 32, 90, 86],
    # ----無名丐---- 棍法+水，坦克型（高HP+ATK+DEF）
    17: [850, 65, 75, 60, 35, 40, 52, 43],
    # ----郭霆黃---- 刀法+金，霸道型（最高ATK）
    18: [820, 55, 85, 62, 32, 40, 50, 36],
    # ----藍靜冥---- 毒術+寒，高內功型
    19: [600, 130, 45, 42, 76, 62, 50, 45],
    # ----黃凱竹---- 奇門+木，機關術（MAT+AGI）
    20: [580, 115, 42, 40, 70, 52, 65, 66],
    # ----劉靜靜---- 奇門+水，毒醫混合（AGI+LUK）
    21: [560, 105, 48, 36, 66, 46, 70, 69],
    # ----七霜---- 醫術+寒，治療專精（最高MP，高MAT+MDF）
    22: [650, 175, 36, 45, 70, 68, 50, 36],
    # ----莫縈懷---- 奇門+風，均衡偏敏
    23: [600, 95, 55, 40, 60, 46, 70, 64],
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_lv1(lv99_stats):
    """Compute Lv1 stats from Lv99 targets using ratio."""
    return [max(5, round(lv99_stats[i] * LV1_RATIO[i])) for i in range(8)]


def generate_curve(lv1_stats, lv99_stats):
    """Generate 100-value growth curve using diminishing returns (sqrt).
    Index 0 = Lv1, index 98 = Lv99, index 99 = Lv100.
    """
    params = []
    for si in range(8):
        s1 = lv1_stats[si]
        s99 = lv99_stats[si]
        curve = []
        for lv in range(1, 101):
            if lv == 1:
                val = s1
            elif lv <= 99:
                val = s1 + (s99 - s1) * math.sqrt((lv - 1) / 98)
            else:  # Lv100 = same as Lv99
                val = s99
            curve.append(max(1, round(val)))
        params.append(curve)
    return params


def compute_lv50_total(params):
    """Sum of all 8 stats at Lv50 (index 49)."""
    return sum(params[i][49] for i in range(8))


def scale_params(params, multipliers):
    """Scale param curves by directional multipliers, then normalize
    so Lv50 total matches the original (keeps variants within ±3%)."""
    base_total = compute_lv50_total(params)
    if base_total <= 0:
        return params

    # First pass: apply directional multipliers
    raw = []
    for si in range(8):
        raw.append([max(1, round(v * multipliers[si])) for v in params[si]])

    # Normalize to match original Lv50 total
    raw_total = compute_lv50_total(raw)
    if raw_total <= 0:
        return raw

    norm = base_total / raw_total
    scaled = []
    for si in range(8):
        scaled.append([max(1, round(v * multipliers[si] * norm))
                       for v in params[si]])
    return scaled


def make_class_entry(class_id, name, params, traits, learnings,
                     exp_params, note):
    """Create a standard RPG Maker MZ class entry."""
    return {
        "id": class_id,
        "expParams": exp_params,
        "traits": traits,
        "learnings": learnings,
        "name": name,
        "note": note,
        "params": params,
    }


def compute_phys_damage(atk, mat, agi, luk, e_def, e_mdf, e_agi, e_luk,
                        power=1.0):
    """SDD physical damage formula."""
    main = atk * 2.2 - e_def * 0.9
    sub = mat * 0.4 - e_mdf * 0.2
    agi_mult = 1 + (agi - e_agi) / 100
    luk_term = luk / (e_luk + 1)
    hp_mult = 1.5  # full HP
    raw = ((main + sub) * agi_mult + luk_term) * hp_mult * power
    return max(1, raw)


def main():
    orig_classes = load_json(CLASSES_PATH)
    actors = load_json(ACTORS_PATH)
    print(f"Loaded {len(orig_classes)} original classes, {len(actors)} actors")

    # ── Determine array size ───────────────────────────────────────
    max_id = max(max(ids) for ids in ACTOR_CLASS_IDS.values())
    arr_size = max_id + 1  # 75

    # Initialize with None
    new_classes = [None] * arr_size

    # Copy existing class data for unused IDs (16, 18, 19, 20, 22)
    used_ids = set()
    for ids in ACTOR_CLASS_IDS.values():
        used_ids.update(ids)

    for i in range(1, min(len(orig_classes), arr_size)):
        if i not in used_ids:
            new_classes[i] = copy.deepcopy(orig_classes[i])

    # ── Generate all 69 class entries ──────────────────────────────
    print(f"\n{'='*70}")
    print(f"Generating 69 classes (23 actors × 3 variants)")
    print(f"{'='*70}")

    errors = 0
    for aid in sorted(ACTOR_CLASS_IDS):
        aname = ACTOR_NAMES[aid]
        orig_cid = ACTOR_ORIG_CLASS[aid]
        ids = ACTOR_CLASS_IDS[aid]
        job_names = JOB_NAMES[aid]
        lv99 = LV99_PROFILES[aid]
        lv1 = compute_lv1(lv99)
        note = f"----{aname}----"

        # Get traits, learnings, expParams from original class
        orig = orig_classes[orig_cid]
        traits = copy.deepcopy(orig.get("traits", []))
        learnings = copy.deepcopy(orig.get("learnings", []))
        exp_params = copy.deepcopy(orig.get("expParams", [30, 20, 30, 30]))

        # Generate Variant A params
        params_a = generate_curve(lv1, lv99)

        # Variant A (均衡)
        new_classes[ids[0]] = make_class_entry(
            ids[0], job_names[0], params_a,
            traits, learnings, exp_params, note)

        # Variant B (攻擊特化)
        params_b = scale_params(params_a, MULT_B)
        new_classes[ids[1]] = make_class_entry(
            ids[1], job_names[1], params_b,
            copy.deepcopy(traits), [], copy.deepcopy(exp_params), note)

        # Variant C (防禦特化)
        params_c = scale_params(params_a, MULT_C)
        new_classes[ids[2]] = make_class_entry(
            ids[2], job_names[2], params_c,
            copy.deepcopy(traits), [], copy.deepcopy(exp_params), note)

        # Verify ±3%
        totals = [compute_lv50_total(p) for p in [params_a, params_b, params_c]]
        avg = sum(totals) / 3
        max_dev = max(abs(t - avg) / avg * 100 for t in totals) if avg else 0
        ok = "OK" if max_dev <= 3.0 else "WARN"
        if max_dev > 3.0:
            errors += 1

        lv50_vals = [params_a[si][49] for si in range(8)]
        print(f"  ----{aname}----  A={ids[0]:2d} B={ids[1]:2d} C={ids[2]:2d}  "
              f"Lv50total: {totals[0]}/{totals[1]}/{totals[2]}  "
              f"dev={max_dev:.2f}% [{ok}]")
        print(f"    Lv50(A): "
              + " ".join(f"{STAT_NAMES[si]}={lv50_vals[si]}" for si in range(8)))

    if errors:
        print(f"\n  WARNING: {errors} actors exceed ±3%!")
    else:
        print(f"\n  All 23 actors within ±3%.")

    # ── Write Classes.json ─────────────────────────────────────────
    with open(CLASSES_PATH, "w", encoding="utf-8") as f:
        json.dump(new_classes, f, ensure_ascii=False, indent=None,
                  separators=(",", ":"))
    print(f"\nClasses.json -> {arr_size} entries (IDs 0-{max_id})")

    # ── Write mapping JSON ─────────────────────────────────────────
    mapping = {}
    for aid in sorted(ACTOR_CLASS_IDS):
        mapping[str(aid)] = {
            "name": ACTOR_NAMES[aid],
            "classes": ACTOR_CLASS_IDS[aid],
            "job_names": list(JOB_NAMES[aid]),
        }
    with open(MAPPING_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"Mapping -> {MAPPING_PATH}")

    # ── Update Actors.json classIds ────────────────────────────────
    for a in actors:
        if not a:
            continue
        aid = a["id"]
        if aid in ACTOR_CLASS_IDS:
            a["classId"] = ACTOR_CLASS_IDS[aid][0]
    with open(ACTORS_PATH, "w", encoding="utf-8") as f:
        json.dump(actors, f, ensure_ascii=False, indent=None,
                  separators=(",", ":"))
    print(f"Actors.json -> classIds updated")

    # ── Damage calibration ─────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"DAMAGE CALIBRATION  (SDD target: Lv1 power=1.0 -> ~35 phys dmg)")
    print(f"Enemy: 帝國武民 DEF=22 MDF=8 AGI=10 LUK=5")
    print(f"{'='*70}")
    e_def, e_mdf, e_agi, e_luk = 22, 8, 10, 5
    for aid in sorted(ACTOR_CLASS_IDS):
        aname = ACTOR_NAMES[aid]
        lv1 = compute_lv1(LV99_PROFILES[aid])
        phys = compute_phys_damage(
            lv1[ATK], lv1[MAT], lv1[AGI], lv1[LUK],
            e_def, e_mdf, e_agi, e_luk, 1.0)
        print(f"  [{aid:2d}] {aname:5s}  "
              f"ATK={lv1[ATK]:2d} MAT={lv1[MAT]:2d} AGI={lv1[AGI]:2d} "
              f"LUK={lv1[LUK]:2d}  -> phys={phys:5.1f}")

    print(f"\nDone!")


if __name__ == "__main__":
    main()
