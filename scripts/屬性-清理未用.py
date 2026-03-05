#!/usr/bin/env python3
"""Clean unused sub-elements from System.json.

Clears the 45 confirmed-unused sub-element entries (IDs 29+) to ""
and trims trailing empty entries from the elements array.
"""
import json
import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "Consilience" / "data"

# 1. Load elements
sys_path = BASE / "System.json"
data = json.loads(sys_path.read_text(encoding="utf-8"))
elems = data["elements"]

# Strip icon tags like \I[3154]
icon_re = re.compile(r"\\I\[\d+\]")
clean = [icon_re.sub("", str(e)).strip() for e in elems]

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

# 3. Find unused sub-elements (ID 29+)
unused_ids = []
for i in range(29, len(clean)):
    name = clean[i]
    if not name or name.startswith("-"):
        continue
    if elem_usage.get(name, 0) == 0:
        unused_ids.append(i)

print(f"Found {len(unused_ids)} unused sub-elements to clear:")
for uid in unused_ids:
    print(f"  {uid:>3}: {clean[uid]}")

# 4. Clear unused entries
for uid in unused_ids:
    elems[uid] = ""

# 5. Trim trailing empty entries
while len(elems) > 1 and elems[-1] == "":
    elems.pop()

print(f"\nElements array trimmed from {len(clean)} to {len(elems)} entries")

# 6. Save
data["elements"] = elems
sys_path.write_text(
    json.dumps(data, ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8",
)
print("System.json updated successfully.")
