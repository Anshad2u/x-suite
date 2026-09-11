import { listGroups } from '@/lib/server/queries';
import { createGroupAction, deleteGroupAction } from './actions';
import { IconPlus, IconTrash } from '@tabler/icons-react';

export default async function GroupsPage() {
  const groups = await listGroups();

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Groups</h1>
        <p className="mt-1 text-muted-foreground">
          Group followers by topic. Group membership drives what the autopilot scrapes and
          curates from.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Create */}
        <div className="rounded-xl border bg-card p-6">
          <h2 className="mb-4 font-semibold">Create group</h2>
          <form action={createGroupAction} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm text-muted-foreground">Name</label>
              <input
                name="name"
                required
                placeholder="e.g. Tech &amp; AI"
                className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-muted-foreground">Description</label>
              <input
                name="description"
                placeholder="optional"
                className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-muted-foreground">Color</label>
              <input
                type="color"
                name="color"
                defaultValue="#6366f1"
                className="h-10 w-16 rounded-md border bg-transparent"
              />
            </div>
            <button
              type="submit"
              className="flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
            >
              <IconPlus className="h-4 w-4" /> Create
            </button>
          </form>
        </div>

        {/* List */}
        <div className="rounded-xl border bg-card lg:col-span-2">
          <div className="border-b px-5 py-4">
            <h2 className="font-semibold">Groups overview</h2>
          </div>
          <div className="p-5">
            {groups.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                No groups yet. Create one on the left.
              </p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 font-medium">Group</th>
                    <th className="py-2 text-right font-medium">Members</th>
                    <th className="py-2 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {groups.map((g) => (
                    <tr key={g.name} className="border-b last:border-0">
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <span
                            className="inline-block h-3 w-3 rounded-full"
                            style={{ backgroundColor: g.color }}
                          />
                          <span className="font-medium">{g.name}</span>
                        </div>
                        {g.description && (
                          <p className="text-xs text-muted-foreground">{g.description}</p>
                        )}
                      </td>
                      <td className="py-3 text-right">
                        <span className="rounded bg-muted px-2 py-0.5 text-xs">{g.member_count}</span>
                      </td>
                      <td className="py-3 text-right">
                        <form action={deleteGroupAction}>
                          <input type="hidden" name="name" value={g.name} />
                          <button
                            type="submit"
                            title={`Delete ${g.name}`}
                            className="inline-flex h-8 w-8 items-center justify-center rounded-md border transition hover:bg-destructive/10 hover:text-destructive"
                          >
                            <IconTrash className="h-4 w-4" />
                          </button>
                        </form>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
