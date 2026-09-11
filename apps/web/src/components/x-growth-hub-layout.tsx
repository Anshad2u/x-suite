'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  IconLayoutDashboard,
  IconUsers,
  IconFolder,
  IconActivity,
  IconSearch,
  IconUsersGroup,
  IconUserCircle,
  IconCalendar,
  IconClock,
  IconSparkles,
  IconCopy,
  IconUserPlus,
  IconCloudDownload,
  IconLogout,
  IconBrandX
} from '@tabler/icons-react';
import { cn } from '@/lib/utils';
import ThemeToggle from '@/components/theme-toggle';

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    label: 'Overview',
    items: [
      { title: 'Dashboard', href: '/', icon: IconLayoutDashboard },
      { title: 'Followers', href: '/followers', icon: IconUsers },
      { title: 'Groups', href: '/groups', icon: IconFolder },
      { title: 'Activity', href: '/activity', icon: IconActivity }
    ]
  },
  {
    label: 'Growth Tools',
    items: [
      { title: 'Analyze Profile', href: '/analyze', icon: IconSearch },
      { title: 'Compare Accounts', href: '/compare', icon: IconUsersGroup },
      { title: 'My Account', href: '/my-account', icon: IconUserCircle },
      { title: 'Content Calendar', href: '/tools/calendar', icon: IconCalendar },
      { title: 'Best Time to Post', href: '/tools/best-time', icon: IconClock },
      { title: 'Pattern Recognition', href: '/tools/patterns', icon: IconSparkles },
      { title: 'Tweet Cloner', href: '/tools/clone', icon: IconCopy },
      { title: 'Growth Scraper', href: '/tools/scraper', icon: IconUserPlus },
      { title: 'Scrape Data', href: '/scrape', icon: IconCloudDownload }
    ]
  }
];

function isActive(pathname: string, href: string): boolean {
  if (href === '/') return pathname === '/';
  return pathname === href || pathname.startsWith(href + '/');
}

export default function XGrowthHubLayout({
  children,
  userEmail
}: {
  children: React.ReactNode;
  userEmail?: string | null;
}) {
  const pathname = usePathname();

  // The login screen renders without the admin chrome.
  if (pathname === '/login') {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-zinc-900 text-zinc-300">
        <div className="flex h-14 items-center gap-2 border-b border-white/10 px-5">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <IconBrandX className="h-5 w-5" />
          </span>
          <span className="text-lg font-semibold text-white">X Suite</span>
        </div>

        <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
          {navGroups.map((group) => (
            <div key={group.label}>
              <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
                {group.label}
              </p>
              <ul className="space-y-1">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(pathname, item.href);
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className={cn(
                          'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                          active
                            ? 'bg-primary/15 text-white'
                            : 'text-zinc-400 hover:bg-white/5 hover:text-white'
                        )}
                      >
                        <Icon className="h-4 w-4 shrink-0" />
                        {item.title}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        <div className="border-t border-white/10 p-3 text-xs text-zinc-500">
          X Growth &amp; Autopilot Console
        </div>
      </aside>

      {/* Top bar */}
      <header className="fixed inset-x-0 left-64 z-30 flex h-14 items-center justify-between border-b bg-background/95 px-6 backdrop-blur">
        <div className="text-sm font-medium text-muted-foreground">
          Admin Console
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden text-sm text-muted-foreground sm:inline">
            {userEmail ?? 'signed in'}
          </span>
          <ThemeToggle />
          <form method="post" action="/api/auth/logout">
            <button
              type="submit"
              className="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium transition hover:bg-muted"
            >
              <IconLogout className="h-4 w-4" />
              Log out
            </button>
          </form>
        </div>
      </header>

      {/* Content */}
      <main className="ml-64 mt-14 p-6 md:p-8">
        <div className="mx-auto max-w-7xl">{children}</div>
      </main>
    </div>
  );
}
