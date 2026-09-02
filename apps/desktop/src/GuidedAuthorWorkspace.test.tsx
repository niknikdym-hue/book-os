import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { AuthorJourney } from "./AuthorJourney";
import { BookTopicPicker, type BusinessSubtype } from "./BookTopicPicker";
import type { ProjectView } from "./types";

it("показывает только реально доступные темы кликабельными", () => {
  const selectPrimary = vi.fn();
  render(
    <BookTopicPicker
      primarySubtype="Strategy"
      secondarySubtype=""
      onPrimarySubtype={selectPrimary}
      onSecondarySubtype={vi.fn()}
    />,
  );

  const startup = screen.getByRole("button", { name: /Стартапы и создание бизнеса/ });
  expect(startup).toBeEnabled();
  fireEvent.click(startup);
  expect(selectPrimary).toHaveBeenCalledWith("Entrepreneurship" satisfies BusinessSubtype);

  expect(screen.getByRole("button", { name: /Психология и саморазвитие/ })).toBeDisabled();
  expect(screen.getByRole("button", { name: /Тайм-менеджмент/ })).toBeDisabled();
  expect(screen.getByText("В разработке")).toBeInTheDocument();
  expect(screen.getAllByText("Пока недоступно").length).toBeGreaterThan(0);
});

it("объясняет новый проект пошагово и показывает встроенную помощь", () => {
  const start = vi.fn();
  render(<AuthorJourney project={null} onStartBook={start} />);

  expect(screen.getByRole("heading", { name: "Создание книги шаг за шагом" })).toBeInTheDocument();
  expect(screen.getByText("Тема и идея")).toBeInTheDocument();
  expect(screen.getByText("Literary Master")).toBeInTheDocument();
  expect(screen.getByText("Как пользоваться BOOK OS")).toBeInTheDocument();
  expect(screen.getByText(/Нажмите «Новая книга»/)).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Начать новую книгу" }));
  expect(start).toHaveBeenCalledTimes(1);
});

it("ведёт автора к архитектуре только после утверждения контракта книги", () => {
  const project: ProjectView = {
    book_id: "01JTESTBOOK000000000000000",
    working_title: "Проверка маршрута",
    mode: "BOOK_FROM_ZERO",
    domain: "BUSINESS_NONFICTION",
    primary_subtype: "Entrepreneurship",
    secondary_subtype: null,
    profile_version: "business-nonfiction-v0.1",
    workflow_stage: "ARCHITECTURE",
    book_contract: {
      entity_id: "contract",
      revision_id: "contract-rev",
      status: "APPROVED",
      authority_revision_id: "contract-rev",
      authority_status: "APPROVED",
      content: {},
    },
    architecture: null,
    chapters: [],
  };

  render(<AuthorJourney project={project} onStartBook={vi.fn()} />);

  expect(screen.getByText(/После утверждения контракта попросите Planner предложить архитектуру/)).toBeInTheDocument();
  const architecture = screen.getByText("Архитектура").closest("li");
  expect(architecture).toHaveClass("current");
  const contract = screen.getByText("Контракт книги").closest("li");
  expect(contract).toHaveClass("done");
});
