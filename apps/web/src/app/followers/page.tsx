import { IconPlus, IconMinus, IconUsers } from '@tabler/icons-react';
import { listFollowers, listGroupNames } from '@/lib/server/queries';
import { assignFollowerAction, removeFollowerAction } from './actions';

type SP = { group?: string; q?: string };

export default async function FollowersPage({
  searchParams
}: {
  searchParams: Promise<SP>;
}) {
  const sp = await searchParams;
  const group = sp.group ?? 'all';
  const q = sp.q ?? '';
  const [followers, groups] = await Promise.all([
    listFollowers({ group, search: q }),
    listGroupNames()
  ]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">All Followers</h1>
        <p className="mt-1 text-muted-foreground">
          Assign followers to groups. Group membership drives which accounts get scraped
          and which sources the autopilot curates from.
        </p>
      </div>

      <form method="get" className="flex flex-wrap items-end gap-3 rounded-xl border bg-card p-4">
        <div>
          <label className="mb-1 block text-sm text-muted-foreground">Group</label>
          <select
            name="group"
            defaultValue={group}
            className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">All followers</option>
            {groups.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1 min-w-56">
          <label className="mb-1 block text-sm text-muted-foreground">Search</label>
          <input
            name="q"
            defaultValue={q}
            placeholder="username or name..."
            className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <button
          type="submit"
          className="h-10 rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
        >
          Filter
        </button>
      </form>

      <div className="rounded-xl border bg-card">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h2 className="flex items-center gap-2 font-semibold">
            <IconUsers className="h-5 w-5" /> Followers
          </h2>
          <span className="text-sm text-muted-foreground">{followers.length} shown</span>
        </div>
        <div className="p-2 sm:p-5">
          {followers.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No followers match. Try a different filter, or scrape data first.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 pr-4 font-medium">Username</th>
                    <th className="py-2 pr-4 font-medium">Name</th>
                    <th className="py-2 pr-4 text-right font-medium">Followers</th>
                    <th className="py-2 pr-4 font-medium">Groups</th>
                    <th className="py-2 font-medium">Assign</th>
                  </tr>
                </thead>
                <tbody>
                  {followers.map((f) => {
                    const current = (f.groups || '')
                      .split(',')
                      .map((s) => s.trim())
                      .filter(Boolean);
                    return (
                      <tr key={f.id} className="border-b last:border-0 align-top">
                        <td className="py-3 pr-4">
                          <a
                            href={`https://x.com/${f.username}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-blue-500 hover:underline"
                          >
                            @{f.username}
                          </a>
                          {f.verified && (
                            <span className="ml-1 rounded border px-1 text-xs">verified</span>
                          )}
                        </td>
                        <td className="py-3 pr-4 text-muted-foreground">{f.display_name || '—'}</td>
                        <td className="py-3 pr-4 text-right font-mono">{f.followers_count.toLocaleString()}</td>
                        <td className="py-3 pr-4">
                          <div className="flex flex-wrap gap-1">
                            {current.length === 0 ? (
                              <span className="text-xs text-muted-foreground">none</span>
                            ) : (
                              current.map((g) => (
                                <span
                                  key={g}
                                  className="inline-flex items-center gap-1 rounded bg-muted px-1.5 py-0.5 text-xs"
                                >
                                  {g}
                                  <form action={removeFollowerAction} className="inline">
                                    <input type="hidden" name="username" value={f.username} />
                                    <input type="hidden" name="group" value={g} />
                                    <button
                                      type="submit"
                                      title={`Remove from ${g}`}
                                      className="text-muted-foreground hover:text-destructive"
                                    >
                                      <IconMinus className="h-3 w-3" />
                                    </button>
                                  </form>
                                </span>
                              ))
                            )}
                          </div>
                        </td>
                        <td className="py-3">
                          {groups.length === 0 ? (
                            <span className="text-xs text-muted-foreground">Create a group first</span>
                          ) : (
                            <form action={assignFollowerAction} className="flex items-center gap-2">
                              <input type="hidden" name="username" value={f.username} />
                              <select
                                name="group"
                                defaultValue={groups[0]}
                                className="h-8 rounded-md border bg-background px-2 text-xs outline-none"
                              >
                                {groups.map((g) => (
                                  <option key={g} value={g}>
                                    {g}
                                  </option>
                                ))}
                              </select>
                              <button
                                type="submit"
                                title="Add to group"
                                className="inline-flex h-8 w-8 items-center justify-center rounded-md border transition hover:bg-muted"
                              >
                                <IconPlus className="h-4 w-4" />
                              </button>
                            </form>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
