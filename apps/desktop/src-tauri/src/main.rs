use rand::distr::Alphanumeric;
use rand::{rng, Rng};
use serde::Deserialize;
use serde_json::Value;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdout, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tauri::Manager;

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

fn validate_core_api_request(method: &str, path: &str) -> Result<(), String> {
    if !matches!(method, "GET" | "POST" | "PUT") {
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

fn spawn_core(data_dir: &Path) -> Result<(Arc<Core>, BufReader<ChildStdout>), String> {
    let token: String = rng()
        .sample_iter(&Alphanumeric)
        .take(48)
        .map(char::from)
        .collect();
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let python = std::env::var("BOOK_OS_PYTHON")
        .map(|value| resolve_python(&value, manifest_dir))
        .unwrap_or_else(|_| default_python(manifest_dir));
    let source_path = std::env::var("BOOK_OS_CORE_PYTHONPATH").unwrap_or_else(|_| {
        format!("{}/../../../services/local-core/src", env!("CARGO_MANIFEST_DIR"))
    });
    let mut child = Command::new(python)
        .args(["-m", "book_os_core"])
        .env("BOOK_OS_SESSION_TOKEN", &token)
        .env("BOOK_OS_DATA_DIR", data_dir)
        .env("PYTHONPATH", source_path)
        .stdout(Stdio::piped())
        .spawn()
        .map_err(|e| e.to_string())?;
    let stdout = child.stdout.take().ok_or("sidecar stdout unavailable")?;
    let core = Arc::new(Core {
        child: Mutex::new(child),
        port: Mutex::new(None),
        token,
    });
    Ok((core, BufReader::new(stdout)))
}

fn wait_for_ready(core: &Core, reader: &mut BufReader<ChildStdout>) -> Result<(), String> {
    let mut ready_line = String::new();
    let read = reader
        .read_line(&mut ready_line)
        .map_err(|e| e.to_string())?;
    if read == 0 {
        return Err("local core exited before readiness".into());
    }
    let ready: Ready = serde_json::from_str(&ready_line).map_err(|e| e.to_string())?;
    request_core_health(core, ready.port)?;
    {
        let mut port = core
            .port
            .lock()
            .map_err(|_| "local core port lock poisoned".to_string())?;
        *port = Some(ready.port);
    }
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
        .map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

fn json_request_body(body: Option<Value>) -> Result<String, String> {
    serde_json::to_string(&body.unwrap_or(Value::Null)).map_err(|e| e.to_string())
}

fn request_core_health(core: &Core, port: u16) -> Result<Value, String> {
    let url = format!("http://127.0.0.1:{port}/health");
    let response = ureq::get(&url)
        .header("Authorization", &format!("Bearer {}", core.token))
        .call()
        .map_err(|e| e.to_string())?;
    read_json_response(response)
}

#[tauri::command]
async fn core_health(state: tauri::State<'_, CoreState>) -> Result<Value, String> {
    let deadline = Instant::now() + Duration::from_secs(30);
    loop {
        if let Some(error) = state.error_message() {
            return Err(format!("local core failed to start: {error}"));
        }
        if let Some(core) = state.current_core()? {
            if let Some(port) = core.port()? {
                return request_core_health(&core, port);
            }
        }
        if Instant::now() >= deadline {
            return Err("local core startup timed out after 30 seconds".into());
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
    let port = core.port()?.ok_or_else(|| "local core is still starting".to_string())?;
    let url = format!("http://127.0.0.1:{port}{}", request.path);
    let authorization = format!("Bearer {}", core.token);
    let response = match method.as_str() {
        "GET" => ureq::get(&url)
            .header("Authorization", &authorization)
            .call(),
        "POST" => ureq::post(&url)
            .header("Authorization", &authorization)
            .content_type("application/json")
            .send(json_request_body(request.body)?),
        "PUT" => ureq::put(&url)
            .header("Authorization", &authorization)
            .content_type("application/json")
            .send(json_request_body(request.body)?),
        _ => unreachable!("validated method"),
    }
    .map_err(|e| e.to_string())?;
    read_json_response(response)
}

fn main() {
    let app = tauri::Builder::default()
        .setup(|app| {
            let data_dir = app.path().app_data_dir()?;
            std::fs::create_dir_all(&data_dir)?;
            app.manage(CoreState::default());
            let state = app.state::<CoreState>();
            match spawn_core(&data_dir) {
                Ok((core, mut reader)) => {
                    let mut managed_core = state
                        .core
                        .lock()
                        .map_err(|_| std::io::Error::other("local core state lock poisoned"))?;
                    *managed_core = Some(Arc::clone(&core));
                    drop(managed_core);
                    let app_handle = app.handle().clone();
                    std::thread::spawn(move || {
                        if let Err(error) = wait_for_ready(&core, &mut reader) {
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
        .invoke_handler(tauri::generate_handler![core_health, frontend_ready, core_api])
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
    use super::{default_python, json_request_body, resolve_python, validate_core_api_request};
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
    fn local_core_proxy_is_bounded_to_api_paths() {
        assert!(validate_core_api_request("GET", "/api/projects").is_ok());
        assert!(validate_core_api_request("POST", "/api/projects").is_ok());
        assert!(validate_core_api_request("PUT", "/api/projects/ABC/book-contract/draft").is_ok());
        assert!(validate_core_api_request("DELETE", "/api/projects/ABC").is_err());
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
}
