#!/usr/bin/env python3
import json, os

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(base, 'Consilience', 'data', 'Classes.json'), 'r', encoding='utf-8') as f:
    classes = json.load(f)

out_path = os.path.join(base, '_class_notes.txt')
with open(out_path, 'w', encoding='utf-8') as out:
    for c in classes:
        if c is None:
            continue
        note = c.get('note', '').strip()
        out.write(f'=== Class#{c["id"]} {c["name"]} ===\n')
        if note:
            out.write(note + '\n')
        else:
            out.write('(empty)\n')
        out.write('\n')
print(f'Written to {out_path}')
