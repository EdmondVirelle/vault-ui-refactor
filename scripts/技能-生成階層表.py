#!/usr/bin/env python3
"""Generate character skill tier document from RPG Maker MZ data."""
import json, re, os

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)

with open(os.path.join(base_dir, 'Consilience', 'data', 'Classes.json'), 'r', encoding='utf-8') as f:
    classes = json.load(f)

with open(os.path.join(base_dir, 'Consilience', 'data', 'Skills.json'), 'r', encoding='utf-8') as f:
    skills = json.load(f)

def get_skill(sid):
    if sid < len(skills) and skills[sid]:
        return skills[sid]
    return None

def clean_desc(desc):
    if not desc:
        return ''
    desc = re.sub(r'\\c\[\d+\]', '', desc)
    desc = re.sub(r'\\[IVN]\[\d+\]', '', desc)
    desc = desc.replace('\n', ' ').strip()
    return desc[:120]

def extract_type_and_element(desc):
    if not desc:
        return '', '', ''
    m = re.search(r'類型：([^｜）]+)', desc)
    skill_type = m.group(1).strip() if m else ''
    m = re.search(r'範圍：([^｜）]+)', desc)
    scope = m.group(1).strip() if m else ''
    m = re.search(r'｜([^｜）]+)｜(?:增加|消耗)策略', desc)
    element = m.group(1).strip() if m else ''
    return skill_type, scope, element

def is_enemy_skill(sid):
    return 3 <= sid <= 499

def parse_skill_info(skill):
    if not skill:
        return {'name':'???','desc':'','mp':0,'tp':0,'dtype':'-','scope':'-','type_str':'','element':''}

    dtypes = {0:'-',1:'外功',2:'內力傷',3:'回復',4:'內力復',5:'吸收',6:'內力吸'}
    scopes_map = {0:'-',1:'敵單',2:'敵全',3:'敵隨1',4:'敵隨2',5:'敵隨3',6:'敵隨4',
              7:'友單',8:'友全',9:'友單(倒)',10:'友全(倒)',11:'自身',12:'-',13:'友全(含倒)',14:'敵全'}

    desc = clean_desc(skill.get('description',''))
    type_str, scope_str, element = extract_type_and_element(desc)

    if not scope_str:
        scope_str = scopes_map.get(skill.get('scope', 0), '-')

    return {
        'name': skill['name'],
        'desc': desc,
        'mp': skill.get('mpCost', 0),
        'tp': skill.get('tpCost', 0),
        'dtype': dtypes.get(skill['damage']['type'], '?'),
        'scope': scope_str,
        'type_str': type_str,
        'element': element,
    }

# Build class list sorted by id
class_list = sorted([c for c in classes if c is not None], key=lambda c: c['id'])

# Find base classes (----name----)
base_classes = [c for c in class_list if c['name'].startswith('----') and c['name'].endswith('----')]

char_groups = []
for bc in base_classes:
    base_id = bc['id']
    char_name = bc['name'].replace('----','').strip()
    trait_classes = [c for c in class_list
                     if c['id'] > base_id and c['id'] <= base_id + 3
                     and not c['name'].startswith('----')]
    if trait_classes:
        char_groups.append({
            'name': char_name,
            'base_id': base_id,
            'traits': trait_classes
        })

# Generate markdown
lines = []
lines.append('# 萬法同歸 — 角色特質職業・技能分級總表')
lines.append('')
lines.append('> 自動產生自 `Classes.json` + `Skills.json`')
lines.append('')
lines.append('## 分級規則')
lines.append('')
lines.append('每位角色擁有 **三條特質路線**（對應三個職業），技能依解鎖等級分為四階：')
lines.append('')
lines.append('| 階級 | 解鎖等級 | 戰略定位 | 消耗特徵 |')
lines.append('|------|---------|---------|---------|')
lines.append('| **T1 基礎** | Lv 1 | 套路容器（三路共用），內含基礎招式 | MP 0 / 自動習得 |')
lines.append('| **T2 進階** | Lv 2~15 | 路線開始分歧，首個專屬技能 | MP 15~28 |')
lines.append('| **T3 精通** | Lv 16~25 | 路線核心技，高威力單體 or 團體輔助 | MP 22~28 |')
lines.append('| **T4 終極** | Lv 26~35 | 路線奧義，角色最強技能 | MP 30~40 + TP 50 |')
lines.append('')
lines.append('> **T4 終極技**通常消耗 40 MP + 50 TP（策略），代表角色傾盡全力的必殺。')
lines.append('> 低 ID 技能（#3~#499）為**繼承自敵技/Boss 技**，僅出現在主特質路線，收進折疊區。')
lines.append('')
lines.append('---')
lines.append('')

for group in char_groups:
    lines.append(f'## {group["name"]}')
    lines.append('')

    all_lv1_sets = []
    for tc in group['traits']:
        lv1_ids = set()
        for l in tc.get('learnings', []):
            if l['level'] == 1:
                lv1_ids.add(l['skillId'])
        all_lv1_sets.append(lv1_ids)

    shared_lv1 = all_lv1_sets[0] if all_lv1_sets else set()
    for s in all_lv1_sets[1:]:
        shared_lv1 = shared_lv1 & s

    if shared_lv1:
        lines.append('**T1 共用套路容器（三路共用）：**')
        lines.append('')
        for sid in sorted(shared_lv1):
            sk = get_skill(sid)
            if sk:
                info = parse_skill_info(sk)
                lines.append(f'- `#{sid}` **{info["name"]}**')
        lines.append('')

    for tc in group['traits']:
        trait_name = tc['name']
        lines.append(f'### {trait_name}（Class#{tc["id"]}）')
        lines.append('')

        learnings = sorted(tc.get('learnings', []), key=lambda x: (x['level'], x['skillId']))

        char_entries = {1: [], 2: [], 3: [], 4: []}
        enemy_entries = []

        for l in learnings:
            sid = l['skillId']
            lv = l['level']

            if lv == 1 and sid in shared_lv1:
                continue

            sk = get_skill(sid)
            info = parse_skill_info(sk) if sk else {
                'name':'???','desc':'','mp':0,'tp':0,
                'dtype':'-','scope':'-','type_str':'','element':''
            }

            entry = {'level': lv, 'sid': sid, 'info': info}

            if is_enemy_skill(sid):
                enemy_entries.append(entry)
            else:
                if lv <= 1:
                    char_entries[1].append(entry)
                elif lv <= 15:
                    char_entries[2].append(entry)
                elif lv <= 25:
                    char_entries[3].append(entry)
                else:
                    char_entries[4].append(entry)

        has_skills = any(char_entries[t] for t in [1,2,3,4])

        if has_skills:
            lines.append('| 階級 | Lv | ID | 名稱 | MP | TP | 類型 | 範圍 | 屬性 |')
            lines.append('|------|----|----|------|----|----|------|------|------|')

            for tier_num in [1, 2, 3, 4]:
                for e in char_entries[tier_num]:
                    info = e['info']
                    element = info.get('element', '') or '-'
                    type_str = info.get('type_str', '') or info['dtype']
                    scope = info['scope']
                    label = f'T{tier_num}'
                    lines.append(f'| {label} | {e["level"]} | #{e["sid"]} | **{info["name"]}** | {info["mp"]} | {info["tp"]} | {type_str} | {scope} | {element} |')

            lines.append('')

        if enemy_entries:
            lines.append(f'<details><summary>繼承敵技（{len(enemy_entries)} 個）</summary>')
            lines.append('')
            lines.append('| Lv | ID | 名稱 | 類型 | 範圍 |')
            lines.append('|----|-----|------|------|------|')
            for e in enemy_entries:
                info = e['info']
                type_str = info.get('type_str', '') or info['dtype']
                lines.append(f'| {e["level"]} | #{e["sid"]} | {info["name"]} | {type_str} | {info["scope"]} |')
            lines.append('')
            lines.append('</details>')
            lines.append('')

        if not has_skills and not enemy_entries:
            lines.append('> (無技能)')
            lines.append('')

    lines.append('---')
    lines.append('')

# Write output
output_path = os.path.join(base_dir, 'consilience-writer', 'references', '角色技能分級總表.md')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f'Done! Written {len(lines)} lines to {output_path}')
print(f'Total characters: {len(char_groups)}')
for g in char_groups:
    trait_names = [t['name'] for t in g['traits']]
    print(f'  {g["name"]}: {" / ".join(trait_names)}')
