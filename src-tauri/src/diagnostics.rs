use crate::model::{CheckResult, CommandCheck, DiagnosticsReport, GuiConfig};
use anyhow::{Context, Result};
use std::collections::HashMap;
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::process::Command;

pub async fn run_diagnostics(cfg: &GuiConfig) -> Result<DiagnosticsReport> {
    let python = cfg
        .python_path
        .clone()
        .unwrap_or_else(|| "python".to_string());

    let python_version = run_command(&python, &["--version"], &cfg.project_root).await;
    let pip_list = run_command(&python, &["-m", "pip", "list"], &cfg.project_root).await;
    let deps = check_dependencies(&pip_list.stdout);
    let docs_write_access = check_docs_write_access(&cfg.docs_dir)?;
    let env_file = check_env_file(&cfg.project_root);
    let path_encoding_warning = check_non_ascii_path(&cfg.project_root);

    let report = DiagnosticsReport {
        timestamp_unix: now_unix(),
        python_version,
        pip_list,
        deps,
        docs_write_access,
        env_file,
        path_encoding_warning,
    };
    persist_report(&report, cfg)?;
    Ok(report)
}

async fn run_command(program: &str, args: &[&str], cwd: &str) -> CommandCheck {
    let mut cmd = Command::new(program);
    cmd.args(args);
    cmd.current_dir(normalize_path(cwd));
    match cmd.output().await {
        Ok(output) => CommandCheck {
            ok: output.status.success(),
            code: output.status.code(),
            stdout: String::from_utf8_lossy(&output.stdout).trim().to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).trim().to_string(),
        },
        Err(e) => CommandCheck {
            ok: false,
            code: None,
            stdout: String::new(),
            stderr: e.to_string(),
        },
    }
}

fn check_dependencies(pip_list_stdout: &str) -> HashMap<String, bool> {
    let mut deps = HashMap::new();
    let list = pip_list_stdout.to_lowercase();
    deps.insert("pandas".to_string(), list.contains("pandas"));
    deps.insert("openpyxl".to_string(), list.contains("openpyxl"));
    deps
}

fn check_docs_write_access(docs_dir: &str) -> Result<CheckResult> {
    let path = Path::new(&normalize_path(docs_dir)).join("diagnostics.tmp");
    let write = std::fs::write(&path, "ok");
    if let Err(err) = write {
        return Ok(CheckResult {
            ok: false,
            message: format!("無法寫入 docs：{}", err),
        });
    }
    let _ = std::fs::remove_file(&path);
    Ok(CheckResult {
        ok: true,
        message: "docs 寫入/刪除測試成功".to_string(),
    })
}

fn check_env_file(project_root: &str) -> CheckResult {
    let path = Path::new(&normalize_path(project_root)).join(".env");
    if path.exists() {
        CheckResult {
            ok: true,
            message: format!("找到 {}", path.display()),
        }
    } else {
        CheckResult {
            ok: false,
            message: format!("缺少 {}", path.display()),
        }
    }
}

fn check_non_ascii_path(path: &str) -> Option<String> {
    if path.chars().any(|c| !c.is_ascii()) {
        Some("project_root 包含非 ASCII 字元，舊版 Python 套件可能有路徑編碼問題。".to_string())
    } else {
        None
    }
}

fn persist_report(report: &DiagnosticsReport, cfg: &GuiConfig) -> Result<()> {
    let Some(path) = &cfg.diagnostics_output else {
        return Ok(());
    };
    let text = serde_json::to_string_pretty(report).context("serialize diagnostics report")?;
    std::fs::write(normalize_path(path), text).context("write diagnostics report")?;
    Ok(())
}

fn now_unix() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

fn normalize_path(path: &str) -> String {
    if cfg!(windows) {
        path.replace('/', "\\")
    } else {
        path.replace('\\', "/")
    }
}
