import type { Dispatch, SetStateAction } from "react";
import type { ArchitectureChapter, BookArchitecturePayload } from "./types";

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function lines(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function newChapter(): ArchitectureChapter {
  return {
    chapter_id: null,
    title: "",
    purpose: "",
    new_contribution: "",
    dependencies: [],
    transition: "",
  };
}

function TextField({
  label,
  value,
  onChange,
  hint,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  hint?: string;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      {hint && <small>{hint}</small>}
      <textarea rows={3} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

type Props = {
  architecture: BookArchitecturePayload;
  setArchitecture: Dispatch<SetStateAction<BookArchitecturePayload>>;
  statusBadge: React.ReactNode;
  busy: boolean;
  onSave: () => void;
  onApprove: () => void;
};

export function ArchitectureEditor({
  architecture,
  setArchitecture,
  statusBadge,
  busy,
  onSave,
  onApprove,
}: Props) {
  function updatePart(partIndex: number, patch: { title?: string; purpose?: string }) {
    setArchitecture((current) => {
      const next = clone(current);
      next.parts[partIndex] = { ...next.parts[partIndex], ...patch };
      return next;
    });
  }

  function updateChapter(
    partIndex: number,
    chapterIndex: number,
    patch: Partial<ArchitectureChapter>,
  ) {
    setArchitecture((current) => {
      const next = clone(current);
      next.parts[partIndex].chapters[chapterIndex] = {
        ...next.parts[partIndex].chapters[chapterIndex],
        ...patch,
      };
      return next;
    });
  }

  function addPart() {
    setArchitecture((current) => {
      const next = clone(current);
      next.parts.push({
        title: `Часть ${next.parts.length + 1}`,
        purpose: "",
        chapters: [newChapter()],
      });
      return next;
    });
  }

  function removePart(partIndex: number) {
    setArchitecture((current) => {
      if (current.parts.length <= 1) return current;
      const next = clone(current);
      next.parts.splice(partIndex, 1);
      return next;
    });
  }

  function addChapter(partIndex: number) {
    setArchitecture((current) => {
      const next = clone(current);
      next.parts[partIndex].chapters.push(newChapter());
      return next;
    });
  }

  function removeChapter(partIndex: number, chapterIndex: number) {
    setArchitecture((current) => {
      if (current.parts[partIndex].chapters.length <= 1) return current;
      const next = clone(current);
      next.parts[partIndex].chapters.splice(chapterIndex, 1);
      return next;
    });
  }

  function moveChapter(partIndex: number, chapterIndex: number, delta: number) {
    setArchitecture((current) => {
      const target = chapterIndex + delta;
      if (target < 0 || target >= current.parts[partIndex].chapters.length) return current;
      const next = clone(current);
      const [item] = next.parts[partIndex].chapters.splice(chapterIndex, 1);
      next.parts[partIndex].chapters.splice(target, 0, item);
      return next;
    });
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ЧЕЛОВЕЧЕСКОЕ РЕШЕНИЕ 2</p>
          <h3>Архитектура книги</h3>
        </div>
        {statusBadge}
      </div>

      <div className="form-grid">
        <TextField
          label="Интеллектуальное движение книги"
          value={architecture.intellectual_progression}
          onChange={(value) =>
            setArchitecture((current) => ({ ...current, intellectual_progression: value }))
          }
        />
        <TextField
          label="Распределение ключевых идей"
          value={architecture.concept_allocation}
          onChange={(value) =>
            setArchitecture((current) => ({ ...current, concept_allocation: value }))
          }
        />
        <TextField
          label="Как архитектура выполняет обещание и тезис"
          value={architecture.promise_thesis_coverage}
          onChange={(value) =>
            setArchitecture((current) => ({ ...current, promise_thesis_coverage: value }))
          }
        />
        <TextField
          label="Крупные переходы"
          value={architecture.major_transitions}
          onChange={(value) =>
            setArchitecture((current) => ({ ...current, major_transitions: value }))
          }
        />
      </div>

      <div className="architecture-parts">
        <div className="subheading">
          <h4>Части и главы</h4>
          <button className="ghost" onClick={addPart} disabled={busy}>
            + Добавить часть
          </button>
        </div>

        {architecture.parts.map((part, partIndex) => (
          <section className="architecture-part" key={`part-${partIndex}`}>
            <div className="panel-heading">
              <strong>Часть {partIndex + 1}</strong>
              {architecture.parts.length > 1 && (
                <button className="ghost small" onClick={() => removePart(partIndex)} disabled={busy}>
                  Удалить часть
                </button>
              )}
            </div>
            <div className="two-columns">
              <label className="field">
                <span>Название части</span>
                <input
                  value={part.title}
                  onChange={(event) => updatePart(partIndex, { title: event.target.value })}
                />
              </label>
              <TextField
                label="Функция части"
                value={part.purpose}
                onChange={(value) => updatePart(partIndex, { purpose: value })}
              />
            </div>

            <div className="chapter-plans">
              <div className="subheading">
                <h4>Главы этой части</h4>
                <button className="ghost" onClick={() => addChapter(partIndex)} disabled={busy}>
                  + Добавить главу
                </button>
              </div>
              {part.chapters.map((chapter, chapterIndex) => (
                <div className="chapter-plan" key={chapter.chapter_id ?? `new-${partIndex}-${chapterIndex}`}>
                  <div className="chapter-order">
                    <strong>Глава {chapterIndex + 1}</strong>
                    <button
                      className="icon"
                      onClick={() => moveChapter(partIndex, chapterIndex, -1)}
                      disabled={chapterIndex === 0 || busy}
                    >
                      ↑
                    </button>
                    <button
                      className="icon"
                      onClick={() => moveChapter(partIndex, chapterIndex, 1)}
                      disabled={chapterIndex === part.chapters.length - 1 || busy}
                    >
                      ↓
                    </button>
                    {part.chapters.length > 1 && (
                      <button
                        className="ghost small"
                        onClick={() => removeChapter(partIndex, chapterIndex)}
                        disabled={busy}
                      >
                        Удалить
                      </button>
                    )}
                  </div>
                  <label className="field">
                    <span>Название</span>
                    <input
                      value={chapter.title}
                      onChange={(event) =>
                        updateChapter(partIndex, chapterIndex, { title: event.target.value })
                      }
                    />
                  </label>
                  <TextField
                    label="Функция главы"
                    value={chapter.purpose}
                    onChange={(value) => updateChapter(partIndex, chapterIndex, { purpose: value })}
                  />
                  <TextField
                    label="Новый вклад главы"
                    value={chapter.new_contribution}
                    onChange={(value) =>
                      updateChapter(partIndex, chapterIndex, { new_contribution: value })
                    }
                  />
                  <TextField
                    label="Зависимости"
                    hint="Одна ссылка на главу/ID на строку"
                    value={chapter.dependencies.join("\n")}
                    onChange={(value) =>
                      updateChapter(partIndex, chapterIndex, { dependencies: lines(value) })
                    }
                  />
                  <TextField
                    label="Переход к следующей главе"
                    value={chapter.transition}
                    onChange={(value) => updateChapter(partIndex, chapterIndex, { transition: value })}
                  />
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>

      <div className="actions">
        <button className="secondary" onClick={onSave} disabled={busy}>
          Сохранить черновик
        </button>
        <button className="primary" onClick={onApprove} disabled={busy}>
          Утвердить архитектуру
        </button>
      </div>
    </section>
  );
}
