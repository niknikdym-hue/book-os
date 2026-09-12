import { useEffect, useState } from "react";
import { formatElapsedTime } from "./autoBookTime";

type Props = {
  startedAt?: string | null;
  updatedAt?: string | null;
  running: boolean;
};

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
