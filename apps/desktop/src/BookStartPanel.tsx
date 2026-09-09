import { useRef, useState } from "react";
import "./launchUx.css";
import {
  AVAILABLE_BUSINESS_SUBTYPES,
  BOOK_CATEGORIES,
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
  const detailsRef = useRef<HTMLDivElement>(null);
  const [topicChosen, setTopicChosen] = useState(false);

  function goToDetails() {
    detailsRef.current?.scrollIntoView?.({ behavior: "smooth", block: "start" });
  }

  return (
    <section className="panel new-book book-start-panel" aria-label="Создание новой книги">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">НОВАЯ КНИГА · БИЗНЕС</p>
          <h2>Выберите тему</h2>
          <p className="muted">
            Сейчас в BOOK OS открыт проверенный профиль делового нон-фикшена. Сначала выберите тему,
            затем задайте рабочее название книги.
          </p>
        </div>
        <button className="ghost" onClick={onClose} type="button">
          Закрыть
        </button>
      </div>

      <div className="topic-grid" aria-label="Темы раздела Бизнес">
        {BUSINESS_TOPICS.map((topic) => {
          const available = topic.availability === "AVAILABLE" && Boolean(topic.subtype);
          const selected = topicChosen && available && topic.subtype === primarySubtype;
          return (
            <button
              key={topic.id}
              type="button"
              className={`topic-card ${selected ? "selected" : ""} ${available ? "available" : "locked"}`}
              disabled={!available}
              aria-pressed={selected}
              aria-label={`${topic.label}${available ? ", доступно" : ", в разработке"}`}
              onClick={() => {
                if (!topic.subtype) return;
                setPrimarySubtype(topic.subtype);
                setTopicChosen(true);
                window.setTimeout(goToDetails, 0);
              }}
              title={topic.note ?? topic.description}
            >
              <span className={`availability ${available ? "ready" : "soon"}`}>
                {selected ? "Выбрано ✓" : available ? "Выбрать" : "В разработке"}
              </span>
              <strong>{topic.label}</strong>
              <small>{topic.description}</small>
            </button>
          );
        })}
      </div>

      <div className="start-details" ref={detailsRef}>
        <div>
          <p className="eyebrow">ШАГ 2</p>
          <h3>Рабочее название</h3>
          <p className="muted">Название можно изменить позже.</p>
        </div>
        <label className="field">
          <span>Название книги</span>
          <input
            value={newTitle}
            onChange={(event) => setNewTitle(event.target.value)}
            placeholder="Например: SMM продвижение"
            disabled={!topicChosen}
          />
        </label>

        <details className="advanced-settings">
          <summary>Дополнительная категория — необязательно</summary>
          <label className="field">
            <span>Вторая категория</span>
            <small>Нужна только если книга действительно лежит на пересечении двух деловых тем.</small>
            <select
              value={secondarySubtype}
              onChange={(event) => setSecondarySubtype(event.target.value)}
              disabled={!topicChosen || !primarySubtype}
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

        <div className="selected-topic-summary" role="status" aria-live="polite">
          <small>Тема книги</small>
          <strong>
            {topicChosen && primarySubtype
              ? `Бизнес → ${SUBTYPE_LABELS[primarySubtype]}`
              : "Выберите тему выше"}
          </strong>
        </div>

        <div className="actions">
          <button
            className="primary"
            onClick={onCreate}
            disabled={busy || !topicChosen || !primarySubtype || newTitle.trim().length === 0}
          >
            Создать книгу
          </button>
        </div>
      </div>

      <details className="help-drawer">
        <summary>Другие направления</summary>
        <div className="category-grid" aria-label="Направления в разработке">
          {BOOK_CATEGORIES.filter((category) => category.id !== "business").map((category) => (
            <div key={category.id} className="category-card locked" aria-label={`${category.label}, в разработке`}>
              <span className="availability soon">В разработке</span>
              <strong>{category.label}</strong>
              <small>{category.description}</small>
            </div>
          ))}
        </div>
      </details>
    </section>
  );
}
