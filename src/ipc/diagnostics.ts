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
