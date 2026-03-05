use crate::model::{TaskLogEvent, TaskStatusEvent};
use anyhow::Result;
use tauri::{Emitter, Window};
use tokio::process::{Child, ChildStderr, ChildStdout};
use tokio::sync::{mpsc, Mutex};
use std::sync::Arc;

pub async fn stream_output(
    window: Window,
    pid: u32,
    task_id: String,
    child: Arc<Mutex<Child>>,
    stdout: Option<ChildStdout>,
    stderr: Option<ChildStderr>,
) -> Result<i32> {
    window.emit(
        "task-status",
        TaskStatusEvent {
            pid,
            task_id: task_id.clone(),
            status: "running".to_string(),
            code: None,
            message: None,
        },
    )?;

    let (tx, mut rx) = mpsc::unbounded_channel::<TaskLogEvent>();
    if let Some(stdout) = stdout {
        let tx = tx.clone();
        let task_id_clone = task_id.clone();
        tokio::spawn(async move {
            let mut lines = crate::runner::stream_to_lines(stdout);
            while let Ok(Some(line)) = lines.next_line().await {
                let _ = tx.send(TaskLogEvent {
                    pid,
                    task_id: task_id_clone.clone(),
                    stream: "stdout".to_string(),
                    line,
                });
            }
        });
    }
    if let Some(stderr) = stderr {
        let tx = tx.clone();
        let task_id_clone = task_id.clone();
        tokio::spawn(async move {
            let mut lines = crate::runner::stream_err_to_lines(stderr);
            while let Ok(Some(line)) = lines.next_line().await {
                let _ = tx.send(TaskLogEvent {
                    pid,
                    task_id: task_id_clone.clone(),
                    stream: "stderr".to_string(),
                    line,
                });
            }
        });
    }
    drop(tx);

    while let Some(event) = rx.recv().await {
        window.emit("task-log", event)?;
    }

    let status = {
        let mut guard = child.lock().await;
        guard.wait().await?
    };
    let code = status.code().unwrap_or(-1);
    let is_ok = code == 0;
    let message = if is_ok {
        None
    } else if code == -1073741515 {
        Some("腳本異常終止：缺少 DLL 或 Python 環境損壞，請檢查 python_path。".to_string())
    } else {
        Some(format!("腳本異常終止 (Code: {})", code))
    };

    let status_payload = TaskStatusEvent {
        pid,
        task_id: task_id.clone(),
        status: if is_ok {
            "success".to_string()
        } else {
            "failed".to_string()
        },
        code: Some(code),
        message: message.clone(),
    };
    window.emit("task-status", status_payload.clone())?;
    if !is_ok {
        window.emit("task-error", status_payload)?;
    }
    Ok(code)
}
