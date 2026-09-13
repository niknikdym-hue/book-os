import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { SeriesStudio } from "./SeriesStudio";

vi.mock("./api", () => ({
  coreApi: vi.fn(async (method: string, path: string) => {
    if (method === "GET" && path === "/api/context/profiles") {
      return [
        {
          profile_id: "01JAUTHOR0000000000000000",
          kind: "AUTHOR",
          name: "Елена Дым",
          status: "APPROVED",
          content: {},
          updated_at: "2026-09-01T10:00:00Z",
        },
        {
          profile_id: "01JAUTHORNEW0000000000000",
          kind: "AUTHOR",
          name: "  Елена Дым ",
          status: "APPROVED",
          content: {},
          updated_at: "2026-09-10T10:00:00Z",
        },
      ];
    }
    if (method === "GET" && path === "/api/series/workspaces") {
      return [
        {
          series_profile_id: "01JSERIES0000000000000000",
          name: "Секреты продвижения услуг",
          profile_status: "APPROVED",
          profile_revision: 2,
          territory: "Самостоятельные практические книги",
          books: [
            {
              book_id: "01JBOOK000000000000000000",
              ordinal: 1,
              title: "Первая книга",
              unique_idea: "Отдельный результат читателю",
              status: "DEFINITION",
              source_kind: "BOOK_OS",
              origin_kind: "CURRENT_REWRITTEN",
              lifecycle: "COMPLETED",
              legacy_content_allowed: false,
              current_corpus_eligible: true,
              definition_ready: true,
              passport_hash: "passport-hash",
              passport_approved: true,
              imported_sources: [
                {
                  source_id: "01JSOURCE0000000000000000",
                  filename: "original.docx",
                  format: "DOCX",
                  analysis_status: "COMPLETE",
                  analysis: {
                    characters: 1200,
                    headings: ["Глава 1"],
                    tables: 1,
                    visuals: 0,
                  },
                },
              ],
            },
            {
              book_id: "01JBOOKLEGACY000000000000",
              ordinal: 2,
              title: "Секреты продвижения услуг психолога в Яндекс Директ",
              unique_idea: "Новая самостоятельная книга о продвижении практики психолога",
              status: "IDEA",
              source_kind: "PLANNED",
              origin_kind: "LEGACY_TITLE_ONLY",
              lifecycle: "PLANNED",
              legacy_content_allowed: false,
              current_corpus_eligible: false,
              definition_ready: false,
              passport_hash: "legacy-passport",
              passport_approved: false,
              imported_sources: [],
            },
            {
              book_id: "01JBOOKNEW000000000000000",
              ordinal: 5,
              title: "Как продавать услуги компаниям: от первого контакта до договора",
              unique_idea: "Решение о покупке внутри компании",
              status: "IDEA",
              source_kind: "PLANNED",
              origin_kind: "NEW",
              lifecycle: "PLANNED",
              legacy_content_allowed: false,
              current_corpus_eligible: false,
              definition_ready: false,
              passport_hash: "new-passport",
              passport_approved: false,
              imported_sources: [],
            },
          ],
          map: null,
        },
      ];
    }
    if (method === "GET" && path === "/api/series/01JSERIES0000000000000000/costs") {
      return {
        series_profile_id: "01JSERIES0000000000000000",
        series_confirmed_cost_usd: 0.42,
        books_confirmed_cost_usd: 2.4,
        total_confirmed_cost_usd: 2.82,
        total_estimated_cost_usd: 6.17,
        total_reserved_cost_usd: 0.5,
        total_unknown_cost_usd: 0.25,
        current_books_forecast_low_usd: null,
        current_books_forecast_high_usd: null,
        production_forecast_low_usd: null,
        production_forecast_high_usd: null,
        production_forecast_status: "INSUFFICIENT_DATA",
        books: [
          {
            book_id: "01JBOOK000000000000000000",
            title: "Первая книга",
            confirmed_cost_usd: 2.4,
            estimated_cost_usd: 5.75,
            reserved_cost_usd: 0.5,
            unknown_cost_usd: 0.25,
            runtime_status: "RUNNING",
            forecast_total_low_usd: null,
            forecast_total_high_usd: null,
          },
        ],
        future_books: [],
        operations: [],
      };
    }
    if (method === "POST" && path.endsWith("/start-fresh")) {
      return { book_id: "01JFRESHBOOK0000000000000" };
    }
    return null;
  }),
}));

afterEach(() => cleanup());

it("offers three persisted series scenarios and keeps Auto as the default", async () => {
  render(<SeriesStudio />);
  fireEvent.click(screen.getByRole("button", { name: "Серии" }));

  expect(await screen.findByRole("button", { name: "Создать серию с нуля" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Добавить внешнюю серию" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Продолжить в BOOK OS" })).toBeInTheDocument();
  expect(screen.getByLabelText("Модель")).toHaveValue("AUTO");
  expect(screen.getAllByRole("option", { name: /Елена Дым/ })).toHaveLength(1);

  fireEvent.click(screen.getByRole("button", { name: "Добавить внешнюю серию" }));
  expect(screen.getByLabelText("Права на файл")).toBeInTheDocument();
  expect(screen.getByText(/импорт не разрешает переписывать или публиковать/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "+ Добавить ещё книгу и файл" }));
  expect(screen.getByText("Книга 2")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Убрать книгу из импорта" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Продолжить в BOOK OS" }));
  expect(await screen.findByText("Секреты продвижения услуг")).toBeInTheDocument();
  expect(screen.getByText("Потрачено на серию $2.82")).toBeInTheDocument();
  expect(screen.getByText("Прогноз всей серии: пока недостаточно данных")).toBeInTheDocument();
  const sections = screen.getByRole("navigation", { name: "Разделы серии «Секреты продвижения услуг»" });
  fireEvent.click(within(sections).getByRole("button", { name: "Правила серии" }));
  expect(screen.getByText(/Карта различий: не построена/)).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Продолжить серию" }),
  ).toBeInTheDocument();
  fireEvent.click(within(sections).getByRole("button", { name: "Книги" }));
  expect(screen.getAllByRole("button", { name: "Начать новую версию" })).toHaveLength(2);
  expect(screen.getByRole("button", { name: "Начать книгу" })).toBeInTheDocument();
  const archiveActions = screen.getAllByRole("button", { name: "Архивировать", hidden: true });
  expect(archiveActions).toHaveLength(3);
  expect(archiveActions.every((item) => item.closest("details.series-book-more"))).toBe(true);
  expect(
    screen.getByRole("button", { name: "Удалить сохранённый оригинал" }),
  ).toBeInTheDocument();
});

it("starts a legacy-title-only entry as a fresh project without premature approval", async () => {
  const onOpenBook = vi.fn();
  render(<SeriesStudio onOpenBook={onOpenBook} />);
  fireEvent.click(screen.getByRole("button", { name: "Серии" }));
  fireEvent.click(await screen.findByRole("button", { name: "Продолжить в BOOK OS" }));
  const sections = screen.getByRole("navigation", {
    name: "Разделы серии «Секреты продвижения услуг»",
  });
  fireEvent.click(within(sections).getByRole("button", { name: "Книги" }));

  const title = screen
    .getAllByText("Секреты продвижения услуг психолога в Яндекс Директ")
    .find((item) => item.closest("li"));
  expect(title).toBeDefined();
  const card = title!.closest("li");
  expect(card).not.toBeNull();
  expect(within(card!).queryByRole("button", { name: "Утвердить паспорт книги" })).toBeNull();
  fireEvent.click(within(card!).getByRole("button", { name: "Начать новую версию" }));

  await waitFor(() => expect(onOpenBook).toHaveBeenCalledWith("01JFRESHBOOK0000000000000"));
});

it("asks for one bounded authorization without forcing the author into Advanced", async () => {
  render(<SeriesStudio embedded />);
  const author = await screen.findByLabelText("Автор / псевдоним");
  const authorId = (author as HTMLSelectElement).options[1].value;
  fireEvent.change(author, { target: { value: authorId } });
  fireEvent.change(screen.getByLabelText("Что это за серия?"), {
    target: { value: "Практическая серия о системном развитии профессиональных услуг." },
  });

  const create = screen.getByRole("button", { name: "Предложить серию" });
  expect(create).toBeEnabled();
  fireEvent.click(create);

  expect(screen.getByRole("dialog", { name: "Разрешить создание концепции серии" })).toBeInTheDocument();
  expect(screen.getByText("Максимальный расход этого шага: до $1.50")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Продолжить" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "Изменить лимит" })).toBeInTheDocument();
});
