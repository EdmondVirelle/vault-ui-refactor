use crate::manifest::resolve_script;
use crate::model::{FormValue, GuiConfig, InputField, PreparedCommand, SelectOption, Task, TaskPathSettings};
use anyhow::{anyhow, Context, Result};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::{Child, ChildStderr, ChildStdout, Command};

pub struct SpawnedTask {
    pub pid: u32,
    pub child: Child,
    pub stdout: Option<ChildStdout>,
    pub stderr: Option<ChildStderr>,
}

pub fn build_command(task: &Task, form: &HashMap<String, FormValue>, cfg: &GuiConfig) -> Result<PreparedCommand> {
    let program = task
        .command
        .clone()
        .or_else(|| cfg.python_path.clone())
        .unwrap_or_else(|| "python".to_string());

    let script_path = if let Some(script) = &task.script {
        let fuzzy_keywords = build_fuzzy_keywords(task, script);
        let fuzzy_refs = fuzzy_keywords.iter().map(String::as_str).collect::<Vec<_>>();
        Some(
            resolve_script(&cfg.scripts_dir, script, &fuzzy_refs)
                .with_context(|| format!("resolve script for task {}", task.id))?,
        )
    } else {
        None
    };

    let rendered_inputs = render_inputs(task, form)?;
    let default_tpl = if task.script.is_some() {
        "{command} {script} {extra_args}"
    } else {
        "{command} {extra_args}"
    };
    let tpl = task.arg_template.as_deref().unwrap_or(default_tpl);
    let rendered = render_task_template(tpl, &program, script_path.as_ref(), &rendered_inputs);
    let mut parts = shell_words::split(&rendered).context("parse command line")?;
    if parts.is_empty() {
        return Err(anyhow!("empty command after rendering task {}", task.id));
    }

    let program = parts.remove(0);
    let args = parts;
    Ok(PreparedCommand {
        rendered: render_display_command(&program, &args),
        program,
        args,
    })
}

pub async fn spawn_task(
    cmd: &PreparedCommand,
    cfg: &GuiConfig,
    path_settings: Option<&TaskPathSettings>,
) -> Result<SpawnedTask> {
    let mut command = Command::new(&cmd.program);
    command.args(&cmd.args);
    command.current_dir(normalize_path(&cfg.project_root));
    inject_env(&mut command, &cfg.project_root)?;
    inject_path_settings_env(&mut command, path_settings);
    command.stdout(std::process::Stdio::piped());
    command.stderr(std::process::Stdio::piped());
    let mut child = command.spawn().context("spawn task")?;
    let pid = child.id().ok_or_else(|| anyhow!("spawned process has no pid"))?;
    let stdout = child.stdout.take();
    let stderr = child.stderr.take();
    Ok(SpawnedTask {
        pid,
        child,
        stdout,
        stderr,
    })
}

pub async fn load_select_options(
    cfg: &GuiConfig,
    command_override: Option<&str>,
    options_source: &str,
) -> Result<Vec<SelectOption>> {
    let command_bin = command_override
        .map(|s| s.to_string())
        .or_else(|| cfg.python_path.clone())
        .unwrap_or_else(|| "python".to_string());
    let script_path = resolve_script(&cfg.scripts_dir, options_source, &[".py"])
        .with_context(|| format!("resolve options_source {}", options_source))?;

    let mut command = Command::new(command_bin);
    command.arg(script_path);
    command.current_dir(normalize_path(&cfg.project_root));
    inject_env(&mut command, &cfg.project_root)?;
    let output = command.output().await.context("run options_source script")?;
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();

    if !output.status.success() {
        return Err(anyhow!(
            "options_source failed (code {:?}): {}",
            output.status.code(),
            stderr
        ));
    }
    parse_options_stdout(&stdout)
}

fn build_fuzzy_keywords(task: &Task, script: &str) -> Vec<String> {
    if task.fuzzy_keywords.is_empty() {
        let fallback = Path::new(script)
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or(script);
        vec![".py".to_string(), fallback.to_string()]
    } else {
        task.fuzzy_keywords.clone()
    }
}

fn render_inputs(task: &Task, form: &HashMap<String, FormValue>) -> Result<HashMap<String, String>> {
    let mut rendered = HashMap::new();
    let mut extra_args = Vec::new();

    for input in &task.inputs {
        let name = field_name(input);
        let value = form.get(name);
        let tokens = render_input_tokens(input, value)?;
        let joined = if tokens.is_empty() {
            String::new()
        } else {
            tokens
                .iter()
                .map(|x| quote_if_needed(x))
                .collect::<Vec<_>>()
                .join(" ")
        };
        rendered.insert(name.to_string(), joined);
        extra_args.extend(tokens);
    }

    rendered.insert(
        "extra_args".to_string(),
        extra_args
            .iter()
            .map(|x| quote_if_needed(x))
            .collect::<Vec<_>>()
            .join(" "),
    );
    Ok(rendered)
}

fn render_input_tokens(input: &InputField, value: Option<&FormValue>) -> Result<Vec<String>> {
    let tpl = field_template(input);

    match input {
        InputField::Boolean { .. } => {
            let enabled = value.and_then(|v| v.as_bool()).unwrap_or(false);
            if !enabled {
                return Ok(Vec::new());
            }
            if let Some(template) = tpl {
                split_template_tokens(&template.replace("{value}", "true"))
            } else {
                Ok(Vec::new())
            }
        }
        _ => {
            let Some(v) = value else {
                return Ok(Vec::new());
            };
            if v.is_null() {
                return Ok(Vec::new());
            }

            if let Some(items) = v.as_array() {
                let mut out = Vec::new();
                for item in items {
                    if let Some(s) = value_to_str(item) {
                        out.extend(render_template_tokens(tpl.as_deref(), &s)?);
                    }
                }
                return Ok(out);
            }

            let rendered = value_to_str(v).unwrap_or_default();
            if rendered.is_empty() {
                return Ok(Vec::new());
            }
            render_template_tokens(tpl.as_deref(), &rendered)
        }
    }
}

fn render_template_tokens(tpl: Option<&str>, value: &str) -> Result<Vec<String>> {
    if let Some(template) = tpl {
        let normalized = normalize_shell_path(value);
        let quoted = shell_words::quote(&normalized);
        split_template_tokens(&template.replace("{value}", &quoted))
    } else {
        Ok(vec![normalize_shell_path(value)])
    }
}

fn split_template_tokens(s: &str) -> Result<Vec<String>> {
    if s.trim().is_empty() {
        return Ok(Vec::new());
    }
    shell_words::split(s).context("split arg_template")
}

fn render_task_template(
    template: &str,
    program: &str,
    script_path: Option<&PathBuf>,
    rendered_inputs: &HashMap<String, String>,
) -> String {
    let mut out = template.replace("{command}", &quote_if_needed(program));
    let script_text = script_path
        .map(|p| quote_if_needed(&p.to_string_lossy()))
        .unwrap_or_default();
    out = out.replace("{script}", &script_text);
    for (k, v) in rendered_inputs {
        out = out.replace(&format!("{{{}}}", k), v);
    }
    out
}

fn parse_options_stdout(stdout: &str) -> Result<Vec<SelectOption>> {
    if stdout.trim().is_empty() {
        return Ok(Vec::new());
    }
    if let Ok(options) = serde_json::from_str::<Vec<SelectOption>>(stdout) {
        return Ok(options);
    }
    if let Ok(values) = serde_json::from_str::<Vec<String>>(stdout) {
        return Ok(values
            .into_iter()
            .map(|v| SelectOption {
                label: v.clone(),
                value: v,
            })
            .collect());
    }

    let mut options = Vec::new();
    for line in stdout.lines().map(str::trim).filter(|line| !line.is_empty()) {
        if let Some((label, value)) = line.split_once('|') {
            options.push(SelectOption {
                label: label.trim().to_string(),
                value: value.trim().to_string(),
            });
        } else if let Some((label, value)) = line.split_once('\t') {
            options.push(SelectOption {
                label: label.trim().to_string(),
                value: value.trim().to_string(),
            });
        } else {
            options.push(SelectOption {
                label: line.to_string(),
                value: line.to_string(),
            });
        }
    }
    Ok(options)
}

fn inject_env(command: &mut Command, project_root: &str) -> Result<()> {
    let env_path = Path::new(&normalize_path(project_root)).join(".env");
    if env_path.exists() {
        let iter = dotenvy::from_path_iter(&env_path)
            .with_context(|| format!("read {}", env_path.display()))?;
        for item in iter.flatten() {
            command.env(item.0, item.1);
        }
    }
    Ok(())
}

fn inject_path_settings_env(command: &mut Command, path_settings: Option<&TaskPathSettings>) {
    let Some(settings) = path_settings else {
        return;
    };
    if let Some(import_path) = &settings.import_path {
        if !import_path.trim().is_empty() {
            command.env("CONSILIENCE_IMPORT_PATH", import_path.trim());
        }
    }
    if let Some(export_path) = &settings.export_path {
        if !export_path.trim().is_empty() {
            command.env("CONSILIENCE_EXPORT_PATH", export_path.trim());
        }
    }
}

fn value_to_str(value: &FormValue) -> Option<String> {
    match value {
        serde_json::Value::String(v) => Some(v.to_string()),
        serde_json::Value::Number(v) => Some(v.to_string()),
        serde_json::Value::Bool(v) => Some(v.to_string()),
        _ => None,
    }
}

fn field_template(input: &InputField) -> Option<String> {
    match input {
        InputField::Select { arg_template, .. }
        | InputField::Boolean { arg_template, .. }
        | InputField::Text { arg_template, .. }
        | InputField::Number { arg_template, .. } => arg_template.clone(),
    }
}

fn field_name(input: &InputField) -> &str {
    match input {
        InputField::Select { name, .. }
        | InputField::Boolean { name, .. }
        | InputField::Text { name, .. }
        | InputField::Number { name, .. } => name,
    }
}

fn normalize_path(path: &str) -> String {
    if cfg!(windows) {
        path.replace('/', "\\")
    } else {
        path.replace('\\', "/")
    }
}

fn quote_if_needed(s: &str) -> String {
    if s.is_empty() {
        return String::new();
    }
    let normalized = normalize_shell_path(s);
    if normalized.contains(' ') || normalized.contains('"') {
        format!("\"{}\"", normalized.replace('"', "\\\""))
    } else {
        normalized
    }
}

fn render_display_command(program: &str, args: &[String]) -> String {
    let mut out = vec![quote_if_needed(program)];
    out.extend(args.iter().map(|arg| quote_if_needed(arg)));
    out.join(" ")
}

fn normalize_shell_path(input: &str) -> String {
    if cfg!(windows) && input.contains('\\') {
        input.replace('\\', "/")
    } else {
        input.to_string()
    }
}

pub fn stream_to_lines(stdout: ChildStdout) -> tokio::io::Lines<BufReader<ChildStdout>> {
    BufReader::new(stdout).lines()
}

pub fn stream_err_to_lines(stderr: ChildStderr) -> tokio::io::Lines<BufReader<ChildStderr>> {
    BufReader::new(stderr).lines()
}
