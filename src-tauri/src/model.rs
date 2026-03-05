use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct GuiConfig {
    pub project_root: String,
    pub scripts_dir: String,
    pub docs_dir: String,
    pub python_path: Option<String>,
    pub history_file: Option<String>,
    pub diagnostics_output: Option<String>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct TaskManifest {
    #[serde(default)]
    pub tasks: Vec<Task>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct Task {
    pub id: String,
    pub label: String,
    pub description: Option<String>,
    #[serde(default)]
    pub path_policy: PathPolicy,
    pub usage: Option<String>,
    pub import_format: Option<String>,
    pub why_md_import: Option<String>,
    pub sample_template_file: Option<String>,
    pub sample_template_label: Option<String>,
    #[serde(default)]
    pub usage_steps: Vec<String>,
    pub command: Option<String>,
    pub script: Option<String>,
    #[serde(default)]
    pub inputs: Vec<InputField>,
    pub arg_template: Option<String>,
    #[serde(default)]
    pub fuzzy_keywords: Vec<String>,
}

#[derive(Debug, Deserialize, Serialize, Clone, Default)]
pub struct PathPolicy {
    #[serde(default)]
    pub show_import: bool,
    #[serde(default)]
    pub show_export: bool,
    pub default_import_path: Option<String>,
    pub default_export_path: Option<String>,
}

#[derive(Debug, Serialize, Clone)]
pub struct ScriptInfo {
    pub id: String,
    pub file_name: String,
    pub category: String,
    pub summary: String,
    pub options: Vec<ScriptOption>,
}

#[derive(Debug, Serialize, Clone)]
pub struct ScriptOption {
    pub key: String,
    pub flag: String,
    pub help: Option<String>,
    pub is_bool: bool,
    pub takes_value: bool,
    pub required: bool,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
#[serde(tag = "type")]
pub enum InputField {
    #[serde(rename = "select")]
    Select {
        name: String,
        label: String,
        arg_template: Option<String>,
        options_source: Option<String>,
        options: Option<Vec<SelectOption>>,
        default_value: Option<String>,
    },
    #[serde(rename = "boolean")]
    Boolean {
        name: String,
        label: String,
        arg_template: Option<String>,
        default_value: Option<bool>,
    },
    #[serde(rename = "text")]
    Text {
        name: String,
        label: String,
        arg_template: Option<String>,
        default_value: Option<String>,
        browse_folder: Option<bool>,
    },
    #[serde(rename = "number")]
    Number {
        name: String,
        label: String,
        arg_template: Option<String>,
        default_value: Option<f64>,
    },
}

pub type FormValue = serde_json::Value;

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct SelectOption {
    pub label: String,
    pub value: String,
}

#[derive(Debug, Deserialize, Serialize, Clone, Default)]
pub struct TaskPathSettings {
    pub import_path: Option<String>,
    pub export_path: Option<String>,
}

#[derive(Debug, Serialize, Clone)]
pub struct PreparedCommand {
    pub program: String,
    pub args: Vec<String>,
    pub rendered: String,
}

#[derive(Debug, Serialize, Clone)]
pub struct TaskLogEvent {
    pub pid: u32,
    pub task_id: String,
    pub stream: String,
    pub line: String,
}

#[derive(Debug, Serialize, Clone)]
pub struct TaskStatusEvent {
    pub pid: u32,
    pub task_id: String,
    pub status: String,
    pub code: Option<i32>,
    pub message: Option<String>,
}

#[derive(Debug, Serialize, Clone)]
pub struct DiagnosticsReport {
    pub timestamp_unix: u64,
    pub python_version: CommandCheck,
    pub pip_list: CommandCheck,
    pub deps: HashMap<String, bool>,
    pub docs_write_access: CheckResult,
    pub env_file: CheckResult,
    pub path_encoding_warning: Option<String>,
}

#[derive(Debug, Serialize, Clone)]
pub struct CommandCheck {
    pub ok: bool,
    pub code: Option<i32>,
    pub stdout: String,
    pub stderr: String,
}

#[derive(Debug, Serialize, Clone)]
pub struct CheckResult {
    pub ok: bool,
    pub message: String,
}
