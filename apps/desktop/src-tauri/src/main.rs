use rand::distr::Alphanumeric;
use rand::{rng, Rng};
use serde::Deserialize;
use std::io::{BufRead, BufReader};
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
fn launch() -> Result<Core, String> {
    let token: String = rng()
        .sample_iter(&Alphanumeric)
        .take(48)
        .map(char::from)
        .collect();
    let python = std::env::var("BOOK_OS_PYTHON").unwrap_or_else(|_| "python3".into());
    let source_path = std::env::var("BOOK_OS_CORE_PYTHONPATH").unwrap_or_else(|_| {
        format!(
            "{}/../../../services/local-core/src",
            env!("CARGO_MANIFEST_DIR")
        )
    });
    let mut child = Command::new(python)
        .args(["-m", "book_os_core"])
        .env("BOOK_OS_SESSION_TOKEN", &token)
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
#[tauri::command]
fn core_health(core: tauri::State<'_, Core>) -> Result<serde_json::Value, String> {
    let url = format!("http://127.0.0.1:{}/health", core.port);
    let response = ureq::get(&url)
        .header("Authorization", &format!("Bearer {}", core.token))
        .call()
        .map_err(|e| e.to_string())?;
    let text = response
        .into_body()
        .read_to_string()
        .map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}
fn main() {
    tauri::Builder::default()
        .setup(|app| {
            app.manage(launch().map_err(std::io::Error::other)?);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![core_health])
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::Destroyed) {
                if let Some(core) = window.app_handle().try_state::<Core>() {
                    core.stop();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("BOOK OS desktop error");
}
