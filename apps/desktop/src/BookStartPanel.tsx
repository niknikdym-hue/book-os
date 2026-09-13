import { useState } from "react";
import "./launchUx.css";
import {
  AVAILABLE_BUSINESS_SUBTYPES,
  BUSINESS_TOPICS,
  SUBTYPE_LABELS,
  type BusinessSubtype,
} from "./bookCatalog";

type Props = {
  newTitle: string;
  setNewTitle: (value: string) => void;
  idea: string;
  setIdea: (value: string) => void;
  authorName: string;
  setAuthorName: (value: string) => void;
  authorOptions: string[];
  seriesName: string;
  setSeriesName: (value: string) => void;
  seriesOptions: string[];
  readerHint: string;
  setReaderHint: (value: string) => void;
  targetCharacters: string;
  setTargetCharacters: (value: string) => void;
  primarySubtype: BusinessSubtype | null;
  setPrimarySubtype: (value: BusinessSubtype) => void;
  secondarySubtype: string;
  setSecondarySubtype: (value: string) => void;
  busy: boolean;
  onCreate: () => void;
  onClose: () => void;
};

export function BookStartPanel({
  newTitle,
  setNewTitle,
  idea,
  setIdea,
  authorName,
  setAuthorName,
  authorOptions,
  seriesName,
  setSeriesName,
  seriesOptions,
  readerHint,
  setReaderHint,
  targetCharacters,
  setTargetCharacters,
  primarySubtype,
  setPrimarySubtype,
  secondarySubtype,
  setSecondarySubtype,
  busy,
  onCreate,
  onClose,
}: Props) {
  const [topicConfirmed, setTopicConfirmed] = useState(false);
  const [volumePreset, setVolumePreset] = useState<"SHORT" | "STANDARD" | "LARGE" | "CUSTOM">(
    targetCharacters === "60000" ? "SHORT" : targetCharacters === "350000" ? "LARGE" : "STANDARD",
  );
  const availableTopics = BUSINESS_TOPICS.filter(
    (topic) => topic.availability === "AVAILABLE" && Boolean(topic.subtype),
  );
  const titleReady = newTitle.trim().length > 0;
  const ideaReady = idea.trim().length >= 3;
  const authorReady = authorName.trim().length > 0;
  const target = Number(targetCharacters);
  const targetReady = Number.isInteger(target) && target >= 4_000 && target <= 2_000_000;
  const canCreate = !busy && titleReady && ideaReady && authorReady && targetReady;

  function chooseVolume(preset: "SHORT" | "STANDARD" | "LARGE" | "CUSTOM") {
    setVolumePreset(preset);
    if (preset === "SHORT") setTargetCharacters("60000");
    if (preset === "STANDARD") setTargetCharacters("180000");
    if (preset === "LARGE") setTargetCharacters("350000");
  }

  return (
    <section className="panel new-book book-start-panel simplified-book-start" aria-label="Создание новой книги">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">НОВАЯ КНИГА</p>
          <h2>Создайте проект книги</h2>
          <p className="muted">
            Расскажите о книге обычными словами. Всё, что BOOK OS способен определить сам,
            появится на следующем шаге как предложение для проверки.
          </p>
        </div>
        <button className="ghost" onClick={onClose} type="button">
          Закрыть
        </button>
      </div>

      <div className="start-details simple-start-details">
        <label className="field required-field">
          <span>
            Рабочее название <b className="required-mark">*</b>
          </span>
          <input
            value={newTitle}
            onChange={(event) => setNewTitle(event.target.value)}
            placeholder="Например: Как продавать услуги"
            aria-invalid={!titleReady}
          />
          <small>Название можно изменить позже.</small>
        </label>

        <label className="field required-field">
          <span>
            Идея книги <b className="required-mark">*</b>
          </span>
          <textarea
            rows={6}
            value={idea}
            onChange={(event) => setIdea(event.target.value)}
            placeholder="Расскажите своими словами, какую книгу вы хотите создать: о чём она, зачем она читателю и какой результат должна дать."
            aria-invalid={!ideaReady}
          />
        </label>

        <div className="form-grid book-identity-fields">
          <label className="field required-field">
            <span>Автор / псевдоним <b className="required-mark">*</b></span>
            <input
              list="book-author-options"
              value={authorName}
              onChange={(event) => setAuthorName(event.target.value)}
              placeholder="Выберите или введите нового автора"
              aria-invalid={!authorReady}
            />
            <datalist id="book-author-options">
              {authorOptions.map((name) => <option key={name} value={name} />)}
            </datalist>
            <small>Можно выбрать сохранённый профиль или сразу указать новый псевдоним.</small>
          </label>
          <label className="field">
            <span>Серия</span>
            <select value={seriesName} onChange={(event) => setSeriesName(event.target.value)}>
              <option value="">Отдельная книга</option>
              {seriesOptions.map((name) => <option key={name} value={name}>{name}</option>)}
            </select>
          </label>
        </div>

        <label className="field">
          <span>Кому книга — необязательно</span>
          <textarea
            rows={3}
            value={readerHint}
            onChange={(event) => setReaderHint(event.target.value)}
            placeholder="Можно оставить пустым — BOOK OS предложит аудиторию сам"
          />
        </label>

        <fieldset className="volume-choice">
          <legend>Объём</legend>
          <div className="writer-levels" role="group" aria-label="Объём книги">
            {([
              ["SHORT", "Короткая"],
              ["STANDARD", "Стандартная"],
              ["LARGE", "Большая"],
              ["CUSTOM", "Свой объём"],
            ] as const).map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={volumePreset === id ? "active" : ""}
                aria-pressed={volumePreset === id}
                onClick={() => chooseVolume(id)}
              >
                {label}
              </button>
            ))}
          </div>
          {volumePreset === "CUSTOM" && (
            <label className="field compact-number-field">
              <span>Знаков с пробелами</span>
              <input
                inputMode="numeric"
                value={targetCharacters}
                onChange={(event) => setTargetCharacters(event.target.value)}
                aria-invalid={!targetReady}
              />
              <small>От 4 000 до 2 000 000 знаков.</small>
            </label>
          )}
        </fieldset>

        <details className="advanced-settings">
          <summary>Уточнить направление книги — необязательно</summary>
          <p className="muted">Если не выбирать, BOOK OS начнёт с универсального делового профиля и уточнит замысел дальше.</p>
          <div className="topic-grid start-topic-grid" role="group" aria-label="Доступные темы книги">
            {availableTopics.map((topic) => {
              const selected = topicConfirmed && topic.subtype === primarySubtype;
              return (
                <button
                  key={topic.id}
                  type="button"
                  className={`topic-card available compact ${selected ? "selected" : ""}`}
                  aria-pressed={selected}
                  onClick={() => {
                    if (!topic.subtype) return;
                    setPrimarySubtype(topic.subtype);
                    setTopicConfirmed(true);
                  }}
                >
                  <strong>{topic.label}</strong>
                  <small>{topic.description}</small>
                </button>
              );
            })}
          </div>
          <label className="field">
            <span>Вторая категория</span>
            <small>Используйте только если книга действительно лежит на пересечении двух тем.</small>
            <select
              value={secondarySubtype}
              onChange={(event) => setSecondarySubtype(event.target.value)}
              disabled={!primarySubtype}
            >
              <option value="">Нет</option>
              {AVAILABLE_BUSINESS_SUBTYPES.filter((value) => value !== primarySubtype).map((value) => (
                <option key={value} value={value}>
                  {SUBTYPE_LABELS[value]}
                </option>
              ))}
            </select>
          </label>
        </details>

        <div className="launch-readiness compact-readiness" aria-label="Готовность проекта">
          <span className={titleReady ? "ready" : "missing"}>
            {titleReady ? "✓" : "○"} Рабочее название
          </span>
          <span className={ideaReady ? "ready" : "missing"}>
            {ideaReady ? "✓" : "○"} Идея книги
          </span>
          <span className={authorReady ? "ready" : "missing"}>
            {authorReady ? "✓" : "○"} Автор
          </span>
        </div>

        <button
          className={`primary auto-launch-button ${canCreate ? "ready" : ""}`}
          onClick={onCreate}
          disabled={!canCreate}
          type="button"
        >
          {canCreate ? "Перейти к запуску книги" : "Заполните обязательные поля"}
        </button>
      </div>
    </section>
  );
}
