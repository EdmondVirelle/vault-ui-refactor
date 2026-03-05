"""
Reshuffle Actors.json so that Actor ID N matches image files $A{N}_xxx and Face{N}_xxx.
Preserves all character data (classId, equips, traits, note, profile, etc.)
and updates characterName, faceName, faceIndex, characterIndex, and Menu Portrait.
"""
import json
import re
import copy

INPUT = r"C:\Consilience\Consilience\data\Actors.json"

# ── Target mapping: image number → character name ──
IMAGE_TO_CHAR = {
    1: "東方啟",
    2: "青兒",
    3: "湮菲花",
    4: "闕崇陽",
    5: "絲塔娜",
    6: "瑤琴劍",
    7: "沅花",
    8: "談笑",
    9: "白沫檸",
    10: "珞堇",
    11: "龍玉",
    12: "司徒長生",
    13: "楊古晨",
    14: "殷染幽",
    15: "墨汐若",
    16: "聶思泠",
    17: "無名丐",
    18: "郭霆黃",
    19: "藍靜冥",
    20: "黃凱竹",
    21: "劉靜靜",
    22: "七霜",
    23: "莫縈懷",
}

# ── Name normalization: current JSON name → canonical name ──
NAME_FIXES = {
    "東方啓": "東方啟",
    "闕重陽": "闕崇陽",
}

# ── Portrait mapping: character name → Menu Portrait filename ──
PORTRAIT_MAP = {
    "東方啟": "狀態_東方啟",
    "青兒": "狀態_青兒",
    "湮菲花": "狀態_湮菲花",
    "闕崇陽": "狀態_闕崇陽",
    "絲塔娜": "狀態_絲塔娜",
    "瑤琴劍": "狀態_瑤琴劍",
    "沅花": "狀態_沅花",
    "談笑": "狀態_談笑",
    "白沫檸": "狀態_白沫檸",
    "珞堇": "狀態_珞堇",
    "龍玉": "狀態_龍玉",
    "司徒長生": "狀態_司徒長生",
    "楊古晨": "狀態_楊古晨",
    "殷染幽": "狀態_殷染幽",
    "墨汐若": "狀態_墨汐若",
    "聶思泠": "狀態_聶思泠",
    "無名丐": "狀態_無名丐",
    "郭霆黃": "狀態_郭霆黃",
    "藍靜冥": "狀態_藍靜冥",
    "黃凱竹": "狀態_黃凱竹",
    "劉靜靜": "狀態_劉靜靜",
    "七霜": "狀態_七霜",
    "莫縈懷": "狀態_莫縈懷",
}


def normalize_name(name: str) -> str:
    return NAME_FIXES.get(name, name)


def update_portrait_in_note(note: str, char_name: str) -> str:
    """Update or add <Menu Portrait: xxx> in the note field."""
    portrait = PORTRAIT_MAP.get(char_name)
    if not portrait:
        return note

    # Replace existing Menu Portrait line
    if "<Menu Portrait:" in note:
        note = re.sub(
            r"<Menu Portrait:\s*[^>]*>",
            f"<Menu Portrait: {portrait}>",
            note,
        )
    else:
        # Add after </Trait Sets> if it exists
        if "</Trait Sets>" in note:
            note = note.replace(
                "</Trait Sets>",
                f"</Trait Sets>\n<Menu Portrait: {portrait}>",
            )
    return note


def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        actors = json.load(f)

    # Build name → actor data mapping (using canonical names)
    name_to_data = {}
    for actor in actors:
        if actor is None:
            continue
        raw_name = actor.get("name", "")
        if not raw_name:
            continue
        canonical = normalize_name(raw_name)
        name_to_data[canonical] = copy.deepcopy(actor)

    # Build new array: [null, actor1, actor2, ..., actor23, empty24, empty25, empty26]
    new_actors = [None]  # index 0 is always null

    for target_id in range(1, 24):
        char_name = IMAGE_TO_CHAR[target_id]
        if char_name not in name_to_data:
            print(f"WARNING: No data found for {char_name} (target ID {target_id})")
            # Create minimal placeholder
            new_actors.append({
                "id": target_id,
                "battlerName": "",
                "characterIndex": 0,
                "characterName": f"$A{target_id}_{char_name}",
                "classId": 1,
                "equips": [0, 0, 0, 0, 0],
                "faceIndex": 0,
                "faceName": f"Face{target_id}_{char_name}",
                "traits": [],
                "initialLevel": 1,
                "maxLevel": 99,
                "name": char_name,
                "nickname": "",
                "note": "",
                "profile": "",
            })
            continue

        actor = name_to_data[char_name]

        # Update fields
        actor["id"] = target_id
        actor["name"] = char_name  # fix typos
        actor["characterName"] = f"$A{target_id}_{char_name}"
        actor["characterIndex"] = 0  # $ prefix = single sprite
        actor["faceName"] = f"Face{target_id}_{char_name}"
        actor["faceIndex"] = 0

        # Update Menu Portrait in note
        actor["note"] = update_portrait_in_note(actor["note"], char_name)

        new_actors.append(actor)

    # Add empty slots for IDs 24-26 (preserve array length)
    for empty_id in range(24, 27):
        new_actors.append({
            "id": empty_id,
            "battlerName": "",
            "characterIndex": 0,
            "characterName": "",
            "classId": 1,
            "equips": [0, 0, 0, 0, 0],
            "faceIndex": 0,
            "faceName": "",
            "traits": [],
            "initialLevel": 1,
            "maxLevel": 99,
            "name": "",
            "nickname": "",
            "note": "",
            "profile": "",
        })

    # Verify
    print("=== Actor Reshuffling Result ===")
    for i, actor in enumerate(new_actors):
        if actor is None:
            continue
        name = actor.get("name", "(empty)")
        char = actor.get("characterName", "")
        face = actor.get("faceName", "")
        portrait_match = re.search(r"<Menu Portrait:\s*([^>]*)>", actor.get("note", ""))
        portrait = portrait_match.group(1) if portrait_match else "(none)"
        print(f"  ID {actor['id']:2d}: {name:6s}  walk={char:20s}  face={face:20s}  portrait={portrait}")

    # Write in RPG Maker MZ format: [\nnull,\n{actor1},\n{actor2},\n...\n{actorN}\n]
    with open(INPUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("[\n")
        for i, actor in enumerate(new_actors):
            if actor is None:
                line = "null"
            else:
                line = json.dumps(actor, ensure_ascii=False, separators=(",", ":"))
            if i < len(new_actors) - 1:
                f.write(line + ",\n")
            else:
                f.write(line + "\n")
        f.write("]\n")

    print(f"\nWritten to {INPUT} (RPG Maker format)")


if __name__ == "__main__":
    main()
