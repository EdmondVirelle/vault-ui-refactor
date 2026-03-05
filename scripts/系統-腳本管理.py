"""
萬法同歸 — 腳本管理工具
=======================
CustomTkinter GUI，一鍵執行 scripts/ 下的 14 個 Python 腳本。

啟動方式：
    python scripts/系統-腳本管理.py

功能：
    - 左側腳本清單（按分類分組）
    - 右側控制面板（描述 + 參數 + Run/Stop）
    - 即時日誌串流 + 進度條
    - 匯出劇本章節選擇器（9 章 checkbox + 支線 toggle）
    - 路徑設定對話框（儲存至 scripts/gui_config.json）
    - JSON 寫入警告（提醒關閉 RPG Maker）
"""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue, Empty
from tkinter import filedialog, messagebox

import customtkinter as ctk

# ═══════════════════════════════════════════════════════════════
#  Config — 路徑設定 load / save
# ═══════════════════════════════════════════════════════════════

CONFIG_PATH = Path(__file__).parent / "gui_config.json"
DEFAULT_ROOT = str(Path(__file__).resolve().parent.parent)   # …/Consilience

_DERIVED = {
    "game_data":       r"Consilience\data",
    "writer_dir":      r"consilience-writer",
    "docs_dir":        r"docs",
    "plugins_dir":     r"Consilience\js\plugins",
    "frontend_public": r"consilience-web\frontend\public\images\faces",
}


def _cfg_defaults(root: str = DEFAULT_ROOT) -> dict:
    root_p = Path(root)
    cfg = {"project_root": root}
    for key, rel in _DERIVED.items():
        cfg[key] = str(root_p / rel)
    return cfg


def cfg_load() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return _cfg_defaults()


def cfg_save(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
#  Script Registry — 14 個腳本元資料
# ═══════════════════════════════════════════════════════════════

@dataclass
class ScriptMeta:
    id: str
    name: str
    description: str
    script_path: str          # relative to project_root
    category: str
    writes_json: bool = False
    needs_cwd: bool = True
    has_chapter_args: bool = False
    dependencies: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)


SCRIPTS: list[ScriptMeta] = [
    # ── 劇本 ──
    ScriptMeta(
        id="export_scripts",
        name="匯出劇本到Excel",
        description="將 Markdown 劇本匯出到設計文件 Excel，支援選擇章節。\n"
                    "可選擇序章～第八章，以及是否包含支線擴充。",
        script_path=r"scripts\劇本-匯出Excel.py",
        category="劇本",
        has_chapter_args=True,
        dependencies=["openpyxl"],
        outputs=[r"docs\萬法同歸_設計文件.xlsx"],
    ),
    ScriptMeta(
        id="sync_scripts",
        name="同步劇本到Excel",
        description="將序章、第一章的 Markdown 差異同步回 Excel（增刪改對照），\n"
                    "同時更新世界觀分頁。只處理序章 + 第一章。",
        script_path=r"scripts\劇本-同步Excel.py",
        category="劇本",
        dependencies=["openpyxl"],
        outputs=[r"docs\萬法同歸_設計文件.xlsx"],
    ),
    # ── 角色 ──
    ScriptMeta(
        id="sync_actors_excel",
        name="同步角色到Excel",
        description="讀取 Actors.json，同步角色資料（名稱、稱號、等級、簡介、備註）到 Excel。",
        script_path=r"scripts\角色-同步Excel.py",
        category="角色",
        dependencies=["openpyxl"],
        outputs=[r"docs\萬法同歸_資料庫.xlsx"],
    ),
    ScriptMeta(
        id="update_profiles",
        name="角色簡介更新",
        description="更新 Actors.json 中角色的 profile（狀態畫面簡介）\n"
                    "和 <Biography> notetag。",
        script_path=r"scripts\角色-更新簡介.py",
        category="角色",
        writes_json=True,
        outputs=[r"Consilience\data\Actors.json"],
    ),
    ScriptMeta(
        id="sync_images",
        name="角色圖片同步",
        description="重新排列 Actors.json，讓 Actor ID 與圖片編號一致。\n"
                    "會重建整個 Actors 陣列，跑完務必用 RPG Maker 測試。",
        script_path=r"scripts\角色-同步圖片.py",
        category="角色",
        writes_json=True,
        outputs=[r"Consilience\data\Actors.json"],
    ),
    ScriptMeta(
        id="gen_classes",
        name="生成職業",
        description="為 23 位角色各生成 3 種職業變體\n"
                    "（A 均衡、B 攻擊特化、C 防禦特化），共 69 個職業。",
        script_path=r"scripts\職業-生成資料.py",
        category="角色",
        writes_json=True,
        outputs=[r"Consilience\data\Classes.json",
                 r"Consilience\data\Actors.json",
                 r"Consilience\data\actor_class_mapping.json"],
    ),
    ScriptMeta(
        id="gen_weapons",
        name="生成角色武器",
        description="為 22 位角色各生成 6 把專屬武器（6 階漸強），\n"
                    "共 154 筆寫入 Weapons.json（ID 151 起）。",
        script_path=r"scripts\角色-生成武器.py",
        category="角色",
        writes_json=True,
        outputs=[r"Consilience\data\Weapons.json"],
    ),
    # ── 敵人 ──
    ScriptMeta(
        id="gen_enemies",
        name="生成敵人",
        description="生成敵人技能（Skills 32–250）和敵人資料（Enemies 3–91）。\n"
                    "需要 git 在 PATH 中。",
        script_path=r"scripts\敵人-生成資料.py",
        category="敵人",
        writes_json=True,
        outputs=[r"Consilience\data\Skills.json",
                 r"Consilience\data\Enemies.json"],
    ),
    ScriptMeta(
        id="fix_enemy_tags",
        name="敵人標籤修正",
        description="為所有敵人（ID 4–91）補上完整的 VisuStella notetag。\n"
                    "通常接在「生成敵人」之後執行。",
        script_path=r"scripts\敵人-修補標籤.py",
        category="敵人",
        writes_json=True,
        outputs=[r"Consilience\data\Enemies.json"],
    ),
    # ── 素材 ──
    ScriptMeta(
        id="rename_assets",
        name="素材批次改名",
        description="批次修正素材檔名（連字號→底線、缺少底線、大小寫錯誤），\n"
                    "同時自動更新 data/*.json 中的所有引用。",
        script_path=r"scripts\素材-批次改名.py",
        category="素材",
        writes_json=True,
    ),
    ScriptMeta(
        id="crop_faces",
        name="裁切頭像",
        description="從 RPG Maker 頭像圖（4×2 格）裁切左上角第一格，\n"
                    "存為網站用的角色頭像 (144×144 PNG)。",
        script_path=r"scripts\素材-裁切頭像.py",
        category="素材",
        dependencies=["Pillow"],
        outputs=[r"consilience-web\frontend\public\images\faces"],
    ),
    # ── 插件 ──
    ScriptMeta(
        id="extract_plugins",
        name="提取插件文檔",
        description="從所有 VisuStella 插件的 @help 區塊提取文檔，\n"
                    "產出每個插件的 .txt 摘要。",
        script_path=r"scripts\插件-提取文檔.py",
        category="插件",
        outputs=[r"scripts\plugin_extracts"],
    ),
    ScriptMeta(
        id="plugin_reference",
        name="插件語法參考",
        description="讀取插件摘要，整合成 notetag / 插件指令語法參考。\n"
                    "需先執行「提取插件文檔」。",
        script_path=r"scripts\插件-語法參考.py",
        category="插件",
        outputs=[r"consilience-writer\references\visustella-notetags.md"],
    ),
    # ── 數值 ──
    ScriptMeta(
        id="damage_calc",
        name="傷害計算表",
        description="生成 7 個分頁的傷害計算 Excel：招式資料、角色數值、\n"
                    "敵人數值、元素抗性、攻擊模擬、招式速查。",
        script_path=r"scripts\戰鬥-傷害計算表.py",
        category="數值",
        dependencies=["openpyxl"],
        outputs=[r"萬法同歸_傷害計算表.xlsx"],
    ),
]

CATEGORIES = ["劇本", "角色", "敵人", "素材", "插件", "數值"]


# ═══════════════════════════════════════════════════════════════
#  Runner — subprocess 執行器
# ═══════════════════════════════════════════════════════════════

class ScriptRunner:
    """Runs a Python script in a subprocess, streaming output via a queue."""

    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self.queue: Queue[str | None] = Queue()
        self.running = False
        self.return_code: int | None = None

    def start(self, script_path: str, cwd: str, extra_args: list[str] | None = None):
        if self.running:
            raise RuntimeError("已有腳本在執行中")
        cmd = [sys.executable, "-u", script_path]
        if extra_args:
            cmd.extend(extra_args)
        self.return_code = None
        self.running = True
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except Empty:
                break
        self._thread = threading.Thread(target=self._run, args=(cmd, cwd), daemon=True)
        self._thread.start()

    def _run(self, cmd: list[str], cwd: str):
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=cwd,
                env=env,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in self._process.stdout:
                self.queue.put(line)
            self._process.wait()
            self.return_code = self._process.returncode
        except Exception as exc:
            self.queue.put(f"\n[ERROR] {exc}\n")
            self.return_code = -1
        finally:
            self.running = False
            self._process = None
            self.queue.put(None)

    def stop(self):
        proc = self._process
        if proc and proc.poll() is None:
            proc.kill()
            self.queue.put("\n[中止] 腳本已被終止\n")

    def poll(self, max_lines: int = 200) -> tuple[list[str], bool]:
        lines: list[str] = []
        done = False
        for _ in range(max_lines):
            try:
                item = self.queue.get_nowait()
            except Empty:
                break
            if item is None:
                done = True
                break
            lines.append(item)
        return lines, done


# ═══════════════════════════════════════════════════════════════
#  Widgets
# ═══════════════════════════════════════════════════════════════

# ── LogPanel ──

class LogPanel(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=4, pady=(4, 0))
        ctk.CTkLabel(toolbar, text="執行日誌",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(toolbar, text="儲存日誌", width=80, height=28,
                      command=self._save_log).pack(side="right", padx=2)
        ctk.CTkButton(toolbar, text="清除", width=60, height=28,
                      command=self.clear).pack(side="right", padx=2)

        self._progress = ctk.CTkProgressBar(self, mode="indeterminate", height=3)
        self._progress.pack(fill="x", padx=4, pady=(4, 0))
        self._progress.set(0)

        self._textbox = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word", state="disabled", activate_scrollbars=True,
        )
        self._textbox.pack(fill="both", expand=True, padx=4, pady=4)

    def append(self, text: str):
        self._textbox.configure(state="normal")
        self._textbox.insert("end", text)
        self._textbox.see("end")
        self._textbox.configure(state="disabled")

    def clear(self):
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.configure(state="disabled")

    def start_progress(self):
        self._progress.start()

    def stop_progress(self):
        self._progress.stop()
        self._progress.set(0)

    def _save_log(self):
        text = self._textbox.get("1.0", "end").strip()
        if not text:
            return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"log_{ts}.txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")],
        )
        if path:
            Path(path).write_text(text, encoding="utf-8")


# ── ChapterSelector ──

CHAPTERS = [
    (0, "序章　黃裳典籍"),
    (1, "第一章　劃月風雲"),
    (2, "第二章　西域來風"),
    (3, "第三章　暗流湧動"),
    (4, "第四章　逍遙雲霧"),
    (5, "第五章　梅莊庇護"),
    (6, "第六章　陰山暗影"),
    (7, "第七章　江湖再起"),
    (8, "第八章　萬法同歸"),
]


class ChapterSelector(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        ctk.CTkLabel(self, text="選擇章節",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=8, pady=(6, 2))

        self._vars: list[ctk.BooleanVar] = []
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=8)
        for i, (_idx, label) in enumerate(CHAPTERS):
            var = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(grid, text=label, variable=var, width=200)
            row, col = divmod(i, 3)
            cb.grid(row=row, column=col, sticky="w", padx=4, pady=2)
            self._vars.append(var)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(4, 0))
        ctk.CTkButton(btn_row, text="全選", width=60, height=28,
                      command=lambda: [v.set(True) for v in self._vars]).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="全不選", width=60, height=28,
                      command=lambda: [v.set(False) for v in self._vars]).pack(side="left", padx=2)

        self._expansion_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(btn_row, text="包含支線擴充 (--with-expansion)",
                        variable=self._expansion_var).pack(side="left", padx=(16, 0))

    def selected_chapters(self) -> list[int]:
        return [i for i, var in enumerate(self._vars) if var.get()]

    def with_expansion(self) -> bool:
        return self._expansion_var.get()


# ── ScriptPanel ──

class ScriptPanel(ctk.CTkFrame):
    def __init__(self, master, on_run, on_stop, **kw):
        super().__init__(master, **kw)
        self._on_run = on_run
        self._on_stop = on_stop
        self._current: ScriptMeta | None = None

        self._title = ctk.CTkLabel(self, text="選擇左側腳本",
                                   font=ctk.CTkFont(size=16, weight="bold"), anchor="w")
        self._title.pack(fill="x", padx=12, pady=(10, 0))

        self._category = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11),
                                      text_color="#888888", anchor="w")
        self._category.pack(fill="x", padx=12)

        self._desc = ctk.CTkLabel(self, text="", anchor="nw", justify="left",
                                  wraplength=500, font=ctk.CTkFont(size=12))
        self._desc.pack(fill="x", padx=12, pady=(6, 0))

        self._outputs_label = ctk.CTkLabel(self, text="", anchor="w", justify="left",
                                           text_color="#aaaaaa", font=ctk.CTkFont(size=11))
        self._outputs_label.pack(fill="x", padx=12, pady=(4, 0))

        self._chapter_sel = ChapterSelector(self)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(10, 8))
        self._run_btn = ctk.CTkButton(
            btn_frame, text="▶  執行", width=120, height=36,
            fg_color="#2d7d46", hover_color="#3a9e5a", command=self._handle_run,
        )
        self._run_btn.pack(side="left", padx=(0, 8))
        self._stop_btn = ctk.CTkButton(
            btn_frame, text="■  停止", width=100, height=36,
            fg_color="#8b2500", hover_color="#b03020",
            command=self._on_stop, state="disabled",
        )
        self._stop_btn.pack(side="left")

    def show_script(self, meta: ScriptMeta):
        self._current = meta
        self._title.configure(text=meta.name)
        self._category.configure(text=f"分類：{meta.category}")
        self._desc.configure(text=meta.description)
        self._outputs_label.configure(
            text=("輸出：" + "、".join(meta.outputs)) if meta.outputs else ""
        )
        if meta.has_chapter_args:
            self._chapter_sel.pack(fill="x", padx=8, pady=(4, 0),
                                   before=self._run_btn.master)
        else:
            self._chapter_sel.pack_forget()

    def set_running(self, running: bool):
        self._run_btn.configure(state="disabled" if running else "normal")
        self._stop_btn.configure(state="normal" if running else "disabled")

    def get_extra_args(self) -> list[str]:
        if not self._current or not self._current.has_chapter_args:
            return []
        args = [str(ch) for ch in self._chapter_sel.selected_chapters()]
        if self._chapter_sel.with_expansion():
            args.append("--with-expansion")
        return args

    def _handle_run(self):
        meta = self._current
        if not meta:
            return
        if meta.writes_json:
            ok = messagebox.askokcancel(
                "JSON 寫入警告",
                f"腳本「{meta.name}」會修改 data/*.json。\n\n"
                "請確認已關閉 RPG Maker MZ，否則修改會被覆蓋。\n\n"
                "是否繼續執行？",
                icon="warning",
            )
            if not ok:
                return
        self._on_run(meta, self.get_extra_args())


# ── PathSettingsDialog ──

_PATH_LABELS = {
    "project_root":    "專案根目錄",
    "game_data":       "遊戲資料 (data/)",
    "writer_dir":      "劇本目錄 (writer/)",
    "docs_dir":        "文件輸出 (docs/)",
    "plugins_dir":     "插件目錄 (plugins/)",
    "frontend_public": "前端頭像 (faces/)",
}


class PathSettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, cfg: dict, on_save):
        super().__init__(master)
        self.title("路徑設定")
        self.geometry("700x420")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._cfg = dict(cfg)
        self._on_save = on_save
        self._entries: dict[str, ctk.CTkEntry] = {}

        form = ctk.CTkScrollableFrame(self)
        form.pack(fill="both", expand=True, padx=16, pady=(16, 8))

        for i, (key, label) in enumerate(_PATH_LABELS.items()):
            ctk.CTkLabel(form, text=label, anchor="w").grid(
                row=i, column=0, sticky="w", padx=(0, 8), pady=4)
            entry = ctk.CTkEntry(form, width=420)
            entry.insert(0, self._cfg.get(key, ""))
            entry.grid(row=i, column=1, sticky="ew", pady=4)
            self._entries[key] = entry
            ctk.CTkButton(form, text="瀏覽", width=60, height=28,
                          command=lambda k=key: self._browse(k)).grid(
                row=i, column=2, padx=(4, 0), pady=4)

        form.grid_columnconfigure(1, weight=1)
        self._entries["project_root"].bind("<FocusOut>", self._on_root_change)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(bottom, text="儲存", width=100,
                      command=self._save).pack(side="right", padx=4)
        ctk.CTkButton(bottom, text="重設為預設", width=100,
                      command=self._reset).pack(side="right", padx=4)
        ctk.CTkButton(bottom, text="取消", width=80,
                      command=self.destroy).pack(side="right")

    def _browse(self, key: str):
        path = filedialog.askdirectory(title=_PATH_LABELS.get(key, key))
        if path:
            entry = self._entries[key]
            entry.delete(0, "end")
            entry.insert(0, path)
            if key == "project_root":
                self._on_root_change()

    def _on_root_change(self, _event=None):
        new_root = self._entries["project_root"].get().strip()
        if not new_root:
            return
        root_p = Path(new_root)
        for key, rel in _DERIVED.items():
            entry = self._entries.get(key)
            if entry:
                entry.delete(0, "end")
                entry.insert(0, str(root_p / rel))

    def _reset(self):
        defaults = _cfg_defaults()
        for key, entry in self._entries.items():
            entry.delete(0, "end")
            entry.insert(0, defaults.get(key, ""))

    def _save(self):
        for key, entry in self._entries.items():
            self._cfg[key] = entry.get().strip()
        cfg_save(self._cfg)
        self._on_save(self._cfg)
        self.destroy()


# ═══════════════════════════════════════════════════════════════
#  App — 主視窗
# ═══════════════════════════════════════════════════════════════

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("萬法同歸 — 腳本管理工具")
        self.geometry("1200x750")
        self.minsize(900, 550)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._cfg = cfg_load()
        self._runner = ScriptRunner()
        self._build_ui()
        self._show_welcome()

    def _build_ui(self):
        # ── toolbar ──
        toolbar = ctk.CTkFrame(self, height=40, corner_radius=0)
        toolbar.pack(fill="x")
        ctk.CTkLabel(toolbar, text="萬法同歸 腳本管理工具",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=12)
        ctk.CTkButton(toolbar, text="⚙ 設定", width=80, height=30,
                      command=self._open_settings).pack(side="right", padx=4, pady=4)
        ctk.CTkButton(toolbar, text="📂 開啟輸出資料夾", width=140, height=30,
                      command=self._open_output_dir).pack(side="right", padx=4, pady=4)

        # ── main ──
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=4, pady=4)

        left = ctk.CTkFrame(main, width=300)
        left.pack(side="left", fill="y", padx=(0, 4))
        left.pack_propagate(False)
        self._build_script_list(left)

        right = ctk.CTkFrame(main, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)
        self._script_panel = ScriptPanel(right, on_run=self._run_script,
                                         on_stop=self._stop_script)
        self._script_panel.pack(fill="x")
        self._log_panel = LogPanel(right)
        self._log_panel.pack(fill="both", expand=True, pady=(4, 0))

        # ── status bar ──
        self._status = ctk.CTkLabel(
            self, text=f"專案：{self._cfg.get('project_root', '?')}",
            font=ctk.CTkFont(size=11), text_color="#888888", anchor="w",
        )
        self._status.pack(fill="x", padx=8, pady=(0, 4))

    def _build_script_list(self, parent):
        ctk.CTkLabel(parent, text="腳本清單",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(padx=8, pady=(8, 4), anchor="w")
        scroll = ctk.CTkScrollableFrame(parent)
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self._list_buttons: list[ctk.CTkButton] = []
        by_cat: dict[str, list[ScriptMeta]] = {c: [] for c in CATEGORIES}
        for s in SCRIPTS:
            by_cat[s.category].append(s)

        for cat in CATEGORIES:
            scripts = by_cat.get(cat, [])
            if not scripts:
                continue
            ctk.CTkLabel(scroll, text=cat, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#aaaaaa").pack(anchor="w", padx=4, pady=(8, 2))
            for meta in scripts:
                prefix = "⚠ " if meta.writes_json else "   "
                btn = ctk.CTkButton(
                    scroll, text=f"{prefix}{meta.name}", anchor="w", height=32,
                    fg_color="transparent", text_color="#dddddd", hover_color="#333333",
                    command=lambda m=meta: self._select_script(m),
                )
                btn.pack(fill="x", padx=2, pady=1)
                btn._script_id = meta.id
                self._list_buttons.append(btn)

    # ── actions ──

    def _select_script(self, meta: ScriptMeta):
        for btn in self._list_buttons:
            btn.configure(fg_color="#1a5276" if btn._script_id == meta.id else "transparent")
        self._script_panel.show_script(meta)

    def _run_script(self, meta: ScriptMeta, extra_args: list[str]):
        root = self._cfg.get("project_root", DEFAULT_ROOT)
        script_full = str(Path(root) / meta.script_path)

        if not Path(script_full).exists():
            self._log_panel.append(f"[錯誤] 找不到腳本：{script_full}\n")
            return

        cwd = root if meta.needs_cwd else str(Path(script_full).parent)
        self._log_panel.append(f"{'─' * 50}\n")
        self._log_panel.append(f"▶ 執行：{meta.name}\n")
        self._log_panel.append(f"  路徑：{script_full}\n")
        if extra_args:
            self._log_panel.append(f"  參數：{' '.join(extra_args)}\n")
        self._log_panel.append(f"{'─' * 50}\n")

        self._script_panel.set_running(True)
        self._log_panel.start_progress()
        try:
            self._runner.start(script_full, cwd, extra_args)
        except RuntimeError as e:
            self._log_panel.append(f"[錯誤] {e}\n")
            self._script_panel.set_running(False)
            self._log_panel.stop_progress()
            return
        self._poll_output()

    def _stop_script(self):
        self._runner.stop()

    def _poll_output(self):
        lines, done = self._runner.poll()
        for line in lines:
            self._log_panel.append(line)
        if done:
            rc = self._runner.return_code
            if rc == 0:
                self._log_panel.append("\n✔ 執行完成\n\n")
            else:
                self._log_panel.append(f"\n✘ 執行結束（exit code {rc}）\n\n")
            self._script_panel.set_running(False)
            self._log_panel.stop_progress()
        else:
            self.after(100, self._poll_output)

    def _open_settings(self):
        PathSettingsDialog(self, self._cfg, on_save=self._apply_config)

    def _apply_config(self, new_cfg: dict):
        self._cfg = new_cfg
        self._status.configure(text=f"專案：{new_cfg.get('project_root', '?')}")

    def _show_welcome(self):
        self._log_panel.append(
            "╔══════════════════════════════════════════════╗\n"
            "║     萬法同歸 — 腳本管理工具                 ║\n"
            "╚══════════════════════════════════════════════╝\n"
            "\n"
            "使用方式：\n"
            "  1. 從左側清單點選要執行的腳本\n"
            "  2. 右上方會顯示腳本說明和輸出檔案路徑\n"
            "  3. 按「▶ 執行」開始，日誌會即時顯示在這裡\n"
            "  4. 執行中可按「■ 停止」中斷腳本\n"
            "\n"
            "範例操作：\n"
            "  ● 匯出第三章劇本到 Excel：\n"
            "      左側點「匯出劇本到Excel」→ 只勾第三章 → 按執行\n"
            "\n"
            "  ● 匯出全部章節 + 支線：\n"
            "      點「匯出劇本到Excel」→ 全選 → 勾「包含支線擴充」→ 按執行\n"
            "\n"
            "  ● 生成敵人（完整流程）：\n"
            "      先跑「生成敵人」→ 再跑「敵人標籤修正」→ 最後跑「傷害計算表」\n"
            "\n"
            "注意事項：\n"
            "  ⚠ 標示的腳本會修改 data/*.json，執行前請先關閉 RPG Maker MZ\n"
            "  ⚙ 點右上角「設定」可修改專案路徑\n"
            "\n"
        )

    def _open_output_dir(self):
        docs = self._cfg.get("docs_dir", "")
        if docs and Path(docs).is_dir():
            os.startfile(docs)
        else:
            root = self._cfg.get("project_root", DEFAULT_ROOT)
            if Path(root).is_dir():
                os.startfile(root)


# ═══════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    App().mainloop()
