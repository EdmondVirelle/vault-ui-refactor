import { invoke, isTauri } from "@tauri-apps/api/core";

export const TAURI_REQUIRED_MSG =
  "載入失敗：找不到 Tauri 介面，請透過 Tauri 視窗啟動（npm run tauri dev）";

export function assertTauri(): void {
  if (!isTauri()) {
    throw new Error(TAURI_REQUIRED_MSG);
  }
}

export async function invokeCmd<T>(command: string, args?: Record<string, unknown>): Promise<T> {
  assertTauri();
  return invoke<T>(command, args);
}
