import { useEffect, useState } from "react";

type Props = {
  startedAt?: string | null;
  updatedAt?: string | null;
  running: boolean;
};

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

export function AutoBookClock({ startedAt, updatedAt, running }: Props) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!running) return;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [running, startedAt]);

  const endAt = running ? new Date(now).toISOString() : updatedAt;

  return (
    <span className="auto-progress-clock" aria-label="Время работы Auto Book">
      Время работы <strong>{formatElapsedTime(startedAt, endAt)}</strong>
    </span>
  );
}
