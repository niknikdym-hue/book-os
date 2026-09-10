import { useEffect, useState } from "react";
import {
  getPendingOpenAIWorkLevel,
  OPENAI_WORK_LEVEL_OPTIONS,
  openAIWorkLevelLabel,
  setPendingOpenAIWorkLevel,
  subscribeOpenAIWorkLevel,
  type OpenAIWorkLevel,
} from "./openaiWorkLevel";

// Validated against this account's non-billable OpenAI Models metadata on 2026-09-10.
// Keep model identity separate from reasoning effort: they are different API fields.
export const OPENAI_ASTRA_MODELS = [
  {
    id: "gpt-6-astra",
    label: "GPT-6 Astra",
    workLevels: ["medium", "high", "xhigh"] as const,
  },
] as const;

export function OpenAIWorkLevelPanel() {
  const [workLevel, setWorkLevel] = useState<OpenAIWorkLevel | null>(
    getPendingOpenAIWorkLevel(),
  );

  useEffect(() => subscribeOpenAIWorkLevel(setWorkLevel), []);

  return (
    <section className="panel legacy-openai-work-level-panel" aria-label="Уровень работы OpenAI">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ASTRA · СЛЕДУЮЩАЯ ОПЕРАЦИЯ</p>
          <h3>Модель и глубина работы</h3>
        </div>
        <span className={`badge ${workLevel ? "approved" : "draft"}`}>
          {openAIWorkLevelLabel(workLevel)}
        </span>
      </div>
      <label className="field">
        <span>Модель Astra</span>
        <select aria-label="Модель Astra" value="gpt-6-astra" disabled>
          {OPENAI_ASTRA_MODELS.map((model) => (
            <option key={model.id} value={model.id}>{model.label}</option>
          ))}
        </select>
      </label>
      <p className="muted">Выберите глубину для следующей операции. Модель и уровень работы — отдельные параметры API.</p>
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
