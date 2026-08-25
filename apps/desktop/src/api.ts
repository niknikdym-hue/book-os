import { invoke } from "@tauri-apps/api/core";

export async function coreApi<T>(
  method: "GET" | "POST" | "PUT",
  path: string,
  body?: unknown,
): Promise<T> {
  return invoke<T>("core_api", {
    request: { method, path, body: body ?? null },
  });
}
