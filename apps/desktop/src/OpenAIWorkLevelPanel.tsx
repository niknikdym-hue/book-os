import { useEffect, useState } from "react";
import {
  getPendingOpenAIWorkLevel,
  OPENAI_WORK_LEVEL_OPTIONS,
  openAIWorkLevelLabel,
  setPendingOpenAIWorkLevel,
  subscribeOpenAIWorkLevel,
  type OpenAIWorkLevel,
} from "./openaiWorkLevel";

export function OpenAIWorkLevelPanel() {
  const [workLevel, setWorkLevel] = useState<OpenAIWorkLevel | null>(getPendingOpenAIWorkLevel());

  useEffect(() => subscribeOpenAIWorkLevel(setWorkLevel), []);

  return (
    <section className="panel compact-work-level" aria-label="Уровень работы OpenAI">
      <div className="compact-control-heading">
        <div>
          <p className="eyebrow">OPENAI</p>
          <h3>Глубина работы</h3>
        </div>
        <span className={`badge ${workLevel ? "approved" : "draft"}`}>
          {openAIWorkLevelLabel(workLevel)}
        </span>
      </div>
      <div className="actions planning-action left-actions compact-actions">
        {OPENAI_WORK_LEVEL_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            className={workLevel === option.value ? "primary" : "ghost"}
            aria-pressed={workLevel === option.value}
            onClick={() => setPendingOpenAIWorkLevel(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
      <small className="muted">Выбор действует на следующую существенную OpenAI-операцию.</small>
    </section>
  );
}
