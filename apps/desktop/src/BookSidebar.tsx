import { useCallback, useEffect, useState } from "react";
import { coreApi } from "./api";
import { subtypeLabel } from "./bookCatalog";
import type { ProjectSummary } from "./types";

type Props = {
  projects: ProjectSummary[];
  activeBookId: string | null;
  busy: boolean;
  onNew: () => void;
  onOpen: (bookId: string) => void;
  onProjectListChanged: (removedBookId?: string) => void | Promise<void>;
  stageLabel: (value: string) => string;
};

type BookLocation = "active" | "library";

type Target = {
  item: ProjectSummary;
  location: BookLocation;
};

export function BookSidebar({
  projects,
  activeBookId,
  busy,
  onNew,
  onOpen,
  onProjectListChanged,
  stageLabel,
}: Props) {
  const [library, setLibrary] = useState<ProjectSummary[]>([]);
  const [target, setTarget] = useState<Target | null>(null);
  const [confirmPermanent, setConfirmPermanent] = useState(false);
  const [actionBusy, setActionBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshLibrary = useCallback(async () => {
    try {
      setLibrary(await coreApi<ProjectSummary[]>("GET", "/api/library"));
    } catch (reason) {
      setError(String(reason));
    }
  }, []);

  useEffect(() => {
    void refreshLibrary();
  }, [refreshLibrary]);

  useEffect(() => {
    if (!target) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !actionBusy) {
        setTarget(null);
        setConfirmPermanent(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [actionBusy, target]);

  function openActions(item: ProjectSummary, location: BookLocation) {
    setError(null);
    setConfirmPermanent(false);
    setTarget({ item, location });
  }

  function closeActions() {
    if (actionBusy) return;
    setTarget(null);
    setConfirmPermanent(false);
  }

  async function archiveBook() {
    if (!target || target.location !== "active") return;
    setActionBusy(true);
    setError(null);
    try {
      await coreApi("POST", `/api/projects/${target.item.book_id}/archive`);
      await refreshLibrary();
      await onProjectListChanged(target.item.book_id);
      setTarget(null);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setActionBusy(false);
    }
  }

  async function restoreBook() {
    if (!target || target.location !== "library") return;
    setActionBusy(true);
    setError(null);
    try {
      await coreApi("POST", `/api/library/${target.item.book_id}/restore`);
      await refreshLibrary();
      await onProjectListChanged();
      setTarget(null);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setActionBusy(false);
    }
  }

  async function deleteBookPermanently() {
    if (!target) return;
    setActionBusy(true);
    setError(null);
    try {
      const path =
        target.location === "active"
          ? `/api/projects/${target.item.book_id}`
          : `/api/library/${target.item.book_id}`;
      await coreApi("DELETE", path);
      await refreshLibrary();
      await onProjectListChanged(target.location === "active" ? target.item.book_id : undefined);
      setTarget(null);
      setConfirmPermanent(false);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setActionBusy(false);
    }
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-heading">
        <h2>Книги</h2>
        <button className="primary small" onClick={onNew} disabled={busy || actionBusy}>
          + Новая
        </button>
      </div>

      {projects.length === 0 && <p className="muted">Проектов книг пока нет.</p>}
      <nav aria-label="Активные книги" className="book-list">
        {projects.map((item) => (
          <div className="project-row" key={item.book_id}>
            <button
              className={`project-link ${activeBookId === item.book_id ? "active" : ""}`}
              onClick={() => onOpen(item.book_id)}
              disabled={busy || actionBusy}
            >
              <strong>{item.working_title}</strong>
              <span>{subtypeLabel(item.primary_subtype)}</span>
              <small>{stageLabel(item.workflow_stage)}</small>
            </button>
            <button
              type="button"
              className="book-trash"
              aria-label={`Управление книгой «${item.working_title}»`}
              title="Удалить или перенести в библиотеку"
              onClick={() => openActions(item, "active")}
              disabled={busy || actionBusy}
            >
              <span aria-hidden="true">🗑︎</span>
            </button>
          </div>
        ))}
      </nav>

      <details className="library-drawer">
        <summary>Библиотека{library.length > 0 ? ` · ${library.length}` : ""}</summary>
        {library.length === 0 ? (
          <p className="muted library-empty">В библиотеке пока нет книг.</p>
        ) : (
          <div className="library-list">
            {library.map((item) => (
              <div className="library-row" key={item.book_id}>
                <div className="library-book-meta">
                  <strong>{item.working_title}</strong>
                  <span>{subtypeLabel(item.primary_subtype)}</span>
                  <small>{stageLabel(item.workflow_stage)}</small>
                </div>
                <div className="library-actions">
                  <button
                    type="button"
                    className="ghost library-restore"
                    onClick={() => {
                      setTarget({ item, location: "library" });
                      setConfirmPermanent(false);
                    }}
                    disabled={busy || actionBusy}
                  >
                    Вернуть
                  </button>
                  <button
                    type="button"
                    className="book-trash"
                    aria-label={`Управление книгой из библиотеки «${item.working_title}»`}
                    title="Удалить книгу из библиотеки"
                    onClick={() => openActions(item, "library")}
                    disabled={busy || actionBusy}
                  >
                    <span aria-hidden="true">🗑︎</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </details>

      {error && <div className="book-lifecycle-error">{error}</div>}

      {target && (
        <div className="book-lifecycle-overlay" role="presentation" onMouseDown={closeActions}>
          <section
            className="book-lifecycle-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="book-lifecycle-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            {!confirmPermanent ? (
              <>
                <p className="eyebrow">УПРАВЛЕНИЕ КНИГОЙ</p>
                <h3 id="book-lifecycle-title">{target.item.working_title}</h3>
                <p className="muted">
                  {target.location === "active"
                    ? "Можно убрать книгу с рабочей панели без потери данных или удалить её полностью."
                    : "Книга хранится в библиотеке целиком. Её можно вернуть на рабочую панель или удалить навсегда."}
                </p>
                <div className="book-lifecycle-actions">
                  {target.location === "active" ? (
                    <button className="primary" type="button" onClick={() => void archiveBook()} disabled={actionBusy}>
                      Перенести в библиотеку
                    </button>
                  ) : (
                    <button className="primary" type="button" onClick={() => void restoreBook()} disabled={actionBusy}>
                      Вернуть на панель
                    </button>
                  )}
                  <button
                    className="danger"
                    type="button"
                    onClick={() => setConfirmPermanent(true)}
                    disabled={actionBusy}
                  >
                    Удалить навсегда
                  </button>
                  <button className="ghost" type="button" onClick={closeActions} disabled={actionBusy}>
                    Отмена
                  </button>
                </div>
              </>
            ) : (
              <>
                <p className="eyebrow danger-text">БЕЗВОЗВРАТНОЕ УДАЛЕНИЕ</p>
                <h3 id="book-lifecycle-title">Удалить «{target.item.working_title}»?</h3>
                <p>
                  Будет удалена вся папка этой книги: база проекта, тексты, ревизии, authority-история и локальные материалы.
                  Восстановить книгу средствами BOOK OS после этого нельзя.
                </p>
                <div className="book-lifecycle-actions">
                  <button
                    className="danger"
                    type="button"
                    onClick={() => void deleteBookPermanently()}
                    disabled={actionBusy}
                  >
                    Да, удалить навсегда
                  </button>
                  <button
                    className="ghost"
                    type="button"
                    onClick={() => setConfirmPermanent(false)}
                    disabled={actionBusy}
                  >
                    Назад
                  </button>
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </aside>
  );
}
