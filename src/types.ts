// Backward-compatible barrel file.
// New code should import from `domain/*` and `ipc/*` directly.
export type {
  InputField,
  PathPolicy,
  SelectOption,
  Task,
  TaskManifest,
  TaskPathSettings,
  TaskStatus,
} from "./domain/task";
export type { ScriptInfo, ScriptOption } from "./domain/script";
export type { TaskLogEvent, TaskStatusEvent } from "./ipc/events";
export type { DiagnosticsReport } from "./ipc/diagnostics";
