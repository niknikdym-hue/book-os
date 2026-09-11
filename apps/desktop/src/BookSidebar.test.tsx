import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { coreApi } from "./api";
import { BookSidebar } from "./BookSidebar";
import type { ProjectSummary } from "./types";

vi.mock("./api", () => ({ coreApi: vi.fn() }));

const apiMock = vi.mocked(coreApi);

const book: ProjectSummary = {
  book_id: "01JBOOK000000000000000000",
  working_title: "Книга для управления",
  primary_subtype: "Strategy",
  secondary_subtype: null,
  workflow_stage: "BOOK DEFINITION",
};

afterEach(() => {
  cleanup();
  apiMock.mockReset();
});

it("переносит активную книгу в библиотеку через корзину", async () => {
  apiMock.mockImplementation(async (method, path) => {
    if (method === "GET" && path === "/api/library") return [];
    if (method === "POST" && path.endsWith("/archive")) return book;
    throw new Error(`unexpected request: ${method} ${path}`);
  });
  const changed = vi.fn();

  render(
    <BookSidebar
      projects={[book]}
      activeBookId={book.book_id}
      busy={false}
      onNew={() => undefined}
      onOpen={() => undefined}
      onProjectListChanged={changed}
      stageLabel={(value) => value}
    />,
  );

  fireEvent.click(await screen.findByRole("button", { name: "Управление книгой «Книга для управления»" }));
  fireEvent.click(screen.getByRole("button", { name: "Перенести в библиотеку" }));

  await waitFor(() =>
    expect(apiMock).toHaveBeenCalledWith("POST", `/api/projects/${book.book_id}/archive`),
  );
  expect(changed).toHaveBeenCalledWith(book.book_id);
});

it("требует второй шаг перед полным удалением", async () => {
  apiMock.mockImplementation(async (method, path) => {
    if (method === "GET" && path === "/api/library") return [];
    if (method === "DELETE" && path === `/api/projects/${book.book_id}`) {
      return { deleted: true, book_id: book.book_id };
    }
    throw new Error(`unexpected request: ${method} ${path}`);
  });

  render(
    <BookSidebar
      projects={[book]}
      activeBookId={book.book_id}
      busy={false}
      onNew={() => undefined}
      onOpen={() => undefined}
      onProjectListChanged={() => undefined}
      stageLabel={(value) => value}
    />,
  );

  fireEvent.click(await screen.findByRole("button", { name: "Управление книгой «Книга для управления»" }));
  fireEvent.click(screen.getByRole("button", { name: "Удалить навсегда" }));
  expect(apiMock).not.toHaveBeenCalledWith("DELETE", expect.any(String));

  fireEvent.click(screen.getByRole("button", { name: "Да, удалить навсегда" }));
  await waitFor(() =>
    expect(apiMock).toHaveBeenCalledWith("DELETE", `/api/projects/${book.book_id}`),
  );
});
