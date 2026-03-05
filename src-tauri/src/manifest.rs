use crate::model::*;
use anyhow::{anyhow, Context, Result};
use std::{
    collections::HashMap,
    fs,
    path::{Path, PathBuf},
};

pub fn load_manifest(path: &Path) -> Result<TaskManifest> {
    let text = fs::read_to_string(path)
        .with_context(|| format!("read manifest {}", path.display()))?;
    let mf: TaskManifest = serde_json::from_str(&text)
        .with_context(|| format!("parse manifest {}", path.display()))?;
    Ok(mf)
}

pub fn load_config(path: &Path) -> Result<GuiConfig> {
    let text = fs::read_to_string(path)
        .with_context(|| format!("read gui_config {}", path.display()))?;
    let cfg: GuiConfig = serde_json::from_str(&text)
        .with_context(|| format!("parse gui_config {}", path.display()))?;
    Ok(cfg)
}

pub fn resolve_script(
    scripts_dir: &str,
    script: &str,
    fuzzy_keywords: &[&str],
) -> Result<PathBuf> {
    let base = PathBuf::from(normalize_path(scripts_dir));
    let normalized_script = normalize_path(script);
    let direct = PathBuf::from(&normalized_script);
    if direct.is_absolute() && direct.exists() {
        return Ok(direct);
    }
    let candidate = base.join(&normalized_script);
    if candidate.exists() {
        return Ok(candidate);
    }
    let mut hits = Vec::new();
    if base.is_dir() {
        for entry in fs::read_dir(&base)? {
            let entry = entry?;
            let n = entry.file_name().to_string_lossy().to_string();
            if fuzzy_keywords.iter().all(|k| n.contains(k)) {
                hits.push(entry.path());
            }
        }
    }
    hits.into_iter()
        .next()
        .ok_or_else(|| anyhow!("script not found: {} (keywords {:?})", script, fuzzy_keywords))
}

fn normalize_path(path: &str) -> String {
    if cfg!(windows) {
        path.replace('/', "\\")
    } else {
        path.replace('\\', "/")
    }
}

pub fn read_manifest_task<'a>(manifest: &'a TaskManifest, task_id: &str) -> Result<&'a Task> {
    manifest
        .tasks
        .iter()
        .find(|t| t.id == task_id)
        .ok_or_else(|| anyhow!("task not found: {}", task_id))
}

pub fn read_select_field<'a>(task: &'a Task, input_name: &str) -> Result<&'a InputField> {
    task.inputs
        .iter()
        .find(|input| match input {
            InputField::Select { name, .. } => name == input_name,
            _ => false,
        })
        .ok_or_else(|| anyhow!("select input not found: {}::{}", task.id, input_name))
}

pub fn default_form(task: &Task) -> HashMap<String, serde_json::Value> {
    let mut map = HashMap::new();
    for input in &task.inputs {
        match input {
            InputField::Select { name, default_value, .. }
            | InputField::Text { name, default_value, .. } => {
                if let Some(v) = default_value {
                    map.insert(name.clone(), serde_json::Value::String(v.clone()));
                }
            }
            InputField::Boolean {
                name,
                default_value,
                ..
            } => {
                if let Some(v) = default_value {
                    map.insert(name.clone(), serde_json::Value::Bool(*v));
                }
            }
            InputField::Number {
                name,
                default_value,
                ..
            } => {
                if let Some(v) = default_value {
                    map.insert(
                        name.clone(),
                        serde_json::Value::Number(
                            serde_json::Number::from_f64(*v)
                                .unwrap_or_else(|| serde_json::Number::from(0)),
                        ),
                    );
                }
            }
        }
    }
    map
}
