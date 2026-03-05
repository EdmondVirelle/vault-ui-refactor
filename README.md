# Vault UI Refactor

Consilience Vault 的 Tauri + Rust + React 桌面工具重構版。

目前核心目標是「實用優先」：
- 任務面板（匯入/匯出/診斷/路徑設定）
- 傷害計算機分頁（專用，取代腳本工作臺）

## 功能概要

1. 任務面板
- 讀取 `tasks.json` 動態任務
- 支援每個任務獨立路徑策略（顯示/隱藏匯入匯出路徑、默認路徑）
- 執行任務時即時顯示日誌與狀態
- 支援停止任務與環境診斷

2. 傷害計算機
- 僅載入檔名含「傷害計算表」的 Python 腳本
- 自動解析腳本參數並生成輸入欄位
- 支援執行、停止、即時日誌

3. 劇本匯入（Python）
- `scripts/劇本-匯出Excel.py` 已調整為：
  - 匯入 `consilience-writer` 的序章～第八章前綴檔
  - 自動分類劇本/任務內容
  - 各章產生「整合」分頁
  - 路人觸發對話彙整到單一總表
  - 依劇本序號自動整理任務索引

## 專案結構

```text
vault-ui-refactor/
  src/                  # React 前端
  src-tauri/            # Rust / Tauri 後端
  scripts/              # Python 工具腳本
  tasks.json            # 任務定義（配置驅動）
  gui_config.json       # 專案路徑與執行設定
```

## 開發環境

- Node.js 20+
- Rust stable（建議已安裝 cargo）
- Python 3.10+
- Windows 10/11（目前配置預設 Windows 路徑）

## 安裝與啟動

```bash
npm install
npm run tauri dev
```

## 常用指令

```bash
# 僅前端型別檢查
npx tsc --noEmit

# Rust 檢查
cd src-tauri
cargo check
```

## 重要設定

1. `gui_config.json`
- `project_root`: 專案根路徑
- `scripts_dir`: Python 腳本資料夾
- `docs_dir`: 報表輸出資料夾
- `python_path`: Python 執行檔（如 `python` 或完整路徑）

2. `tasks.json`
- 定義任務、參數、執行模板
- 可設定 `path_policy`：
  - `show_import`
  - `show_export`
  - `default_import_path`
  - `default_export_path`

## 常見問題

1. 看見「找不到 Tauri 介面」
- 請用 `npm run tauri dev` 開啟，不要只跑 Vite。

2. Python 腳本找不到
- 檢查 `gui_config.json` 的 `scripts_dir` 與 `python_path`。

3. 匯入/匯出失敗
- 先確認路徑是否存在、是否為絕對路徑。
- 若檔案被 Excel 佔用，請先關閉再重試。

## 備註

- 目前為實用導向重構版本，優先解決工作流與穩定性。
- 若要擴充分頁，可沿用現有 Tauri command + React tab 架構。
## CI/CD Release

本專案已內建 GitHub Actions：

1. CI (`.github/workflows/ci.yml`)
- 觸發：`push main`、`pull_request`
- 動作：
  - `npm ci`
  - `npm run build`
  - `cargo check`

2. CD Release (`.github/workflows/release.yml`)
- 觸發：
  - push tag `v*`（例如 `v0.1.0`）
  - 或手動 `workflow_dispatch`
- 動作：
  - Windows / Linux / macOS 三平台打包 Tauri
  - 自動建立 GitHub Release
  - 上傳 `src-tauri/target/release/bundle/**` 產物

### 發版方式

```bash
git tag v0.1.0
git push origin v0.1.0
```

推送 tag 後，GitHub Actions 會自動打包並建立 Release。

### 注意事項

- 若 Linux 打包失敗，請確認 workflow 內 apt 套件安裝步驟未被移除。
- 若你之後要做簽章（code signing / notarization），可再補 secrets（例如 Apple / Windows signing）。
