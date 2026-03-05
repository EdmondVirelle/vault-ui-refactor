import { listen } from "@tauri-apps/api/event";
import React, { useEffect, useMemo, useState } from "react";
import { TAURI_REQUIRED_MSG, assertTauri, invokeCmd } from "../../core/tauri";
import { isValidPathFormat } from "../../shared/utils/path";
import {
  DiagnosticsReport,
  InputField,
  SelectOption,
  Task,
  TaskLogEvent,
  TaskPathSettings,
  TaskStatus,
  TaskStatusEvent,
} from "../../types";

type Props = {
  tasks: Task[];
  onReload: () => Promise<void>;
};

const STATUS_CLASS: Record<TaskStatus, string> = {
  idle: "status-idle",
  pending: "status-pending",
  running: "status-running",
  success: "status-success",
  failed: "status-failed",
};

const PATH_SETTINGS_STORAGE_KEY = "cv_task_path_settings_v5";

const TaskPanel: React.FC<Props> = ({ tasks, onReload }) => {
  const [selectedTaskId, setSelectedTaskId] = useState<string>(tasks[0]?.id ?? "");
  const selected = useMemo(
    () => tasks.find((task) => task.id === selectedTaskId) ?? null,
    [tasks, selectedTaskId],
  );

  const [form, setForm] = useState<Record<string, unknown>>({});
  const [selectOptions, setSelectOptions] = useState<Record<string, SelectOption[]>>({});
  const [pathSettings, setPathSettings] = useState<Record<string, TaskPathSettings>>({});

  const [log, setLog] = useState<string[]>([]);
  const [statuses, setStatuses] = useState<Record<string, TaskStatus>>(
    Object.fromEntries(tasks.map((task) => [task.id, "idle"])),
  );

  const [runningPid, setRunningPid] = useState<number | null>(null);
  const [runningTaskId, setRunningTaskId] = useState<string | null>(null);
  const [diagnostics, setDiagnostics] = useState<DiagnosticsReport | null>(null);

  const [busyDiagnostics, setBusyDiagnostics] = useState(false);
  const [busyRun, setBusyRun] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [templateOpen, setTemplateOpen] = useState(false);
  const [templateTitle, setTemplateTitle] = useState("範本");
  const [templateContent, setTemplateContent] = useState("");

  const statusText = selected ? statuses[selected.id] ?? "idle" : "idle";
  const currentPathSettings = selected ? pathSettings[selected.id] ?? {} : {};

  const showImportPath = Boolean(selected?.path_policy?.show_import);
  const showExportPath = Boolean(selected?.path_policy?.show_export);

  const effectivePathSettings: TaskPathSettings = {
    import_path: showImportPath ? currentPathSettings.import_path : undefined,
    export_path: showExportPath ? currentPathSettings.export_path : undefined,
  };

  useEffect(() => {
    try {
      const raw = localStorage.getItem(PATH_SETTINGS_STORAGE_KEY);
      if (!raw) return;
      setPathSettings(JSON.parse(raw) as Record<string, TaskPathSettings>);
    } catch {
      localStorage.removeItem(PATH_SETTINGS_STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(PATH_SETTINGS_STORAGE_KEY, JSON.stringify(pathSettings));
  }, [pathSettings]);

  useEffect(() => {
    setStatuses((prev) => {
      const next = { ...prev };
      for (const task of tasks) {
        if (!next[task.id]) next[task.id] = "idle";
      }
      return next;
    });

    if (!selectedTaskId && tasks[0]?.id) {
      setSelectedTaskId(tasks[0].id);
    }
  }, [tasks, selectedTaskId]);

  useEffect(() => {
    if (!selected) return;

    setPathSettings((prev) => {
      const existing = prev[selected.id] ?? {};
      const next = { ...existing };

      const defaultImport = selected.path_policy?.default_import_path?.trim() ?? "";
      const defaultExport = selected.path_policy?.default_export_path?.trim() ?? "";

      if (showImportPath && !next.import_path?.trim() && defaultImport) {
        next.import_path = defaultImport;
      }
      if (showExportPath && !next.export_path?.trim() && defaultExport) {
        next.export_path = defaultExport;
      }

      const changed =
        next.import_path !== existing.import_path || next.export_path !== existing.export_path;
      if (!changed && prev[selected.id]) return prev;
      return { ...prev, [selected.id]: next };
    });
  }, [selected, showImportPath, showExportPath]);

  useEffect(() => {
    let active = true;
    setError(null);
    setDiagnostics(null);

    if (!selected) {
      setForm({});
      setSelectOptions({});
      return;
    }

    const defaults: Record<string, unknown> = {};
    for (const input of selected.inputs ?? []) {
      if ("default_value" in input && input.default_value !== undefined) {
        defaults[input.name] = input.default_value;
      }
    }
    setForm(defaults);

    const loadOptions = async () => {
      try {
        assertTauri();
        const allOptions: Record<string, SelectOption[]> = {};
        for (const input of selected.inputs ?? []) {
          if (input.type !== "select") continue;

          if (input.options && input.options.length > 0) {
            allOptions[input.name] = input.options;
            continue;
          }

          if (input.options_source) {
            const options = await invokeCmd<SelectOption[]>("load_task_options", {
              taskId: selected.id,
              task_id: selected.id,
              inputName: input.name,
              input_name: input.name,
            });
            allOptions[input.name] = options;
          } else {
            allOptions[input.name] = [];
          }
        }

        if (active) {
          setSelectOptions(allOptions);
        }
      } catch (e) {
        if (active) {
          setError(`載入選項失敗：${String(e)}`);
        }
      }
    };

    void loadOptions();

    return () => {
      active = false;
    };
  }, [selected]);

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
          if (payload.task_id?.startsWith("script::")) return;

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
          if (payload.task_id?.startsWith("script::")) return;

          setStatuses((prev) => ({ ...prev, [payload.task_id]: payload.status }));

          if (payload.status === "success" || payload.status === "failed") {
            if (runningTaskId === payload.task_id) {
              setRunningPid(null);
              setRunningTaskId(null);
              setBusyRun(false);
            }

            if (payload.status === "success") {
              setLog((prev) => [...prev, "任務已成功完成"]);
            } else {
              const codeText = payload.code !== undefined && payload.code !== null ? String(payload.code) : "未知";
              setLog((prev) => [...prev, `任務失敗（錯誤碼: ${codeText}）`]);
            }

            if (payload.message) {
              setLog((prev) => [...prev, String(payload.message)]);
            }
          }
        });

        unlistenError = await listen<TaskStatusEvent>("task-error", (event) => {
          const payload = event.payload;
          if (payload.task_id?.startsWith("script::")) return;

          setError(payload.message ?? "任務執行失敗");
          setStatuses((prev) => ({ ...prev, [payload.task_id]: "failed" }));
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
  }, [runningTaskId]);

  const onChange = (name: string, value: unknown) => {
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const updatePathSetting = (key: keyof TaskPathSettings, value: string) => {
    if (!selected) return;
    setPathSettings((prev) => ({
      ...prev,
      [selected.id]: {
        ...prev[selected.id],
        [key]: value,
      },
    }));
  };

  const validatePathSettings = (settings: TaskPathSettings): string | null => {
    const importPath = settings.import_path?.trim() ?? "";
    const exportPath = settings.export_path?.trim() ?? "";

    if (importPath && !isValidPathFormat(importPath)) return "匯入路徑格式不符";
    if (exportPath && !isValidPathFormat(exportPath)) return "匯出路徑格式不符";

    return null;
  };

  const pickFolder = async (initial?: string): Promise<string | null> => {
    return invokeCmd<string | null>("pick_folder", {
      initialDir: initial ?? null,
      initial_dir: initial ?? null,
    });
  };

  const browsePathSetting = async (key: keyof TaskPathSettings) => {
    try {
      const current = String(effectivePathSettings[key] ?? "").trim();
      const selectedPath = await pickFolder(current);
      if (selectedPath) updatePathSetting(key, selectedPath);
    } catch (e) {
      setError(`選擇資料夾失敗：${String(e)}`);
    }
  };

  const runTask = async () => {
    if (!selected) return;

    const pathError = validatePathSettings(effectivePathSettings);
    if (pathError) {
      setError(pathError);
      return;
    }

    setError(null);
    setBusyRun(true);
    setLog([]);
    setStatuses((prev) => ({ ...prev, [selected.id]: "pending" }));

    try {
      const pid = await invokeCmd<number>("run_task_cmd", {
        taskId: selected.id,
        task_id: selected.id,
        form,
        pathSettings: effectivePathSettings,
        path_settings: effectivePathSettings,
      });

      setRunningPid(pid);
      setRunningTaskId(selected.id);
      setStatuses((prev) => ({ ...prev, [selected.id]: "running" }));
      setLog((prev) => [...prev, `[SYS] 任務已啟動，PID=${pid}`]);
    } catch (e) {
      setBusyRun(false);
      setStatuses((prev) => ({ ...prev, [selected.id]: "failed" }));
      setError(`啟動任務失敗：${String(e)}`);
    }
  };

  const stopTask = async () => {
    if (!runningPid) return;

    try {
      await invokeCmd<void>("stop_task", { pid: runningPid });
      setBusyRun(false);
    } catch (e) {
      setError(`停止任務失敗：${String(e)}`);
    }
  };

  const runDiagnostics = async () => {
    setBusyDiagnostics(true);
    setError(null);

    try {
      const report = await invokeCmd<DiagnosticsReport>("run_diagnostics_cmd");
      setDiagnostics(report);
    } catch (e) {
      setError(`診斷失敗：${String(e)}`);
    } finally {
      setBusyDiagnostics(false);
    }
  };

  const browseTaskField = async (fieldName: string) => {
    try {
      const current = String(form[fieldName] ?? "").trim();
      const selectedPath = await pickFolder(current);
      if (selectedPath) onChange(fieldName, selectedPath);
    } catch (e) {
      setError(`選擇資料夾失敗：${String(e)}`);
    }
  };

  const openTemplate = async () => {
    if (!selected) return;

    try {
      const content = await invokeCmd<string | null>("load_task_template", {
        taskId: selected.id,
        task_id: selected.id,
      });

      if (!content) {
        setError("此任務沒有範本");
        return;
      }

      setTemplateTitle(selected.sample_template_label ?? "範本");
      setTemplateContent(content);
      setTemplateOpen(true);
    } catch (e) {
      setError(`讀取範本失敗：${String(e)}`);
    }
  };

  const copyTemplate = async () => {
    if (!templateContent) return;

    try {
      await navigator.clipboard.writeText(templateContent);
      setLog((prev) => [...prev, "[SYS] 範本已複製到剪貼簿"]);
    } catch (e) {
      setError(`複製範本失敗：${String(e)}`);
    }
  };

  const renderInput = (input: InputField) => {
    if (input.type === "select") {
      const options = selectOptions[input.name] ?? [];
      return (
        <select
          className="cv-input"
          value={String(form[input.name] ?? "")}
          onChange={(e) => onChange(input.name, e.target.value)}
        >
          <option value="">請選擇</option>
          {options.map((option) => (
            <option key={`${input.name}_${option.value}`} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    }

    if (input.type === "boolean") {
      return (
        <label className="cv-checkbox">
          <input
            type="checkbox"
            checked={Boolean(form[input.name])}
            onChange={(e) => onChange(input.name, e.target.checked)}
          />
          <span>{input.label}</span>
        </label>
      );
    }

    if (input.type === "number") {
      return (
        <input
          type="number"
          className="cv-input"
          value={String(form[input.name] ?? "")}
          onChange={(e) => onChange(input.name, Number(e.target.value))}
        />
      );
    }

    if (input.browse_folder) {
      return (
        <div className="cv-input-row">
          <input className="cv-input" readOnly value={String(form[input.name] ?? "")} />
          <button
            type="button"
            className="cv-mini-btn"
            onClick={() => void browseTaskField(input.name)}
          >
            Browse
          </button>
          <button
            type="button"
            className="cv-mini-btn"
            onClick={() => onChange(input.name, "")}
          >
            Clear
          </button>
        </div>
      );
    }

    return (
      <input
        className="cv-input"
        value={String(form[input.name] ?? "")}
        onChange={(e) => onChange(input.name, e.target.value)}
      />
    );
  };

  return (
    <div className="cv-layout">
      <aside className="cv-sidebar">
        <div className="cv-side-head">
          <h2>任務清單</h2>
          <button className="cv-mini-btn" onClick={() => void onReload()}>
            重新載入
          </button>
        </div>

        <div className="cv-task-list">
          {tasks.map((task) => {
            const status = statuses[task.id] ?? "idle";
            return (
              <button
                key={task.id}
                className={`cv-task-item ${selectedTaskId === task.id ? "active" : ""}`}
                onClick={() => setSelectedTaskId(task.id)}
              >
                <span className={`cv-status-dot ${STATUS_CLASS[status]}`} />
                <span className="cv-task-main">
                  <strong>{task.label}</strong>
                  <small>{task.description ?? "-"}</small>
                </span>
              </button>
            );
          })}
        </div>
      </aside>

      <main className="cv-main">
        <section className="cv-card">
          <div className="cv-card-head">
            <div>
              <h3>{selected?.label ?? "請選擇任務"}</h3>
              <p>{selected?.description ?? "選取任務後可執行"} | 狀態：{statusText}</p>
            </div>
            <div className="cv-actions">
              <button
                className="cv-btn secondary"
                onClick={runDiagnostics}
                disabled={busyDiagnostics}
              >
                {busyDiagnostics ? "診斷中..." : "診斷"}
              </button>
              <button className="cv-btn primary" onClick={runTask} disabled={!selected || busyRun}>
                {busyRun ? "執行中..." : "執行任務"}
              </button>
              <button className="cv-btn danger" onClick={stopTask} disabled={!runningPid}>
                停止
              </button>
            </div>
          </div>

          {(showImportPath || showExportPath) && (
            <div className="cv-path-settings">
              {showImportPath && (
                <div className="cv-field">
                  <label>匯入路徑</label>
                  <div className="cv-input-row">
                    <input
                      className="cv-input"
                      readOnly
                      placeholder="使用默認路徑或點選資料夾"
                      value={currentPathSettings.import_path ?? ""}
                    />
                    <button
                      type="button"
                      className="cv-mini-btn"
                      onClick={() => void browsePathSetting("import_path")}
                    >
                      瀏覽
                    </button>
                    <button
                      type="button"
                      className="cv-mini-btn"
                      onClick={() => updatePathSetting("import_path", "")}
                    >
                      清空
                    </button>
                  </div>
                </div>
              )}

              {showExportPath && (
                <div className="cv-field">
                  <label>匯出路徑</label>
                  <div className="cv-input-row">
                    <input
                      className="cv-input"
                      readOnly
                      placeholder="使用默認路徑或點選資料夾"
                      value={currentPathSettings.export_path ?? ""}
                    />
                    <button
                      type="button"
                      className="cv-mini-btn"
                      onClick={() => void browsePathSetting("export_path")}
                    >
                      瀏覽
                    </button>
                    <button
                      type="button"
                      className="cv-mini-btn"
                      onClick={() => updatePathSetting("export_path", "")}
                    >
                      清空
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="cv-form-grid">
            {(selected?.inputs ?? []).map((input) => (
              <div key={input.name} className="cv-field">
                {input.type !== "boolean" && <label>{input.label}</label>}
                {renderInput(input)}
              </div>
            ))}
          </div>
        </section>

        {selected && (
          <section className="cv-card">
            <div className="cv-card-head">
              <h3>使用說明與格式</h3>
              {selected.sample_template_file && (
                <button className="cv-mini-btn" onClick={() => void openTemplate()}>
                  {selected.sample_template_label ?? "查看範本"}
                </button>
              )}
            </div>

            <div className="cv-diagnostics">
              {selected.usage && (
                <div>
                  <strong>用途：</strong>
                  {selected.usage}
                </div>
              )}

              {selected.usage_steps && selected.usage_steps.length > 0 && (
                <div>
                  <strong>步驟：</strong>
                  <ol className="cv-steps">
                    {selected.usage_steps.map((step, idx) => (
                      <li key={`${selected.id}_step_${idx}`}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}

              {selected.import_format && (
                <div>
                  <strong>匯入格式：</strong>
                  {selected.import_format}
                </div>
              )}

              {selected.why_md_import && (
                <div>
                  <strong>為什麼支援 MD：</strong>
                  {selected.why_md_import}
                </div>
              )}
            </div>
          </section>
        )}

        <section className="cv-card">
          <div className="cv-card-head">
            <h3>執行日誌</h3>
            <div className="cv-actions">
              {runningTaskId && <p>執行中：{runningTaskId}</p>}
              <button className="cv-mini-btn" onClick={() => setLog([])}>
                清空日誌
              </button>
            </div>
          </div>

          <div className="cv-log-box">
            {log.length === 0 ? (
              <div className="cv-log-empty">尚無日誌</div>
            ) : (
              log.map((line, idx) => <div key={idx}>{line}</div>)
            )}
          </div>
        </section>

        {diagnostics && (
          <section className="cv-card">
            <div className="cv-card-head">
              <h3>診斷報告</h3>
              <p>Unix Timestamp: {diagnostics.timestamp_unix}</p>
            </div>

            <div className="cv-diagnostics">
              <div>Python 版本：{diagnostics.python_version.ok ? "OK" : "FAILED"}</div>
              <div>pip list：{diagnostics.pip_list.ok ? "OK" : "FAILED"}</div>
              <div>docs 寫入：{diagnostics.docs_write_access.message}</div>
              <div>.env：{diagnostics.env_file.message}</div>
              <div>
                依賴：
                {Object.entries(diagnostics.deps)
                  .map(([name, ok]) => `${name}:${ok ? "OK" : "MISSING"}`)
                  .join(", ")}
              </div>
              {diagnostics.path_encoding_warning && (
                <div className="warn">{diagnostics.path_encoding_warning}</div>
              )}
            </div>
          </section>
        )}

        {error && <section className="cv-error">{error}</section>}
      </main>

      {templateOpen && (
        <div className="cv-modal-backdrop" onClick={() => setTemplateOpen(false)}>
          <div className="cv-modal" onClick={(e) => e.stopPropagation()}>
            <div className="cv-card-head">
              <h3>{templateTitle}</h3>
              <div className="cv-actions">
                <button className="cv-mini-btn" onClick={() => void copyTemplate()}>
                  複製
                </button>
                <button className="cv-mini-btn" onClick={() => setTemplateOpen(false)}>
                  關閉
                </button>
              </div>
            </div>
            <pre className="cv-template-pre">{templateContent}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskPanel;
