"""
Organize project root: delete junk files, move misplaced files,
and categorize screenshots into docs/screenshots/.

Usage:
    python scripts/cleanup_project.py          # dry-run (preview only)
    python scripts/cleanup_project.py --apply  # actually perform changes
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DRY_RUN = "--apply" not in sys.argv

# ── Files to DELETE ──────────────────────────────────────────────
DELETE = [
    BASE / "nul",                              # Windows artifact
    BASE / "Consilience" / "data" / "nul",     # Windows artifact
    BASE / "tmp_system.json",                  # temp debug file
    BASE / "gui_error.log",                    # GUI test output
    BASE / "gui_out.txt",                      # GUI test output
    BASE / "actor_stats.txt",                  # temp output
    BASE / "_logs" / "build.log",              # old build log
]

# Playwright console logs (all of them)
PW_DIR = BASE / ".playwright-mcp"
if PW_DIR.exists():
    DELETE.extend(sorted(PW_DIR.glob("console-*.log")))

# ── Files to MOVE ────────────────────────────────────────────────
MOVE = [
    (BASE / "parse_data.py", BASE / "scripts" / "parse_data.py"),
]

# ── Screenshots → docs/screenshots/ ─────────────────────────────
SCREENSHOT_DIR = BASE / "docs" / "screenshots"
SCREENSHOTS = [
    "keybinds-preview.png",
    "keybinds-v2.png",
    "keybinds-v3.png",
    "keybinds-v4.png",
    "keybinds-1920.png",
    "guide-page.png",
    "guide-page-bottom.png",
    "guide-keyboard-raw.png",
    "guide-keyboard-1280x720.png",
]
for name in SCREENSHOTS:
    src = BASE / name
    if src.exists():
        MOVE.append((src, SCREENSHOT_DIR / name))


def main():
    if DRY_RUN:
        print("=== DRY RUN (preview only) ===")
        print("Add --apply to actually perform changes.\n")
    else:
        print("=== APPLYING CHANGES ===\n")

    # ── Deletions ─────────────────────────────────────────────
    print("[1] Files to DELETE:")
    deleted = 0
    for f in DELETE:
        if f.exists():
            size = f.stat().st_size
            print(f"  DEL  {f.relative_to(BASE)}  ({size:,} bytes)")
            if not DRY_RUN:
                try:
                    f.unlink()
                except OSError:
                    # Windows reserved names (nul, con, etc.) need \\?\ prefix
                    long_path = f"\\\\?\\{f}"
                    try:
                        os.remove(long_path)
                    except OSError:
                        # Last resort: del command
                        subprocess.run(
                            ["cmd", "/c", f'del "\\\\?\\{f}"'],
                            check=False, capture_output=True,
                        )
                        if f.exists():
                            print(f"  WARN: Could not delete {f.relative_to(BASE)}")
            deleted += 1
        else:
            print(f"  SKIP {f.relative_to(BASE)}  (not found)")
    print(f"  Total: {deleted} files\n")

    # ── Moves ─────────────────────────────────────────────────
    print("[2] Files to MOVE:")
    moved = 0
    for src, dst in MOVE:
        if not src.exists():
            print(f"  SKIP {src.relative_to(BASE)} → {dst.relative_to(BASE)}  (source not found)")
            continue
        if dst.exists():
            print(f"  SKIP {src.relative_to(BASE)} → {dst.relative_to(BASE)}  (destination exists)")
            continue
        print(f"  MOVE {src.relative_to(BASE)} → {dst.relative_to(BASE)}")
        if not DRY_RUN:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        moved += 1
    print(f"  Total: {moved} files\n")

    # ── Cleanup empty dirs ────────────────────────────────────
    print("[3] Empty directory cleanup:")
    empty_dirs = [
        BASE / "_logs",
    ]
    cleaned = 0
    for d in empty_dirs:
        if d.exists() and not any(d.iterdir()):
            print(f"  RMDIR {d.relative_to(BASE)}")
            if not DRY_RUN:
                d.rmdir()
            cleaned += 1
        elif d.exists():
            remaining = list(d.iterdir())
            print(f"  SKIP  {d.relative_to(BASE)}  (still has {len(remaining)} items)")
        else:
            print(f"  SKIP  {d.relative_to(BASE)}  (not found)")
    print(f"  Total: {cleaned} dirs\n")

    # ── Summary ───────────────────────────────────────────────
    print("=" * 50)
    print(f"Summary: {deleted} deleted, {moved} moved, {cleaned} dirs cleaned")
    if DRY_RUN:
        print("\nThis was a DRY RUN. Run with --apply to execute.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
