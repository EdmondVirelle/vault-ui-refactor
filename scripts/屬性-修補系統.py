#!/usr/bin/env python3
"""
Patch character elements and 殷染幽 weapon change.
1. Fix 奇門 skill icons (1083-1094) → iconIndex 3165
2. Update Multi-Element tags for 6 characters whose attribute changed
3. Update 殷染幽 skills: 劍法→奇門, 暗器→奇門, 水→寒
4. Update 殷染幽 class notes & learnings (劍法→奇門, 水→寒 shared skills)
"""
import json, re, os, sys

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)

skills_path = os.path.join(base_dir, 'Consilience', 'data', 'Skills.json')
classes_path = os.path.join(base_dir, 'Consilience', 'data', 'Classes.json')

with open(skills_path, 'r', encoding='utf-8') as f:
    skills = json.load(f)
with open(classes_path, 'r', encoding='utf-8') as f:
    classes = json.load(f)

report = []

# ========================================
# STEP 1: Fix 奇門 icons → 3165
# ========================================
icon_fixed = 0
for sid in range(1083, 1095):
    if sid >= len(skills) or skills[sid] is None:
        continue
    sk = skills[sid]
    if sk.get('iconIndex') != 3165:
        old = sk['iconIndex']
        sk['iconIndex'] = 3165
        icon_fixed += 1
        report.append(f'[ICON] #{sid} {sk["name"]}: {old} → 3165')

# ========================================
# STEP 2: Update Multi-Element for attribute changes
# ========================================
# Character skill ranges (from class learnings)
# We need to find ALL skills belonging to each character

# Build character -> skill IDs mapping from class learnings
char_skill_ids = {}
char_classes = {
    '殷染幽': [54, 55, 56],
    '珞堇':   [38, 39, 40],
    '黃凱竹': [78, 79, 80],
    '劉靜靜': [82, 83, 84],
    '墨汐若': [58, 59, 60],
    '藍靜冥': [74, 75, 76],
}

for char, cids in char_classes.items():
    sids = set()
    for cid in cids:
        cls = classes[cid]
        if cls is None:
            continue
        for l in cls.get('learnings', []):
            sid = l['skillId']
            if 1351 <= sid <= 1879:
                sids.add(sid)
    # Also include tier skills (1605+) and universal skills (2000+)
    for cid in cids:
        cls = classes[cid]
        if cls is None:
            continue
        for l in cls.get('learnings', []):
            sid = l['skillId']
            if 1605 <= sid <= 1880 or sid >= 2000:
                sids.add(sid)
    char_skill_ids[char] = sids

# Attribute changes: old_element → new_element
attr_changes = {
    '珞堇':   ('木', '炎'),
    '黃凱竹': ('木', '炎'),
    '殷染幽': ('水', '寒'),
    '劉靜靜': ('水', '火'),
    '墨汐若': ('風', '炎'),
    '藍靜冥': ('寒', '電'),
}

# For 殷染幽, also change weapon elements
ran_you_weapon_changes = {
    '劍法': '奇門',
    '暗器': '奇門',
}

element_fixed = 0
for char, (old_el, new_el) in attr_changes.items():
    sids = char_skill_ids.get(char, set())
    for sid in sorted(sids):
        if sid >= len(skills) or skills[sid] is None:
            continue
        sk = skills[sid]
        note = sk.get('note', '')
        if not note:
            continue

        original_note = note
        changes = []

        # Replace attribute element in Multi-Element tags
        # Pattern: <Multi-Element: ..., 水, ...> → <Multi-Element: ..., 寒, ...>
        def replace_element_in_tag(match):
            tag_content = match.group(1)
            elements = [e.strip() for e in tag_content.split(',')]
            changed = False
            new_elements = []
            for e in elements:
                if e == old_el:
                    new_elements.append(new_el)
                    changed = True
                else:
                    new_elements.append(e)
            if changed:
                return f'<Multi-Element: {", ".join(new_elements)}>'
            return match.group(0)

        note = re.sub(r'<Multi-Element:\s*([^>]+)>', replace_element_in_tag, note)

        # For 殷染幽: also replace weapon elements, then deduplicate
        if char == '殷染幽':
            for old_w, new_w in ran_you_weapon_changes.items():
                def replace_weapon_in_tag(match):
                    tag_content = match.group(1)
                    elements = [e.strip() for e in tag_content.split(',')]
                    changed = False
                    new_elements = []
                    for e in elements:
                        if e == old_w:
                            new_elements.append(new_w)
                            changed = True
                        else:
                            new_elements.append(e)
                    if changed:
                        # Deduplicate while preserving order
                        seen = set()
                        deduped = []
                        for e in new_elements:
                            if e not in seen:
                                seen.add(e)
                                deduped.append(e)
                        return f'<Multi-Element: {", ".join(deduped)}>'
                    return match.group(0)
                note = re.sub(r'<Multi-Element:\s*([^>]+)>', replace_weapon_in_tag, note)

        if note != original_note:
            sk['note'] = note
            # Show what changed
            old_tags = re.findall(r'<Multi-Element:[^>]+>', original_note)
            new_tags = re.findall(r'<Multi-Element:[^>]+>', note)
            for ot, nt in zip(old_tags, new_tags):
                if ot != nt:
                    report.append(f'[ELEMENT] #{sid} {sk["name"]}: {ot} → {nt}')
                    element_fixed += 1

# ========================================
# STEP 3: Update 殷染幽's class notes & learnings
# ========================================
class_fixed = 0
for cid in [54, 55, 56]:
    cls = classes[cid]
    if cls is None:
        continue

    note = cls.get('note', '')
    original_note = note

    # Replace 劍法 basics with 奇門 basics
    note = note.replace('<Learn Skills: 1002 to 1016>', '<Learn Skills: 1083 to 1094>')

    # Replace 水 shared skills (1265-1276) with 寒 shared skills (1330-1341)
    old_water = '<Learn Skills: 1265, 1266, 1267, 1268, 1269, 1270, 1271, 1272, 1273, 1274, 1275, 1276>'
    new_cold = '<Learn Skills: 1330, 1331, 1332, 1333, 1334, 1335, 1336, 1337, 1338, 1339, 1340, 1341>'
    note = note.replace(old_water, new_cold)

    if note != original_note:
        cls['note'] = note
        report.append(f'[CLASS] Class#{cid} {cls["name"]}: Updated Learn Skills (劍法→奇門, 水→寒)')
        class_fixed += 1

    # Update learnings array:
    # Remove 1002-1016 (劍法), add 1083-1094 (奇門)
    # Remove 1265-1276 (水 shared), add 1330-1341 (寒 shared)
    old_sword = set(range(1002, 1017))
    old_water_set = set(range(1265, 1277))
    new_qimen = set(range(1083, 1095))
    new_cold_set = set(range(1330, 1342))

    # Get existing learnings
    existing = {l['skillId']: l for l in cls.get('learnings', [])}
    added = 0
    removed = 0

    # Remove old weapon/element skills
    new_learnings = []
    for l in cls['learnings']:
        if l['skillId'] in old_sword or l['skillId'] in old_water_set:
            removed += 1
        else:
            new_learnings.append(l)

    # Add new weapon skills (奇門 1083-1094) at appropriate levels
    # Use similar level distribution as the old sword skills
    for sid in sorted(new_qimen):
        if sid not in existing:
            # Distribute across early levels (1-15 like weapon basics)
            idx = sid - 1083
            lv = 1 + int(round(idx * 14 / max(11, 1)))
            lv = max(1, min(lv, 15))
            new_learnings.append({'level': lv, 'skillId': sid, 'note': ''})
            added += 1

    # Add new element skills (寒 1330-1341) at appropriate levels
    for sid in sorted(new_cold_set):
        if sid not in existing:
            idx = sid - 1330
            lv = 1 + int(round(idx * 14 / max(11, 1)))
            lv = max(1, min(lv, 15))
            new_learnings.append({'level': lv, 'skillId': sid, 'note': ''})
            added += 1

    new_learnings.sort(key=lambda x: (x['level'], x['skillId']))
    cls['learnings'] = new_learnings

    if added > 0 or removed > 0:
        report.append(f'[LEARNINGS] Class#{cid} {cls["name"]}: removed {removed}, added {added} (total {len(new_learnings)})')

# ========================================
# Report
# ========================================
print('=== Element Patch Report ===')
print(f'奇門 icons fixed: {icon_fixed}')
print(f'Multi-Element tags updated: {element_fixed}')
print(f'Class notes updated: {class_fixed}')
print()
for line in report:
    print(f'  {line}')

if '--apply' in sys.argv:
    print('\nWriting Skills.json...')
    with open(skills_path, 'w', encoding='utf-8') as f:
        json.dump(skills, f, ensure_ascii=False, indent=None)
    print('Writing Classes.json...')
    with open(classes_path, 'w', encoding='utf-8') as f:
        json.dump(classes, f, ensure_ascii=False, indent=None)
    print('Done!')
else:
    print('\nDRY RUN — add --apply to write changes')
