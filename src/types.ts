export type SelectOption = {
  label: string;
  value: string;
};

export type InputField =
  | {
      type: "select";
      name: string;
      label: string;
      arg_template?: string;
      options_source?: string;
      options?: SelectOption[];
      default_value?: string;
    }
  | {
      type: "boolean";
      name: string;
      label: string;
      arg_template?: string;
      default_value?: boolean;
    }
  | {
      type: "text";
      name: string;
      label: string;
      arg_template?: string;
      default_value?: string;
      browse_folder?: boolean;
    }
  | {
      type: "number";
      name: string;
      label: string;
      arg_template?: string;
      default_value?: number;
    };

export type Task = {
  id: string;
  label: string;
  description?: string;
  path_policy?: PathPolicy;
  usage?: string;
  import_format?: string;
  why_md_import?: string;
  sample_template_file?: string;
  sample_template_label?: string;
  usage_steps?: string[];
  command?: string;
  script?: string;
  inputs?: InputField[];
  arg_template?: string;
  fuzzy_keywords?: string[];
};

export type PathPolicy = {
  show_import?: boolean;
  show_export?: boolean;
  default_import_path?: string;
  default_export_path?: string;
};

export type ScriptOption = {
  key: string;
  flag: string;
  help?: string | null;
  is_bool: boolean;
  takes_value: boolean;
  required: boolean;
};

export type ScriptInfo = {
  id: string;
  file_name: string;
  category: string;
  summary: string;
  options: ScriptOption[];
};

export type TaskManifest = {
  tasks: Task[];
};

export type TaskLogEvent = {
  pid: number;
  task_id: string;
  stream: "stdout" | "stderr" | "system" | string;
  line: string;
};

export type TaskStatus = "idle" | "pending" | "running" | "success" | "failed";

export type TaskStatusEvent = {
  pid: number;
  task_id: string;
  status: Exclude<TaskStatus, "idle" | "pending">;
  code?: number | null;
  message?: string | null;
};

export type DiagnosticsReport = {
  timestamp_unix: number;
  python_version: {
    ok: boolean;
    code: number | null;
    stdout: string;
    stderr: string;
  };
  pip_list: {
    ok: boolean;
    code: number | null;
    stdout: string;
    stderr: string;
  };
  deps: Record<string, boolean>;
  docs_write_access: {
    ok: boolean;
    message: string;
  };
  env_file: {
    ok: boolean;
    message: string;
  };
  path_encoding_warning?: string | null;
};

export type TaskPathSettings = {
  import_path?: string;
  export_path?: string;
};
