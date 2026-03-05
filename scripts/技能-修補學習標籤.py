#!/usr/bin/env python3
"""
Add Learn System notetags to character skills 1351-1879.
- Add <Learn AP Cost>, <Learn SP Cost>, <Learn Item Cost> to skills missing them
- Add <Learn Require Skill> for Lv25/35 prerequisite chains
- Add <Learn Require Level> to ALL skills based on class learnings
- Does NOT modify Classes.json
"""
import json, re, os, sys
from collections import Counter

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)

skills_path = os.path.join(base_dir, 'Consilience', 'data', 'Skills.json')
classes_path = os.path.join(base_dir, 'Consilience', 'data', 'Classes.json')

with open(skills_path, 'r', encoding='utf-8') as f:
    skills = json.load(f)
with open(classes_path, 'r', encoding='utf-8') as f:
    classes = json.load(f)


# === Step 1: Build maps ===

# skill -> min class learning level
skill_min_level = {}
# skill -> list of (class_id, level)
skill_classes = {}

for cls in classes:
    if cls is None:
        continue
    for l in cls.get('learnings', []):
        sid = l['skillId']
        if 1351 <= sid <= 1879:
            if sid not in skill_min_level or l['level'] < skill_min_level[sid]:
                skill_min_level[sid] = l['level']
            skill_classes.setdefault(sid, []).append((cls['id'], l['level']))

# class -> primary item ID (from character-specific skills only)
class_item = {}
for cls in classes:
    if cls is None:
        continue
    cid = cls['id']
    items = Counter()
    for l in cls.get('learnings', []):
        sid = l['skillId']
        if sid < 1351 or sid > 1879:
            continue
        if sid >= len(skills) or skills[sid] is None:
            continue
        note = skills[sid].get('note', '')
        for m in re.finditer(r'<Learn Item (\d+) Cost:', note):
            items[int(m.group(1))] += 1
    if items:
        class_item[cid] = max(items, key=items.get)

# Orphan skills (墨汐若 1773-1783) - manually assign
orphan_map = {
    # Class#58 花開花落
    1773: (58, 15), 1774: (58, 25), 1775: (58, 35),
    # Class#59 落花飛刃
    1777: (59, 15), 1778: (59, 25), 1779: (59, 35),
    # Class#60 花雨凝甲
    1781: (60, 15), 1782: (60, 25), 1783: (60, 35),
}
# Assign item for orphan classes (墨汐若 uses Item#1017)
for cid in [58, 59, 60]:
    if cid not in class_item:
        class_item[cid] = 1017

for sid, (cid, lv) in orphan_map.items():
    skill_min_level[sid] = lv
    skill_classes[sid] = [(cid, lv)]

# Cost tiers by level
COST_TIERS = {
    15: {'ap': 55, 'sp': 12, 'item_cost': 5},
    25: {'ap': 80, 'sp': 20, 'item_cost': 8},
    35: {'ap': 120, 'sp': 35, 'item_cost': 12},
}

# Build prerequisite chains: within each class, Lv25 requires Lv15, Lv35 requires Lv25
# Find untagged skill groups per class
untagged_per_class = {}  # class_id -> {level: skill_id}
for sid in range(1351, 1880):
    if sid >= len(skills) or skills[sid] is None:
        continue
    sk = skills[sid]
    name = sk.get('name', '')
    if not name or name.startswith('----'):
        continue
    note = sk.get('note', '')
    if re.search(r'<Learn (AP|SP|Item)', note):
        continue  # already tagged

    # Find which class this skill is in
    if sid in orphan_map:
        cid, lv = orphan_map[sid]
    elif sid in skill_classes:
        # Use the first class assignment
        cid, lv = skill_classes[sid][0]
    else:
        continue

    untagged_per_class.setdefault(cid, {})[lv] = sid


# === Step 2: Apply changes ===

added_learn_tags = 0
added_require_level = 0
report = []

for sid in range(1351, 1880):
    if sid >= len(skills) or skills[sid] is None:
        continue
    sk = skills[sid]
    name = sk.get('name', '')
    if not name or name.startswith('----'):
        continue

    note = sk.get('note', '')
    changes = []

    # Check if needs Learn cost tags
    has_ap = bool(re.search(r'<Learn AP Cost:', note))
    has_sp = bool(re.search(r'<Learn SP Cost:', note))
    has_item = bool(re.search(r'<Learn Item \d+ Cost:', note))

    if not has_ap:
        # Determine class and level for cost assignment
        if sid in orphan_map:
            cid, lv = orphan_map[sid]
        elif sid in skill_classes:
            cid, lv = skill_classes[sid][0]
        else:
            cid, lv = None, None

        if cid and lv in COST_TIERS:
            tier = COST_TIERS[lv]
            item_id = class_item.get(cid, 1009)

            tags_to_add = []
            tags_to_add.append(f'<Learn AP Cost: {tier["ap"]}>')
            tags_to_add.append(f'<Learn SP Cost: {tier["sp"]}>')
            tags_to_add.append(f'<Learn Item {item_id} Cost: {tier["item_cost"]}>')

            # Prerequisite: Lv25 requires Lv15 skill, Lv35 requires Lv25 skill
            class_untagged = untagged_per_class.get(cid, {})
            if lv == 25 and 15 in class_untagged:
                tags_to_add.append(f'<Learn Require Skill: {class_untagged[15]}>')
            elif lv == 35 and 25 in class_untagged:
                tags_to_add.append(f'<Learn Require Skill: {class_untagged[25]}>')

            note = note.rstrip('\n') + '\n' + '\n'.join(tags_to_add) + '\n'
            changes.append(f'costs(AP{tier["ap"]}/SP{tier["sp"]}/Item#{item_id}x{tier["item_cost"]})')
            added_learn_tags += 1

    # Add <Learn Require Level> if not present
    has_level = bool(re.search(r'<Learn Require Level:', note))
    if not has_level and sid in skill_min_level:
        lv = skill_min_level[sid]
        note = note.rstrip('\n') + '\n' + f'<Learn Require Level: {lv}>\n'
        changes.append(f'ReqLv{lv}')
        added_require_level += 1

    if changes:
        sk['note'] = note
        report.append(f'  #{sid} {name:<16} {", ".join(changes)}')


# === Report ===
print(f'=== Skill Learn Tags Patch Report ===')
print(f'Skills with new Learn cost tags: {added_learn_tags}')
print(f'Skills with new Require Level:   {added_require_level}')
print(f'Total skills modified:           {len(report)}')
print()
for line in report:
    print(line)

if '--apply' in sys.argv:
    print('\nWriting Skills.json...')
    with open(skills_path, 'w', encoding='utf-8') as f:
        json.dump(skills, f, ensure_ascii=False, indent=None)
    print('Done!')
else:
    print('\nDRY RUN — add --apply to write changes')
