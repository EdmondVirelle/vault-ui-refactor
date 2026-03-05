import { listen } from "@tauri-apps/api/event";
import { useEffect, useMemo, useState } from "react";
import { TAURI_REQUIRED_MSG, assertTauri, invokeCmd } from "../../core/tauri";
import { ScriptInfo, ScriptOption, TaskLogEvent, TaskStatusEvent } from "../../types";

const DAMAGE_SCRIPT_RE = /(傷害計算表|damage)/i;

const DamagePanel = () => {
  const [scripts, setScripts] = useState<ScriptInfo[]>([]);
  const [selectedScriptName, setSelectedScriptName] = useState("");
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [extraArgs, setExtraArgs] = useState("");
  const [log, setLog] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [runningPid, setRunningPid] = useState<number | null>(null);
  const [runningTaskId, setRunningTaskId] = useState<string | null>(null);

  const selectedScript = useMemo(
    () => scripts.find((s) => s.file_name === selectedScriptName) ?? null,
    [scripts, selectedScriptName],
  );

  const activeTaskId =
    runningTaskId ?? (selectedScript ? `script::${selectedScript.file_name}` : "");

  useEffect(() => {
    void loadDamageScripts();
  }, []);

  useEffect(() => {
    if (!selectedScript) return;

    const init: Record<string, unknown> = {};
    for (const opt of selectedScript.options) {
      init[opt.key] = opt.is_bool ? false : "";
    }

    setValues(init);
    setExtraArgs("");
  }, [selectedScript]);

  useEffect(() => {
    let unlistenLog: (() => void) | undefined;
    let unlistenStatus: (() => void) | undefined;
    let unlistenError: (() => void) | undefined;
    let active = true;

    const bind = async () => {
      try {
        assertTauri();

        unlistenLog = await listen<TaskLogEvent>("task-log", (event) => {
          const payload = event.payload;
          if (!payload.task_id?.startsWith("script::")) return;
          if (activeTaskId && payload.task_id !== activeTaskId) return;

          const head =
            payload.stream === "stderr"
              ? "[ERR]"
              : payload.stream === "system"
                ? "[SYS]"
                : "[LOG]";
          setLog((prev) => [...prev, `${head} ${payload.line}`]);
        });

        unlistenStatus = await listen<TaskStatusEvent>("task-status", (event) => {
          const payload = event.payload;
          if (!payload.task_id?.startsWith("script::")) return;
          if (runningTaskId && payload.task_id !== runningTaskId) return;

          if (payload.status === "success" || payload.status === "failed") {
            setBusy(false);
            setRunningPid(null);
            setRunningTaskId(null);

            if (payload.status === "success") {
              setLog((prev) => [...prev, "傷害計算完成"]);
            } else {
              setLog((prev) => [
                ...prev,
                `傷害計算失敗（錯誤碼: ${payload.code ?? "未知"}）`,
              ]);
            }

            if (payload.message) {
              setLog((prev) => [...prev, payload.message ?? ""]);
            }
          }
        });

        unlistenError = await listen<TaskStatusEvent>("task-error", (event) => {
          const payload = event.payload;
          if (!payload.task_id?.startsWith("script::")) return;
          if (runningTaskId && payload.task_id !== runningTaskId) return;

          setError(payload.message ?? "傷害計算執行失敗");
          setBusy(false);
          setRunningPid(null);
          setRunningTaskId(null);
        });
      } catch (e) {
        if (active) {
          setError(`事件監聽失敗：${String(e)}`);
        }
      }
    };

    void bind();

    return () => {
      active = false;
      if (unlistenLog) unlistenLog();
      if (unlistenStatus) unlistenStatus();
      if (unlistenError) unlistenError();
    };
  }, [activeTaskId, runningTaskId]);

  const loadDamageScripts = async () => {
    try {
      setError(null);
      const all = await invokeCmd<ScriptInfo[]>("list_scripts");
      const damageScripts = all.filter((s) => DAMAGE_SCRIPT_RE.test(s.file_name));
      setScripts(damageScripts);

      if (damageScripts.length > 0) {
        setSelectedScriptName(damageScripts[0].file_name);
      } else {
        setError("找不到傷害計算腳本（檔名需包含：傷害計算表）");
      }
    } catch (e) {
      setError(`載入腳本失敗：${String(e)}`);
    }
  };

  const updateOption = (opt: ScriptOption, value: unknown) => {
    setValues((prev) => ({ ...prev, [opt.key]: value }));
  };

  const runCalculator = async () => {
    if (!selectedScript) return;

    try {
      setError(null);
      setBusy(true);
      setLog([]);

      const pid = await invokeCmd<number>("run_script_cmd", {
        scriptName: selectedScript.file_name,
        script_name: selectedScript.file_name,
        values,
        extraArgs,
        extra_args: extraArgs,
      });

      const taskId = `script::${selectedScript.file_name}`;
      setRunningPid(pid);
      setRunningTaskId(taskId);
      setLog((prev) => [...prev, `[SYS] 傷害計算已啟動，PID=${pid}`]);
    } catch (e) {
      setBusy(false);
      setError(`啟動失敗：${String(e)}`);
    }
  };

  const stopCalculator = async () => {
    if (!runningPid) return;

    try {
      await invokeCmd<void>("stop_task", { pid: runningPid });
      setBusy(false);
    } catch (e) {
      setError(`停止失敗：${String(e)}`);
    }
  };

  return (
    <div className="cv-layout">
      <aside className="cv-sidebar">
        <div className="cv-side-head">
          <h2>傷害計算機</h2>
          <button className="cv-mini-btn" onClick={() => void loadDamageScripts()}>
            重新載入
          </button>
        </div>

        <div className="cv-field">
          <label>腳本版本</label>
          <select
            className="cv-input"
            value={selectedScriptName}
            onChange={(e) => setSelectedScriptName(e.target.value)}
          >
            {scripts.map((s) => (
              <option key={s.file_name} value={s.file_name}>
                {s.file_name}
              </option>
            ))}
          </select>
        </div>
      </aside>

      <main className="cv-main">
        <section className="cv-card">
          <div className="cv-card-head">
            <div>
              <h3>{selectedScript?.file_name ?? "請選擇傷害計算腳本"}</h3>
              <p>{selectedScript?.summary ?? "提供戰鬥傷害計算批次執行"}</p>
            </div>
            <div className="cv-actions">
              <button
                className="cv-btn primary"
                onClick={() => void runCalculator()}
                disabled={!selectedScript || busy}
              >
                {busy ? "計算中..." : "執行計算"}
              </button>
              <button
                className="cv-btn danger"
                onClick={() => void stopCalculator()}
                disabled={!runningPid}
              >
                停止
              </button>
            </div>
          </div>

          <div className="cv-form-grid">
            {(selectedScript?.options ?? []).map((opt) => {
              if (opt.is_bool) {
                return (
                  <label key={opt.key} className="cv-checkbox">
                    <input
                      type="checkbox"
                      checked={Boolean(values[opt.key])}
                      onChange={(e) => updateOption(opt, e.target.checked)}
                    />
                    <span>{opt.flag}</span>
                  </label>
                );
              }
              return (
                <div key={opt.key} className="cv-field">
                  <label>{opt.flag}</label>
                  <input
                    className="cv-input"
                    value={String(values[opt.key] ?? "")}
                    onChange={(e) => updateOption(opt, e.target.value)}
                    placeholder={opt.help ?? ""}
                  />
                </div>
              );
            })}

            <div className="cv-field">
              <label>額外參數（可留空）</label>
              <input
                className="cv-input"
                value={extraArgs}
                onChange={(e) => setExtraArgs(e.target.value)}
                placeholder="例如: --dry-run"
              />
            </div>
          </div>
        </section>

        <section className="cv-card">
          <div className="cv-card-head">
            <h3>執行日誌</h3>
            <button className="cv-mini-btn" onClick={() => setLog([])}>
              清空日誌
            </button>
          </div>

          <div className="cv-log-box">
            {log.length === 0 ? (
              <div className="cv-log-empty">尚無日誌</div>
            ) : (
              log.map((line, idx) => <div key={idx}>{line}</div>)
            )}
          </div>
        </section>

        {error && <section className="cv-error">{error}</section>}
      </main>
    </div>
  );
};

export default DamagePanel;
