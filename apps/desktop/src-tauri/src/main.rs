use rand::distr::Alphanumeric;
use rand::{rng, Rng};
use serde::Deserialize;
use serde_json::Value;
use std::fs::OpenOptions;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdout, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tauri::{path::BaseDirectory, Manager};

const CORE_HEALTH_CALL_TIMEOUT: Duration = Duration::from_secs(2);
const CORE_STARTUP_DEADLINE: Duration = Duration::from_secs(60);
const CORE_HEALTH_RETRY_DEADLINE: Duration = Duration::from_secs(8);
const CORE_STARTUP_LOG: &str = "local-core-startup.log";
const BUNDLED_CORE_RESOURCE: &str = "book-os-core";

struct Core {
    child: Mutex<Child>,
    port: Mutex<Option<u16>>,
    token: String,
}

impl Core {
    fn stop(&self) {
        if let Ok(mut child) = self.child.lock() {
            if child.try_wait().ok().flatten().is_none() {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    }

    fn port(&self) -> Result<Option<u16>, String> {
        self.port
            .lock()
            .map(|port| *port)
            .map_err(|_| "local core port lock poisoned".to_string())
    }
}

impl Drop for Core {
    fn drop(&mut self) {
        self.stop();
    }
}

#[derive(Default)]
struct CoreState {
    core: Mutex<Option<Arc<Core>>>,
    error: Mutex<Option<String>>,
}

impl CoreState {
    fn current_core(&self) -> Result<Option<Arc<Core>>, String> {
        self.core
            .lock()
            .map(|core| core.clone())
            .map_err(|_| "local core state lock poisoned".to_string())
    }

    fn error_message(&self) -> Option<String> {
        self.error.lock().ok().and_then(|error| error.clone())
    }

    fn set_error(&self, error: String) {
        if let Ok(mut managed_error) = self.error.lock() {
            *managed_error = Some(error);
        }
    }

    fn stop(&self) {
        if let Ok(core) = self.core.lock() {
            if let Some(core) = core.as_ref() {
                core.stop();
            }
        }
    }
}

#[derive(Deserialize)]
struct Ready {
    port: u16,
}

#[derive(Deserialize)]
struct CoreApiRequest {
    method: String,
    path: String,
    body: Option<Value>,
}

fn resolve_python(value: &str, manifest_dir: &Path) -> PathBuf {
    let path = PathBuf::from(value);
    if path.is_absolute() {
        path
    } else {
        manifest_dir
            .parent()
            .expect("Tauri manifest directory must have a desktop package parent")
            .join(path)
    }
}

fn default_python(manifest_dir: &Path) -> PathBuf {
    resolve_python("../../services/local-core/.venv/bin/python", manifest_dir)
}

fn canonical_existing_path(path: PathBuf, label: &str) -> Result<PathBuf, String> {
    path.canonicalize()
        .map_err(|error| format!("{label} unavailable at {}: {error}", path.display()))
}

fn preserve_venv_python(path: PathBuf) -> Result<PathBuf, String> {
    // Do not canonicalize the final `python` path. A venv interpreter is commonly a
    // symlink to the framework/system Python; resolving that symlink changes Python's
    // executable identity and can make it ignore the venv's installed packages.
    if !path.is_file() {
        return Err(format!(
            "local core Python unavailable at {}",
            path.display()
        ));
    }
    Ok(path)
}

fn append_startup_log(path: &Path, message: &str) {
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(path) {
        let _ = writeln!(file, "{message}");
    }
}

fn validate_core_api_request(method: &str, path: &str) -> Result<(), String> {
    if !matches!(method, "GET" | "POST" | "PUT" | "DELETE") {
        return Err("unsupported local-core API method".into());
    }
    if !path.starts_with("/api/")
        || path.contains("..")
        || path.contains("://")
        || path.contains('\\')
        || path.contains('#')
    {
        return Err("invalid local-core API path".into());
    }
    Ok(())
}

#[cfg(target_os = "macos")]
fn desktop_app_bundle() -> Result<PathBuf, String> {
    let home = std::env::var_os("HOME").ok_or("HOME is unavailable")?;
    Ok(PathBuf::from(home).join("Desktop").join("BOOK OS.app"))
}

#[cfg(target_os = "macos")]
fn source_app_bundle(executable: &Path) -> Option<PathBuf> {
    let macos_dir = executable.parent()?;
    if macos_dir.file_name()?.to_str()? != "MacOS" {
        return None;
    }
    let contents_dir = macos_dir.parent()?;
    if contents_dir.file_name()?.to_str()? != "Contents" {
        return None;
    }
    let app_dir = contents_dir.parent()?;
    if app_dir.extension()?.to_str()? != "app" {
        return None;
    }
    Some(app_dir.to_path_buf())
}

#[cfg(target_os = "macos")]
fn install_desktop_app() -> Result<Option<PathBuf>, String> {
    use std::fs;

    if cfg!(debug_assertions) {
        return Ok(None);
    }

    let app_dir = desktop_app_bundle()?;
    let installed_executable = app_dir.join("Contents").join("MacOS").join("BOOK OS");
    let current_executable = std::env::current_exe().map_err(|error| error.to_string())?;

    if current_executable == installed_executable {
        return Ok(Some(app_dir));
    }

    let source_bundle = source_app_bundle(&current_executable).ok_or_else(|| {
        format!(
            "current production executable is not inside a macOS app bundle: {}",
            current_executable.display()
        )
    })?;

    if app_dir.exists() {
        fs::remove_dir_all(&app_dir).map_err(|error| error.to_string())?;
    }
    let status = Command::new("/usr/bin/ditto")
        .arg(&source_bundle)
        .arg(&app_dir)
        .status()
        .map_err(|error| format!("unable to copy BOOK OS.app to Desktop: {error}"))?;
    if !status.success() {
        return Err(format!("ditto app copy failed with status {status}"));
    }

    let _ = Command::new("/usr/bin/xattr")
        .args(["-dr", "com.apple.quarantine"])
        .arg(&app_dir)
        .status();

    let status = Command::new("/usr/bin/codesign")
        .args(["--force", "--deep", "--sign", "-"])
        .arg(&app_dir)
        .status()
        .map_err(|error| format!("unable to invoke codesign: {error}"))?;
    if !status.success() {
        return Err(format!("ad-hoc codesign failed with status {status}"));
    }

    if !installed_executable.is_file() {
        return Err("Desktop BOOK OS.app has no executable after installation".into());
    }
    if !app_dir
        .join("Contents")
        .join("Resources")
        .join(BUNDLED_CORE_RESOURCE)
        .is_file()
    {
        return Err("Desktop BOOK OS.app is missing its bundled Local Core".into());
    }

    Ok(Some(app_dir))
}

#[cfg(not(target_os = "macos"))]
fn install_desktop_app() -> Result<Option<PathBuf>, String> {
    Ok(None)
}

fn dev_python_command(startup_log: &Path) -> Result<Command, String> {
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let python = std::env::var("BOOK_OS_PYTHON")
        .map(|value| resolve_python(&value, manifest_dir))
        .unwrap_or_else(|_| default_python(manifest_dir));
    let python = preserve_venv_python(python)?;
    let source_path = std::env::var("BOOK_OS_CORE_PYTHONPATH")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            PathBuf::from(format!(
                "{}/../../../services/local-core/src",
                env!("CARGO_MANIFEST_DIR")
            ))
        });
    let source_path = canonical_existing_path(source_path, "local core source")?;

    append_startup_log(startup_log, "core_mode=development-python");
    append_startup_log(startup_log, &format!("python={}", python.display()));
    append_startup_log(
        startup_log,
        &format!("pythonpath={}", source_path.display()),
    );

    let mut command = Command::new(&python);
    command
        .args(["-m", "book_os_core"])
        .env("PYTHONPATH", source_path);
    Ok(command)
}

fn spawn_core(
    data_dir: &Path,
    bundled_core: Option<&Path>,
) -> Result<(Arc<Core>, BufReader<ChildStdout>, PathBuf), String> {
    let token: String = rng()
        .sample_iter(&Alphanumeric)
        .take(48)
        .map(char::from)
        .collect();
    let startup_log = data_dir.join(CORE_STARTUP_LOG);
    std::fs::write(&startup_log, "")
        .map_err(|error| format!("unable to initialize local core startup log: {error}"))?;

    let mut command = if std::env::var_os("BOOK_OS_PYTHON").is_some() || cfg!(debug_assertions) {
        dev_python_command(&startup_log)?
    } else {
        let binary = bundled_core.ok_or("production app has no bundled Local Core path")?;
        let binary = canonical_existing_path(binary.to_path_buf(), "bundled local core")?;
        append_startup_log(&startup_log, "core_mode=bundled");
        append_startup_log(&startup_log, &format!("core_binary={}", binary.display()));
        Command::new(binary)
    };

    append_startup_log(&startup_log, &format!("data_dir={}", data_dir.display()));
    let stderr = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&startup_log)
        .map_err(|error| format!("unable to open local core startup log: {error}"))?;
    let mut child = command
        .env("BOOK_OS_SESSION_TOKEN", &token)
        .env("BOOK_OS_DATA_DIR", data_dir)
        .env("PYTHONUNBUFFERED", "1")
        .stdout(Stdio::piped())
        .stderr(Stdio::from(stderr))
        .spawn()
        .map_err(|error| format!("unable to spawn local core: {error}"))?;
    append_startup_log(&startup_log, &format!("pid={}", child.id()));
    let stdout = child.stdout.take().ok_or("sidecar stdout unavailable")?;
    let core = Arc::new(Core {
        child: Mutex::new(child),
        port: Mutex::new(None),
        token,
    });
    Ok((core, BufReader::new(stdout), startup_log))
}

fn health_agent() -> ureq::Agent {
    let config = ureq::Agent::config_builder()
        .timeout_global(Some(CORE_HEALTH_CALL_TIMEOUT))
        .build();
    config.into()
}

fn wait_for_ready(
    core: &Core,
    reader: &mut BufReader<ChildStdout>,
    startup_log: &Path,
) -> Result<(), String> {
    let mut ready_line = String::new();
    let read = reader
        .read_line(&mut ready_line)
        .map_err(|error| format!("unable to read local core readiness: {error}"))?;
    if read == 0 {
        return Err(format!(
            "local core exited before readiness; see {}",
            startup_log.display()
        ));
    }
    append_startup_log(
        startup_log,
        &format!("stdout_readiness={}", ready_line.trim()),
    );
    let ready: Ready = serde_json::from_str(&ready_line)
        .map_err(|error| format!("invalid local core readiness payload: {error}"))?;

    // Publish the announced port before the redundant HTTP probe. Python emits the
    // readiness line only after Uvicorn startup, so an HTTP-client stall must never
    // keep the desktop UI stuck forever in `port=None`.
    {
        let mut port = core
            .port
            .lock()
            .map_err(|_| "local core port lock poisoned".to_string())?;
        *port = Some(ready.port);
    }
    append_startup_log(startup_log, &format!("announced_port={}", ready.port));

    let deadline = Instant::now() + CORE_HEALTH_RETRY_DEADLINE;
    loop {
        match request_core_health(core, ready.port) {
            Ok(_) => break,
            Err(error) => {
                if Instant::now() >= deadline {
                    return Err(format!(
                        "local core announced port {} but /health did not become ready: {error}; see {}",
                        ready.port,
                        startup_log.display()
                    ));
                }
            }
        }
        std::thread::sleep(Duration::from_millis(150));
    }

    append_startup_log(startup_log, "health=healthy");
    println!("BOOK OS local core healthy");
    if let Some(path) = std::env::var_os("BOOK_OS_CORE_READY_FILE") {
        std::fs::write(PathBuf::from(path), b"healthy\n")
            .map_err(|error| format!("unable to write local core readiness marker: {error}"))?;
    }
    Ok(())
}

fn read_json_response(mut response: ureq::http::Response<ureq::Body>) -> Result<Value, String> {
    let text = response
        .body_mut()
        .read_to_string()
        .map_err(|error| error.to_string())?;
    serde_json::from_str(&text).map_err(|error| error.to_string())
}

fn json_request_body(body: Option<Value>) -> Result<String, String> {
    serde_json::to_string(&body.unwrap_or(Value::Null)).map_err(|error| error.to_string())
}

fn request_core_health(core: &Core, port: u16) -> Result<Value, String> {
    let url = format!("http://127.0.0.1:{port}/health");
    let response = health_agent()
        .get(&url)
        .header("Authorization", &format!("Bearer {}", core.token))
        .call()
        .map_err(|error| format!("local core health request failed: {error}"))?;
    read_json_response(response)
}

#[tauri::command]
async fn core_health(state: tauri::State<'_, CoreState>) -> Result<Value, String> {
    let deadline = Instant::now() + CORE_STARTUP_DEADLINE;
    let mut last_health_error = None;
    loop {
        if let Some(error) = state.error_message() {
            return Err(format!("local core failed to start: {error}"));
        }
        if let Some(core) = state.current_core()? {
            if let Some(port) = core.port()? {
                match request_core_health(&core, port) {
                    Ok(value) => return Ok(value),
                    Err(error) => last_health_error = Some(error),
                }
            }
        }
        if Instant::now() >= deadline {
            if let Some(error) = last_health_error {
                return Err(format!(
                    "local core health did not become available within 60 seconds: {error}"
                ));
            }
            return Err("local core did not announce a port within 60 seconds".into());
        }
        std::thread::sleep(Duration::from_millis(100));
    }
}

#[tauri::command]
fn frontend_ready() -> Result<bool, String> {
    println!("BOOK OS frontend ready");
    if let Some(path) = std::env::var_os("BOOK_OS_FRONTEND_READY_FILE") {
        std::fs::write(PathBuf::from(path), b"ready\n")
            .map_err(|error| format!("unable to write frontend readiness marker: {error}"))?;
    }
    Ok(true)
}

#[tauri::command]
fn core_api(request: CoreApiRequest, state: tauri::State<'_, CoreState>) -> Result<Value, String> {
    let method = request.method.to_ascii_uppercase();
    validate_core_api_request(&method, &request.path)?;
    let core = state.current_core()?.ok_or_else(|| {
        state
            .error_message()
            .map(|error| format!("local core failed to start: {error}"))
            .unwrap_or_else(|| "local core is still starting".to_string())
    })?;
    let port = core
        .port()?
        .ok_or_else(|| "local core is still starting".to_string())?;
    let url = format!("http://127.0.0.1:{port}{}", request.path);
    let authorization = format!("Bearer {}", core.token);
    let response = match method.as_str() {
        "GET" => ureq::get(&url)
            .header("Authorization", &authorization)
            .config()
            .http_status_as_error(false)
            .build()
            .call(),
        "POST" => ureq::post(&url)
            .header("Authorization", &authorization)
            .content_type("application/json")
            .config()
            .http_status_as_error(false)
            .build()
            .send(json_request_body(request.body)?),
        "PUT" => ureq::put(&url)
            .header("Authorization", &authorization)
            .content_type("application/json")
            .config()
            .http_status_as_error(false)
            .build()
            .send(json_request_body(request.body)?),
        "DELETE" => ureq::delete(&url)
            .header("Authorization", &authorization)
            .config()
            .http_status_as_error(false)
            .build()
            .call(),
        _ => unreachable!("validated method"),
    }
    .map_err(|error| error.to_string())?;
    if !response.status().is_success() {
        let status = response.status();
        let detail = read_json_response(response)
            .ok()
            .and_then(|body| body.get("detail").and_then(Value::as_str).map(str::to_string))
            .unwrap_or_else(|| "Local Core did not provide a diagnostic".to_string());
        return Err(format!("Local Core returned HTTP {status}: {detail}"));
    }
    read_json_response(response)
}

fn main() {
    let app = tauri::Builder::default()
        .setup(|app| {
            match install_desktop_app() {
                Ok(Some(path)) => println!("BOOK OS desktop app ready: {}", path.display()),
                Ok(None) => {}
                Err(error) => eprintln!("BOOK OS desktop app installation failed: {error}"),
            }

            let data_dir = app.path().app_data_dir()?;
            std::fs::create_dir_all(&data_dir)?;
            app.manage(CoreState::default());
            let state = app.state::<CoreState>();
            let bundled_core = if cfg!(debug_assertions) || std::env::var_os("BOOK_OS_PYTHON").is_some() {
                None
            } else {
                Some(
                    app.path()
                        .resolve(BUNDLED_CORE_RESOURCE, BaseDirectory::Resource)
                        .map_err(|error| std::io::Error::other(error.to_string()))?,
                )
            };
            match spawn_core(&data_dir, bundled_core.as_deref()) {
                Ok((core, mut reader, startup_log)) => {
                    let mut managed_core = state
                        .core
                        .lock()
                        .map_err(|_| std::io::Error::other("local core state lock poisoned"))?;
                    *managed_core = Some(Arc::clone(&core));
                    drop(managed_core);
                    let app_handle = app.handle().clone();
                    std::thread::spawn(move || {
                        if let Err(error) = wait_for_ready(&core, &mut reader, &startup_log) {
                            append_startup_log(&startup_log, &format!("startup_error={error}"));
                            core.stop();
                            if let Some(state) = app_handle.try_state::<CoreState>() {
                                state.set_error(error);
                            }
                        }
                    });
                }
                Err(error) => state.set_error(error),
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            core_health,
            frontend_ready,
            core_api
        ])
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::Destroyed) {
                if let Some(state) = window.app_handle().try_state::<CoreState>() {
                    state.stop();
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("BOOK OS desktop build error");

    app.run(|app_handle, event| {
        if matches!(
            event,
            tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit
        ) {
            if let Some(state) = app_handle.try_state::<CoreState>() {
                state.stop();
            }
        }
    });
}

#[cfg(test)]
mod tests {
    use super::{
        canonical_existing_path, default_python, json_request_body, preserve_venv_python,
        resolve_python, validate_core_api_request,
    };
    use serde_json::json;
    use std::path::{Path, PathBuf};

    #[test]
    fn resolves_relative_python_from_desktop_package() {
        let manifest_dir = Path::new("/checkout/book-os/apps/desktop/src-tauri");

        assert_eq!(
            resolve_python("../../services/local-core/.venv/bin/python", manifest_dir),
            PathBuf::from(
                "/checkout/book-os/apps/desktop/../../services/local-core/.venv/bin/python"
            )
        );
    }

    #[test]
    fn defaults_to_the_project_local_python_environment() {
        let manifest_dir = Path::new("/checkout/book-os/apps/desktop/src-tauri");

        assert_eq!(
            default_python(manifest_dir),
            PathBuf::from(
                "/checkout/book-os/apps/desktop/../../services/local-core/.venv/bin/python"
            )
        );
    }

    #[test]
    fn preserves_absolute_python_path() {
        let manifest_dir = Path::new("/checkout/book-os/apps/desktop/src-tauri");
        let python = if cfg!(windows) {
            r"C:\Python312\python.exe"
        } else {
            "/opt/python/bin/python3"
        };

        assert_eq!(resolve_python(python, manifest_dir), PathBuf::from(python));
    }

    #[test]
    fn canonical_existing_path_rejects_missing_paths() {
        let missing = PathBuf::from("/definitely/not/a/book-os-path");
        assert!(canonical_existing_path(missing, "test path").is_err());
    }

    #[test]
    fn venv_python_validation_does_not_canonicalize_the_interpreter() {
        let current = std::env::current_exe().expect("current executable");
        let preserved = preserve_venv_python(current.clone()).expect("existing executable");
        assert_eq!(preserved, current);
    }

    #[test]
    fn local_core_proxy_is_bounded_to_api_paths() {
        assert!(validate_core_api_request("GET", "/api/projects").is_ok());
        assert!(validate_core_api_request("POST", "/api/projects").is_ok());
        assert!(validate_core_api_request("PUT", "/api/projects/ABC/book-contract/draft").is_ok());
        assert!(validate_core_api_request("DELETE", "/api/projects/ABC").is_ok());
        assert!(validate_core_api_request("PATCH", "/api/projects/ABC").is_err());
        assert!(validate_core_api_request("GET", "/health").is_err());
        assert!(validate_core_api_request("GET", "http://example.com/api/projects").is_err());
        assert!(validate_core_api_request("GET", "/api/../health").is_err());
    }

    #[test]
    fn local_core_proxy_serializes_json_without_optional_ureq_json_feature() {
        let body = json_request_body(Some(json!({"title": "Привет", "count": 2}))).unwrap();
        let parsed: serde_json::Value = serde_json::from_str(&body).unwrap();
        assert_eq!(parsed["title"], "Привет");
        assert_eq!(parsed["count"], 2);
    }

    #[cfg(target_os = "macos")]
    #[test]
    fn detects_the_source_app_bundle_from_a_macos_executable_path() {
        use super::source_app_bundle;

        assert_eq!(
            source_app_bundle(Path::new("/tmp/BOOK OS.app/Contents/MacOS/BOOK OS")),
            Some(PathBuf::from("/tmp/BOOK OS.app"))
        );
        assert_eq!(source_app_bundle(Path::new("/tmp/BOOK OS")), None);
    }
}
