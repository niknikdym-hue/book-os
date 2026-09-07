import { useCallback, useEffect, useMemo, useState } from "react";
import { coreApi } from "./api";
import type { ProjectView } from "./types";

type ProfileKind = "AUTHOR" | "SERIES" | "STYLE";

type ProfileView = {
  profile_id: string;
  kind: ProfileKind;
  name: string;
  status: "DRAFT" | "APPROVED";
  current_revision: number;
  content_hash: string;
  content: Record<string, unknown>;
};

type BookContextView = {
  author_profile: ProfileView | null;
  series_profile: ProfileView | null;
  style_profile: ProfileView | null;
  target_characters: number | null;
  min_characters: number | null;
  max_characters: number | null;
  characters_unit: "characters_with_spaces";
  ready_for_planning: boolean;
};

type Props = {
  project: ProjectView;
};

function lines(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function ProfileStatus({ profile }: { profile: ProfileView | null }) {
  if (!profile) return <span className="badge empty">НЕ ВЫБРАН</span>;
  return (
    <span className={`badge ${profile.status === "APPROVED" ? "approved" : "draft"}`}>
      {profile.status === "APPROVED" ? "УТВЕРЖДЁН" : "ЧЕРНОВИК"}
    </span>
  );
}

export function BookContextPanel({ project }: Props) {
  const [profiles, setProfiles] = useState<ProfileView[]>([]);
  const [context, setContext] = useState<BookContextView | null>(null);
  const [authorId, setAuthorId] = useState("");
  const [seriesId, setSeriesId] = useState("");
  const [styleId, setStyleId] = useState("");
  const [seriesMode, setSeriesMode] = useState<"STANDALONE" | "SERIES">("STANDALONE");
  const [targetCharacters, setTargetCharacters] = useState("300000");
  const [minCharacters, setMinCharacters] = useState("");
  const [maxCharacters, setMaxCharacters] = useState("");

  const [authorName, setAuthorName] = useState("");
  const [authorVoice, setAuthorVoice] = useState("");
  const [authorEvidence, setAuthorEvidence] = useState("");
  const [authorStorytelling, setAuthorStorytelling] = useState("");
  const [authorRhythm, setAuthorRhythm] = useState("");
  const [authorProhibitions, setAuthorProhibitions] = useState("");
  const [authorBenchmark, setAuthorBenchmark] = useState("");

  const [seriesName, setSeriesName] = useState("");
  const [seriesPurpose, setSeriesPurpose] = useState("");
  const [plannedBooks, setPlannedBooks] = useState("");
  const [seriesReservations, setSeriesReservations] = useState("");
  const [seriesUniqueness, setSeriesUniqueness] = useState("");
  const [seriesExclusions, setSeriesExclusions] = useState("");

  const [styleName, setStyleName] = useState("");
  const [styleRegister, setStyleRegister] = useState("");
  const [stylePresence, setStylePresence] = useState("");
  const [styleDirectness, setStyleDirectness] = useState("");
  const [styleRhythm, setStyleRhythm] = useState("");
  const [styleScenes, setStyleScenes] = useState("");
  const [styleEvidence, setStyleEvidence] = useState("");
  const [styleDepth, setStyleDepth] = useState("");
  const [styleIrony, setStyleIrony] = useState("");
  const [styleTemperature, setStyleTemperature] = useState("");
  const [stylePractical, setStylePractical] = useState("");
  const [styleTerminology, setStyleTerminology] = useState("");
  const [styleProhibitions, setStyleProhibitions] = useState("");
  const [styleBenchmark, setStyleBenchmark] = useState("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    const [profileItems, currentContext] = await Promise.all([
      coreApi<ProfileView[]>("GET", "/api/context/profiles"),
      coreApi<BookContextView>("GET", `/api/projects/${project.book_id}/context`),
    ]);
    setProfiles(profileItems);
    setContext(currentContext);
    if (currentContext.author_profile) setAuthorId(currentContext.author_profile.profile_id);
    if (currentContext.series_profile) {
      setSeriesMode("SERIES");
      setSeriesId(currentContext.series_profile.profile_id);
    }
    if (currentContext.style_profile) setStyleId(currentContext.style_profile.profile_id);
    if (currentContext.target_characters) {
      setTargetCharacters(String(currentContext.target_characters));
    }
    setMinCharacters(currentContext.min_characters ? String(currentContext.min_characters) : "");
    setMaxCharacters(currentContext.max_characters ? String(currentContext.max_characters) : "");
  }, [project.book_id]);

  useEffect(() => {
    void reload().catch((reason: unknown) => setError(String(reason)));
  }, [reload]);

  const authors = useMemo(
    () => profiles.filter((item) => item.kind === "AUTHOR"),
    [profiles],
  );
  const approvedAuthors = authors.filter((item) => item.status === "APPROVED");
  const selectedAuthor = authors.find((item) => item.profile_id === authorId) ?? null;
  const seriesProfiles = useMemo(
    () =>
      profiles.filter(
        (item) =>
          item.kind === "SERIES" &&
          item.content.author_profile_id === authorId,
      ),
    [authorId, profiles],
  );
  const approvedSeries = seriesProfiles.filter((item) => item.status === "APPROVED");
  const styles = useMemo(
    () =>
      profiles.filter(
        (item) =>
          item.kind === "STYLE" &&
          (!item.content.author_profile_id || item.content.author_profile_id === authorId),
      ),
    [authorId, profiles],
  );
  const approvedStyles = styles.filter((item) => item.status === "APPROVED");
  const selectedSeries = seriesProfiles.find((item) => item.profile_id === seriesId) ?? null;
  const selectedStyle = styles.find((item) => item.profile_id === styleId) ?? null;

  async function createProfile(kind: ProfileKind, content: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    try {
      const created = await coreApi<ProfileView>("POST", "/api/context/profiles", {
        kind,
        content,
      });
      await reload();
      if (kind === "AUTHOR") setAuthorId(created.profile_id);
      if (kind === "SERIES") setSeriesId(created.profile_id);
      if (kind === "STYLE") setStyleId(created.profile_id);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function approveProfile(profileId: string) {
    setBusy(true);
    setError(null);
    try {
      const approved = await coreApi<ProfileView>(
        "POST",
        `/api/context/profiles/${profileId}/approve`,
      );
      await reload();
      if (approved.kind === "AUTHOR") setAuthorId(approved.profile_id);
      if (approved.kind === "SERIES") setSeriesId(approved.profile_id);
      if (approved.kind === "STYLE") setStyleId(approved.profile_id);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  async function saveContext() {
    const target = Number(targetCharacters);
    const minimum = minCharacters.trim() ? Number(minCharacters) : null;
    const maximum = maxCharacters.trim() ? Number(maxCharacters) : null;
    if (!authorId || !styleId || !Number.isInteger(target) || target <= 0) return;
    setBusy(true);
    setError(null);
    try {
      const next = await coreApi<BookContextView>(
        "PUT",
        `/api/projects/${project.book_id}/context`,
        {
          author_profile_id: authorId,
          series_profile_id: seriesMode === "SERIES" ? seriesId || null : null,
          style_profile_id: styleId,
          target_characters: target,
          min_characters: minimum,
          max_characters: maximum,
        },
      );
      setContext(next);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setBusy(false);
    }
  }

  const target = Number(targetCharacters);
  const canSave =
    selectedAuthor?.status === "APPROVED" &&
    selectedStyle?.status === "APPROVED" &&
    Number.isInteger(target) &&
    target > 0 &&
    (seriesMode === "STANDALONE" || selectedSeries?.status === "APPROVED");

  return (
    <section className="panel" aria-label="Контекст автора, серии, стиля и объёма">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ОБЯЗАТЕЛЬНО ДО AI-ПЛАНИРОВАНИЯ</p>
          <h3>Автор, серия, стиль и объём</h3>
        </div>
        <span className={`badge ${context?.ready_for_planning ? "approved" : "draft"}`}>
          {context?.ready_for_planning ? "КОНТЕКСТ ГОТОВ" : "НУЖНО НАСТРОИТЬ"}
        </span>
      </div>
      <p className="muted">
        Эти настройки становятся входным authority-контекстом книги. AI не может утвердить профиль
        автора, серии или стиля за вас.
      </p>

      <section className="planning-step">
        <div className="panel-heading">
          <h4>1. Автор</h4>
          <ProfileStatus profile={selectedAuthor} />
        </div>
        <label className="field">
          <span>Утверждённый Author Profile</span>
          <select value={authorId} onChange={(event) => {
            setAuthorId(event.target.value);
            setSeriesId("");
            setStyleId("");
          }}>
            <option value="">Выберите автора</option>
            {approvedAuthors.map((item) => (
              <option key={item.profile_id} value={item.profile_id}>{item.name}</option>
            ))}
            {authors.filter((item) => item.status === "DRAFT").map((item) => (
              <option key={item.profile_id} value={item.profile_id}>{item.name} — черновик</option>
            ))}
          </select>
        </label>
        {selectedAuthor?.status === "DRAFT" && (
          <button className="primary" disabled={busy} onClick={() => void approveProfile(selectedAuthor.profile_id)}>
            Утвердить Author Profile
          </button>
        )}
        <details className="advanced-settings">
          <summary>Создать новый Author Profile</summary>
          <div className="form-grid">
            <label className="field"><span>Имя / псевдоним</span><input value={authorName} onChange={(event) => setAuthorName(event.target.value)} /></label>
            <label className="field"><span>Голос и требования к прозе</span><textarea rows={4} value={authorVoice} onChange={(event) => setAuthorVoice(event.target.value)} /></label>
            <label className="field"><span>Доказательность</span><textarea rows={3} value={authorEvidence} onChange={(event) => setAuthorEvidence(event.target.value)} /></label>
            <label className="field"><span>Storytelling</span><textarea rows={3} value={authorStorytelling} onChange={(event) => setAuthorStorytelling(event.target.value)} /></label>
            <label className="field"><span>Ритм и синтаксис</span><textarea rows={3} value={authorRhythm} onChange={(event) => setAuthorRhythm(event.target.value)} /></label>
            <label className="field"><span>Запреты — по одному на строке</span><textarea rows={4} value={authorProhibitions} onChange={(event) => setAuthorProhibitions(event.target.value)} /></label>
            <label className="field"><span>Утверждённый benchmark — необязательно</span><textarea rows={5} value={authorBenchmark} onChange={(event) => setAuthorBenchmark(event.target.value)} /></label>
          </div>
          <button
            className="ghost"
            disabled={busy || authorName.trim().length === 0}
            onClick={() => void createProfile("AUTHOR", {
              author_name: authorName.trim(),
              voice_requirements: authorVoice.trim(),
              evidence_discipline: authorEvidence.trim(),
              storytelling_expectations: authorStorytelling.trim(),
              rhythm_syntax: authorRhythm.trim(),
              prose_prohibitions: lines(authorProhibitions),
              benchmark_excerpts: authorBenchmark.trim() ? [authorBenchmark.trim()] : [],
            })}
          >
            Создать черновик Author Profile
          </button>
        </details>
      </section>

      <section className="planning-step">
        <div className="panel-heading">
          <h4>2. Серия</h4>
          <ProfileStatus profile={seriesMode === "SERIES" ? selectedSeries : null} />
        </div>
        <div className="actions planning-action">
          <button type="button" className={seriesMode === "STANDALONE" ? "primary" : "ghost"} onClick={() => setSeriesMode("STANDALONE")}>Отдельная книга</button>
          <button type="button" className={seriesMode === "SERIES" ? "primary" : "ghost"} disabled={!authorId} onClick={() => setSeriesMode("SERIES")}>Книга серии</button>
        </div>
        {seriesMode === "SERIES" && (
          <>
            <label className="field">
              <span>Series Profile</span>
              <select value={seriesId} onChange={(event) => setSeriesId(event.target.value)}>
                <option value="">Выберите серию</option>
                {approvedSeries.map((item) => <option key={item.profile_id} value={item.profile_id}>{item.name}</option>)}
                {seriesProfiles.filter((item) => item.status === "DRAFT").map((item) => <option key={item.profile_id} value={item.profile_id}>{item.name} — черновик</option>)}
              </select>
            </label>
            {selectedSeries?.status === "DRAFT" && (
              <button className="primary" disabled={busy} onClick={() => void approveProfile(selectedSeries.profile_id)}>Утвердить Series Profile</button>
            )}
            <details className="advanced-settings">
              <summary>Создать новую серию</summary>
              <div className="form-grid">
                <label className="field"><span>Название серии</span><input value={seriesName} onChange={(event) => setSeriesName(event.target.value)} /></label>
                <label className="field"><span>Назначение и позиционирование</span><textarea rows={3} value={seriesPurpose} onChange={(event) => setSeriesPurpose(event.target.value)} /></label>
                <label className="field"><span>Планируемые книги — по одной на строке</span><textarea rows={4} value={plannedBooks} onChange={(event) => setPlannedBooks(event.target.value)} /></label>
                <label className="field"><span>Темы будущих книг, которые нельзя расходовать</span><textarea rows={4} value={seriesReservations} onChange={(event) => setSeriesReservations(event.target.value)} /></label>
                <label className="field"><span>Правила уникальности между книгами</span><textarea rows={5} value={seriesUniqueness} onChange={(event) => setSeriesUniqueness(event.target.value)} /></label>
                <label className="field"><span>Что проверять на overlap</span><textarea rows={4} value={seriesExclusions} onChange={(event) => setSeriesExclusions(event.target.value)} placeholder="тезисы\nсцены\nмеханизмы\nисследовательские функции\nметафоры и аналогии" /></label>
              </div>
              <button
                className="ghost"
                disabled={busy || !authorId || seriesName.trim().length === 0}
                onClick={() => void createProfile("SERIES", {
                  series_name: seriesName.trim(),
                  author_profile_id: authorId,
                  purpose_positioning: seriesPurpose.trim(),
                  planned_books: lines(plannedBooks),
                  future_book_reservations: lines(seriesReservations),
                  cross_book_uniqueness_rules: lines(seriesUniqueness),
                  exclusion_dimensions: lines(seriesExclusions),
                  prewriting_overlap_requirements: ["Создать карту уникальности до написания"],
                  whole_book_audit_requirements: ["Провести cross-book audit перед Literary Master"],
                })}
              >
                Создать черновик Series Profile
              </button>
            </details>
          </>
        )}
      </section>

      <section className="planning-step">
        <div className="panel-heading">
          <h4>3. Манера письма</h4>
          <ProfileStatus profile={selectedStyle} />
        </div>
        <label className="field">
          <span>Style Profile</span>
          <select value={styleId} onChange={(event) => setStyleId(event.target.value)} disabled={!authorId}>
            <option value="">Выберите стиль</option>
            {approvedStyles.map((item) => <option key={item.profile_id} value={item.profile_id}>{item.name}</option>)}
            {styles.filter((item) => item.status === "DRAFT").map((item) => <option key={item.profile_id} value={item.profile_id}>{item.name} — черновик</option>)}
          </select>
        </label>
        {selectedStyle?.status === "DRAFT" && (
          <button className="primary" disabled={busy} onClick={() => void approveProfile(selectedStyle.profile_id)}>Утвердить Style Profile</button>
        )}
        <details className="advanced-settings">
          <summary>Создать / настроить Style Profile</summary>
          <div className="form-grid">
            <label className="field"><span>Название стиля</span><input value={styleName} onChange={(event) => setStyleName(event.target.value)} /></label>
            <label className="field"><span>Литературный регистр</span><input value={styleRegister} onChange={(event) => setStyleRegister(event.target.value)} /></label>
            <label className="field"><span>Присутствие автора</span><input value={stylePresence} onChange={(event) => setStylePresence(event.target.value)} /></label>
            <label className="field"><span>Прямота</span><input value={styleDirectness} onChange={(event) => setStyleDirectness(event.target.value)} /></label>
            <label className="field"><span>Ритм предложений и абзацев</span><textarea rows={3} value={styleRhythm} onChange={(event) => setStyleRhythm(event.target.value)} /></label>
            <label className="field"><span>Плотность сцен</span><input value={styleScenes} onChange={(event) => setStyleScenes(event.target.value)} /></label>
            <label className="field"><span>Плотность доказательств</span><input value={styleEvidence} onChange={(event) => setStyleEvidence(event.target.value)} /></label>
            <label className="field"><span>Аналитическая глубина</span><input value={styleDepth} onChange={(event) => setStyleDepth(event.target.value)} /></label>
            <label className="field"><span>Ирония / юмор</span><input value={styleIrony} onChange={(event) => setStyleIrony(event.target.value)} /></label>
            <label className="field"><span>Эмоциональная температура</span><input value={styleTemperature} onChange={(event) => setStyleTemperature(event.target.value)} /></label>
            <label className="field"><span>Практичность</span><input value={stylePractical} onChange={(event) => setStylePractical(event.target.value)} /></label>
            <label className="field"><span>Уровень терминологии</span><input value={styleTerminology} onChange={(event) => setStyleTerminology(event.target.value)} /></label>
            <label className="field"><span>Запрещённые паттерны — по одному на строке</span><textarea rows={4} value={styleProhibitions} onChange={(event) => setStyleProhibitions(event.target.value)} /></label>
            <label className="field"><span>Benchmark этого стиля — необязательно</span><textarea rows={5} value={styleBenchmark} onChange={(event) => setStyleBenchmark(event.target.value)} /></label>
          </div>
          <button
            className="ghost"
            disabled={busy || !authorId || styleName.trim().length === 0}
            onClick={() => void createProfile("STYLE", {
              style_name: styleName.trim(),
              author_profile_id: authorId,
              literary_register: styleRegister.trim(),
              authorial_presence: stylePresence.trim(),
              directness: styleDirectness.trim(),
              sentence_paragraph_rhythm: styleRhythm.trim(),
              scene_density: styleScenes.trim(),
              evidence_density: styleEvidence.trim(),
              analytical_depth: styleDepth.trim(),
              irony_humor: styleIrony.trim(),
              emotional_temperature: styleTemperature.trim(),
              practical_instruction_intensity: stylePractical.trim(),
              terminology_level: styleTerminology.trim(),
              prohibited_patterns: lines(styleProhibitions),
              benchmark_excerpts: styleBenchmark.trim() ? [styleBenchmark.trim()] : [],
            })}
          >
            Создать черновик Style Profile
          </button>
        </details>
        <p className="muted">
          Следующий slice добавит сравнимые сгенерированные примеры: один и тот же brief в нескольких
          Style Profiles до утверждения манеры письма.
        </p>
      </section>

      <section className="planning-step">
        <h4>4. Примерный объём книги</h4>
        <p className="muted">
          Единица — знаки с пробелами. Это ориентир для архитектуры и контроля плотности, а не квота,
          которую разрешено добивать водой.
        </p>
        <div className="form-grid">
          <label className="field"><span>Цель, знаков с пробелами</span><input inputMode="numeric" value={targetCharacters} onChange={(event) => setTargetCharacters(event.target.value)} /></label>
          <label className="field"><span>Минимум — необязательно</span><input inputMode="numeric" value={minCharacters} onChange={(event) => setMinCharacters(event.target.value)} /></label>
          <label className="field"><span>Максимум — необязательно</span><input inputMode="numeric" value={maxCharacters} onChange={(event) => setMaxCharacters(event.target.value)} /></label>
        </div>
        {context?.target_characters && (
          <p className="selected-topic-summary">
            Сохранено: {context.target_characters.toLocaleString("ru-RU")} знаков с пробелами
            {context.min_characters ? ` · минимум ${context.min_characters.toLocaleString("ru-RU")}` : ""}
            {context.max_characters ? ` · максимум ${context.max_characters.toLocaleString("ru-RU")}` : ""}
          </p>
        )}
      </section>

      <div className="actions">
        <button className="primary" disabled={busy || !canSave} onClick={() => void saveContext()}>
          {busy ? "Сохраняю…" : "Сохранить контекст книги"}
        </button>
      </div>
      {!canSave && (
        <small className="muted">
          Для сохранения нужны утверждённые Author Profile и Style Profile, корректный объём и — если
          выбрана серия — утверждённый Series Profile.
        </small>
      )}
      {error && <div className="alert inline-alert">{error}</div>}
    </section>
  );
}
