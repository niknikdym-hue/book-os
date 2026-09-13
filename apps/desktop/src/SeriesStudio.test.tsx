import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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
        },
      ];
    }
    if (method === "GET" && path === "/api/series/workspaces") {
      return [
        {
          series_profile_id: "01JSERIES0000000000000000",
          name: "Секреты сильной работы",
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
            },
          ],
          map: null,
        },
      ];
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

  fireEvent.click(screen.getByRole("button", { name: "Добавить внешнюю серию" }));
  expect(screen.getByLabelText("Права на файл")).toBeInTheDocument();
  expect(screen.getByText(/импорт не разрешает переписывать или публиковать/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "+ Добавить ещё книгу и файл" }));
  expect(screen.getByText("Книга 2")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Убрать книгу из импорта" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Продолжить в BOOK OS" }));
  expect(await screen.findByText("Секреты сильной работы")).toBeInTheDocument();
  expect(screen.getByText(/Карта различий: не построена/)).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Загрузить «Секреты продвижения услуг»" }),
  ).toBeInTheDocument();
});
