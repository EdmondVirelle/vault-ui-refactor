#!/usr/bin/env python3
"""Check which elements are used vs unused."""
import json, re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"

# 1. Load elements from System.json
data = json.loads((BASE / "System.json").read_text(encoding="utf-8"))
elems = data["elements"]

# Strip icon tags like \I[3154]
icon_re = re.compile(r"\\I\[\d+\]")
clean = [icon_re.sub("", str(e)).strip() for e in elems]

print("=== System.json Elements ===")
for i, name in enumerate(clean):
    if i <= 28:
        print(f"  {i:>3}: {name}")
if len(clean) > 29:
    print(f"  --- IDs 29-{len(clean)-1}: {len(clean)-29} sub-element entries (skill/style names) ---")

# 2. Count Multi-Element usage in skills
skills = json.loads((BASE / "Skills.json").read_text(encoding="utf-8"))
elem_usage = Counter()
for s in skills:
    if s is None:
        continue
    note = s.get("note", "")
    for m in re.findall(r"<Multi-Element:\s*([^>]+)>", note):
        for part in m.split(","):
            part = part.strip()
            if part:
                elem_usage[part] += 1

print("\n=== Multi-Element Tag Usage (top 30) ===")
for name, count in sorted(elem_usage.items(), key=lambda x: -x[1])[:30]:
    print(f"  {name}: {count}")

# 3. Cross-reference base elements (1-28) with usage
print("\n=== Base Element (1-28) Usage ===")
print(f"  {'ID':>3}  {'Name':<6}  {'Multi-Element':>14}  {'As Sub-Element':>14}  Status")
print("  " + "-" * 65)

# Also check sub-element names (29+) that reference base elements
sub_elem_names = set(clean[29:]) if len(clean) > 29 else set()

for i in range(1, min(29, len(clean))):
    name = clean[i]
    direct = elem_usage.get(name, 0)
    # Check if this element name appears as part of any Multi-Element value
    indirect = sum(v for k, v in elem_usage.items() if name in k and k != name)
    status = "USED" if direct > 0 else ("INDIRECT" if indirect > 0 else "NOT USED")
    print(f"  {i:>3}  {name:<6}  {direct:>14}  {indirect:>14}  {status}")

# 4. Check which sub-elements (29+) are used
print("\n=== Sub-Elements (29+) Usage ===")
used_subs = []
unused_subs = []
for i in range(29, len(clean)):
    name = clean[i]
    if not name or name.startswith("-"):
        continue
    count = elem_usage.get(name, 0)
    if count > 0:
        used_subs.append((i, name, count))
    else:
        unused_subs.append((i, name))

print(f"  Used: {len(used_subs)}")
for sid, name, count in used_subs:
    print(f"    {sid:>3}: {name} ({count} skills)")

print(f"\n  Unused: {len(unused_subs)}")
for sid, name in unused_subs:
    print(f"    {sid:>3}: {name}")
