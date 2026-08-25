use rand::distr::Alphanumeric;
use rand::{rng, Rng};
use serde::Deserialize;
use serde_json::Value;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::Manager;

struct Core {
    child: Mutex<Child>,
    port: u16,
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
}
impl Drop for Core {
    fn drop(&mut self) {
        self.stop();
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

fn launch(data_dir: &Path) -> Result<Core, String> {
    let token: String = rng()
        .sample_iter(&Alphanumeric)
        .take(48)
        .map(char::from)
        .collect();
    let python = std::env::var("BOOK_OS_PYTHON")
        .map(|value| resolve_python(&value, Path::new(env!("CARGO_MANIFEST_DIR"))))
        .unwrap_or_else(|_| PathBuf::from("python3"));
    let source_path = std::env::var("BOOK_OS_CORE_PYTHONPATH").unwrap_or_else(|_| {
        format!(
            "{}/../../../services/local-core/src",
            env!("CARGO_MANIFEST_DIR")
        )
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
    let mut reader = BufReader::new(stdout);
    let mut ready_line = String::new();
    reader
        .read_line(&mut ready_line)
        .map_err(|e| e.to_string())?;
    let ready: Ready = serde_json::from_str(&ready_line).map_err(|e| e.to_string())?;
    Ok(Core {
        child: Mutex::new(child),
        port: ready.port,
        token,
    })
}

fn read_json_response(response: ureq::http::Response<ureq::Body>) -> Result<Value, String> {
    let text = response
        .into_body()
        .read_to_string()
        .map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

#[tauri::command]
fn core_health(core: tauri::State<'_, Core>) -> Result<Value, String> {
    let url = format!("http://127.0.0.1:{}/health", core.port);
    let response = ureq::get(&url)
        .header("Authorization", &format!("Bearer {}", core.token))
        .call()
        .map_err(|e| e.to_string())?;
    read_json_response(response)
}

#[tauri::command]
fn core_api(request: CoreApiRequest, core: tauri::State<'_, Core>) -> Result<Value, String> {
    let method = request.method.to_ascii_uppercase();
    validate_core_api_request(&method, &request.path)?;
    let url = format!("http://127.0.0.1:{}{}", core.port, request.path);
    let authorization = format!("Bearer {}", core.token);
    let response = match method.as_str() {
        "GET" => ureq::get(&url)
            .header("Authorization", &authorization)
            .call(),
        "POST" => ureq::post(&url)
            .header("Authorization", &authorization)
            .send_json(request.body.unwrap_or(Value::Null)),
        "PUT" => ureq::put(&url)
            .header("Authorization", &authorization)
            .send_json(request.body.unwrap_or(Value::Null)),
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
            app.manage(launch(&data_dir).map_err(std::io::Error::other)?);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![core_health, core_api])
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::Destroyed) {
                if let Some(core) = window.app_handle().try_state::<Core>() {
                    core.stop();
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
            if let Some(core) = app_handle.try_state::<Core>() {
                core.stop();
            }
        }
    });
}

#[cfg(test)]
mod tests {
    use super::{resolve_python, validate_core_api_request};
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
}
