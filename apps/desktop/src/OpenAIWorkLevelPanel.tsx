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
  const [workLevel, setWorkLevel] = useState<OpenAIWorkLevel | null>(
    getPendingOpenAIWorkLevel(),
  );

  useEffect(() => subscribeOpenAIWorkLevel(setWorkLevel), []);

  return (
    <section className="panel legacy-openai-work-level-panel" aria-label="Уровень работы OpenAI">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">OPENAI · СЛЕДУЮЩАЯ ОПЕРАЦИЯ</p>
          <h3>Уровень работы модели</h3>
        </div>
        <span className={`badge ${workLevel ? "approved" : "draft"}`}>
          {openAIWorkLevelLabel(workLevel)}
        </span>
      </div>
      <p className="muted">
        Выберите уровень для следующей OpenAI-операции. После любой попытки BOOK OS сбросит выбор,
        поэтому следующая существенная операция снова потребует явного решения. Authority, этапы,
        quality gates и редакционные правила от уровня модели не меняются.
      </p>
      <div className="actions planning-action">
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
      <small className="muted">
        Medium = medium · High = high · Extra High = xhigh. Точный уровень сохраняется в provenance
        модельного запуска.
      </small>
    </section>
  );
}
