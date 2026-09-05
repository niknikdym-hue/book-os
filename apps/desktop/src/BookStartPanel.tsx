import { useRef } from "react";
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
  const topicsRef = useRef<HTMLDivElement>(null);
  const detailsRef = useRef<HTMLDivElement>(null);

  function goTo(element: HTMLDivElement | null) {
    element?.scrollIntoView?.({ behavior: "smooth", block: "start" });
  }

  return (
    <section className="panel new-book book-start-panel" aria-label="Создание новой книги">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">НОВАЯ КНИГА · ШАГ 1</p>
          <h2>Выберите направление книги</h2>
          <p className="muted">
            BOOK OS показывает весь каталог, но открыть можно только те направления, для которых уже
            есть проверяемый production-профиль.
          </p>
        </div>
        <button className="ghost" onClick={onClose} type="button">
          Закрыть
        </button>
      </div>

      <div className="category-grid" aria-label="Разделы книг">
        {BOOK_CATEGORIES.map((category) => {
          const available = category.availability === "AVAILABLE";
          return (
            <button
              key={category.id}
              type="button"
              className={`category-card ${available ? "available selected" : "locked"}`}
              disabled={!available}
              aria-label={`${category.label}${available ? ", доступно" : ", в разработке"}`}
              onClick={() => available && goTo(topicsRef.current)}
            >
              <span className={`availability ${available ? "ready" : "soon"}`}>
                {available ? "Доступно" : "В разработке"}
              </span>
              <strong>{category.label}</strong>
              <small>{category.description}</small>
            </button>
          );
        })}
      </div>

      <div className="catalog-section" ref={topicsRef}>
        <div className="subheading">
          <div>
            <p className="eyebrow">БИЗНЕС</p>
            <h3>Выберите тему</h3>
          </div>
          <span className="muted">Активны только реально поддерживаемые темы</span>
        </div>
        <div className="topic-grid" aria-label="Темы раздела Бизнес">
          {BUSINESS_TOPICS.map((topic) => {
            const available = topic.availability === "AVAILABLE" && Boolean(topic.subtype);
            const selected = available && topic.subtype === primarySubtype;
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
                  goTo(detailsRef.current);
                }}
                title={topic.note ?? topic.description}
              >
                <span className={`availability ${available ? "ready" : "soon"}`}>
                  {selected ? "Выбрано ✓" : available ? "Доступно сейчас" : "В разработке"}
                </span>
                <strong>{topic.label}</strong>
                <small>{topic.description}</small>
                {!available && topic.note && <em>{topic.note}</em>}
              </button>
            );
          })}
        </div>
      </div>

      <div className="start-details" ref={detailsRef}>
        <div>
          <p className="eyebrow">ШАГ 2</p>
          <h3>Назовите рабочий проект</h3>
          <p className="muted">
            Название можно изменить позже. После создания проекта BOOK OS попросит описать саму идею
            книги и предложит контракт.
          </p>
        </div>
        <label className="field">
          <span>Рабочее название</span>
          <input
            value={newTitle}
            onChange={(event) => setNewTitle(event.target.value)}
            placeholder="Например: Бизнес держится на мне"
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

        <div className="selected-topic-summary" role="status" aria-live="polite">
          <small>Выбрано</small>
          <strong>
            {primarySubtype ? `Бизнес → ${SUBTYPE_LABELS[primarySubtype]}` : "Сначала выберите тему"}
          </strong>
        </div>

        <div className="actions">
          <button
            className="primary"
            onClick={onCreate}
            disabled={busy || !primarySubtype || newTitle.trim().length === 0}
          >
            Создать проект книги
          </button>
        </div>
      </div>

      <details className="help-drawer">
        <summary>Как пользоваться BOOK OS</summary>
        <ol className="help-steps">
          <li><strong>Выберите направление и тему.</strong> Недоступные профили видны, но не открываются.</li>
          <li><strong>Опишите идею.</strong> Нескольких точных предложений достаточно для первого предложения BOOK OS.</li>
          <li><strong>Проверьте и утвердите контракт книги.</strong> AI может предложить, но не может утвердить решение за автора.</li>
          <li><strong>Проверьте архитектуру.</strong> Части и главы можно править до утверждения.</li>
          <li><strong>Подготовьте контракт главы и пишите.</strong> BOOK OS ведёт по одной управляемой задаче за раз.</li>
          <li><strong>Проверьте факты, редактуру и BookBench.</strong> Финал выпускается только после человеческого решения.</li>
        </ol>
      </details>
    </section>
  );
}
