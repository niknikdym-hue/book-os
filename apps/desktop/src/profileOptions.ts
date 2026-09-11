export type NamedProfile = {
  profile_id: string;
  name: string;
  updated_at: string;
};

/**
 * A person should appear once in selection controls even if older profile
 * snapshots with the same displayed name are retained for provenance.
 */
export function uniqueProfileNames<T extends NamedProfile>(profiles: T[]): T[] {
  const byName = new Map<string, T>();
  for (const profile of profiles) {
    const key = profile.name.trim().toLocaleLowerCase("ru-RU");
    const current = byName.get(key);
    if (
      !current ||
      profile.updated_at > current.updated_at ||
      (profile.updated_at === current.updated_at && profile.profile_id > current.profile_id)
    ) {
      byName.set(key, profile);
    }
  }
  return [...byName.values()].sort((left, right) => left.name.localeCompare(right.name, "ru"));
}
