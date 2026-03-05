#!/usr/bin/env python3
"""
Clean up Classes.json:
- Remove learnings that reference placeholder skills (----name---- or empty name)
- Remove learnings that reference empty/null skill slots
- Report all changes for review
"""
import json, os, sys

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)

classes_path = os.path.join(base_dir, 'Consilience', 'data', 'Classes.json')
skills_path = os.path.join(base_dir, 'Consilience', 'data', 'Skills.json')

with open(classes_path, 'r', encoding='utf-8') as f:
    classes = json.load(f)

with open(skills_path, 'r', encoding='utf-8') as f:
    skills = json.load(f)

def is_bad_skill(sid):
    """Check if a skill ID should be removed from learnings."""
    if sid < 0 or sid >= len(skills):
        return True, "ID out of range"
    sk = skills[sid]
    if sk is None:
        return True, "null slot"
    name = sk.get('name', '')
    if not name:
        return True, "empty name"
    if name.startswith('----') and name.endswith('----'):
        return True, f"placeholder: {name}"
    return False, ""

# DRY RUN: collect all changes
changes = []
total_removed = 0

for cls in classes:
    if cls is None:
        continue
    if not cls.get('learnings'):
        continue

    cls_id = cls['id']
    cls_name = cls['name']
    original_count = len(cls['learnings'])
    removed = []
    kept = []

    for learning in cls['learnings']:
        sid = learning['skillId']
        bad, reason = is_bad_skill(sid)
        if bad:
            removed.append((learning['level'], sid, reason))
        else:
            kept.append(learning)

    if removed:
        changes.append({
            'cls_id': cls_id,
            'cls_name': cls_name,
            'original': original_count,
            'kept': len(kept),
            'removed': removed,
        })
        total_removed += len(removed)

# Print report
print(f"=== Clean-up Report ===")
print(f"Total learnings to remove: {total_removed}")
print()

for c in changes:
    print(f"Class#{c['cls_id']} {c['cls_name']} ({c['original']} -> {c['kept']})")
    for lv, sid, reason in c['removed']:
        sk = skills[sid] if sid < len(skills) and skills[sid] else None
        sk_name = sk['name'] if sk else '(null)'
        print(f"  REMOVE Lv{lv}: #{sid} {sk_name} [{reason}]")
    print()

# Check for --apply flag
if '--apply' in sys.argv:
    print("Applying changes...")
    for cls in classes:
        if cls is None:
            continue
        if not cls.get('learnings'):
            continue

        new_learnings = []
        for learning in cls['learnings']:
            sid = learning['skillId']
            bad, _ = is_bad_skill(sid)
            if not bad:
                new_learnings.append(learning)
        cls['learnings'] = new_learnings

    with open(classes_path, 'w', encoding='utf-8') as f:
        json.dump(classes, f, ensure_ascii=False, indent=None)

    print(f"Done! Removed {total_removed} learnings from Classes.json")
else:
    print("DRY RUN — add --apply to actually modify Classes.json")
