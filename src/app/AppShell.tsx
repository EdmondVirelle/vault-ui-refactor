import { useCallback, useEffect, useState } from "react";
import { invokeCmd } from "../core/tauri";
import DamagePanel from "../features/damage/DamagePanel";
import TaskPanel from "../features/tasks/TaskPanel";
import { TaskManifest } from "../types";

type MainTab = "tasks" | "damage";

const AppShell = () => {
  const [manifest, setManifest] = useState<TaskManifest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<MainTab>("tasks");

  const loadManifest = useCallback(async () => {
    try {
      const data = await invokeCmd<TaskManifest>("load_tasks");
      setManifest(data);
      setError(null);
    } catch (e) {
      setError(`載入失敗：${String(e)}`);
    }
  }, []);

  useEffect(() => {
    void loadManifest();
  }, [loadManifest]);

  if (error) return <div className="cv-error-shell">{error}</div>;
  if (!manifest) return <div className="cv-loading">載入中...</div>;

  return (
    <div className="cv-shell">
      <header className="cv-header">
        <h1>Consilience Vault</h1>
        <p>配置驅動任務管理、劇本匯入匯出、診斷與傷害計算工具。</p>
      </header>

      <div className="cv-main-tabs">
        <button
          className={`cv-main-tab ${tab === "tasks" ? "active" : ""}`}
          onClick={() => setTab("tasks")}
        >
          任務中心
        </button>
        <button
          className={`cv-main-tab ${tab === "damage" ? "active" : ""}`}
          onClick={() => setTab("damage")}
        >
          傷害計算機
        </button>
      </div>

      {tab === "tasks" ? (
        <TaskPanel tasks={manifest.tasks} onReload={loadManifest} />
      ) : (
        <DamagePanel />
      )}
    </div>
  );
};

export default AppShell;
