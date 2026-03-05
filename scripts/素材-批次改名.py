#!/usr/bin/env python3
"""
rename_assets.py — 修正素材檔案命名違規，同步更新 JSON 資料參照
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import glob

PROJECT = r"C:\Consilience\Consilience"
DATA_DIR = os.path.join(PROJECT, "data")

# ═══ 重新命名清單 ═══
# (資料夾相對路徑, 舊檔名不含副檔名, 新檔名不含副檔名)
# RPG Maker JSON 中只存檔名（不含副檔名），所以只需替換 stem

RENAMES = [
    # ── img/faces/: Npc 缺底線 ──
    ("img/faces", "Npc村民成女",           "Npc_村民成女"),
    ("img/faces", "Npc村民老人",           "Npc_村民老人"),
    ("img/faces", "Npc村民婦人",           "Npc_村民婦人"),
    ("img/faces", "Npc村民成男",           "Npc_村民成男"),
    ("img/faces", "Npc村民蘿莉",           "Npc_村民蘿莉"),
    ("img/faces", "Npc村民正太",           "Npc_村民正太"),
    ("img/faces", "Npc仙池劍派女弟子",     "Npc_仙池劍派_女弟子"),
    ("img/faces", "Npc仙池劍派男弟子",     "Npc_仙池劍派_男弟子"),
    ("img/faces", "Npc仙池劍派_師叔雷霍",  "Npc_仙池劍派_師叔雷霍"),

    # ── img/faces/: 變體缺底線 ──
    ("img/faces", "Face17_珞堇OLD",       "Face17_珞堇_OLD"),

    # ── img/faces/: state 小寫 ──
    ("img/faces", "state_lemon",          "State_Lemon"),

    # ── img/characters/: 對應 state ──
    ("img/characters", "$state_lemon",    "$State_Lemon"),

    # ── img/enemies/: 連字號 ──
    ("img/enemies", "Darklord-final",     "Darklord_Final"),

    # ── img/pictures/: 連字號 ──
    ("img/pictures", "Darklord-final",    "Darklord_Final"),

    # ── img/system/: 雙底線 ──
    ("img/system", "Window__",            "Window_Alt"),

    # ── audio/bgm/: 小寫開頭 ──
    ("audio/bgm", "kashi_battle3_mvt",    "Kashi_Battle3_mvt"),

    # ── audio/bgm/: 拼寫錯誤 darkfntl → darkfnt ──
    ("audio/bgm", "Field_darkfntl2_mvt",  "Field_darkfnt2_mvt"),
    ("audio/bgm", "Thema_darkfntl4_mvt",  "Thema_darkfnt4_mvt"),
]


def find_file_ext(folder, stem):
    """找到實際檔案的副檔名"""
    folder_path = os.path.join(PROJECT, folder)
    for f in os.listdir(folder_path):
        name, ext = os.path.splitext(f)
        if name == stem:
            return ext
    return None


def update_json_references(old_stem, new_stem):
    """搜尋所有 JSON 資料檔，替換字串參照"""
    count = 0
    json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))

    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            content = f.read()

        if old_stem in content:
            new_content = content.replace(old_stem, new_stem)
            with open(jf, "w", encoding="utf-8") as f:
                f.write(new_content)
            basename = os.path.basename(jf)
            count += 1
            print(f"    JSON 更新: {basename}")

    return count


def main():
    print("=" * 60)
    print("  萬法同歸 — 素材檔案命名修正")
    print("=" * 60)

    total_renamed = 0
    total_json = 0
    errors = []

    for folder, old_stem, new_stem in RENAMES:
        ext = find_file_ext(folder, old_stem)
        if ext is None:
            errors.append(f"  找不到: {folder}/{old_stem}.*")
            continue

        old_path = os.path.join(PROJECT, folder, old_stem + ext)
        new_path = os.path.join(PROJECT, folder, new_stem + ext)

        if os.path.exists(new_path):
            errors.append(f"  目標已存在: {folder}/{new_stem}{ext}")
            continue

        # 重新命名檔案
        os.rename(old_path, new_path)
        print(f"\n  {folder}/{old_stem}{ext}")
        print(f"  → {folder}/{new_stem}{ext}")
        total_renamed += 1

        # 更新 JSON 參照
        json_count = update_json_references(old_stem, new_stem)
        total_json += json_count

    # ── 報告 ──
    print("\n" + "=" * 60)
    print(f"  重新命名: {total_renamed} 個檔案")
    print(f"  JSON 更新: {total_json} 個檔案")

    if errors:
        print(f"\n  警告 ({len(errors)}):")
        for e in errors:
            print(e)

    print("=" * 60)

    # ── 驗證 ──
    print("\n驗證...")
    missing = []
    for folder, _, new_stem in RENAMES:
        ext = find_file_ext(folder, new_stem)
        if ext is None:
            missing.append(f"  {folder}/{new_stem}")
    if missing:
        print("  以下檔案驗證失敗:")
        for m in missing:
            print(m)
    else:
        print("  所有重新命名的檔案皆已確認存在。")

    print("\n完成！")


if __name__ == "__main__":
    main()
