'use client';
import {
  IconHome,
  IconUsers,
  IconTarget,
  IconSearch,
  IconCalendar,
  IconClock,
  IconSparkles,
  IconCopy,
  IconUserPlus,
  IconCloudDownload,
  IconFolder,
  IconAddressBook,
  IconActivity
} from '@tabler/icons-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const navItems = [
  // Growth analysis
  { title: 'Home', href: '/', icon: IconHome },
  { title: 'Analyze', href: '/analyze', icon: IconSearch },
  { title: 'Compare', href: '/compare', icon: IconUsers },
  { title: 'My Account', href: '/my-account', icon: IconTarget },
  { title: 'Calendar', href: '/tools/calendar', icon: IconCalendar },
  { title: 'Best Time', href: '/tools/best-time', icon: IconClock },
  { title: 'Patterns', href: '/tools/patterns', icon: IconSparkles },
  { title: 'Cloner', href: '/tools/clone', icon: IconCopy },
  // Account management (ported from the retired Vue dashboard)
  { title: 'Scrape', href: '/scrape', icon: IconCloudDownload },
  { title: 'Groups', href: '/groups', icon: IconFolder },
  { title: 'Followers', href: '/followers', icon: IconAddressBook },
  { title: 'Activity', href: '/activity', icon: IconActivity },
  { title: 'Scraper', href: '/tools/scraper', icon: IconUserPlus }
];

export default function XGrowthHubLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className='min-h-screen bg-background'>
      <header className='border-b bg-background/95 backdrop-blur'>
        <div className='container mx-auto flex min-h-14 flex-wrap items-center justify-between gap-y-1 py-1'>
          <Link href='/' className='font-bold text-xl'>
            X Growth Hub
          </Link>
          <nav className='flex flex-wrap items-center gap-1'>
            {navItems.map((item) => {
              const Icon = item.icon;
              const active =
                pathname === item.href ||
                (item.href !== '/' && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors',
                    active
                      ? 'bg-muted text-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  )}
                >
                  <Icon className='h-4 w-4' />
                  {item.title}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      {children}
    </div>
  );
}
