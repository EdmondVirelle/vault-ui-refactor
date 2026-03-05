#![cfg_attr(all(not(debug_assertions), target_os = "windows"), windows_subsystem = "windows")]

mod diagnostics;
mod logger;
mod manifest;
mod model;
mod runner;

use diagnostics::run_diagnostics;
use logger::stream_output;
use manifest::{default_form, load_config, load_manifest, read_manifest_task, read_select_field};
use model::{
    DiagnosticsReport, InputField, PreparedCommand, ScriptInfo, ScriptOption, SelectOption,
    TaskManifest, TaskPathSettings,
};
use runner::{build_command, load_select_options, spawn_task};
use regex::Regex;
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tauri::{Emitter, Listener, Manager, State};
use tokio::sync::Mutex;

type SharedChild = Arc<Mutex<tokio::process::Child>>;

struct AppState {
    manifest_path: PathBuf,
    config_path: PathBuf,
    running: HashMap<u32, SharedChild>,
}

#[tauri::command]
async fn load_tasks(state: State<'_, Mutex<AppState>>) -> std::result::Result<TaskManifest, String> {
    let state = state.lock().await;
    load_manifest(&state.manifest_path).map_err(|e| e.to_string())
}

#[tauri::command]
async fn load_task_options(
    state: State<'_, Mutex<AppState>>,
    task_id: String,
    input_name: String,
) -> std::result::Result<Vec<SelectOption>, String> {
    let state_guard = state.lock().await;
    let mf = load_manifest(&state_guard.manifest_path).map_err(|e| e.to_string())?;
    let cfg = load_config(&state_guard.config_path).map_err(|e| e.to_string())?;
    drop(state_guard);

    let task = read_manifest_task(&mf, &task_id).map_err(|e| e.to_string())?;
    let input = read_select_field(task, &input_name).map_err(|e| e.to_string())?;
    if let InputField::Select {
        options,
        options_source,
        ..
    } = input
    {
        if let Some(static_options) = options {
            return Ok(static_options.clone());
        }
        if let Some(source) = options_source {
            return load_select_options(&cfg, task.command.as_deref(), source)
                .await
                .map_err(|e| e.to_string());
        }
    }
    Ok(Vec::new())
}

#[tauri::command]
async fn run_task_cmd(
    state: State<'_, Mutex<AppState>>,
    task_id: String,
    form: HashMap<String, serde_json::Value>,
    path_settings: Option<TaskPathSettings>,
    window: tauri::Window,
) -> std::result::Result<u32, String> {
    let state_guard = state.lock().await;
    let manifest_path = state_guard.manifest_path.clone();
    let config_path = state_guard.config_path.clone();
    drop(state_guard);

    let mf = load_manifest(&manifest_path).map_err(|e| e.to_string())?;
    let cfg = load_config(&config_path).map_err(|e| e.to_string())?;
    let task = read_manifest_task(&mf, &task_id).map_err(|e| e.to_string())?;
    validate_task_path_settings(path_settings.as_ref())?;
    let form_filled = merge_form(task, form);
    let form_filled = apply_task_path_settings(task, form_filled, path_settings.as_ref());
    let prepared = build_command(task, &form_filled, &cfg).map_err(|e| e.to_string())?;

    window
        .emit(
            "task-log",
            serde_json::json!({
                "pid": 0,
                "task_id": task_id,
                "stream": "system",
                "line": format!("COMMAND: {}", prepared.rendered),
            }),
        )
        .map_err(|e| e.to_string())?;

    let spawned = spawn_task(&prepared, &cfg, path_settings.as_ref())
        .await
        .map_err(|e| e.to_string())?;
    let pid = spawned.pid;

    let child = Arc::new(Mutex::new(spawned.child));
    {
        let mut state_guard = state.lock().await;
        state_guard.running.insert(pid, child.clone());
    }

    let window_for_spawn = window.clone();
    let app_handle = window.app_handle().clone();
    let task_id_for_spawn = task_id.clone();
    tauri::async_runtime::spawn(async move {
        let result = stream_output(
            window_for_spawn.clone(),
            pid,
            task_id_for_spawn.clone(),
            child.clone(),
            spawned.stdout,
            spawned.stderr,
        )
        .await;

        if let Err(err) = result {
            let _ = window_for_spawn.emit(
                "task-error",
                serde_json::json!({
                    "pid": pid,
                    "task_id": task_id_for_spawn,
                    "status": "failed",
                    "code": -1,
                    "message": err.to_string()
                }),
            );
        }

        let app_state = app_handle.state::<Mutex<AppState>>();
        let mut guard = app_state.lock().await;
        guard.running.remove(&pid);
    });

    Ok(pid)
}

#[tauri::command]
async fn stop_task(
    state: State<'_, Mutex<AppState>>,
    pid: u32,
    window: tauri::Window,
) -> std::result::Result<(), String> {
    let child = {
        let state_guard = state.lock().await;
        state_guard.running.get(&pid).cloned()
    };
    let Some(child) = child else {
        return Err(format!("pid {} not found", pid));
    };

    {
        let mut child_guard = child.lock().await;
        child_guard.kill().await.map_err(|e| e.to_string())?;
    }
    window
        .emit(
            "task-log",
            serde_json::json!({
                "pid": pid,
                "task_id": "",
                "stream": "system",
                "line": "[User Aborted]"
            }),
        )
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn run_diagnostics_cmd(
    state: State<'_, Mutex<AppState>>,
) -> std::result::Result<DiagnosticsReport, String> {
    let state_guard = state.lock().await;
    let cfg = load_config(&state_guard.config_path).map_err(|e| e.to_string())?;
    drop(state_guard);
    run_diagnostics(&cfg).await.map_err(|e| e.to_string())
}

#[tauri::command]
fn pick_folder(initial_dir: Option<String>) -> std::result::Result<Option<String>, String> {
    let mut dialog = rfd::FileDialog::new();
    if let Some(initial) = initial_dir {
        let trimmed = initial.trim();
        if !trimmed.is_empty() {
            let p = PathBuf::from(trimmed);
            if p.exists() {
                dialog = dialog.set_directory(p);
            }
        }
    }
    let selected = dialog.pick_folder();
    Ok(selected.map(|path| path.to_string_lossy().to_string()))
}

#[tauri::command]
async fn load_task_template(
    state: State<'_, Mutex<AppState>>,
    task_id: String,
) -> std::result::Result<Option<String>, String> {
    let state_guard = state.lock().await;
    let manifest_path = state_guard.manifest_path.clone();
    drop(state_guard);

    let manifest = load_manifest(&manifest_path).map_err(|e| e.to_string())?;
    let task = read_manifest_task(&manifest, &task_id).map_err(|e| e.to_string())?;
    let Some(template_file) = &task.sample_template_file else {
        return Ok(None);
    };

    let template_path = resolve_manifest_relative_path(&manifest_path, template_file);
    if !template_path.exists() {
        return Err(format!(
            "template file not found: {}",
            template_path.to_string_lossy()
        ));
    }

    let content = std::fs::read_to_string(&template_path).map_err(|e| e.to_string())?;
    if content.len() > 1_000_000 {
        return Err("template file is too large".to_string());
    }
    Ok(Some(content))
}

#[tauri::command]
async fn list_scripts(state: State<'_, Mutex<AppState>>) -> std::result::Result<Vec<ScriptInfo>, String> {
    let state_guard = state.lock().await;
    let cfg = load_config(&state_guard.config_path).map_err(|e| e.to_string())?;
    drop(state_guard);

    let scripts_dir = PathBuf::from(cfg.scripts_dir);
    if !scripts_dir.exists() {
        return Err(format!("scripts dir not found: {}", scripts_dir.to_string_lossy()));
    }

    let mut out = Vec::new();
    let entries = fs::read_dir(&scripts_dir).map_err(|e| e.to_string())?;
    for entry in entries {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();
        if path.extension().and_then(|x| x.to_str()) != Some("py") {
            continue;
        }
        let Some(file_name) = path.file_name().and_then(|x| x.to_str()).map(|x| x.to_string()) else {
            continue;
        };
        let id = path
            .file_stem()
            .and_then(|x| x.to_str())
            .map(|x| x.to_string())
            .unwrap_or_else(|| file_name.clone());
        let content = fs::read_to_string(&path).unwrap_or_default();
        out.push(ScriptInfo {
            id,
            file_name: file_name.clone(),
            category: derive_script_category(&file_name),
            summary: parse_script_summary(&content),
            options: parse_script_options(&content),
        });
    }

    out.sort_by(|a, b| {
        a.category
            .cmp(&b.category)
            .then_with(|| a.file_name.cmp(&b.file_name))
    });
    Ok(out)
}

#[tauri::command]
async fn run_script_cmd(
    state: State<'_, Mutex<AppState>>,
    script_name: String,
    values: HashMap<String, serde_json::Value>,
    extra_args: Option<String>,
    path_settings: Option<TaskPathSettings>,
    window: tauri::Window,
) -> std::result::Result<u32, String> {
    let state_guard = state.lock().await;
    let config_path = state_guard.config_path.clone();
    drop(state_guard);

    let cfg = load_config(&config_path).map_err(|e| e.to_string())?;
    validate_task_path_settings(path_settings.as_ref())?;

    let script_path = PathBuf::from(&cfg.scripts_dir).join(&script_name);
    if !script_path.exists() {
        return Err(format!("script not found: {}", script_path.to_string_lossy()));
    }

    let program = cfg.python_path.clone().unwrap_or_else(|| "python".to_string());
    let mut args = vec![script_path.to_string_lossy().to_string()];
    let mut keys = values.keys().cloned().collect::<Vec<_>>();
    keys.sort();
    for key in keys {
        let Some(v) = values.get(&key) else {
            continue;
        };
        let flag = if key.starts_with("--") {
            key.clone()
        } else {
            format!("--{}", key.replace('_', "-"))
        };
        match v {
            serde_json::Value::Bool(enabled) => {
                if *enabled {
                    args.push(flag);
                }
            }
            serde_json::Value::String(s) => {
                let s = s.trim();
                if !s.is_empty() {
                    args.push(flag);
                    args.push(s.to_string());
                }
            }
            serde_json::Value::Number(n) => {
                args.push(flag);
                args.push(n.to_string());
            }
            _ => {}
        }
    }

    if let Some(extra) = extra_args {
        let extra = extra.trim();
        if !extra.is_empty() {
            let parts = shell_words::split(extra).map_err(|e| e.to_string())?;
            args.extend(parts);
        }
    }

    let prepared = PreparedCommand {
        rendered: render_command_for_display(&program, &args),
        program,
        args,
    };

    let task_id = format!("script::{}", script_name);
    window
        .emit(
            "task-log",
            serde_json::json!({
                "pid": 0,
                "task_id": task_id,
                "stream": "system",
                "line": format!("COMMAND: {}", prepared.rendered),
            }),
        )
        .map_err(|e| e.to_string())?;

    let spawned = spawn_task(&prepared, &cfg, path_settings.as_ref())
        .await
        .map_err(|e| e.to_string())?;
    let pid = spawned.pid;
    let child = Arc::new(Mutex::new(spawned.child));
    {
        let mut state_guard = state.lock().await;
        state_guard.running.insert(pid, child.clone());
    }

    let window_for_spawn = window.clone();
    let app_handle = window.app_handle().clone();
    let task_id_for_spawn = task_id.clone();
    tauri::async_runtime::spawn(async move {
        let result = stream_output(
            window_for_spawn.clone(),
            pid,
            task_id_for_spawn.clone(),
            child.clone(),
            spawned.stdout,
            spawned.stderr,
        )
        .await;

        if let Err(err) = result {
            let _ = window_for_spawn.emit(
                "task-error",
                serde_json::json!({
                    "pid": pid,
                    "task_id": task_id_for_spawn,
                    "status": "failed",
                    "code": -1,
                    "message": err.to_string()
                }),
            );
        }
        let app_state = app_handle.state::<Mutex<AppState>>();
        let mut guard = app_state.lock().await;
        guard.running.remove(&pid);
    });
    Ok(pid)
}

fn merge_form(
    task: &model::Task,
    mut form: HashMap<String, serde_json::Value>,
) -> HashMap<String, serde_json::Value> {
    let defaults = default_form(task);
    for (k, v) in defaults {
        form.entry(k).or_insert(v);
    }
    form
}

fn render_command_for_display(program: &str, args: &[String]) -> String {
    let mut parts = vec![shell_words::quote(program).into_owned()];
    parts.extend(args.iter().map(|arg| shell_words::quote(arg).into_owned()));
    parts.join(" ")
}

fn derive_script_category(file_name: &str) -> String {
    file_name
        .split('-')
        .next()
        .map(|x| x.trim().to_string())
        .filter(|x| !x.is_empty())
        .unwrap_or_else(|| "其他".to_string())
}

fn parse_script_summary(content: &str) -> String {
    for raw in content.lines().take(120) {
        let s = raw.trim();
        if s.is_empty() {
            continue;
        }
        if s.starts_with("#!") || s.starts_with("# -*-") {
            continue;
        }
        if s == "\"\"\"" || s == "'''" {
            continue;
        }
        if s.starts_with('#') {
            continue;
        }
        let cleaned = s.trim_matches('"').trim_matches('\'').trim();
        if !cleaned.is_empty() {
            return cleaned.to_string();
        }
    }
    "無摘要".to_string()
}

fn parse_script_options(content: &str) -> Vec<ScriptOption> {
    let block_re = Regex::new(r#"(?s)add_argument\s*\((.*?)\)"#).expect("valid regex");
    let long_flag_re = Regex::new(r#"--[A-Za-z0-9][A-Za-z0-9\-]*"#).expect("valid regex");
    let help_re = Regex::new(r#"help\s*=\s*["']([^"']+)["']"#).expect("valid regex");
    let mut map = HashMap::<String, ScriptOption>::new();

    for caps in block_re.captures_iter(content) {
        let block = caps.get(1).map(|m| m.as_str()).unwrap_or_default();
        let Some(flag) = long_flag_re.find(block).map(|m| m.as_str().to_string()) else {
            continue;
        };
        let key = flag.trim_start_matches("--").to_string();
        let is_bool = block.contains("store_true") || block.contains("store_false");
        let required = block.contains("required=True");
        let help = help_re
            .captures(block)
            .and_then(|c| c.get(1).map(|m| m.as_str().trim().to_string()))
            .filter(|x| !x.is_empty());

        map.entry(key.clone()).or_insert(ScriptOption {
            key,
            flag,
            help,
            is_bool,
            takes_value: !is_bool,
            required,
        });
    }

    let mut options = map.into_values().collect::<Vec<_>>();
    options.sort_by(|a, b| a.flag.cmp(&b.flag));
    options
}

fn resolve_manifest_relative_path(manifest_path: &Path, candidate: &str) -> PathBuf {
    let p = PathBuf::from(candidate);
    if p.is_absolute() {
        return p;
    }
    let base = manifest_path.parent().unwrap_or(Path::new("."));
    base.join(p)
}

fn validate_task_path_settings(
    path_settings: Option<&TaskPathSettings>,
) -> std::result::Result<(), String> {
    let Some(settings) = path_settings else {
        return Ok(());
    };
    if let Some(import_path) = &settings.import_path {
        let import_path = import_path.trim();
        if !import_path.is_empty() {
            if !looks_absolute_path(import_path) {
                return Err("匯入地點格式不符".to_string());
            }
            if !Path::new(import_path).exists() {
                return Err("匯入地點不存在".to_string());
            }
        }
    }
    if let Some(export_path) = &settings.export_path {
        let export_path = export_path.trim();
        if !export_path.is_empty() && !looks_absolute_path(export_path) {
            return Err("匯出地點格式不符".to_string());
        }
    }
    Ok(())
}

fn looks_absolute_path(path: &str) -> bool {
    let p = path.trim();
    if p.is_empty() {
        return false;
    }
    if cfg!(windows) {
        if p.starts_with("\\\\") {
            return true;
        }
        let b = p.as_bytes();
        return b.len() >= 3
            && (b[0] as char).is_ascii_alphabetic()
            && b[1] == b':'
            && (b[2] == b'\\' || b[2] == b'/');
    }
    Path::new(p).is_absolute()
}

fn apply_task_path_settings(
    task: &model::Task,
    mut form: HashMap<String, serde_json::Value>,
    path_settings: Option<&TaskPathSettings>,
) -> HashMap<String, serde_json::Value> {
    let Some(settings) = path_settings else {
        return form;
    };

    if let Some(import_path) = &settings.import_path {
        let import_path = import_path.trim();
        if !import_path.is_empty() {
            let import_aliases = [
                "import_path",
                "snapshot_root",
                "source_root",
                "input_path",
                "input_dir",
            ];
            for alias in import_aliases {
                upsert_form_field_if_input_exists(task, &mut form, alias, import_path);
            }
        }
    }
    if let Some(export_path) = &settings.export_path {
        let export_path = export_path.trim();
        if !export_path.is_empty() {
            let export_aliases = [
                "export_path",
                "backup_root",
                "output_path",
                "output_dir",
                "target_root",
            ];
            for alias in export_aliases {
                upsert_form_field_if_input_exists(task, &mut form, alias, export_path);
            }
        }
    }
    form
}

fn upsert_form_field_if_input_exists(
    task: &model::Task,
    form: &mut HashMap<String, serde_json::Value>,
    field_name: &str,
    value: &str,
) {
    let exists_in_task = task.inputs.iter().any(|input| match input {
        InputField::Select { name, .. }
        | InputField::Boolean { name, .. }
        | InputField::Text { name, .. }
        | InputField::Number { name, .. } => name == field_name,
    });
    if exists_in_task {
        form.insert(
            field_name.to_string(),
            serde_json::Value::String(value.to_string()),
        );
    }
}

fn register_panic_hook() {
    std::panic::set_hook(Box::new(|info| {
        let dir = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
        let path = dir.join("crash.log");
        let message = format!("panic: {}\n", info);
        let _ = std::fs::write(path, message);
    }));
}

async fn kill_all_children(app: &tauri::AppHandle) {
    let state = app.state::<Mutex<AppState>>();
    let children = {
        let guard = state.lock().await;
        guard.running.values().cloned().collect::<Vec<_>>()
    };
    for child in children {
        let mut guard = child.lock().await;
        let _ = guard.kill().await;
    }
}

fn main() {
    register_panic_hook();
    tauri::Builder::default()
        .manage(Mutex::new(AppState {
            manifest_path: PathBuf::from("../tasks.json"),
            config_path: PathBuf::from("../gui_config.json"),
            running: HashMap::new(),
        }))
        .setup(|app| {
            let app_handle = app.handle().clone();
            app.listen("request-stop-all", move |_| {
                let app_handle = app_handle.clone();
                tauri::async_runtime::spawn(async move {
                    kill_all_children(&app_handle).await;
                });
            });
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let app = window.app_handle().clone();
                tauri::async_runtime::spawn(async move {
                    kill_all_children(&app).await;
                });
            }
        })
        .invoke_handler(tauri::generate_handler![
            load_tasks,
            load_task_options,
            list_scripts,
            run_task_cmd,
            run_script_cmd,
            stop_task,
            run_diagnostics_cmd,
            pick_folder,
            load_task_template
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
