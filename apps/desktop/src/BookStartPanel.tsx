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
  primarySubtype,
  setPrimarySubtype,
  secondarySubtype,
  setSecondarySubtype,
  busy,
  onCreate,
  onClose,
}: Props) {
  const [topicConfirmed, setTopicConfirmed] = useState(false);
  const availableTopics = BUSINESS_TOPICS.filter(
    (topic) => topic.availability === "AVAILABLE" && Boolean(topic.subtype),
  );
  const titleReady = newTitle.trim().length > 0;
  const topicReady = topicConfirmed && Boolean(primarySubtype);
  const canCreate = !busy && titleReady && topicReady;

  return (
    <section className="panel new-book book-start-panel simplified-book-start" aria-label="Создание новой книги">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">НОВАЯ КНИГА</p>
          <h2>Создайте проект книги</h2>
          <p className="muted">
            Здесь только два обязательных выбора. После создания проекта откроется единый запуск Auto Book.
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

        <div className="field required-field">
          <span>
            Тема книги <b className="required-mark">*</b>
          </span>
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
                  <span className={`availability ${selected ? "ready" : "soon"}`}>
                    {selected ? "Выбрано ✓" : "Выбрать"}
                  </span>
                  <strong>{topic.label}</strong>
                  <small>{topic.description}</small>
                </button>
              );
            })}
          </div>
        </div>

        <details className="advanced-settings">
          <summary>Дополнительная категория — необязательно</summary>
          <label className="field">
            <span>Вторая категория</span>
            <small>Используйте только если книга действительно лежит на пересечении двух тем.</small>
            <select
              value={secondarySubtype}
              onChange={(event) => setSecondarySubtype(event.target.value)}
              disabled={!topicReady}
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
          <span className={topicReady ? "ready" : "missing"}>
            {topicReady ? "✓" : "○"} Тема книги
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
