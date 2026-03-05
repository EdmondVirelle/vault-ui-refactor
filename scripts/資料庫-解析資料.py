# -*- coding: utf-8 -*-
import json, sys, os

os.environ['PYTHONUTF8'] = '1'
data_dir = 'C:/Consilience/Consilience/data'

# Weapons
with open(os.path.join(data_dir, 'Weapons.json'), 'r', encoding='utf-8') as f:
    weapons = json.load(f)
print('=== WEAPONS ===')
for w in weapons:
    if w and w.get('name', '').strip():
        p = w.get('params', [0]*8)
        print('ID=%d | %s | ATK=%d DEF=%d MAT=%d MDF=%d AGI=%d | price=%d' % (
            w['id'], w['name'], p[2], p[3], p[4], p[5], p[6], w.get('price', 0)))

# Armors (only with real stats)
print('\n=== KEY ARMORS (with stats, excluding qinggong/典籍) ===')
with open(os.path.join(data_dir, 'Armors.json'), 'r', encoding='utf-8') as f:
    armors = json.load(f)
for a in armors:
    if a and a.get('name', '').strip():
        p = a.get('params', [0]*8)
        eid = a.get('etypeId', 0)
        if any(x != 0 for x in p) and eid in (2, 3, 4, 5, 6):
            etype_map = {2: 'shield', 3: 'head', 4: 'body', 5: 'acc', 6: 'acc2'}
            print('ID=%d | %s | type=%s | HP=%d MP=%d ATK=%d DEF=%d MAT=%d MDF=%d AGI=%d LUK=%d | price=%d' % (
                a['id'], a['name'], etype_map.get(eid, str(eid)),
                p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], a.get('price', 0)))

# Skills (ID 1-560)
print('\n=== SKILLS (ID 1-560) ===')
with open(os.path.join(data_dir, 'Skills.json'), 'r', encoding='utf-8') as f:
    skills = json.load(f)
for s in skills:
    if s and s.get('id', 0) <= 560 and s.get('name', '').strip():
        dmg = s.get('damage', {})
        print('ID=%d | %s | mp=%d tp=%d | scope=%d | dmgType=%d' % (
            s['id'], s['name'], s.get('mpCost', 0), s.get('tpCost', 0),
            s.get('scope', 0), dmg.get('type', 0)))

# States
print('\n=== STATES ID 42-78 ===')
with open(os.path.join(data_dir, 'States.json'), 'r', encoding='utf-8') as f:
    states = json.load(f)
for st in states:
    if st and 42 <= st.get('id', 0) <= 78:
        nm = st.get('name', '')
        if nm.strip():
            print('ID=%d | %s | icon=%d' % (st['id'], nm, st.get('icon', 0)))
        else:
            print('ID=%d | (empty)' % st['id'])

print('\n=== STATES ID 230+ (check existing) ===')
count = 0
for st in states:
    if st and st.get('id', 0) >= 230 and st.get('name', '').strip():
        count += 1
        if count <= 20:
            print('ID=%d | %s' % (st['id'], st['name']))
print('Total states >= 230 with names: %d' % count)
print('Total states array size: %d' % len(states))
