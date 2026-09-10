import { expect, it } from "vitest";

import { uniqueProfileNames } from "./profileOptions";

it("shows one current approved profile for a repeated author name", () => {
  const options = uniqueProfileNames([
    { profile_id: "01OLD", name: "Елена Дым", updated_at: "2026-09-01T10:00:00Z" },
    { profile_id: "01NEW", name: "  Елена Дым ", updated_at: "2026-09-10T10:00:00Z" },
    { profile_id: "01OTHER", name: "Елена Дилон", updated_at: "2026-09-10T10:00:00Z" },
  ]);

  expect(options).toEqual([
    { profile_id: "01NEW", name: "  Елена Дым ", updated_at: "2026-09-10T10:00:00Z" },
    { profile_id: "01OTHER", name: "Елена Дилон", updated_at: "2026-09-10T10:00:00Z" },
  ]);
});
