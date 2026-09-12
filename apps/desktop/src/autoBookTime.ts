export function formatElapsedTime(startedAt?: string | null, endAt?: string | null): string {
  if (!startedAt || !endAt) return "00:00:00";
  const startedMs = Date.parse(startedAt);
  const endMs = Date.parse(endAt);
  if (!Number.isFinite(startedMs) || !Number.isFinite(endMs)) return "00:00:00";
  const totalSeconds = Math.max(0, Math.floor((endMs - startedMs) / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return [hours, minutes, seconds].map((value) => String(value).padStart(2, "0")).join(":");
}
