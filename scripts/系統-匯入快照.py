#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快照匯入工具

規則：
1. 第一次執行先做完整備份，資料夾名稱固定為「原檔」，包含 .git（commit 歷史）。
2. 第二次之後做快照備份，名稱為「快照_YYYYMMDD_HHMMSS」，
   只備份常用資產（音樂、圖片、資料庫、腳本與文件）。
3. 完成備份後，將 snapshot_root 的內容覆蓋匯入到 project_root。
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="匯入快照並自動備份專案")
    parser.add_argument(
        "--snapshot-root",
        required=True,
        help="快照來源根目錄（內部結構應與專案根目錄相同）",
    )
    parser.add_argument(
        "--project-root",
        default=r"C:\Consilience",
        help="目標專案根目錄，預設 C:\\Consilience",
    )
    parser.add_argument(
        "--backup-root",
        default=r"C:\Consilience\快照備份",
        help="備份根目錄，預設 C:\\Consilience\\快照備份",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只顯示將執行的動作，不實際寫入",
    )
    return parser.parse_args()


def safe_rmtree(path: Path, dry_run: bool) -> None:
    if not path.exists():
        return
    if dry_run:
        print(f"[DRY-RUN] remove {path}")
        return
    shutil.rmtree(path)


def copy_tree(src: Path, dst: Path, dry_run: bool) -> None:
    if not src.exists():
        return
    if dry_run:
        print(f"[DRY-RUN] copy {src} -> {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)


def copy_file(src: Path, dst: Path, dry_run: bool) -> None:
    if not src.exists():
        return
    if dry_run:
        print(f"[DRY-RUN] copy {src} -> {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def iter_project_items(project_root: Path, backup_root: Path) -> Iterable[Path]:
    for item in project_root.iterdir():
        if item.resolve() == backup_root.resolve():
            continue
        yield item


def create_full_backup(project_root: Path, backup_root: Path, dry_run: bool) -> Path:
    target = backup_root / "原檔"
    print(f"[備份] 第一次完整備份 -> {target}")
    safe_rmtree(target, dry_run=dry_run)
    for item in iter_project_items(project_root, backup_root):
        dst = target / item.name
        if item.is_dir():
            copy_tree(item, dst, dry_run=dry_run)
        elif item.is_file():
            copy_file(item, dst, dry_run=dry_run)
    return target


def create_snapshot_backup(project_root: Path, backup_root: Path, dry_run: bool) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = backup_root / f"快照_{ts}"
    print(f"[備份] 快照備份 -> {target}")

    # 第二次後只備份常變動資產，避免備份體積過大
    snapshot_paths = [
        Path("Consilience/audio"),
        Path("Consilience/img"),
        Path("Consilience/data"),
        Path("Consilience/js"),
        Path("docs"),
        Path("consilience-writer"),
    ]

    for rel in snapshot_paths:
        src = project_root / rel
        dst = target / rel
        if src.is_dir():
            copy_tree(src, dst, dry_run=dry_run)
        elif src.is_file():
            copy_file(src, dst, dry_run=dry_run)
    return target


def import_snapshot(snapshot_root: Path, project_root: Path, dry_run: bool) -> tuple[int, int]:
    copied_dirs = 0
    copied_files = 0
    for item in snapshot_root.iterdir():
        dst = project_root / item.name
        if item.is_dir():
            copy_tree(item, dst, dry_run=dry_run)
            copied_dirs += 1
        elif item.is_file():
            copy_file(item, dst, dry_run=dry_run)
            copied_files += 1
    return copied_dirs, copied_files


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    snapshot_root = Path(args.snapshot_root).resolve()
    backup_root = Path(args.backup_root).resolve()

    if not project_root.exists():
        raise SystemExit(f"[錯誤] project_root 不存在: {project_root}")
    if not snapshot_root.exists():
        raise SystemExit(f"[錯誤] snapshot_root 不存在: {snapshot_root}")

    if not args.dry_run:
        backup_root.mkdir(parents=True, exist_ok=True)

    original_backup = backup_root / "原檔"
    if original_backup.exists():
        backup_path = create_snapshot_backup(project_root, backup_root, args.dry_run)
    else:
        backup_path = create_full_backup(project_root, backup_root, args.dry_run)

    copied_dirs, copied_files = import_snapshot(snapshot_root, project_root, args.dry_run)

    print("\n=== 完成 ===")
    print(f"專案根目錄: {project_root}")
    print(f"快照來源: {snapshot_root}")
    print(f"備份位置: {backup_path}")
    print(f"匯入項目: 目錄 {copied_dirs} 個, 檔案 {copied_files} 個")
    if args.dry_run:
        print("模式: DRY-RUN（未實際寫入）")


if __name__ == "__main__":
    main()
