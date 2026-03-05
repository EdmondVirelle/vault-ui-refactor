#!/usr/bin/env python3
"""
Import <Learn Skills> notetags into the learnings array of Classes.json.
- Parse all <Learn Skills: ...> and <Learn Skills: X to Y> from each class note
- Distribute new skills across levels, merging with existing learnings
- Preserve existing level assignments
"""
import json, re, os, sys, math

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)

classes_path = os.path.join(base_dir, 'Consilience', 'data', 'Classes.json')
skills_path = os.path.join(base_dir, 'Consilience', 'data', 'Skills.json')

with open(classes_path, 'r', encoding='utf-8') as f:
    classes = json.load(f)

with open(skills_path, 'r', encoding='utf-8') as f:
    skills = json.load(f)


def parse_learn_skills(note):
    """Parse all <Learn Skills: ...> notetags from a class note."""
    skill_ids = set()
    if not note:
        return skill_ids

    # Match <Learn Skills: X to Y>
    for m in re.finditer(r'<Learn Skills:\s*(\d+)\s+to\s+(\d+)\s*>', note):
        start, end = int(m.group(1)), int(m.group(2))
        for sid in range(start, end + 1):
            skill_ids.add(sid)

    # Match <Learn Skills: id1, id2, id3, ...>
    for m in re.finditer(r'<Learn Skills:\s*([\d,\s]+?)>', note):
        text = m.group(1)
        # Skip if it's a "to" pattern (already handled)
        if 'to' in m.group(0):
            continue
        for num in re.findall(r'\d+', text):
            skill_ids.add(int(num))

    return skill_ids


def get_existing_learnings(cls):
    """Get {skillId: level} from existing learnings array."""
    result = {}
    for l in cls.get('learnings', []):
        result[l['skillId']] = l['level']
    return result


def is_valid_skill(sid):
    """Check if skill ID references a valid, non-placeholder skill."""
    if sid < 1 or sid >= len(skills):
        return False
    sk = skills[sid]
    if sk is None:
        return False
    name = sk.get('name', '')
    if not name or (name.startswith('----') and name.endswith('----')):
        return False
    # 391~1000 are weapon/armor attached skills, not auto-learnable
    if 391 <= sid <= 1000:
        return False
    return True


def classify_skill(sid):
    """Classify skill for level ordering: lower priority = earlier level."""
    # Universal / utility
    if sid == 1976 or sid >= 2000:
        return 0, sid  # earliest
    # Shared weapon basics (1002-1172 ranges)
    if 1002 <= sid <= 1172:
        return 1, sid
    # Additional shared sets (1174-1341)
    if 1174 <= sid <= 1341:
        return 2, sid
    # Character-specific (1352-1603)
    if 1352 <= sid <= 1603:
        return 3, sid
    # T2/T3/T4 advanced (1605-1723)
    if 1605 <= sid <= 1880:
        return 4, sid
    # Container skills (1881-1975)
    if 1881 <= sid <= 1975:
        return -1, sid  # Lv1 always
    # Fallback
    return 5, sid


# Process each class
MAX_LEVEL = 35  # distribute up to this level

report = []

for cls in classes:
    if cls is None:
        continue

    cls_id = cls['id']
    cls_name = cls['name']
    note = cls.get('note', '')

    # Skip base classes (----name----)
    if cls_name.startswith('----'):
        continue

    # Parse <Learn Skills> from note
    learn_skills = parse_learn_skills(note)
    if not learn_skills:
        continue

    # Get existing learnings
    existing = get_existing_learnings(cls)

    # Find skills to add (in Learn Skills but not in learnings)
    new_skills = []
    for sid in learn_skills:
        if sid not in existing and is_valid_skill(sid):
            new_skills.append(sid)

    if not new_skills:
        continue

    # Sort new skills by classification then ID
    new_skills.sort(key=classify_skill)

    # Find the max existing level to know our ceiling
    existing_levels = set(existing.values())

    # Determine level range for new skills
    # Container-class skills go to Lv1
    # Others spread from Lv1 to MAX_LEVEL
    assignments = []
    non_container = []

    for sid in new_skills:
        cat, _ = classify_skill(sid)
        if cat == -1:  # container
            assignments.append((sid, 1))
        elif cat == 0:  # universal/utility → Lv1
            assignments.append((sid, 1))
        else:
            non_container.append(sid)

    # Distribute non-container skills across levels
    if non_container:
        n = len(non_container)
        # Use levels from 1 to MAX_LEVEL, spread evenly
        for i, sid in enumerate(non_container):
            # Linear interpolation from 1 to MAX_LEVEL
            lv = 1 + int(round(i * (MAX_LEVEL - 1) / max(n - 1, 1)))
            # Clamp
            lv = max(1, min(lv, MAX_LEVEL))
            assignments.append((sid, lv))

    # Merge into learnings
    for sid, lv in assignments:
        if sid not in existing:
            cls['learnings'].append({
                'level': lv,
                'skillId': sid,
                'note': ''
            })

    # Sort learnings by level then skillId
    cls['learnings'].sort(key=lambda x: (x['level'], x['skillId']))

    report.append({
        'id': cls_id,
        'name': cls_name,
        'note_skills': len(learn_skills),
        'existing': len(existing),
        'added': len(assignments),
        'total': len(cls['learnings']),
    })


# Print report
print(f"=== Import Report ===")
print(f"Classes modified: {len(report)}")
print()
print(f"{'ID':>3} {'Name':<16} {'Note':>5} {'Existed':>7} {'Added':>5} {'Total':>5}")
print(f"{'---':>3} {'----':<16} {'----':>5} {'-------':>7} {'-----':>5} {'-----':>5}")
for r in report:
    print(f"{r['id']:>3} {r['name']:<16} {r['note_skills']:>5} {r['existing']:>7} {r['added']:>5} {r['total']:>5}")

total_added = sum(r['added'] for r in report)
print(f"\nTotal new learnings added: {total_added}")

# Apply
if '--apply' in sys.argv:
    print("\nWriting Classes.json...")
    with open(classes_path, 'w', encoding='utf-8') as f:
        json.dump(classes, f, ensure_ascii=False, indent=None)
    print("Done!")
else:
    print("\nDRY RUN — add --apply to write changes")
