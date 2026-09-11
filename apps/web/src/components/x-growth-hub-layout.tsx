'use client';
import {
  IconHome,
  IconChartBar,
  IconUsers,
  IconTarget,
  IconSearch,
  IconCalendar,
  IconClock,
  IconSparkles,
  IconCopy,
  IconUserPlus
} from '@tabler/icons-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const navItems = [
  { title: 'Home', href: '/', icon: IconHome },
  { title: 'Analyze', href: '/analyze', icon: IconSearch },
  { title: 'Compare', href: '/compare', icon: IconUsers },
  { title: 'My Account', href: '/my-account', icon: IconTarget },
  { title: 'Calendar', href: '/tools/calendar', icon: IconCalendar },
  { title: 'Best Time', href: '/tools/best-time', icon: IconClock },
  { title: 'Patterns', href: '/tools/patterns', icon: IconSparkles },
  { title: 'Cloner', href: '/tools/clone', icon: IconCopy },
  { title: 'Scraper', href: '/tools/scraper', icon: IconUserPlus },
  { title: 'Dashboard', href: '/dashboard/overview', icon: IconChartBar }
];

export default function XGrowthHubLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className='min-h-screen bg-background'>
      <header className='border-b bg-background/95 backdrop-blur'>
        <div className='container mx-auto flex h-14 items-center justify-between'>
          <Link href='/' className='font-bold text-xl'>
            X Growth Hub
          </Link>
          <nav className='flex items-center space-x-2'>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                    pathname === item.href
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
