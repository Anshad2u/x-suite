import { NavGroup } from '@/types';

export const navGroups: NavGroup[] = [
  {
    label: 'X Growth Hub',
    items: [
      {
        title: 'Home',
        url: '/',
        icon: 'logo',
        isActive: false,
        items: []
      },
      {
        title: 'Analyze Profile',
        url: '/analyze',
        icon: 'search',
        isActive: false,
        items: []
      },
      {
        title: 'Compare Accounts',
        url: '/compare',
        icon: 'teams',
        isActive: false,
        items: []
      },
      {
        title: 'My Account Audit',
        url: '/my-account',
        icon: 'user',
        isActive: false,
        items: []
      }
    ]
  },
  {
    label: 'Growth Tools',
    items: [
      {
        title: 'Content Calendar',
        url: '/tools/calendar',
        icon: 'calendar',
        isActive: false,
        items: []
      },
      {
        title: 'Best Time to Post',
        url: '/tools/best-time',
        icon: 'clock',
        isActive: false,
        items: []
      },
      {
        title: 'Pattern Recognition',
        url: '/tools/patterns',
        icon: 'sparkles',
        isActive: false,
        items: []
      },
      {
        title: 'Tweet Cloner',
        url: '/tools/clone',
        icon: 'edit',
        isActive: false,
        items: []
      },
      {
        title: 'Growth Scraper',
        url: '/tools/scraper',
        icon: 'teams',
        isActive: false,
        items: []
      }
    ]
  },
  {
    label: 'Dashboard',
    items: [
      {
        title: 'Overview',
        url: '/dashboard/overview',
        icon: 'dashboard',
        isActive: false,
        items: []
      },
      {
        title: 'Kanban Board',
        url: '/dashboard/kanban',
        icon: 'product',
        isActive: false,
        items: []
      },
      {
        title: 'Notifications',
        url: '/dashboard/notifications',
        icon: 'notification',
        isActive: false,
        items: []
      }
    ]
  }
];
