import { useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import DamageCalculator from "./DamageCalculator";
import FormBuilder from "./FormBuilder";
import { TaskManifest } from "./types";
import "./index.css";

const TAURI_REQUIRED_MSG =
  "載入失敗：找不到 Tauri 介面，請透過 Tauri 視窗啟動（npm run tauri dev）";

type MainTab = "tasks" | "damage";

const App = () => {
  const [manifest, setManifest] = useState<TaskManifest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<MainTab>("tasks");

  const loadManifest = useCallback(async () => {
    try {
      const { invoke, isTauri } = await import("@tauri-apps/api/core");
      if (!isTauri()) throw new Error(TAURI_REQUIRED_MSG);
      const data = await invoke<TaskManifest>("load_tasks");
      setManifest(data);
      setError(null);
    } catch (e) {
      setError(`載入任務失敗：${String(e)}`);
    }
  }, []);

  useEffect(() => {
    void loadManifest();
  }, [loadManifest]);

  if (error) return <div className="cv-error-shell">{error}</div>;
  if (!manifest) return <div className="cv-loading">載入任務中...</div>;

  return (
    <div className="cv-shell">
      <header className="cv-header">
        <h1>Consilience Vault Tool</h1>
        <p>任務操作與傷害計算的整合桌面工具。</p>
      </header>

      <div className="cv-main-tabs">
        <button
          className={`cv-main-tab ${tab === "tasks" ? "active" : ""}`}
          onClick={() => setTab("tasks")}
        >
          任務面板
        </button>
        <button
          className={`cv-main-tab ${tab === "damage" ? "active" : ""}`}
          onClick={() => setTab("damage")}
        >
          傷害計算機
        </button>
      </div>

      {tab === "tasks" ? (
        <FormBuilder tasks={manifest.tasks} onReload={loadManifest} />
      ) : (
        <DamageCalculator />
      )}
    </div>
  );
};

const root = createRoot(document.getElementById("root")!);
root.render(<App />);
